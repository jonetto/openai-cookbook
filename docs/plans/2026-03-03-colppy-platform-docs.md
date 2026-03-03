# Colppy Platform Documentation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create 10 AI-optimized reference files in `docs/colppy-platform/` documenting the Colppy platform architecture for fast agent context loading.

**Architecture:** Each file is a self-contained navigation map (200-400 lines) with explicit file paths relative to `github-jonetto/`. Files are written in dependency order so later files can cross-reference earlier ones.

**Tech Stack:** Markdown files, no code. Source material from `github-jonetto/` existing docs (`APP_SYSTEM_MAP.md`, `CORE_DEPENDENCY_GRAPH.md`, `APP_REQUEST_PATHS.md`, `REPO_CONTEXT_INDEX.md`, `REPO_OPERATING_SHEET.md`) plus direct file exploration.

**Source codebase:** `/Users/virulana/github-jonetto/` (108 independent repos)

---

## Format Template (all files follow this)

```markdown
# [Title]

> One-line purpose statement

## Overview
2-3 sentences of context.

## [Domain-Specific Sections]
- Tables with file paths (relative to github-jonetto/)
- Decision trees where applicable
- Code snippets for patterns

## Gotchas
- Bullet list of non-obvious behaviors

## Cross-References
- Links to related docs in this directory
```

**Rules:**
- File paths always relative to `github-jonetto/` root
- No narrative prose — use tables, bullets, code blocks
- Gotchas section mandatory
- 200-400 lines per file
- No duplication — each fact lives in exactly one file

---

### Task 1: Create directory and README.md (master index)

**Files:**
- Create: `docs/colppy-platform/README.md`

**Step 1: Create directory**

```bash
mkdir -p docs/colppy-platform
```

**Step 2: Write README.md**

Content must include:
- **What Colppy Is**: Argentine SaaS accounting/ERP for PyMEs and accountants
- **Architecture diagram** (ASCII): 5 layers — MFE Shell → Auth Bridge → Legacy Gateway + Modern API → MySQL
- **Service map table**: Each service with purpose, tech, and path in github-jonetto/
- **Index**: Links to all 9 other docs in this directory
- **Key concepts**: CUIT, ICP (Cuenta Contador vs Pyme), Provisiones, Frontera 2.0
- **Platform status**: Hybrid transitional — monolith to microservices migration in progress

**Source material:**
- `github-jonetto/APP_SYSTEM_MAP.md` — architecture overview
- `github-jonetto/CORE_DEPENDENCY_GRAPH.md` — Mermaid dependency graph
- `github-jonetto/APP_REQUEST_PATHS.md` — request flow paths

**Step 3: Commit**

```bash
git add docs/colppy-platform/README.md
git commit -m "docs(colppy-platform): add master index and architecture overview"
```

---

### Task 2: repo-directory.md (108 repos catalog)

**Files:**
- Create: `docs/colppy-platform/repo-directory.md`

**Step 1: Write repo-directory.md**

Content must include:
- **Category table**: Application (4), Backend service (6), Backend service NestJS (9), Connector library (9), Infrastructure/DevOps (23), Microfrontend (8), Migrations (2), SDK/Library (7), Serverless service (15), Shared library (3), Testing/QA (4)
- **Runtime core repos** (with paths): app_root, mfe_authentication, mfe_onboarding, svc_settings, colppy-app, colppy-benjamin
- **Shared dependency repos**: lib_ui, sdk_interlink, inf_workflows
- **Repos missing READMEs** (12 listed in REPO_CONTEXT_INDEX.md)
- **How repos relate**: Not a monorepo — independent repos, coordinated via inf_workflows CI/CD

**Source material:**
- `github-jonetto/REPO_CONTEXT_INDEX.md` — full 108 repo inventory
- `github-jonetto/REPO_OPERATING_SHEET.md` — per-repo tech stack and how-to-run
- `github-jonetto/CORE_DEPENDENCY_GRAPH.md` — centrality signals

**Step 2: Commit**

```bash
git add docs/colppy-platform/repo-directory.md
git commit -m "docs(colppy-platform): add 108-repo directory with categories and paths"
```

---

### Task 3: backend-architecture.md (Frontera + Benjamin + NestJS)

**Files:**
- Create: `docs/colppy-platform/backend-architecture.md`

**Step 1: Research source files**

