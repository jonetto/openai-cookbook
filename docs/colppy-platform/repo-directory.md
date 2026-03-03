# Repository Directory

> Catalog of all 108 Colppy platform repositories with categories, paths, and tech stacks.

## Overview

- 108 independent git repositories, NOT a monorepo. Each repo has its own git history, CI, and deployment lifecycle.
- Two org directories: `colppy/` (modern services, MFEs, infra) and `nubox-spa/` (legacy core: colppy-app, colppy-benjamin, production connectors).
- Coordinated via `colppy/inf_workflows/` reusable GitHub Actions (37 repos reference it for CI/CD).

## Category Summary

| Category | Count | Description |
|----------|-------|-------------|
| Application | 4 | Full apps (app_root shell, backoffice, mobile, API assistant) |
| Backend service | 6 | PHP/Laravel services (importer, CRM, paybook, backoffice, reporter, fusionauth) |
| Backend service (NestJS) | 9 | TypeScript microservices (settings, security, afip, inventory, sales, mercado_pago, etc.) |
| Connector library | 9 | PHP Composer packages bridging services (base, border, CRM, database, auth, paypertic) |
| Infrastructure/DevOps | 23 | Terraform, Docker, Helm, Lambda ops, CI/CD workflows |
| Microfrontend | 8 | React MFE apps (auth, onboarding, dashboard, sales, mercado_pago, archetypes, vue) |
| Migrations | 2 | Database migration repos |
| SDK/Library | 7 | Shared packages (sdk_interlink, auth-oauth, paypertic-sdk) |
| Serverless service | 15 | AWS Lambda functions (SAM-based) |
| Shared library | 3 | Shared NestJS libraries (lib_ui, lib_log_nest, lib_response_nest) |
| Testing/QA | 4 | E2E tests, stress tests |
| Other/Uncategorized | 18 | Misc repos (POCs, websites, storage, discovery, front-end legacy) |

## Runtime Core

The 9 most important repos for understanding and operating the platform.

| Repo | Path | Tech | Purpose | Has README? |
|------|------|------|---------|-------------|
| `app_root` | `colppy/app_root/` | React, single-spa, Webpack, pnpm | SPA shell that loads all MFEs | No |
| `mfe_authentication` | `nubox-spa/colppy-app/mfe_authentication/` | React, Vite, Redux, pnpm | Login/auth UX (mounted at `/`) | Boilerplate only |
| `mfe_onboarding` | `colppy/mfe_onboarding/` | React, Vite, Redux, pnpm | Wizard UX (mounted at `/inicio`) | Boilerplate only |
| `svc_settings` | `colppy/svc_settings/` | NestJS, TypeScript, pnpm | Auth bridge, session, onboarding API | Boilerplate only |
| `colppy-app` | `nubox-spa/colppy-app/` | PHP, Laravel 5.4, Frontera | Legacy monolith gateway (36+ Provisiones) | **No README** |
| `colppy-benjamin` | `nubox-spa/colppy-benjamin/` | Laravel 5.4, OAuth2, Vue | Modern API layer | Yes |
| `lib_ui` | `colppy/lib_ui/` | React, Storybook, TypeScript, pnpm | Shared UI component library | No |
| `sdk_interlink` | `colppy/sdk_interlink/` | TypeScript, pnpm | Token management between MFEs and backend | No |
| `inf_workflows` | `colppy/inf_workflows/` | GitHub Actions YAML | CI/CD hub (37 repos reference this) | No |

## Microfrontends

8 repos. All use React + TypeScript + Vite except `mfe_vue`.

