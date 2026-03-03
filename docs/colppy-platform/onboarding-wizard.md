# Onboarding Wizard

> Post-registration wizard that provisions a new Colppy company. Runs once per user, then redirects to the legacy app.

---

## End-to-End Flow

```
mfe_authentication (login)
  |
  v
POST /login --> FusionAuth --> iniciar_colppy (Frontera)
  |
  v
getUserData() --> checks wizardEnabled field
  |
  +-- wizardEnabled === '0' --> redirectColppyApp()  (VITE_COLPPY_APP_URL)
  +-- wizardEnabled !== '0' --> redirectOnboarding()  (pushState to /inicio)
  |
  v
mfe_onboarding mounts at /inicio
  |
  v
Step 1: CUIT entry --> ARCA auto-fill --> company info form
  |
  v
Step 2 (optional): Industry + implementation timeline  <-- SKIPPABLE via "Omitir"
  |
  v
POST /finish-onboarding --> svc_settings orchestrates 6 Frontera calls
  |
  v
Redirect to VITE_COLPPY_APP_URL (legacy app)
```

### Key Decision Point: `wizardEnabled`

| Value | Meaning | Redirect Target |
|-------|---------|-----------------|
| `'0'` | Wizard already completed | `VITE_COLPPY_APP_URL` (legacy app) |
| `'1'` or any truthy | Wizard pending | `/inicio` (onboarding MFE) |

- Source: `usuario.usa_wizard` column in MySQL, aliased as `wizardEnabled` in `getUserData()` query
- See [Auth and Sessions](auth-and-sessions.md) for login flow details

---

## Wizard Steps

### Step 1 -- Company Information (Required)

- **Route**: `/inicio/` (root of onboarding MFE)
- **Component**: `mfe_onboarding/src/views/screens/step-one/step-one.tsx`
- **Responsive**: `StepOneDesktop` / `StepOneMobile` (breakpoint: 500px)

#### CUIT Entry and ARCA Auto-Fill

1. User enters 11-digit CUIT (raw digits, no dashes)
2. On submit, calls `Tercero/obtener_datos_tercero_de_afip` via Frontera
3. On success, auto-populates form fields from ARCA response:

| ARCA Response Field | Form Field Populated |
|---------------------|---------------------|
| `nombre` | `Nombre`, `razonSocial` |
| `domicilioFiscal.direccion` | `domicilio` |
| `domicilioFiscal.localidad` | `localidad` |
| `domicilioFiscal.codPostal` | `codigoPostal` |
| `domicilioFiscal.provinciaObj` | `provincia` |
| `condicionIva` | `idCondicionIva` |

#### Form Fields (Step 1)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `cuit` | string (11 digits) | Yes | Input-masked, triggers ARCA lookup |
| `Nombre` | string | Yes | Company display name |
| `razonSocial` | string | Yes | Legal business name |
| `domicilio` | string | Yes | Street address |
| `localidad` | string | Yes | City |
| `codigoPostal` | string | Yes | Postal code |
| `provincia` | `{value, label}` | Yes | Dropdown, loaded from `Empresa/leer_provinciasdecodificadora` |
| `nroIIBB` | string | No | Ingresos brutos number |
| `idCondicionIva` | `{value, label}` | Yes | Dropdown, loaded from `CondicionIVA/getCondicionesIVA` |
| `tipoOperacion` | `{value, label}` | Yes | Activity type, from `CondicionIVA/getTipoActividad` |
| `is_multilateral` | boolean | No | Multilateral IIBB flag |

#### Frontera Calls (Form Data Loading)

| Provision | Operation | Purpose |
|-----------|-----------|---------|
| `Tercero` | `obtener_datos_tercero_de_afip` | Auto-fill from ARCA via CUIT |
| `CondicionIVA` | `getCondicionesIVA` | Load IVA condition dropdown |
| `CondicionIVA` | `getTipoActividad` | Load activity type dropdown |
| `Empresa` | `leer_provinciasdecodificadora` | Load province dropdown |
| `Usuario` | `leer_datos_atividad_usuario` | Load role + industry options for Step 2 |

### Step 2 -- Industry & Implementation (Skippable)

- **Route**: `/inicio/datos-de-tu-empresa` (desktop) or step 2 of 2 (mobile)
- **Component**: `mfe_onboarding/src/views/screens/components/step-two/stepThreeJoin.tsx`
- **Responsive**: `StepThree` (desktop) / `StepTwoMobile` (mobile)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `industriaWizard` | `{value, label}` | No | Industry dropdown (from `leer_datos_atividad_usuario` where `id_pregunta = '3'`) |
| `implementacionWizard` | `{value, label}` | No | Implementation timeline (from `leer_datos_atividad_usuario` where `id_pregunta = '2'`) |

