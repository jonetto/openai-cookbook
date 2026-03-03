# Colppy Platform Reference

> AI-optimized architecture reference for the Colppy SaaS accounting/ERP platform.
> All file paths are relative to the `github-jonetto/` root unless stated otherwise.

---

## What Colppy Is

- Argentine SaaS accounting/ERP for PyMEs (SMBs) and accountants
- Two ICPs: **Cuenta Contador** (accountant firms managing multiple companies) and **Cuenta Pyme** (direct SMBs)
- ~3000+ paying customers, MRR-based SaaS model
- Core modules: invoicing (facturas), accounting (contabilidad), inventory, treasury, AFIP/ARCA tax integration
- HubSpot CRM for sales + Mixpanel for product analytics + Intercom for support
- Hybrid transitional architecture: PHP monolith being incrementally migrated to NestJS microservices + React MFEs
- Multi-tenant: one MySQL database, tenant isolation via `idEmpresa` foreign keys

---

## Architecture Diagram

```
┌─ Frontend (SPA Shell) ──────────────────────────────────────────┐
│  app_root (single-spa, Webpack)                                  │
│  Mounts MFE apps:                                                │
│    - mfe_authentication (React/Vite/Redux) — login form          │
│    - mfe_onboarding (React/Vite/Redux) — company setup wizard    │
│  Legacy: colppy-vue (Vue.js) — wizard-empresa, dashboard         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ JWT + cookies
┌───────────────────────────▼─────────────────────────────────────┐
│  Auth Bridge: svc_settings (NestJS)                              │
│  POST /login  ·  GET /session-info  ·  POST /finish-onboarding   │
│  Translates FusionAuth JWT ←→ legacy session table               │
└────────┬──────────────────────────────┬─────────────────────────┘
         │                              │
┌────────▼────────────┐  ┌──────────────▼──────────────────────┐
│ Frontera 2.0        │  │ Benjamin (Laravel 5.4)               │
│ Legacy PHP gateway  │  │ Modern REST API                      │
│ 36+ Provisiones     │  │ OAuth2 + Eloquent (207 models)       │
│ service.php         │←→│ BenjaminConnector bridge              │
└────────┬────────────┘  └──────────────┬──────────────────────┘
         │                              │
┌────────▼──────────────────────────────▼──────────────────────┐
│  MySQL (colppy DB) — 207 tables                               │
│  Shared by both Frontera (raw PDO) and Benjamin (Eloquent)    │
└──────────────────────────────────────────────────────────────┘

Side-band services (NestJS):
  svc_afip · svc_inventory · svc_security · svc_notifications · svc_marketplace

AWS Lambda functions: 15 (PDF generation, async jobs, webhooks)
```

---

## Runtime Core Repos

| Repo | Path | Tech | Purpose |
|------|------|------|---------|
| app_root | `colppy/app_root/` | React, single-spa, Webpack | SPA shell, route registration |
| mfe_authentication | `nubox-spa/colppy-app/mfe_authentication/` | React, Vite, Redux | Login form, session cookie |
| mfe_onboarding | `colppy/mfe_onboarding/` | React, Vite, Redux | Company setup wizard |
| svc_settings | `colppy/svc_settings/` | NestJS, TypeScript | Auth bridge (FusionAuth <-> Frontera) |
| colppy-app | `nubox-spa/colppy-app/` | PHP, Laravel 5.4 | Legacy gateway + 36 Provisiones |
| colppy-benjamin | `nubox-spa/colppy-benjamin/` | Laravel 5.4, OAuth2 | Modern business API, 207 Eloquent models |
| lib_ui | `colppy/lib_ui/` | React, Storybook | Shared UI component library (`colppy-lib` npm) |
| sdk_interlink | `colppy/sdk_interlink/` | TypeScript | Token/cookie management across MFEs |
| inf_workflows | `colppy/inf_workflows/` | GitHub Actions | Reusable CI/CD workflows (37 repos reference it) |

---

## Documentation Index

| File | What It Covers |
|------|---------------|
| [repo-directory.md](repo-directory.md) | All 108 repos categorized with paths |
| [backend-architecture.md](backend-architecture.md) | Frontera 2.0, Benjamin, NestJS services |
| [provisiones-reference.md](provisiones-reference.md) | 36+ business modules (delegate pattern) |
| [database-schema.md](database-schema.md) | 207 MySQL tables by domain |
| [api-reference.md](api-reference.md) | Frontera envelope format, REST endpoints |
| [auth-and-sessions.md](auth-and-sessions.md) | FusionAuth + legacy dual auth system |
| [frontend-architecture.md](frontend-architecture.md) | MFE shell, lib_ui, sdk_interlink |
| [onboarding-wizard.md](onboarding-wizard.md) | Wizard flow with backend orchestration |
| [deployment-and-infra.md](deployment-and-infra.md) | CI/CD workflows, Docker, AWS |

---

## Key Concepts

- **CUIT**
  Argentine tax ID. Format: `XX-XXXXXXXX-X` (always with hyphens).
  Universal entity key across all Colppy systems, AFIP, and HubSpot.

- **Provision (Provisiones)**
  Feature module in Frontera — analogous to a bounded context.
  Each Provision has a delegate class hierarchy: `EditarDelegate`, `ListarDelegate`, etc.
  Examples: `FacturaVenta`, `FacturaCompra`, `Cliente`, `Proveedor`, `Empresa`.

