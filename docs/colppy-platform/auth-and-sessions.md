# Auth and Sessions

## Overview

Colppy uses **two concurrent authentication systems** that operate in parallel:

| System | Purpose | Token type | Used for API validation |
|--------|---------|------------|------------------------|
| **FusionAuth** | Identity management (login, registration, password reset) | JWT (`token`, `refreshToken`) | **No** |
| **Legacy Frontera** | Session lifecycle for all Frontera API calls | MD5 `claveSesion` in `usuario_sesion` table | **Yes** |

- FusionAuth is integrated through `svc_settings` (NestJS) and optionally through `ApiGatewayConnector` in the PHP backend
- Every Frontera API call validates against the `usuario_sesion` table -- FusionAuth JWTs are never checked
- See [Backend Architecture](backend-architecture.md) for the svc_settings and Frontera layer relationship

---

## Login Flow Sequence

```
 Browser (MFE)             svc_settings             FusionAuth           Frontera (service.php)        DB (usuario_sesion)
      |                        |                        |                        |                        |
      |-- POST /login -------->|                        |                        |                        |
      |   {email, password}    |                        |                        |                        |
      |   (password is         |                        |                        |                        |
      |    AES-encrypted)      |                        |                        |                        |
      |                        |-- AES.decrypt -------->|                        |                        |
      |                        |   (SECRET_KEY)         |                        |                        |
      |                        |                        |                        |                        |
      |                        |-- POST /api/login ---->|                        |                        |
      |                        |   {loginId, password,  |                        |                        |
      |                        |    applicationId}      |                        |                        |
      |                        |<-- JWT token ----------|                        |                        |
      |                        |                        |                        |                        |
      |                        |-- POST service.php ----|----------------------->|                        |
      |                        |   {iniciar_colppy,     |                        |                        |
      |                        |    MD5(password),      |                        |                        |
      |                        |    fusionAuth=1}       |                        |                        |
      |                        |                        |                        |-- INSERT session ----->|
      |                        |                        |                        |   (claveSesion=MD5())  |
      |                        |                        |                        |<-- claveSesion --------|
      |                        |<-- claveSesion + tokens-|----------------------|                        |
      |                        |                        |                        |                        |
      |<-- FusionAuth JWT -----|                        |                        |                        |
      |                        |                        |                        |                        |
      |-- SET cookie: token--->|  (via sdk_interlink)   |                        |                        |
      |                        |                        |                        |                        |
      |-- GET /session-info -->|                        |                        |                        |
      |   (cookie: token)      |                        |                        |                        |
      |                        |-- decode JWT (sub) --->|                        |                        |
      |                        |   GET /api/user/{sub}  |                        |                        |
      |                        |<-- user.email ---------|                        |                        |
      |                        |-- query DB by email ---|------------------------|----------------------->|
      |                        |<-- full user data -----|------------------------|------------------------|
      |<-- session-info JSON --|                        |                        |                        |
      |   (includes            |                        |                        |                        |
      |    wizardEnabled,      |                        |                        |                        |
      |    sessionKey, etc.)   |                        |                        |                        |
```

---

## Dual Auth System Detail

### 1. FusionAuth (New MFE Flows)

- **Used by**: `mfe_authentication` login form, `svc_settings` NestJS service
- **Operations**: `login()`, `register()`, `logout()`, `changePassword()`, `forgotPassword()`, `refreshToken()`
- **Token format**: Standard JWT with `sub` claim (FusionAuth user ID)
- **Storage**: Set as `token` cookie on `.colppy.com` domain (1-hour expiry)