| Repo | Path | Mount Route | Status | Tech |
|------|------|-------------|--------|------|
| `mfe_authentication` | `nubox-spa/colppy-app/mfe_authentication/` | `/` | Active | React, Vite, Redux, pnpm |
| `mfe_onboarding` | `colppy/mfe_onboarding/` | `/inicio` | Active | React, Vite, Redux, pnpm |
| `mfe_dashboard` | `colppy/mfe_dashboard/` | Not mounted | Inactive | React, Vite, pnpm |
| `mfe_sales` | `colppy/mfe_sales/` | Not mounted | Inactive | React, Vite, pnpm |
| `mfe_mercado_pago` | `colppy/mfe_mercado_pago/` | Not mounted | Inactive | React, Vite, pnpm |
| `mfe_vue` | `colppy/mfe_vue/` | Legacy routes | Active (separate) | Vue, npm |
| `mfe_archetype` | `colppy/mfe_archetype/` | N/A | Template | React, Vite, pnpm |
| `mfe_archetype_single_spa` | `colppy/mfe_archetype_single_spa/` | N/A | Template | React, Vite, pnpm |

## Backend Services -- NestJS

9 repos. All use TypeScript + NestJS + pnpm. Run locally with `pnpm install && pnpm start:dev` (or `docker compose up` for some).

| Repo | Path | Purpose | Key Detail |
|------|------|---------|------------|
| `svc_settings` | `colppy/svc_settings/` | Auth/session/onboarding bridge | `src/fusionauth/` for FusionAuth integration |
| `svc_security` | `colppy/svc_security/` | RBAC permissions | Uses Docker Compose for local dev |
| `svc_afip` | `colppy/svc_afip/` | AFIP tax service wrapper | Archetype-based README |
| `svc_inventory` | `colppy/svc_inventory/` | Inventory domain service | Archetype-based README |
| `svc_sales` | `colppy/svc_sales/` | Sales domain service | Archetype-based README |
| `svc_mercado_pago` | `colppy/svc_mercado_pago/` | MercadoPago payment integration | Archetype-based README |
| `svc_importer_data` | `colppy/svc_importer_data/` | Data import orchestration | Uses Docker Compose for local dev |
| `svc_utils` | `colppy/svc_utils/` | Utility/shared service | Archetype-based README |
| `svc_archetype_nestjs` | `colppy/svc_archetype_nestjs/` | Template for new NestJS services | Archetype scaffold |

## Backend Services -- PHP/Laravel

6 repos. All use PHP + Laravel. Run locally with `npm install && npm run dev` (Laravel Mix) or Composer.

| Repo | Path | Purpose |
|------|------|---------|
| `svc_importer` | `colppy/svc_importer/` | CSV/PDF invoice importer |
| `svc_integracion_crm` | `colppy/svc_integracion_crm/` | HubSpot CRM integration |
| `svc_integracion_paybook` | `colppy/svc_integracion_paybook/` | Bank sync via Paybook |
| `svc_backoffice` | `colppy/svc_backoffice/` | Admin backend API |
| `svc_reporter` | `colppy/svc_reporter/` | Report generation |
| `svc_fusionauth` | `colppy/svc_fusionauth/` | FusionAuth config/Docker setup |

## Serverless / Lambda

15 repos. All AWS SAM-based. Run locally with `sam build && sam local start-api`.

| Repo | Purpose |
|------|---------|
| `svc_agip_lambda` | AGIP tax jurisdiction service |
| `svc_api_internal_lambda` | Internal API gateway Lambda |
| `svc_api_public_lambda` | Public API gateway Lambda |
| `svc_archetype_lambda` | Template for new Lambda services |
| `svc_authorization_lambda` | FusionAuth authorization Lambda |
| `svc_calendar_events_lambda` | Calendar event notifications |
| `svc_create_database_psql_lambda` | PostgreSQL database provisioning |
| `svc_file_validator_lambda` | File validation service |
| `svc_insert_imports_lambda` | Import data insertion |
| `svc_internal_api` | Internal API SAM deployment |
| `svc_mandrill_notification_lambda` | Mandrill email notification sender |
| `svc_parser_lambda` | Document/file parser |
| `svc_product_assistant_lambda` | Product assistant AI service |
| `svc_public_webhooks_lambda` | Public webhook receiver |
| `svc_slackassistant_lambda` | Slack bot/assistant Lambda |