- **Frontera 2.0**
  Legacy PHP API gateway. Single entry point (`service.php`) dispatches to Provisiones via JSON envelope.
  Request format: `{ "service": { "provision": "FacturaVenta", "operacion": "listar_facturasventa" } }`.

- **Benjamin**
  Modern Laravel API layer. Frontera delegates to it via `BenjaminConnector` for migrated domains.
  Has its own OAuth2 auth + 207 Eloquent models mapping to the shared MySQL DB.

- **ICP**
  Ideal Customer Profile.
  - **Cuenta Contador**: Accountant firm managing 5+ client companies.
  - **Cuenta Pyme**: Direct SMB using Colppy for their own bookkeeping.

- **MFE (Micro-Frontend)**
  React apps mounted by the single-spa shell (`app_root`).
  Each MFE is an independent repo with its own build pipeline.

- **FusionAuth**
  External identity provider for new auth flows.
  Issues JWTs consumed by `svc_settings`, which bridges to legacy session table.

- **BenjaminConnector**
  PHP class in Frontera that forwards requests to Benjamin's REST API.
  Used when a Provision's business logic has been migrated but the entry point remains Frontera.

---

## Platform Status

- **Hybrid transitional architecture**: monolith to microservices migration in progress
- New auth UX (MFE + FusionAuth) coexists with legacy `usuario_sesion` table
- Most post-login business operations still run through Frontera / colppy-app
- 108 independent repos coordinated via GitHub Actions reusable workflows (`inf_workflows`)
- Only 2 of 8 MFE repos are currently mounted in production (`mfe_authentication`, `mfe_onboarding`)
- Benjamin adoption growing: new API endpoints go here, Frontera delegates via BenjaminConnector

---

## Gotchas

### Repo structure
- **Not a monorepo**: 108 independent git repos in `github-jonetto/`, NOT git submodules
- **Two GitHub orgs**: `colppy/` (modern services, MFEs, infra) and `nubox-spa/` (legacy core: colppy-app, colppy-benjamin)

### Authentication
- **Dual auth is live**: FusionAuth JWT for MFE flows + legacy `usuario_sesion` table for Frontera operations -- both active simultaneously
- **Session bridging**: `svc_settings` creates entries in the legacy session table so Frontera accepts MFE-authenticated users
- **Dev API auth**: Two-layer -- dev credentials (MD5 hashed password) + user session (`claveSesion`)

### Database
- **Shared DB, no schema separation**: Single MySQL database (`colppy`) used by both Frontera (raw PDO) and Benjamin (Eloquent ORM)
- **207 tables**: No migration system for Frontera side; Benjamin uses Laravel migrations for its subset

### Frontend
- **Only 2 MFEs active**: Despite 8 MFE repos existing, only `mfe_authentication` and `mfe_onboarding` are mounted in `app_root`
- **Legacy Vue coexists**: `colppy-vue` (wizard-empresa, dashboard) still serves post-login UI alongside MFEs

### PHP
- **PHP version varies**: `colppy-app` uses PHP 5.6+, newer services target 7.4/8.2
- **Case-sensitive operation names**: `listar_facturasCompra` (camelCase C) vs `listar_facturasventa` (all lowercase) -- not consistent

### Business logic
- **CUIT format**: Always use `XX-XXXXXXXX-X` with hyphens as canonical format
- **Wizard Step 2 is skippable**: "Omitir" button lets users skip -- enrichment and onboarding logic must not depend on it
- **Frontera envelope**: Every API call wraps params in `{ "service": { "provision": "...", "operacion": "..." } }` -- malformed envelopes fail silently

### API
- **apidocs.colppy.com is incomplete**: Only documents 4 of 15 provisions; the Atlassian wiki (2021) has more; PyPI `colppy-api` source is the most complete reference
- **Frontera single endpoint**: All operations go through `POST /lib/frontera2/service.php` -- there are no RESTful routes

---

## Cross-References

Files in the `github-jonetto/` root that provide additional platform context:

| File | Description |
|------|-------------|
| `APP_SYSTEM_MAP.md` | High-level architecture notes and system boundaries |
| `CORE_DEPENDENCY_GRAPH.md` | Mermaid dependency graph across core services |
| `APP_REQUEST_PATHS.md` | End-to-end request flows (login, invoice creation, etc.) |
| `REPO_CONTEXT_INDEX.md` | 108-repo inventory with descriptions and status |
| `REPO_OPERATING_SHEET.md` | Per-repo tech stack, ports, build commands |

---

## Quick Command Reference

```bash
# Frontera API call (from tools/scripts/)
curl -X POST https://login.colppy.com/lib/frontera2/service.php \
  -H "Content-Type: application/json" \
  -d '{"service":{"provision":"Empresa","operacion":"listar_empresa"},"parameters":{...}}'

# Benjamin API call
curl -X GET https://api.colppy.com/v1/companies \
  -H "Authorization: Bearer <oauth2_token>"

# Local dev — app_root
cd colppy/app_root && npm install && npm start  # port 9000

# Local dev — svc_settings
cd colppy/svc_settings && npm install && npm run start:dev  # port 3000

# Local dev — colppy-app (Docker)
cd nubox-spa/colppy-app && docker-compose up
```

---

*Last updated: 2026-03-03*
