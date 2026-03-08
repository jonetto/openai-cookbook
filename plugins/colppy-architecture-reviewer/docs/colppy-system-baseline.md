# Colppy System Baseline

> Auto-generated from docs/colppy-platform/ + production DB verification. Last regenerated: 2026-03-08

## Database

### Production Main DB (verified 2026-03-08 via direct query)
- **Engine**: MySQL 5.6.51-log -- self-managed on EC2 (NOT Aurora, NOT RDS)
- **Hostname**: `ip-10-10-2-148.ec2.internal` (endpoint: `colppydb-prod.colppy.com:3306`, VPN required)
- **Datadir**: `/mysql/prod_n_db_colppy_56/`
- **Buffer pool**: ~285 GB (large EC2 instance, likely r5.8xlarge or bigger)
- **Max connections**: 3,000 (peak observed: 2,726; ~170K connections/day)
- **Server charset**: `latin1` (latin1_swedish_ci) -- NOT utf8 at server level
- **SSL/TLS**: DISABLED
- **Binary logging**: ON
- **Auth plugin**: `mysql_native_password` (MySQL 5.6 default)
- **Latin1 tables**: `empresa`, `usuario`, `facturacion`, `pago`, `plan`, `usuario_empresa`, `empresasHubspot` (7 of 10 visible)
- **UTF8 tables**: `crm_match` (utf8), `mrr_calculo` (utf8), `payment_detail` (utf8mb4)
- **Table counts**: 204 tables in colppy.sql dump; 207 Eloquent models in Benjamin (only 10 visible to read-only user)
- **Stored procedures**: 270 stored procedures + 26 functions (from colppy.sql dump); none individually tested against MySQL 8.0
- **DB access patterns**: 3 concurrent patterns against one schema -- Frontera raw PDO, Benjamin Eloquent ORM (207 models), NestJS TypeORM with raw SQL

### Aurora Serverless v2 Clusters (Terraform-defined, NOT the main DB)
- These clusters exist in Terraform (`rds.tf`) but the main `colppy` schema has NOT migrated to them
- `{env}-n-rds-microservices` -- Aurora MySQL 8.0 (3.08.2), 0.5--3 ACU (migration target)
- `{env}-n-rds-microservices-pgsql` -- Aurora PostgreSQL 15.12, 0.5--3 ACU
- `{env}-n-rds-afip-pgsql` -- Aurora PostgreSQL 15.12, 0.5--7 ACU (AFIP/ARCA tax API)
- `{env}-n-rds-paybook` -- Aurora MySQL 8.0, 0.5--3 ACU (Paybook banking)
- `{env}-rds-fusionauth` -- Aurora PostgreSQL, 0.5--3 ACU (test/stg only)
- Auto-pause 600s idle (non-prod); 12-day backup retention (prod)
- Credentials via Terraform `random_password` in AWS Secrets Manager

### Migration Reality
- **MySQL 5.6 -> 8.0 migration is still pending** -- production runs 5.6.51 on EC2
- **Known MySQL 8.0 breaks**: ERROR 1055 (GROUP BY), ERROR 1064 (`system` reserved), ERROR 1292 (zero dates)
- **`caching_sha2_password`**: NOT a current blocker (only applies when upgrading to 8.0; 5.6 uses `mysql_native_password`)
- **Latin1 encoding**: server default is latin1; migration to utf8mb4 needed before or during engine upgrade
- **Migration files**: 107 in `nubox-spa/colppy-benjamin/database/migrations/` (2014--2025)

## Backend

### Layer 1: Frontera 2.0 (Legacy Gateway)
- **Version**: FM_VERSION = `1.6.21.26`
- **PHP**: 5.6 (no type hints, no strict types)
- **Entry**: `nubox-spa/colppy-app/lib/frontera2/service.php`
- **Provisiones**: 32 folders (31 business + ColppyCommon); 6 dispatcher types (REST, JSON, XML, SOAP, CLI, Default)
- **Request format**: JSON envelope with `auth.sign` (MD5), `service.provision`, `service.operacion`
- **Key constraint**: Shares the SAME MySQL database as Benjamin with no schema isolation

### Layer 2: Benjamin (Modern Laravel API)
- **Framework**: Laravel 5.4
- **Auth**: OAuth2 via Laravel Passport
- **Models**: 207 Eloquent models
- **Migrations**: 109 migration files
- **API base**: `/api/v1/`
- **Pattern**: Repository + Service + Controller
- **Modules**: Core (31 tables), AR (24), AP (19), GL (15), ST (10), TX (8)
- **BenjaminConnector**: Guzzle HTTP client in `nubox-spa/colppy-app/lib/BenjaminConnector/BenjaminConnector.php`; OAuth2 tokens in `usuario_external_tokens` table; synchronous token refresh blocks requests