- **Skip mechanism**: "Omitir" button on desktop redirects directly to `VITE_COLPPY_APP_URL`; on mobile navigates to `/inicio/finalizar`
- **Submission**: Calls `Empresa/enviar_datos_atividad_usuario` with selected values
- Step numbering in UI: desktop shows "Step 3 of 3"; mobile shows "Step 2 of 2"

### Mobile-Only: Finish Screen

- **Route**: `/inicio/finalizar`
- **Component**: `mfe_onboarding/src/views/screens/mobile/step-finish/step-finish.tsx`
- Offers two CTAs: "Continue to Colppy" (`VITE_COLPPY_APP_URL`) and "Download mobile app" (App Store / Play Store link)

---

## Desktop Combined Flow (Current)

On desktop, Step 1 and Step 2 are merged into a single form in `StepOneDesktop`. The `onSubmit` handler:

1. Calls `POST /finish-onboarding` with company data (awaits response)
2. If Step 2 fields are filled, calls `Empresa/enviar_datos_atividad_usuario`
3. Tracks analytics (Mixpanel + Intercom)
4. Redirects to `VITE_COLPPY_APP_URL`

```typescript
// step-one.tsx -- desktop onSubmit (simplified)
const finishResult = await postFinishOnboring({ ...companyData }).unwrap()
if (!finishResult?.success) return  // abort on failure

if (parameters.industriaWizard && parameters.implementacionWizard) {
  await postSendDataActivity({ ...activityData }).unwrap()
}

trackFinishOnboarding()
window.location.href = import.meta.env.VITE_COLPPY_APP_URL
```

---

## Backend Orchestration: `finishWizard()`

- **Service**: `svc_settings/src/fusionauth/services/fusionauth.service.ts`
- **Controller**: `POST /finish-onboarding` in `svc_settings/src/fusionauth/controllers/fusionauth.controller.ts`
- **DTO**: `FinishOnboardingDto` in `svc_settings/src/fusionauth/dto/finish-onboarding.dto.ts`

The `finishWizard()` method executes **6 sequential Frontera calls** via `HttpCustomService`. All must succeed; there is no partial rollback.

### Frontera Calls Table

| # | Method | Provision | Operation | Purpose | Key Parameters |
|---|--------|-----------|-----------|---------|----------------|
| 1 | `updateEnterprise` | `Empresa` | `editar_empresa` | Update company master record | All company fields (name, CUIT, address, IVA, etc.) |
| 2 | `createChartOfAccounts` | `Empresa` | `crear_plan_cuentas` | Generate default chart of accounts | `idCondicionIva`, `tipoOperacion`, `planDeCuentasColppy: true` |
| 3 | `copyClientSeed` | `Empresa` | `copiar_cliente_semilla` | Create default "Consumidor Final" client | `idEmpresa` only |
| 4 | `createSeedSupplier` | `Empresa` | `copiar_proveedor_semilla` | Create default supplier record | `idEmpresa` only |
| 5 | `createSetupEvent` | `Tax` | `alta_setup_evento` | Register initial tax setup event | `idEmpresa`, `idUsuario` |
| 6 | `createInvoiceData` | `Empresa` | `crear_datos_facturacion` | Create billing/invoicing profile | `razonSocial`, `CUIT`, `idCondicionIva`, address fields |

See [Provisiones Reference](provisiones-reference.md) for Empresa operation details.

### Frontera Request Envelope

Each call uses the standard Frontera envelope built by `HttpCustomService.request()`:

```json
{
  "auth": {
    "usuario": "FRONTERA_API_USERNAME",
    "password": "FRONTERA_API_PASSWORD"
  },
  "service": {
    "provision": "Empresa",
    "operacion": "editar_empresa"
  },
  "parameters": {
    "sesion": {
      "usuario": "<email>",
      "claveSesion": null
    },
    "idEmpresa": "78500",
    "Nombre": "De Quesos S.R.L",
    "...": "..."
  }
}
```

See [API Reference](api-reference.md) for the full Frontera envelope spec.

### FinishOnboardingDto

```typescript
class FinishOnboardingDto {
  company_id: string       // @IsNumberString
  company_name: string     // @IsString
  business_name: string    // @IsString
  nro_iibb: string         // @IsString @IsOptional
  cuit: string             // @IsString
  address: string          // @IsString
  postal_code: string      // @IsString
  location: string         // @IsString
  province: string         // @IsString
  country: string          // @IsString
  phone: string            // @IsString
  email: string            // @IsEmail
  iva_condition: string    // @IsString
  operation_type: string   // @IsString
  is_multilateral: number  // @IsNumber
}
```

---

## Post-Wizard Redirect