Read these files for accurate content:
- `github-jonetto/colppy/frontera2/docs/arquitectura_frontera_benjamin.md`
- `github-jonetto/nubox-spa/colppy-app/lib/frontera2/service.php` (first 50 lines)
- `github-jonetto/nubox-spa/colppy-app/lib/BenjaminConnector/BenjaminConnector.php` (first 50 lines)
- `github-jonetto/nubox-spa/colppy-benjamin/routes/api.php`
- `github-jonetto/colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts` (first 80 lines)

**Step 2: Write backend-architecture.md**

Content must include:
- **Three backend layers**: Frontera 2.0 (PHP legacy gateway), Benjamin (Laravel modern API), NestJS microservices
- **Frontera 2.0 section**: Entry point (`lib/frontera2/service.php`), request dispatch, Provision pattern, MainController
- **Benjamin section**: Laravel 5.4, OAuth2/Passport, REST API routes, Eloquent models, BenjaminConnector bridge
- **NestJS services table**: svc_settings, svc_security, svc_afip, svc_inventory, svc_sales, svc_importer_data, svc_mercado_pago — with purpose and key files
- **Lambda functions**: 15 serverless services (svc_*_lambda, sas-colppy-*)
- **Request flow**: How a request moves from Frontera → BenjaminConnector → Benjamin
- **Gotchas**: PHP 5.6 legacy, dual DB access patterns (PDO vs Eloquent), session validation in UsuarioCommon

**Step 3: Commit**

```bash
git add docs/colppy-platform/backend-architecture.md
git commit -m "docs(colppy-platform): add backend architecture — Frontera, Benjamin, NestJS"
```

---

### Task 4: provisiones-reference.md (36+ business modules)

**Files:**
- Create: `docs/colppy-platform/provisiones-reference.md`

**Step 1: Research source files**

```bash
ls github-jonetto/nubox-spa/colppy-app/resources/Provisiones/
```

Also read:
- A sample provision structure (e.g., `FacturaVenta/1_0_0_0/FacturaVenta.php` first 50 lines)
- A sample delegate (e.g., `FacturaVenta/1_0_0_0/delegates/AltaDelegate.php` first 50 lines)
- `ColppyCommon/` subdirectory listing

**Step 2: Write provisiones-reference.md**

Content must include:
- **What a Provision is**: Feature module equivalent (like a bounded context in DDD)
- **Directory pattern**: `Provisiones/<Name>/<Version>/delegates/<Op>Delegate.php`
- **Version scheme**: `1_0_0_0/` allows backward compatibility
- **Delegate pattern**: Alta (create), Leer (read), Editar (update), Borrar (delete), Listar (list)
- **Full provisions table**: All 36+ provisions with one-line purpose
- **ColppyCommon deep dive**: DAO pattern, UsuarioCommon (session validation), FileManagement, shared persistence
- **Key provisions for AI agents**: FacturaVenta, FacturaCompra, Cliente, Empresa, AFIP, Tesoreria, Inventario
- **Gotchas**: Some provisions delegate to Benjamin via BenjaminConnector, version folders are not all 1_0_0_0

**Step 3: Commit**

```bash
git add docs/colppy-platform/provisiones-reference.md
git commit -m "docs(colppy-platform): add Provisiones reference — 36+ business modules"
```

---

### Task 5: database-schema.md (207 tables)

**Files:**
- Create: `docs/colppy-platform/database-schema.md`

**Step 1: Research source files**

- `github-jonetto/nubox-spa/colppy-benjamin/database/migrations/` — list files for table names
- `github-jonetto/nubox-spa/colppy-benjamin/app/Models/` — list Eloquent models
- `github-jonetto/colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts` — MySQL query joins (shows key table relationships)

**Step 2: Write database-schema.md**

Content must include:
- **Single shared MySQL DB**: `colppy` database used by both Frontera and Benjamin
- **Tables by domain**: Sales (factura_venta, comprobante_venta, cliente), Purchase (factura_compra, proveedor), Accounting (asiento_contable, cuenta_contable), Inventory, Tax/AFIP, User/Session (usuario, usuario_sesion, usuario_empresa, empresa, plan, facturacion)
- **Key relationships**: usuario → usuario_empresa → empresa, empresa → plan, factura_venta → comprobante_venta → cliente
- **Session table**: `usuario_sesion` — MD5 token, IP, expiry (legacy auth)
- **Migration count**: 109 files in Benjamin
- **Gotchas**: Both Frontera (raw PDO) and Benjamin (Eloquent) write to same tables, some tables orphaned during migration