### Layer 3: NestJS Microservices (16 services)
- svc_settings (FusionAuth bridge, company config, BFF)
- svc_security (RBAC permissions, product access)
- svc_afip (ARCA/AFIP tax web services, circuit-breaker)
- svc_inventory (inventory domain)
- svc_sales (sales domain)
- svc_mercado_pago (MercadoPago payments, SQS)
- svc_importer_data (bulk import orchestration, SQS)
- svc_utils (utility/CRM integration)
- svc_backoffice (internal ops)
- svc_importer (legacy importer)
- svc_integracion_crm (CRM integration)
- svc_integracion_paybook (Paybook banking)
- svc_internal_api (internal API layer)
- svc_reporter (report generation)
- svc_fusionauth (FusionAuth discovery/config)
- svc_archetype_nestjs (template)

### Layer 4: Lambda Functions (20 total: 14 application + 6 infrastructure)
- **Application** (14): svc_agip_lambda, svc_api_internal_lambda, svc_api_public_lambda, svc_authorization_lambda, svc_calendar_events_lambda, svc_create_database_psql_lambda, svc_file_validator_lambda, svc_insert_imports_lambda, svc_mandrill_notification_lambda, svc_parser_lambda, svc_product_assistant_lambda, svc_public_webhooks_lambda, svc_slackassistant_lambda, svc_archetype_lambda
- **Infrastructure** (6): inf_SNSToSlack_lambda_lambda, inf_eks_auto_shutdown_startup_lambda, inf_rds_auto_shutdown_startup_lambda, sas-colppy-auth-lambda, sas-colppy-cloudops-rdsrestoretostaging-lambda, sas-colppy-commandManagement-lambda
- **Deployment**: AWS SAM (`sam build --use-container` -> `sam deploy`)

### Migration Status
- **Fully migrated** (7): Inventario, Tax, PriceList, Cliente, Tercero, Contabilidad, Empresa -- path: Frontera -> BenjaminConnector -> Benjamin REST -> Eloquent -> MySQL
- **Partially migrated** (5): FacturaVenta (list only), FacturaCompra (list only), Receipt (read only), Usuario (last payment), BillStub (list/create) -- list/read via Benjamin; create/edit still in Frontera DAO
- **Legacy (not migrated)** (16): Afip, Paybook, Pos, Tesoreria, Pago, Location, Moneda, CondicionIVA, CondicionPago, Help, Archivo, Notificaciones, Referido, Socio, Desarrollador, Retencion -- Frontera -> DAO -> MySQL direct

## Frontend

### Single-spa Shell (app_root)
- **Package**: `@colppy/root-config`
- **Bundler**: Webpack 5 (`webpack-config-single-spa-ts`)
- **Language**: TypeScript 4.x
- **Module loader**: SystemJS 6.8.3 (CDN)
- **Layout engine**: `single-spa-layout` ^1.6.0
- **Org namespace**: `@colppy/`
- **Import map overrides**: `import-map-overrides` 2.2.0
- **Analytics**: Google Tag Manager `GTM-KQV2QTWJ`
- **Dev server port**: 9000

### Active MFEs (2 mounted in production)
- `mfe_authentication` v1.1.4 -- default route `/`, React 18 + TS + Vite + MUI 5.15.x + Redux Toolkit + react-hook-form + yup, react-router-dom v6.22.x
- `mfe_onboarding` v1.0.8 -- route `/inicio`, React 18 + TS + Vite + MUI 7.0.x + Redux Toolkit + react-hook-form, react-router-dom v7.5.x

### Inactive MFEs (not mounted in layout)
- `mfe_dashboard` v1.0.0 -- React 18 + Vite + chart.js
- `mfe_mercado_pago` v1.0.3 -- React 18 + Vite + TanStack Table
- `mfe_sales` v0.0.1 -- archetype clone, never renamed
- `colppy-vue` v2.5.12 -- Vue 2.5 + Vuex 3 + Webpack 3 + Bootstrap 4 (legacy, 2018-era)

### Templates
- `mfe_archetype` v0.0.1 -- standalone Vite
- `mfe_archetype_single_spa` v0.0.1 -- single-spa integrated

### Legacy Vue SPA
- `colppy-vue` (Vue 2.5.12, Webpack 3, Bootstrap 4) handles most post-login UX (dashboard, invoicing, reports)
- After MFE login, browser redirects to legacy PHP + Vue monolith at `staging.colppy.com`