| Platform | Redirect Target | Mechanism |
|----------|----------------|-----------|
| Desktop | `VITE_COLPPY_APP_URL` | `window.location.href` after `finishWizard` success |
| Mobile | `/inicio/finalizar` first, then `VITE_COLPPY_APP_URL` | `navigate()` to finish screen, then button click |

- On subsequent logins, `wizardEnabled === '0'` causes immediate redirect to legacy app
- The `useCheckOnboarding` hook in `mfe_authentication` re-checks this on mount
- See [Frontend Architecture](frontend-architecture.md) for MFE mounting details

---

## State Management

- **Redux slice**: `mfe_onboarding/src/views/screens/global-state.slice.ts`
- **Slice name**: `globalState`
- **Shape**: Flat `Record<string, unknown>` populated by `setUserData` action
- **Population**: `getUserData()` response from svc_settings is dispatched into the slice on mount
- **RTK Query APIs**:
  - `authenticationApi` -- `POST /finish-onboarding` (svc_settings)
  - `fronteraApi` -- all Frontera `service.php` calls (ARCA lookup, dropdowns, activity data)

---

## Integration with ARCA Prototype

The ARCA prototype (`openai-cookbook/arca-prototype/`) provides deeper CUIT enrichment that extends the wizard's built-in ARCA lookup.

### Wizard's Built-In ARCA Lookup

- Frontera call: `Tercero/obtener_datos_tercero_de_afip`
- Returns: company name, address, IVA condition
- Limitation: no business age, no RNS data, no activity periods

### ARCA Prototype Enrichment (Extended)

- Endpoint: `POST /api/onboarding/import` (FastAPI)
- Service: `arca-prototype/backend/services/cuit_enrichment.py`
- Runs AFIP Live API + RNS dataset lookup in parallel
- Returns via SSE stream: `enrichment_afip` and `enrichment_rns` events

| Data Source | Fields Added | Latency |
|------------|-------------|---------|
| AFIP Live API (`afip_cuit_lookup.py`) | Activities with `periodo`, estado, full address | 1-2s |
| RNS Open Data (`rns_dataset_lookup.py`) | `fecha_contrato_social`, `tipo_societario`, business age | ~12s cold / ~100ms warm |

### Integration Point

- The ARCA prototype enrichment is designed to hook into the wizard **before or during Step 1**
- CUIT entered in wizard triggers parallel enrichment call to ARCA prototype backend
- Enriched data (business age, incorporation date) flows to HubSpot for lead scoring
- See `openai-cookbook/docs/plans/POST_CUIT_ENRICHMENT_PIPELINE.md` for the 4-phase integration plan

---

## Route Map

| Route | MFE | Component | Description |
|-------|-----|-----------|-------------|
| `/` | `mfe_authentication` | `Login` | Login form |
| `/registro` | `mfe_authentication` | Register | Registration |
| `/inicio` | `mfe_onboarding` | `StepOne` | Wizard Step 1 (company info) |
| `/inicio/datos-de-tu-empresa` | `mfe_onboarding` | `StepThreeJoin` | Wizard Step 2 (industry) |
| `/inicio/finalizar` | `mfe_onboarding` | `StepFinish` | Mobile-only finish screen |

---

## Analytics Events

| Event | Trigger | Platform |
|-------|---------|----------|
| `Finalizar Wizard` | After `finishWizard` success | Mixpanel + Intercom |
| `Click en completar datos wizard` | CUIT submitted for ARCA lookup | Mixpanel + Intercom |
| `Click en Atras Wizard` | Back button clicked | Mixpanel + Intercom |
| `Tipo de actividad` (property) | Step 1 activity type selected | Mixpanel + Intercom |
| `Industria (colppy)` (property) | Step 2 industry selected | Mixpanel + Intercom |
| `PRODUCT_TOUR_EXPERIMENT` (property) | Experiment variant from localStorage | Mixpanel |

---

## Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `mfe_onboarding`, `mfe_authentication` | svc_settings base URL |
| `VITE_FRONTERA_API_URL` | `mfe_onboarding` | Frontera API endpoint (service.php) |
| `VITE_FRONTERA_API_USER` | `mfe_onboarding` | Frontera dev credentials (user) |
| `VITE_FRONTERA_API_PASSWORD` | `mfe_onboarding` | Frontera dev credentials (password) |
| `VITE_COLPPY_APP_URL` | `mfe_onboarding`, `mfe_authentication` | Legacy app redirect target |
| `FRONTERA_API_URL` | `svc_settings` | Frontera API (server-side) |
| `FRONTERA_API_USERNAME` | `svc_settings` | Frontera auth (server-side) |
| `FRONTERA_API_PASSWORD` | `svc_settings` | Frontera auth (server-side) |