**Step 3: Commit**

```bash
git add docs/colppy-platform/database-schema.md
git commit -m "docs(colppy-platform): add database schema — 207 tables by domain"
```

---

### Task 6: api-reference.md (Frontera envelope + REST)

**Files:**
- Create: `docs/colppy-platform/api-reference.md`

**Step 1: Research source files**

- `github-jonetto/colppy/api-documentation/docs/intro.md` — API envelope format
- `github-jonetto/colppy/api-documentation/docs/flujos/crear-factura-venta.md` — invoice workflow
- `github-jonetto/colppy/svc_settings/src/providers/http/http.service.ts` — Frontera request builder

**Step 2: Write api-reference.md**

Content must include:
- **Two API systems**: Frontera envelope (legacy) + Benjamin REST (modern)
- **Frontera envelope format**: Full JSON request/response structure with auth, service, parameters
- **Key Frontera operations table**: provision + operacion pairs for common operations
- **Benjamin REST endpoints**: `/api/v1/*` routes from `routes/api.php`
- **svc_settings endpoints**: POST /login, GET /session-info, POST /finish-onboarding
- **Authentication patterns**: Dev credentials (MD5 pwd), session token (claveSesion), JWT (FusionAuth)
- **Gotchas**: All Frontera calls go through single `service.php` entry, case-sensitive operation names

**Step 3: Commit**

```bash
git add docs/colppy-platform/api-reference.md
git commit -m "docs(colppy-platform): add API reference — Frontera envelope + REST + svc_settings"
```

---

### Task 7: auth-and-sessions.md (dual auth system)

**Files:**
- Create: `docs/colppy-platform/auth-and-sessions.md`

**Step 1: Research source files**

- `github-jonetto/colppy/frontera2/docs/authentication-flow.md`
- `github-jonetto/colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts`
- `github-jonetto/nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/common/UsuarioCommon.php` (first 80 lines)
- `github-jonetto/nubox-spa/colppy-app/resources/Provisiones/ColppyCommon/persistencia/UsuarioDAO.php` (search for `validar_sesion`)
- `github-jonetto/nubox-spa/colppy-app/resources/Provisiones/Usuario/1_0_0_0/delegates/IniciarSesionDelegate.php`

**Step 2: Write auth-and-sessions.md**

Content must include:
- **Dual auth system**: FusionAuth (new MFE flows) + legacy `usuario_sesion` table (Frontera flows)
- **Login flow sequence diagram**: MFE → svc_settings → FusionAuth + Frontera → JWT + legacy session
- **Session lifecycle**: Token creation, validation (`validar_sesion`), expiry, renewal
- **Password encryption**: Client-side CryptoJS.AES with VITE_SECRET_KEY → backend decrypts with SECRET_KEY
- **Key files table**: Each auth component with exact file path
- **wizardEnabled flag**: How it's determined and how it routes the user
- **Gotchas**: Two concurrent session systems, FusionAuth JWT vs Frontera MD5 token, session validation still reads `usuario_sesion` table

**Step 3: Commit**

```bash
git add docs/colppy-platform/auth-and-sessions.md
git commit -m "docs(colppy-platform): add auth and sessions — dual FusionAuth + legacy system"
```

---

### Task 8: frontend-architecture.md (MFE system)

**Files:**
- Create: `docs/colppy-platform/frontend-architecture.md`

**Step 1: Research source files**

- `github-jonetto/colppy/app_root/src/colppy-root-config.ts`
- `github-jonetto/colppy/app_root/src/microfrontend-layout.html`
- `github-jonetto/colppy/app_root/src/importmap-template.json`
- `github-jonetto/nubox-spa/colppy-app/mfe_authentication/package.json`
- `github-jonetto/colppy/mfe_onboarding/package.json`
- `github-jonetto/colppy/lib_ui/package.json`
- `github-jonetto/colppy/sdk_interlink/src/auth.ts`

**Step 2: Write frontend-architecture.md**

Content must include:
- **Architecture**: single-spa shell (app_root) + React MFE apps + shared libraries
- **app_root**: Webpack, TypeScript, route registration, import map injection
- **MFE inventory table**: All 8 MFEs with purpose, tech, mount route, status (active/inactive)
- **Currently active MFEs**: Only mfe_authentication (/) and mfe_onboarding (/inicio)
- **Shared libraries**: lib_ui (colppy-lib npm package, Storybook), sdk_interlink (token cookies)
- **Tech per MFE**: React + TypeScript + Vite, Redux, MUI, react-hook-form, i18next
- **Build & deploy**: Vite build → Docker → S3 + CloudFront
- **Gotchas**: Import map template is injected at deploy time (not checked into source), only 2 MFEs currently mounted, legacy Vue app still handles most post-login UX