| Env variable | Service | Description |
|-------------|---------|-------------|
| `FUSIONAUTH_URL` | svc_settings | FusionAuth server base URL |
| `FUSIONAUTH_AUTHORIZATION_KEY` | svc_settings | API key for FusionAuth admin operations |
| `FUSIONAUTH_APPLICATION_ID` | svc_settings | Application ID for login scope |
| `SECRET_KEY` | svc_settings | AES decryption key (matches frontend `VITE_SECRET_KEY`) |
| `FRONTERA_API_URL` | svc_settings | Frontera service.php URL for legacy session creation |
| `FRONTERA_API_USERNAME` | svc_settings | Dev auth credentials for Frontera calls |
| `FRONTERA_API_PASSWORD` | svc_settings | Dev auth credentials for Frontera calls |

### 2. Legacy Frontera Session System

- **Used by**: All Frontera API calls (`service.php`), legacy login flows
- **Token format**: MD5 hash -- `md5(usuario + password + timestamp)`
- **Storage**: `usuario_sesion` table in MySQL
- **Validation**: `UsuarioCommon::autenticarUsuarioAPI()` on every API call

---

## Password Encryption

### MFE Frontend to svc_settings

```
Frontend (browser)                         svc_settings (NestJS)
       |                                          |
       |  password = CryptoJS.AES.encrypt(        |
       |    plaintext, VITE_SECRET_KEY)            |
       |                                          |
       |-- POST /login {email, encrypted_pwd} --->|
       |                                          |
       |          bytes = CryptoJS.AES.decrypt(   |
       |            password, SECRET_KEY)          |
       |          plaintext = bytes.toString(Utf8) |
```

- `VITE_SECRET_KEY` (frontend) and `SECRET_KEY` (backend) must be the **same value**
- Library: `CryptoJS` (npm `crypto-js`)
- After decryption, `svc_settings` sends the plaintext to FusionAuth and an MD5 hash to Frontera

### svc_settings to Frontera

```typescript
// fusionauth.service.ts line 436
const md5Hash = CryptoJS.MD5(password).toString();  // password = decrypted plaintext

// Sent to Frontera as:
parameters: {
    password: md5Hash,        // MD5 for legacy DB comparison
    passwordAuth: password,   // plaintext for FusionAuth re-validation
    fusionAuth: 1,
}
```

### Legacy Frontera Password Storage

- Stored with MySQL `AES_ENCRYPT(password, 'aaa')` in `usuario.Password` column
- Validated via: `MD5(AES_DECRYPT(u.Password, 'aaa')) = :password`
- The client sends `MD5(plaintext)` which is compared against `MD5(AES_DECRYPT(stored))`

---

## Session Lifecycle

### Token Creation (`iniciar_sesion` / `iniciar_colppy`)

```php
// UsuarioDAO.php line 341 (iniciar_sesion)
$secret = md5($usuario . $clave . date('Y M d H:i:s'));

// UsuarioDAO.php line 470 (iniciar_colppy)
$claveEnc = md5($idUsuario . $password . date('Y M d H:i:s'));
```

- Session row inserted into `usuario_sesion`:

| Column | Value |
|--------|-------|
| `user_id` | Numeric user ID from `usuario.id` |
| `claveSesion` | MD5 token (see above) |
| `fechaCreacion` | `now()` |
| `fechaAcceso` | `now()` |
| `fechaExpira` | `DATE_ADD(now(), INTERVAL SESION_MINS_DURACION MINUTE)` |
| `fechaSalida` | Same as `fechaExpira` |
| `ipCreacion` | Client IP (if `AUTENTICACION_POR_IP_ACTIVADA = true`) |
| `idEmpresa` | User's last active company |

### Session Validation (`validar_sesion`)

- **Called by**: `UsuarioCommon::autenticarUsuarioAPI()` on **every** Frontera API call
- **File**: `colppy-app/resources/Provisiones/ColppyCommon/persistencia/UsuarioDAO.php` line 647