---

## Source Files

| File | Path (relative to `github-jonetto/`) |
|------|--------------------------------------|
| Login screen | `nubox-spa/colppy-app/mfe_authentication/src/views/screens/login/login.tsx` |
| Onboarding check hook | `nubox-spa/colppy-app/mfe_authentication/src/hooks/use-check-onboarding.tsx` |
| Redirect utils | `nubox-spa/colppy-app/mfe_authentication/src/utils/utils.tsx` |
| Auth routes | `nubox-spa/colppy-app/mfe_authentication/routes.json` |
| Step 1 controller | `colppy/mfe_onboarding/src/views/screens/step-one/step-one.tsx` |
| Step 2 controller | `colppy/mfe_onboarding/src/views/screens/components/step-two/stepThreeJoin.tsx` |
| Step 3 desktop UI | `colppy/mfe_onboarding/src/views/screens/desktop/step-three/step-three.tsx` |
| Step 2 mobile UI | `colppy/mfe_onboarding/src/views/screens/mobile/step-two/step-two.tsx` |
| Finish screen (mobile) | `colppy/mfe_onboarding/src/views/screens/mobile/step-finish/step-finish.tsx` |
| Global state slice | `colppy/mfe_onboarding/src/views/screens/global-state.slice.ts` |
| Frontera RTK API | `colppy/mfe_onboarding/src/services/frontera.ts` |
| Auth RTK API | `colppy/mfe_onboarding/src/services/authentication.ts` |
| Constants & routes | `colppy/mfe_onboarding/src/constants.ts` |
| svc_settings controller | `colppy/svc_settings/src/fusionauth/controllers/fusionauth.controller.ts` |
| finishWizard service | `colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts` |
| FinishOnboardingDto | `colppy/svc_settings/src/fusionauth/dto/finish-onboarding.dto.ts` |
| HttpCustomService | `colppy/svc_settings/src/providers/http/http.service.ts` |
| CUIT enrichment (ARCA proto) | `openai-cookbook/arca-prototype/backend/services/cuit_enrichment.py` |
| Onboarding import router | `openai-cookbook/arca-prototype/backend/routers/onboarding.py` |

---

## Gotchas

- **Step 2 is fully skippable**. The "Omitir" button redirects directly to `VITE_COLPPY_APP_URL` (desktop) or the finish screen (mobile). Any enrichment or scoring logic must NOT depend on Step 2 data being present.
- **`finishWizard` is all-or-nothing**. The 6 Frontera calls run sequentially with no rollback. If call #4 fails, calls #1-3 are already committed. There is no retry or compensation logic.
- **`claveSesion` is null in server-side Frontera calls**. The `HttpCustomService.request()` method sets `sesion.claveSesion: null` -- it relies on `isCron: true` flag for auth bypass.
- **Wizard state lives in Redux only**. There is no server-side draft. If the user closes the browser mid-wizard, all form data is lost. The wizard restarts from Step 1 on next login.
- **Step numbering is inconsistent**. Desktop shows "Step 3 of 3" for industry/implementation; mobile shows "Step 2 of 2" for the same screen. The codebase refers to it as `StepThree` (desktop) and `StepTwo` (mobile).
- **The `postFinishOnboring` typo is intentional** (sic). The RTK Query hook is named `usePostFinishOnboringMutation` (missing 'a' in "onboarding"). Do not "fix" this -- it matches the API slice definition.
- **`location` field mismatch**. The DTO field `location` is documented as city/locality, but `step-one.tsx` passes `'Argentina'` as the location value. The actual locality goes into the `province` DTO field. This is a known mapping inconsistency.
- **Country is hardcoded**. `updateEnterprise` sets `countryId: 12` (Argentina) regardless of input. The wizard is Argentina-only.
- **Desktop merges all steps into one submit**. On desktop, `StepOneDesktop` includes the Step 2 dropdowns inline. The single `onSubmit` calls both `finish-onboarding` and `enviar_datos_atividad_usuario` sequentially.
- **ARCA auto-fill requires exactly 11 digits**. The `handleClick` guard checks `cuil.length === 11` before calling `obtener_datos_tercero_de_afip`. Shorter inputs are silently ignored.

---

## Cross-References

- [Auth and Sessions](auth-and-sessions.md) -- login flow, `wizardEnabled` check, token handling
- [Frontend Architecture](frontend-architecture.md) -- MFE mounting, `mfe_onboarding` lifecycle
- [Backend Architecture](backend-architecture.md) -- svc_settings service structure
- [Provisiones Reference](provisiones-reference.md) -- `Empresa` operations used by `finishWizard`
- [API Reference](api-reference.md) -- Frontera envelope format, auth structure

---

*Last updated: 2026-03-03*