**Step 3: Commit**

```bash
git add docs/colppy-platform/frontend-architecture.md
git commit -m "docs(colppy-platform): add frontend architecture — MFE shell, lib_ui, sdk_interlink"
```

---

### Task 9: onboarding-wizard.md (end-to-end flow)

**Files:**
- Create: `docs/colppy-platform/onboarding-wizard.md`

**Step 1: Research source files**

- `github-jonetto/colppy/mfe_onboarding/src/views/screens/` — step components
- `github-jonetto/colppy/mfe_onboarding/src/services/authentication.ts` — finish-onboarding call
- `github-jonetto/colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts` — finishWizard() orchestration
- `github-jonetto/colppy/svc_settings/src/providers/http/http.service.ts` — Frontera request builder

**Step 2: Write onboarding-wizard.md**

Content must include:
- **End-to-end flow**: Login → wizardEnabled check → /inicio route → wizard steps → finish-onboarding → legacy app
- **Wizard steps**: Step 1 (company info), Step 2 (skippable), final confirmation
- **Backend orchestration**: svc_settings `finishWizard()` calls 6 Frontera operations in sequence
- **Frontera calls table**: Empresa/editar_empresa, Empresa/crear_plan_cuentas, Empresa/copiar_cliente_semilla, Empresa/copiar_proveedor_semilla, Tax/alta_setup_evento, Empresa/crear_datos_facturacion
- **Post-wizard redirect**: To `VITE_COLPPY_APP_URL` (legacy app)
- **Integration with ARCA prototype**: Where CUIT enrichment hooks into the wizard flow
- **Gotchas**: Step 2 is fully skippable ("Omitir"), enrichment must not depend on it; wizard state in Redux; finish-onboarding is all-or-nothing (no partial saves)

**Step 3: Commit**

```bash
git add docs/colppy-platform/onboarding-wizard.md
git commit -m "docs(colppy-platform): add onboarding wizard — end-to-end flow with orchestration"
```

---

### Task 10: deployment-and-infra.md (CI/CD)

**Files:**
- Create: `docs/colppy-platform/deployment-and-infra.md`

**Step 1: Research source files**

- `github-jonetto/colppy/inf_workflows/.github/workflows/` — list all workflow files
- `github-jonetto/colppy/dockervm/README.md` — local dev setup
- Sample deployment workflow (e.g., `colppy/svc_settings/.github/workflows/build_and_deploy.yml`)

**Step 2: Write deployment-and-infra.md**

Content must include:
- **inf_workflows hub**: Central reusable GitHub Actions workflows, 37 repos reference it
- **Deployment patterns table**: MFE (S3+CloudFront), NestJS (Docker+ECR+ECS/EKS), Lambda (SAM), PHP (Docker+EC2/ECS)
- **Local development**: dockervm setup, required repos, local domains, Docker Compose services
- **AWS infrastructure**: Terraform (inf_terraform_aws), Helm charts (inf_helm_charts), EKS, RDS, S3, CloudFront
- **Environment progression**: local → dev → staging → production
- **Key infra repos table**: All 23 Infrastructure/DevOps repos with purpose
- **Gotchas**: dockervm requires specific repos cloned into `code/` subdirectory, PHP version varies by service (5.6/7.4/8.2), some repos still have CircleCI templates alongside GitHub Actions

**Step 3: Commit**

```bash
git add docs/colppy-platform/deployment-and-infra.md
git commit -m "docs(colppy-platform): add deployment and infrastructure — CI/CD, Docker, AWS"
```

---

### Task 11: Final commit and verification

**Step 1: Verify all 10 files exist**

```bash
ls -la docs/colppy-platform/
# Should show 10 .md files
```

**Step 2: Verify line counts are within 200-400 range**

```bash
wc -l docs/colppy-platform/*.md
```

**Step 3: Verify no broken cross-references**

Check that all `[link text](filename.md)` references point to files that exist.

**Step 4: Final commit if any adjustments needed**

```bash
git add docs/colppy-platform/
git commit -m "docs(colppy-platform): complete 10-file platform documentation suite"
```