### Build Toolchain
- MFE build: `node:21` container, `pnpm install && pnpm run build`, Vite output format SystemJS
- Shell build: Webpack 5
- Shared lib (`colppy-lib` ^1.0.27): Rollup, Storybook v7.6
- `sdk_interlink` ^1.0.3: Rollup, ESM + UMD/CDN builds
- No shared dependency externalization -- each MFE bundles its own React, Redux, MUI

### Key Version Mismatches
- MUI: mfe_authentication uses 5.15.x, mfe_onboarding uses 7.0.x
- react-router-dom: mfe_authentication uses v6.22.x, mfe_onboarding uses v7.5.x (breaking API changes)

## Auth

### Dual System
- **FusionAuth**: Identity management (login, registration, password reset); JWT tokens (`token` + `refreshToken`); NOT used for Frontera API validation
- **Legacy Frontera**: Session lifecycle for all API calls; MD5 `claveSesion` in `usuario_sesion` table; validated on every `service.php` call via `UsuarioCommon::autenticarUsuarioAPI()`
- Independent lifetimes: JWT cookie expires 1 hour (client-side via `sdk_interlink`); DB session uses `SESION_MINS_DURACION` with sliding renewal
- Logging out of one does NOT invalidate the other

### svc_settings Bridge Mechanism
- Decodes FusionAuth JWT `sub` claim
- Fetches user profile from FusionAuth API using `FUSIONAUTH_AUTHORIZATION_KEY`
- Queries SAME MySQL database via raw SQL (6+ JOINs across `usuario`, `empresa`, `usuario_empresa`, `plan`, `usuario_sesion`)
- Returns unified session info including plan, company, roles, IVA conditions, IIBB jurisdictions, `sessionKey` (latest `claveSesion`)
- File: `colppy/svc_settings/src/fusionauth/services/fusionauth.service.ts`

### Current Vulnerabilities
- **Hardcoded fallback password**: If `passwordAuth` param missing during password change, code uses hardcoded `'q2w3e4r5t'`
- **PASSWORD_DEFAULT env**: If `passwordAuth` missing during login, Frontera uses `env('PASSWORD_DEFAULT')` for FusionAuth
- **Password stored with weak encryption**: MySQL `AES_ENCRYPT(password, 'aaa')` in `usuario.Password`; validated via `MD5(AES_DECRYPT(stored, 'aaa'))`
- **Raw SQL injection risk**: `svc_settings` `fusionauth.service.ts` uses raw SQL string interpolation (not parameterized) for `getUserData` query
- **Password sync risk**: Password change updates FusionAuth and legacy DB sequentially with no transaction; if one fails, passwords desynchronize
- **AES key mismatch**: `VITE_SECRET_KEY` (frontend) and `SECRET_KEY` (backend) must match; mismatch causes silent login failures

## Infrastructure

### AWS Accounts
| Account | ID | Purpose |
|---------|-----|---------|
| main (management) | `185428918146` | Organization root, shared services, billing |
| prod | `185428918146` | Production workloads (same as main) |
| stg | `599636274800` | Staging/QA |
| test | `828685354428` | Test/dev workloads |
| sec | `962781397405` | Security tooling, develop environment |

Cross-account connectivity via Transit Gateway.

### EKS Cluster Sizing
| Environment | Cluster name | Node type | Nodes | Disk |
|-------------|-------------|-----------|-------|------|
| prod | `PROD-N-EKS-cluster` | `t3a.large` | 6 | 50 GB |
| stg | `STG-N-EKS-cluster` | `t3a.large` | 2 | 50 GB |
| test | `TEST-N-EKS-cluster` | `t3a.xlarge` | 1 | 50 GB |
| develop | `DEVELOP-N-EKS-cluster` | `t3a.large` | 1 | 50 GB |

Managed node groups with auto-scaling. All PHP and NestJS services deploy as Helm releases.

### FusionAuth on ECS Fargate
- Only service on ECS Fargate (not EKS) -- separates identity provider from application workloads
- Defined in `ecs_cluster.tf` + `ecs_service.tf`

### CI/CD
- **Hub**: `colppy/inf_workflows/.github/workflows/` -- 15 reusable GitHub Actions workflows; ~37 repos reference this hub
- **Key workflows**: `build-and-push-dockerimage.yml`, `helm-chart-deploy.yml`, `mfe-build-and-deploy.yml`, `spa-build-and-deploy.yml`, `build-and-deploy-lambda-sam.yml`, `terraform-ci-cd.yml`
- **Runners**: Self-hosted per environment (`runner-prod`, `runner-stg`, `runner-test`, `develop`)
- **Secrets**: AWS Secrets Manager at `{repo_name}/{environment}`; extracted into `.env` at build time