All paths under `colppy/`. All require AWS SAM CLI + AWS credentials.

## Connector Libraries

9 repos. PHP Composer packages. Some exist in both `colppy/` and `nubox-spa/`.

| Repo | Package | Used By | Path |
|------|---------|---------|------|
| `base-connector` | colppy-base-connector | colppy-app | `colppy/base-connector/` |
| `colppy-base-connector` | colppy-base-connector | colppy-app (prod) | `nubox-spa/colppy-base-connector/` |
| `border-connector` | colppy-border-connector | colppy-app | `colppy/border-connector/` |
| `colppy-border-connector` | colppy-border-connector | colppy-app (prod) | `nubox-spa/colppy-border-connector/` |
| `colppy-crmintegration-connector` | colppy-crmintegration-connector | colppy-app | `colppy/colppy-crmintegration-connector/` |
| `colppy-database-connector` | colppy-database-connector | svc_* (NestJS) | `colppy/colppy-database-connector/` |
| `colppy-authentication-oauth-library` | auth-oauth | colppy-benjamin | `colppy/colppy-authentication-oauth-library/` |
| `colppy-authentication-oauth-library` | auth-oauth (prod) | colppy-benjamin | `nubox-spa/colppy-authentication-oauth-library/` |
| `colppy-crmintegration-connector` | crm-connector (prod) | colppy-app | `nubox-spa/colppy-crmintegration-connector/` |

### SDK/Library Repos (not connectors)

| Repo | Path | Tech | Purpose |
|------|------|------|---------|
| `sdk_interlink` | `colppy/sdk_interlink/` | TypeScript, pnpm | Token management between MFEs and backend |
| `authentication-oauth-library` | `colppy/authentication-oauth-library/` | PHP, Composer | OAuth library (colppy/ copy) |
| `colppy-paypertic-sdk` | `colppy/colppy-paypertic-sdk/` | PHP, Composer | PayPerTic SDK (colppy/ copy) |
| `paypertic-sdk` | `colppy/paypertic-sdk/` | PHP, Composer | PayPerTic SDK (duplicate) |
| `colppy-paypertic-sdk` | `nubox-spa/colppy-paypertic-sdk/` | PHP, Composer | PayPerTic SDK (prod, nubox-spa/) |

## Infrastructure/DevOps

23 repos grouped by function.

### CI/CD

| Repo | Path | Purpose |
|------|------|---------|
| `inf_workflows` | `colppy/inf_workflows/` | Reusable GitHub Actions workflows (37 repos reference) |
| `sas-colppy-github-pipelines-templates` | `colppy/sas-colppy-github-pipelines-templates/` | GitHub pipeline templates |
| `sas-colppy-templates-circleci` | `colppy/sas-colppy-templates-circleci/` | CircleCI templates (legacy) |
| `sas-colppy-deploymentTools` | `colppy/sas-colppy-deploymentTools/` | Deployment tooling |

### Terraform

| Repo | Path | Purpose |
|------|------|---------|
| `inf_terraform_aws` | `colppy/inf_terraform_aws/` | Main AWS Terraform definitions |
| `inf_organizations_tf` | `colppy/inf_organizations_tf/` | AWS Organizations Terraform |
| `inf_terraform_testing` | `colppy/inf_terraform_testing/` | S3 bucket infra (test env) |
| `nr_terraform` | `colppy/nr_terraform/` | New Relic Terraform |
| `sas-colppy-infrastructure-cdk` | `colppy/sas-colppy-infrastructure-cdk/` | AWS CDK (Python) infra |
| `cloudops-infra-policies` | `colppy/cloudops-infra-policies/` | CloudOps infra policies |

### Docker