```sql
-- Without IP check (AUTENTICACION_POR_IP_ACTIVADA = false)
SELECT idSesion, fechaAcceso
FROM usuario_sesion us
WHERE us.user_id = :userId
  AND us.claveSesion = :claveSesion
  AND us.fechaExpira >= now()
LIMIT 1

-- With IP check (AUTENTICACION_POR_IP_ACTIVADA = true)
SELECT idSesion, fechaAcceso
FROM usuario_sesion us
WHERE us.user_id = :userId
  AND us.claveSesion = :claveSesion
  AND us.fechaExpira >= now()
  AND us.ipCreacion = :ip
LIMIT 1
```

### Session Renewal (Sliding Expiry)

- On each successful `validar_sesion`, if `fechaAcceso + getSecondsUpdateSession()` < `now()`:
  - `fechaAcceso` is updated to `now()`
  - `fechaExpira` is extended by `SESION_MINS_DURACION` minutes from `now()`
- This creates a **sliding window** -- active users never expire

```php
// UsuarioDAO.php line 700-704
if ($fechaAcceso < new DateTime()) {
    $statement = $db->prepare("UPDATE usuario_sesion SET fechaAcceso = now(),
        fechaExpira=DATE_ADD(now(), INTERVAL :minutosDuracion MINUTE) WHERE idSesion = :idSesion");
    $statement->execute(array(':idSesion' => $idSesion, ':minutosDuracion' => $minutosDuracion));
}
```

### Session Validation in `autenticarUsuarioAPI()`

- **File**: `colppy-app/resources/Provisiones/ColppyCommon/common/UsuarioCommon.php` line 17

```
Step 1: Check required params (sesion.usuario, sesion.claveSesion)
Step 2: Check AUTENTICACION_ACTIVADA flag (if false, skip all validation)
Step 3: Verify user has permission on target empresa (empresa_usuario table)
Step 4: Call validar_sesion(usuario, userId, claveSesion, isMobile)
Step 5: Return true or throw exception
```

- Required request parameters for any authenticated Frontera call:

```json
{
  "parameters": {
    "sesion": {
      "usuario": "email@example.com",
      "userId": "31",
      "claveSesion": "5afa01c3dda9d66547e30893d9c54e2a"
    },
    "idEmpresa": "31166"
  }
}
```

- See [API Reference](api-reference.md) for full request structure

---

## Cookie Management (sdk_interlink)

- **File**: `colppy/sdk_interlink/src/auth.ts`
- `setTokenAuthentication(token)` -- sets `token` cookie on `.colppy.com` domain, `Secure; SameSite=Lax`, 1-hour expiry
- `clearTokenAuthentication()` -- clears the cookie (expires in past)
- `getUserData(url)` -- calls `GET {url}session-info` with `credentials: 'include'`
- The `token` cookie contains the FusionAuth JWT; domain `.colppy.com` allows sharing across subdomains
- `session-info` decodes the JWT `sub` claim, fetches user email from FusionAuth, then queries the DB for full user/company data

---

## `wizardEnabled` Flag

- **DB column**: `usuario.usa_wizard` (INT, nullable)
- **Query**: `u.usa_wizard AS wizardEnabled` (fusionauth.service.ts line 122)
- **DTO transform**: `null` becomes `"0"`; non-null becomes its string value (userInfoResponse.dto.ts line 56)

| `wizardEnabled` value | Behavior |
|-----------------------|----------|
| `"0"` (null in DB) | Redirect to legacy app (`VITE_COLPPY_APP_URL`) |
| Non-zero (e.g. `"1"`) | Redirect to `/inicio` (mounts `mfe_onboarding`) |

- After onboarding completes, a stored procedure sets `usa_wizard = null`, clearing the flag
- See [Onboarding Wizard](onboarding-wizard.md) for the full post-login wizard flow

---

## Key Files