### Deployment Patterns
| Service type | Artifact | Registry | Deploy target |
|-------------|----------|----------|---------------|
| MFE | Static JS/CSS | S3 `{env}-colppy-mfe/{repo}` | CloudFront CDN |
| SPA | Static JS/CSS | S3 `{env}-colppy-frontend/` | CloudFront CDN |
| NestJS service | Docker image | ECR | EKS via Helm |
| PHP service | Docker image | ECR | EKS via Helm |
| Lambda | SAM package | S3 | CloudFormation/SAM |
| Terraform | Plan/Apply | S3 state backend | AWS resources |

### Terraform Structure
- Repo: `colppy/inf_terraform_aws/`
- **Data-driven engine pattern**: single `engine/` directory (~50 `.tf` files), parameterized by per-account data in `data/colppy-{env}/`
- Workspace assembly via `bin/colppy-{env}.sh`; state stored in S3
- CI pipeline runs `fmt`, `plan`, `apply` with Infracost cost estimation
- Key modules: `eks.tf`, `rds.tf`, `ecr.tf`, `s3.tf`, `cloudfront.tf`, `ecs_cluster.tf`, `ecs_service.tf`, `vpc.tf`, `lambda.tf`, `secrets.tf`, `iamrole.tf`, `kms.tf`, `transitgateway.tf`, `cloudwatch_alarms.tf`

### Monitoring
- New Relic Kubernetes integration (`newrelic` Helm chart)
- CloudWatch alarms (`cloudwatch_alarms.tf`, `cloudwatch_dashboard.tf`)
- Goldilocks VPA (`goldilocks` Helm chart) for resource right-sizing

### Cost Optimization
- `inf_eks_auto_shutdown_startup_lambda` -- auto-stops/starts non-prod EKS node groups on schedule
- `inf_rds_auto_shutdown_startup_lambda` -- auto-stops/starts non-prod Aurora clusters on schedule
- Aurora Serverless v2 auto-pause after 600s idle (non-prod)

### Security Scanning
- **Semgrep**: SAST (static code analysis) -- auto-configured rules, runs on every Docker build
- **Trivy**: Container image scan (OS packages, library vulns, embedded secrets)
- Both `continue-on-error: true` -- advisory only, do NOT block push to ECR
- Results uploaded as GitHub Actions artifacts (7-day retention)

### Base Docker Images (`inf_docker_images/`)
- `php_base_5.6` -- legacy colppy-app
- `php_base_7.1`
- `php_base_7.4` -- most PHP services
- `php_base_8.2` -- newer PHP services
- `node_base_21` -- NestJS services
- `node_base_tls` -- Node.js with custom TLS config
- `nginx_base` -- reverse proxy
- `nginx_base_node` -- Nginx + Node.js combo
- `applicaciones_laravel` -- Laravel application base
- `applicaciones_nestjs` -- NestJS application base

## Repos

- **Total**: 108 independent git repositories (NOT a monorepo)
- **GitHub orgs**: 2 -- `colppy/` (modern services, MFEs, infra) and `nubox-spa/` (legacy core)
- **CI coordination**: `colppy/inf_workflows/` reusable workflows; 37 repos reference it

### Breakdown by Category
| Category | Count |
|----------|-------|
| Application | 4 |
| Backend service (PHP/Laravel) | 6 |
| Backend service (NestJS) | 9 |
| Connector library | 9 |
| Infrastructure/DevOps | 23 |
| Microfrontend | 8 |
| Migrations | 2 |
| SDK/Library | 7 |
| Serverless (Lambda) | 15 |
| Shared library | 3 |
| Testing/QA | 4 |
| Other/Uncategorized | 18 |

### Two Deployment Flows
- **Classic Flow** (most backend services, legacy SPAs): `develop` -> test, `release/*` -> stg, `master` -> prod, `migration/*` -> develop
- **GitLab Flow** (newer MFEs: mfe_authentication, mfe_onboarding, mfe_dashboard, mfe_vue, mfe_mercado_pago, svc_importer_data, app_root, app_backoffice): `test` branch -> test env, `staging` branch -> stg env, `master` -> prod; promotion via branch merges

### Branch-to-Environment Mapping
| Branch | Environment | AWS Account ID | Runner |
|--------|-------------|----------------|--------|
| `master` | prod | `185428918146` | `runner-prod` |
| `release/*` | stg | `599636274800` | `runner-stg` |
| `develop` | test | `828685354428` | `runner-test` |
| `feature/*` | test (build only, no deploy) | `828685354428` | `runner-test` |
| `migration/*` | develop | `962781397405` | `develop` |