| Repo | Path | Purpose |
|------|------|---------|
| `dockervm` | `colppy/dockervm/` | Local Docker dev environment (v2.1.1) |
| `inf_docker_images` | `colppy/inf_docker_images/` | Shared Docker images |
| `sas-colppy-dockerfiles` | `colppy/sas-colppy-dockerfiles/` | Dockerfiles collection |
| `docker-recipes` | `colppy/docker-recipes/` | Docker recipes (no README) |

### Helm/K8s

| Repo | Path | Purpose |
|------|------|---------|
| `inf_helm_charts` | `colppy/inf_helm_charts/` | Helm charts for K8s deployments |
| `inf_lt_colppyapp_userdata` | `colppy/inf_lt_colppyapp_userdata/` | Launch template user data |

### Lambda Ops

| Repo | Path | Purpose |
|------|------|---------|
| `inf_eks_auto_shutdown_startup_lambda` | `colppy/inf_eks_auto_shutdown_startup_lambda/` | EKS cluster auto start/stop |
| `inf_rds_auto_shutdown_startup_lambda` | `colppy/inf_rds_auto_shutdown_startup_lambda/` | RDS instance auto start/stop |
| `inf_SNSToSlack_lambda_lambda` | `colppy/inf_SNSToSlack_lambda_lambda/` | SNS-to-Slack notification bridge |

### Other Infra

| Repo | Path | Purpose |
|------|------|---------|
| `sas-colppy-adminTools` | `colppy/sas-colppy-adminTools/` | Admin/Slack command tools |
| `sas-colppy-auth-lambda` | `colppy/sas-colppy-auth-lambda/` | Auth Lambda (infra-level) |
| `sas-colppy-commandManagement-lambda` | `colppy/sas-colppy-commandManagement-lambda/` | Command management Lambda |
| `sas-colppy-fusionauth` | `colppy/sas-colppy-fusionauth/` | FusionAuth Docker setup |
| `sas-colppy-slackCommands` | `colppy/sas-colppy-slackCommands/` | Slack slash commands Lambda |
| `sas-colppy-updateRundeckDNS` | `colppy/sas-colppy-updateRundeckDNS/` | Rundeck DNS updater Lambda |
| `sas-colppy-cloudops-rdsrestoretostaging-lambda` | `colppy/sas-colppy-cloudops-rdsrestoretostaging-lambda/` | RDS restore-to-staging Lambda |

### Shared Libraries

| Repo | Path | Tech | Purpose |
|------|------|------|---------|
| `lib_ui` | `colppy/lib_ui/` | React, Storybook, pnpm | Shared UI components |
| `lib_log_nest` | `colppy/lib_log_nest/` | NestJS, TypeScript | Shared logging library |
| `lib_response_nest` | `colppy/lib_response_nest/` | NestJS, TypeScript | Shared response formatting library |

### Migrations

| Repo | Path | Purpose |
|------|------|---------|
| `colppy-migrations` | `colppy/colppy-migrations/` | Laravel-based DB migrations |
| `db_migrations` | `colppy/db_migrations/` | Additional DB migration scripts |

### Testing/QA

| Repo | Path | Purpose |
|------|------|---------|
| `colppy-test-end-to-end` | `colppy/colppy-test-end-to-end/` | E2E test suite |
| `end2end-tests` | `colppy/end2end-tests/` | E2E test suite (separate) |
| `colppy-stress-tests` | `colppy/colppy-stress-tests/` | Load/stress testing |
| `stress-test` | `colppy/stress-test/` | Stress testing (Vue-based UI) |

### Other/Uncategorized Repos