| Component | File path (relative to `github-jonetto/`) | Description |
|-----------|-------------------------------------------|-------------|
| Session validation entry point | `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/common/UsuarioCommon.php` | `autenticarUsuarioAPI()` -- called on every Frontera API request |
| Session DB operations | `nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/persistencia/UsuarioDAO.php` | `iniciar_sesion()` (line 324), `iniciar_colppy()` (line 396), `validar_sesion()` (line 647), `validar_sesion_cookies()` (line 1023) |
| Login delegate (Frontera) | `nubox-spa/colppy-app/resources/Provisiones/Usuario/1_0_0_0/delegates/IniciarSesionDelegate.php` | `iniciar_sesion()` and `iniciar_colppy()` -- handles FusionAuth optional flow |
| FusionAuth service (svc_settings) | `colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts` | `login()`, `sessionInfo()`, `iniciarSesionColppy()`, `finishWizard()` |
| Session-info DTO | `colppy/svc_settings/src/fusionauth/dto/userInfoResponse.dto.ts` | Maps DB columns to JSON response including `wizardEnabled`, `sessionKey` |
| Login DTO | `colppy/svc_settings/src/fusionauth/dto/login.dto.ts` | `{email, password}` input validation |
| Cookie management (SDK) | `colppy/sdk_interlink/src/auth.ts` | `setTokenAuthentication()`, `clearTokenAuthentication()`, `getUserData()` |
| FusionAuth PHP connector | `nubox-spa/colppy-app/lib/ApiGatewayConnector/ApiGatewayConnector.php` | PHP client for FusionAuth API (login, register, changePassword) |
| Auth flow documentation | `colppy/frontera2/docs/authentication-flow.md` | Detailed dual-auth analysis with Mermaid diagrams |
| System constants | `nubox-spa/colppy-app/lib/frontera2/include/core/constantes.php` | Cache key definitions; `SESION_MINS_DURACION` defined in env/bootstrap |
| Password change delegate | `nubox-spa/colppy-app/resources/Provisiones/Usuario/1_0_0_0/delegates/CambioContrasenaDelegate.php` | Dual password change (FusionAuth + DB) |
| DB schema (reference dump) | `colppy/dockervm/backup-database/colppy.sql` | `usuario`, `usuario_sesion`, `empresa_usuario` table definitions |

---

## Auth-Related Database Tables

Key columns only -- see [Database Schema](database-schema.md) for complete definitions.

| Table | Auth-relevant columns |
|-------|----------------------|
| `usuario` | `id` (PK), `idUsuario` (email), `Password` (AES-encrypted, key `'aaa'`), `external_id` (FusionAuth UUID, nullable), `usa_wizard` (int, nullable) |
| `usuario_sesion` | `idSesion` (PK), `user_id` (FK), `claveSesion` (MD5 token), `fechaCreacion`, `fechaAcceso`, `fechaExpira`, `ipCreacion`, `idEmpresa` |
| `empresa_usuario` | `idEmpresa` + `user_id` (composite PK), `esAdministrador`, `idRol`, `esContador` |

---

## Configuration Constants

| Constant | Description |
|----------|-------------|
| `SESION_MINS_DURACION` | Session duration in minutes (used for `fechaExpira`) |
| `AUTENTICACION_ACTIVADA` | Master kill-switch; if `false`, all API calls skip session validation |
| `AUTENTICACION_POR_IP_ACTIVADA` | If `true`, `validar_sesion` also checks `ipCreacion` matches current IP |
| `RELOAD_COOKIE_VALUE` | Value attached to login response for frontend cookie refresh |
| `PASSWORD_DEFAULT` | `.env` -- fallback password for FusionAuth when `passwordAuth` param missing |
| `API_GATEWAY_CONNECTOR_APPLICATION_ID` | `.env` -- FusionAuth application ID used from PHP backend |

---

## Gotchas

### 1. Two Concurrent Session Systems

- Login creates artifacts in **both** FusionAuth (JWT) and Frontera (DB session row)
- These two sessions have **independent lifetimes** -- the JWT cookie expires in 1 hour (client-side timer), the DB session uses `SESION_MINS_DURACION` with sliding renewal
- Logging out of one does not automatically invalidate the other