| Repo | Path | Purpose |
|------|------|---------|
| `POC_Monorepo` | `colppy/POC_Monorepo/` | Turborepo monorepo PoC (likely stale) |
| `api-documentation` | `colppy/api-documentation/` | API docs site (no README, has `docs/faq.md`) |
| `app_api_assistant` | `colppy/app_api_assistant/` | AI-powered API assistant app |
| `app_backoffice` | `colppy/app_backoffice/` | Backoffice frontend (Vue) |
| `app_mobile` | `colppy/app_mobile/` | Mobile app |
| `autoregistro-esueldos` | `colppy/autoregistro-esueldos/` | E-sueldos auto-registration |
| `base-reporter` | `colppy/base-reporter/` | Base reporter package (PHP) |
| `colppy-front` | `colppy/colppy-front/` | Legacy Vue frontend |
| `colppy-mpc` | `colppy/colppy-mpc/` | MPC API |
| `colppy-ms-autenticacion` | `colppy/colppy-ms-autenticacion/` | Auth microservice (likely deprecated) |
| `directorioWebsite` | `colppy/directorioWebsite/` | Directorio website |
| `discovery_fusionauth` | `colppy/discovery_fusionauth/` | FusionAuth discovery/PoC |
| `frontera2` | `colppy/frontera2/` | Frontera 2.0 RPC framework (no README, has architecture docs) |
| `storage` | `colppy/storage/` | Storage service (PHP) |
| `vencimientos-backend` | `colppy/vencimientos-backend/` | AFIP tax due dates backend |
| `vencimientos-frontend` | `colppy/vencimientos-frontend/` | AFIP tax due dates frontend (React) |
| `colppy-benjamin` | `nubox-spa/colppy-benjamin/` | Modern API layer (Laravel + OAuth2) |
| `colppy-app` | `nubox-spa/colppy-app/` | Legacy monolith gateway |

## Repos Missing READMEs

These 12 repos have no README file at all:

- `colppy/app_root`
- `colppy/autoregistro-esueldos`
- `colppy/base-reporter`
- `colppy/colppy-test-end-to-end`
- `colppy/docker-recipes`
- `colppy/end2end-tests`
- `colppy/inf_workflows`
- `colppy/lib_ui`
- `colppy/nr_terraform`
- `colppy/sas-colppy-templates-circleci`
- `colppy/sdk_interlink`
- `nubox-spa/colppy-app`

## Gotchas

- **Duplicate repos**: Some libraries exist in both `colppy/` and `nubox-spa/` (e.g., `base-connector`, `authentication-oauth-library`, `paypertic-sdk`, `crmintegration-connector`). The `nubox-spa/` versions are the ones used in production by `colppy-app` and `colppy-benjamin`.
- **Boilerplate READMEs**: Many MFE and NestJS repos have template READMEs ("React + TypeScript + Vite" or "Archetype for Colppy MS") with no actual documentation about the specific service.
- **colppy-app has NO README**: The single most important repo (legacy gateway with 36+ Provisiones, the Frontera RPC layer, and all business logic) has zero documentation.
- **Stale repos**: Some repos appear deprecated but remain in the org: `colppy-ms-autenticacion`, `POC_Monorepo`, `colppy-front`. Do not rely on them.
- **Naming inconsistency**: MFEs use `mfe_` prefix, NestJS services use `svc_`, Lambdas use `svc_*_lambda` or `sas-colppy-*`, connectors use `colppy-*-connector` or just `*-connector`.
- **mfe_authentication lives inside colppy-app**: Unlike all other MFEs (which are standalone repos under `colppy/`), `mfe_authentication` is a subdirectory of `nubox-spa/colppy-app/mfe_authentication/`.
- **colppy-database-connector is NestJS**: Despite being named like the other PHP connectors, `colppy-database-connector` uses Node.js/TypeScript/NestJS (not PHP/Composer).

## Cross-References

- [README.md](README.md) -- Architecture overview
- [backend-architecture.md](backend-architecture.md) -- Deep dive on backend services
- `github-jonetto/REPO_CONTEXT_INDEX.md` -- Full repo inventory with README paths
- `github-jonetto/REPO_OPERATING_SHEET.md` -- How to run each repo locally