### 2. FusionAuth JWT vs Frontera MD5 Token

- The FusionAuth JWT stored in the `token` cookie is used **only** for the `session-info` call in `svc_settings`
- The Frontera `claveSesion` (MD5) is used for **every** `service.php` API call
- These are completely different tokens with different formats, lifetimes, and validation paths

### 3. FusionAuth JWTs Are NOT Used for Frontera API Validation

- `UsuarioCommon::autenticarUsuarioAPI()` reads `sesion.claveSesion` from the request body and validates against the `usuario_sesion` table
- FusionAuth is **never consulted** during this flow
- Even if a FusionAuth JWT expires or is revoked, the Frontera session remains valid (and vice versa)

### 4. Password Sync Risk

- Passwords exist in **two places**: FusionAuth and the legacy DB (`usuario.Password`)
- Password change updates both systems sequentially with **no transaction**
- If one update fails, passwords become desynchronized
- The `CambioContrasenaDelegate.php` has a **typo** at line 117: checks `passwordAuth` but reads `passwordFusionAuth`

### 5. Hardcoded Fallback Passwords

- If `passwordAuth` param is missing during login, Frontera uses `env('PASSWORD_DEFAULT')` for FusionAuth
- If `passwordAuth` param is missing during password change, code falls back to hardcoded `'q2w3e4r5t'`
- Both are security risks

### 6. Four Tokens Returned on Login

When `fusionAuth=true`, the Frontera `iniciar_colppy` response includes:

| Token | Source | Actually used |
|-------|--------|---------------|
| `token` (Benjamin) | Internal OAuth | Yes |
| `refreshToken` (Benjamin) | Internal OAuth | Yes |
| `fusionAuthToken` | FusionAuth JWT | No (by Frontera) |
| `fusionAuthRefreshToken` | FusionAuth | No (by Frontera) |

### 7. `session-info` Joins to Latest Session Row

- The `getUserData()` query in `svc_settings` joins to `usuario_sesion` to get the latest `claveSesion`:

```sql
LEFT JOIN (
    SELECT us1.user_id, us1.idEmpresa, us1.claveSesion
    FROM usuario_sesion us1
    INNER JOIN (
        SELECT user_id, MAX(fechaCreacion) AS max_fecha
        FROM usuario_sesion
        GROUP BY user_id
    ) latest ON us1.user_id = latest.user_id
        AND us1.fechaCreacion = latest.max_fecha
) us ON us.user_id = u.id
```

- This means `sessionKey` in the response is always from the **most recent** session, even if multiple active sessions exist

### 8. `usa_wizard` Is Set to NULL by Stored Procedure

- After onboarding completes, a stored procedure sets `usa_wizard = null`
- The DTO transforms `null` to `"0"`, so the frontend sees `wizardEnabled: "0"` and routes to the legacy app
- If the stored procedure fails silently, the user gets stuck in the wizard loop

### 9. AES Key Mismatch Breaks Login Silently

- Frontend encrypts with `VITE_SECRET_KEY`, backend decrypts with `SECRET_KEY`
- If these values differ across deployments, `CryptoJS.AES.decrypt()` returns garbage (not an error)
- FusionAuth then rejects the garbled password with a generic 400 error

---

## Cross-References

- [Backend Architecture](backend-architecture.md) -- svc_settings and Frontera layer details
- [API Reference](api-reference.md) -- authentication in Frontera API calls, `sesion` parameter format
- [Database Schema](database-schema.md) -- `usuario`, `usuario_sesion`, `empresa_usuario` table details
- [Onboarding Wizard](onboarding-wizard.md) -- post-login wizard flow and `wizardEnabled` routing
- [Frontend Architecture](frontend-architecture.md) -- MFE auth flow, single-spa routing, sdk_interlink usage

---

*Last updated: 2026-03-03*
