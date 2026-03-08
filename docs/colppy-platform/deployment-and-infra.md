# Deployment & Infrastructure

> Colppy platform CI/CD pipelines, AWS infrastructure, and local development setup.
>
> Cross-references: [Repo Directory](repo-directory.md) | [Backend Architecture](backend-architecture.md) | [Frontend Architecture](frontend-architecture.md)

---

## CI/CD: inf_workflows Hub

Central reusable GitHub Actions workflows at `colppy/inf_workflows/.github/workflows/`.
All service repos call these via `workflow_call`. ~37 repos reference this hub.

### Reusable Workflows

| Workflow file | Purpose | Used by |
|---|---|---|
| `build-and-push-dockerimage.yml` | Build Docker image, Semgrep SAST scan, Trivy vuln scan, push to ECR | NestJS services, PHP services |
| `build-and-push-dockerimage-base.yml` | Build and push base Docker images (no app code) | `inf_docker_images` |
| `build-and-push-dockerimage-base-with-tag.yml` | Base image build with explicit tag | `inf_docker_images` |
| `build-and-push-dockerimage-base-with-security-scan.yml` | Base image build + Trivy/Semgrep | `inf_docker_images` |
| `build-and-push-dockerimage-manual.yml` | Manual trigger Docker build | Ad-hoc rebuilds |
| `helm-chart-deploy.yml` | Package Helm chart, push to S3 repo, deploy to EKS | NestJS services, PHP services |
| `helm-chart-deploy-manual.yml` | Manual trigger Helm deployment | Hotfixes, rollbacks |
| `mfe-build-and-deploy.yml` | Build MFE, sync to S3, invalidate CloudFront | `mfe_*` repos |
| `mfe-gitlab-flow.yml` | GitLab-flow variant for MFE repos | Select MFE repos |
| `spa-build-and-deploy.yml` | Build SPA, sync to S3, invalidate CloudFront | `app_root`, `app_backoffice` |
| `spa-gitlab-flow.yml` | GitLab-flow variant for SPA repos | Select SPA repos |
| `build-and-deploy-lambda-sam.yml` | SAM build + deploy Lambda functions | `svc_*_lambda` repos |
| `terraform-ci-cd.yml` | Terraform fmt, plan, apply + Infracost | `inf_terraform_aws`, `inf_terraform_testing` |
| `mfe_archetype-createrepo.yml` | Scaffold new MFE repo from archetype | One-time repo creation |
| `nestjs_archetype-createrepo.yml` | Scaffold new NestJS repo from archetype | One-time repo creation |
| `svc_lambda_tempate_createrepo.yml` | Scaffold new Lambda repo from template | One-time repo creation |

### Branch-to-Environment Mapping

All workflows share a consistent branch mapping:

| Branch pattern | Environment | AWS Account ID | ECR URL | Runner |
|---|---|---|---|---|
| `master` | `prod` | `185428918146` | `185428918146.dkr.ecr.us-east-1.amazonaws.com` | `runner-prod` |
| `release/*` | `stg` | `599636274800` | `599636274800.dkr.ecr.us-east-1.amazonaws.com` | `runner-stg` |
| `develop` | `test` | `828685354428` | `828685354428.dkr.ecr.us-east-1.amazonaws.com` | `runner-test` |
| `feature/*` | `test` | `828685354428` | `828685354428.dkr.ecr.us-east-1.amazonaws.com` | `runner-test` |
| `migration/*` | `develop` | `962781397405` | `962781397405.dkr.ecr.us-east-1.amazonaws.com` | `develop` |

- `feature/*` branches build and scan but **skip deploy** (no S3 sync, no Helm deploy)
- Commit message `[SKIP DEPLOY]` skips the entire pipeline
- Repos containing `archetype` in the name are always skipped

### Secrets Management

- All workflows pull secrets from **AWS Secrets Manager** at `{repo_name}/{environment}`
- Secrets are extracted into `.env` files at build time
- Secrets are **not** stored in the repo; `.env.example` serves as the template

---

## Deployment Patterns

| Service type | Build artifact | Registry/Storage | Deploy target | Workflow |
|---|---|---|---|---|
| **MFE** (micro-frontend) | Static JS/CSS bundle | S3 bucket `{env}-colppy-mfe/{repo}` | CloudFront CDN | `mfe-build-and-deploy.yml` |
| **SPA** (single-page app) | Static JS/CSS bundle | S3 bucket `{env}-colppy-frontend/` | CloudFront CDN | `spa-build-and-deploy.yml` |
| **NestJS service** | Docker image | ECR `{account}.dkr.ecr.us-east-1.amazonaws.com/{repo}` | EKS via Helm | `build-and-push-dockerimage.yml` + `helm-chart-deploy.yml` |
| **PHP service** | Docker image | ECR `{account}.dkr.ecr.us-east-1.amazonaws.com/{repo}` | EKS via Helm | `build-and-push-dockerimage.yml` + `helm-chart-deploy.yml` |
| **Lambda** | SAM package | S3 bucket `{env}-colppy-{repo-name}` | CloudFormation/SAM | `build-and-deploy-lambda-sam.yml` |
| **Terraform** | Plan/Apply | S3 state backend | AWS resources | `terraform-ci-cd.yml` |

### Docker Build Pipeline (NestJS / PHP)

```
checkout inf_docker_images (Dockerfile) → checkout app code into {name}/app/
  → pull secrets from AWS Secrets Manager → write .env
  → docker build (ECR base images) → Semgrep SAST scan → Trivy image scan
  → docker push to ECR → Helm package → Helm push to S3 chart repo
  → aws eks update-kubeconfig → helm upgrade --install to EKS namespace
```

### MFE / SPA Build Pipeline

```
checkout app code → pull secrets from AWS Secrets Manager → write .env
  → docker run node:21 (pnpm install && pnpm run build)
  → aws s3 sync ./dist/ to S3 bucket
  → aws cloudfront create-invalidation --paths '/*'
  → git tag (master only)
```

### Lambda SAM Pipeline

```
checkout app code → configure VPC/subnet IDs per environment
  → load secrets into .env (if env-example.* exists)
  → sam build --use-container → sam deploy --stack-name {bucket-name}
  → creates S3 bucket if not exists
```

---

## AWS Infrastructure

### Terraform: inf_terraform_aws

Structure: `colppy/inf_terraform_aws/`

```
inf_terraform_aws/
  engine/              # Terraform resource definitions (~50 .tf files)
  common/              # Shared Terraform configs
  data/
    colppy-main/       # Main account
    colppy-prod/       # Production account data
    colppy-stg/        # Staging account data
    colppy-test/       # Test account data
    colppy-sec/        # Security account data
```

### Key Terraform Modules (engine/)

| Module file | AWS resources managed |
|---|---|
| `eks.tf` | EKS clusters (`{ENV}-N-EKS-cluster`) |
| `rds.tf` | RDS / Aurora Serverless databases |
| `ecr.tf` | ECR container registries (one per service) |
| `s3.tf` | S3 buckets (MFE assets, Helm charts, Lambda packages, backups) |
| `cloudfront.tf` | CloudFront distributions (MFE, SPA) |
| `ecs_cluster.tf`, `ecs_service.tf` | ECS clusters and services (legacy workloads) |
| `ec2.tf`, `autoscaling_group.tf` | EC2 instances and ASGs |
| `lambda.tf` | Lambda function infrastructure |
| `vpc.tf`, `subnet.tf`, `nat.tf` | VPC networking |
| `load_balancer.tf`, `targetgroup.tf` | ALB/NLB load balancers |
| `secrets.tf` | AWS Secrets Manager entries |
| `iamrole.tf`, `iampolicy.tf` | IAM roles and policies |
| `kms.tf` | KMS encryption keys |
| `route53zoneassoc.tf` | DNS zone associations |
| `transitgateway.tf` | Transit Gateway for cross-VPC connectivity |
| `cloudwatch_alarms.tf`, `cloudwatch_dashboard.tf` | Monitoring and alerting |
| `codedeploy.tf` | CodeDeploy applications (legacy) |

### AWS Organizations (Multi-Account)

| Account | ID | Purpose | Terraform data dir |
|---|---|---|---|
| **main** (management) | `185428918146` | Organization root, shared services, billing | `data/colppy-main/` |
| **prod** | `185428918146` | Production workloads | `data/colppy-prod/` |
| **stg** | `599636274800` | Staging/QA | `data/colppy-stg/` |
| **test** | `828685354428` | Test/dev workloads | `data/colppy-test/` |
| **sec** | `962781397405` | Security tooling, develop environment | `data/colppy-sec/` |

Cross-account connectivity via **Transit Gateway** (`transitgateway.tf`). Each account has its own VPC, subnets, NAT gateways.

### Terraform Data-Driven Engine

The `inf_terraform_aws` repo uses a **data-driven engine pattern** — a single `engine/` directory with ~50 `.tf` resource definitions, parameterized by per-account JSON/HCL data files in `data/colppy-{env}/`. This avoids duplicating Terraform code per environment. The CI pipeline (`terraform-ci-cd.yml`) runs `fmt`, `plan`, and `apply` with Infracost cost estimation.

Workspace assembly (`bin/colppy-{env}.sh`): cleans a `workspace/` directory, copies `common/providers.tf.json` + env-specific data files from `data/colppy-{env}/`, then copies only the `engine/*.tf` modules that environment needs. Terraform runs against the assembled `workspace/`. State is stored in S3 (configured in `data/colppy-{env}/backend.tf.json`).

### Compute: EKS Clusters

Each environment runs an EKS managed Kubernetes cluster:

| Environment | Cluster name | Node type | Nodes | Disk |
|---|---|---|---|---|
| prod | `PROD-N-EKS-cluster` | `t3a.large` | 6 | 50 GB |
| stg | `STG-N-EKS-cluster` | `t3a.large` | 2 | 50 GB |
| test | `TEST-N-EKS-cluster` | `t3a.xlarge` | 1 | 50 GB |
| develop | `DEVELOP-N-EKS-cluster` | `t3a.large` | 1 | 50 GB |

- Managed node groups with auto-scaling
- All PHP and NestJS services deploy as Helm releases into these clusters
- Monitoring: New Relic Kubernetes integration (`newrelic` Helm chart) + CloudWatch alarms
- Resource right-sizing: Goldilocks VPA (`goldilocks` Helm chart)

### Compute: ECS Fargate

**FusionAuth** runs on **ECS Fargate** (not EKS) — it's the only service using this pattern. Defined in `ecs_cluster.tf` + `ecs_service.tf`. This separates the identity provider from the application workloads on EKS.

### Database

#### Production Main DB: Self-Managed MySQL 5.6 on EC2

> **Verified 2026-03-08** via direct production query (`SELECT VERSION()`, `SHOW VARIABLES`).

The main `colppy` database runs on a **self-managed MySQL 5.6.51 instance on EC2**, NOT on Aurora or RDS.

| Attribute | Value | Evidence |
|---|---|---|
| Engine | MySQL 5.6.51-log | `SELECT VERSION()` |
| Hosting | EC2 (`ip-10-10-2-148.ec2.internal`) | `SHOW VARIABLES LIKE 'hostname'` |
| Data directory | `/mysql/prod_n_db_colppy_56/` | `SHOW VARIABLES LIKE 'datadir'` |
| Buffer pool | ~285 GB | `innodb_buffer_pool_size` |
| Max connections | 3,000 (peak observed: 2,726) | `SHOW VARIABLES`, `SHOW GLOBAL STATUS` |
| Server charset | `latin1` (latin1_swedish_ci) | `character_set_server`, `collation_server` |
| SSL/TLS | DISABLED | `have_ssl: DISABLED` |
| Binary logging | ON | `log_bin: ON` |
| Auth plugin | `mysql_native_password` (MySQL 5.6 default) | N/A on 5.6 |

- NOT Aurora (0 `aurora_*` variables)
- NOT RDS (0 `rds_*` variables, `basedir: /usr/` not `/rdsdbbin/`)
- Connection endpoint: `colppydb-prod.colppy.com:3306` (CNAME → EC2 internal IP, requires VPN)
- Latin1 encoding on most core tables (`empresa`, `usuario`, `facturacion`, `pago`, `plan`, `usuario_empresa`)

#### Aurora Serverless v2 Clusters (Terraform-defined)

The following Aurora clusters are defined in `rds.tf` in `inf_terraform_aws`. These are provisioned via Terraform but the **main `colppy` schema still lives on the legacy EC2 MySQL 5.6 instance above**, not on these clusters:

| Cluster | Engine | ACU range | Purpose |
|---|---|---|---|
| `{env}-n-rds-microservices` | Aurora MySQL 8.0 (3.08.2) | 0.5–3 ACU | Microservices DB (target for migration) |
| `{env}-n-rds-microservices-pgsql` | Aurora PostgreSQL 15.12 | 0.5–3 ACU | PostgreSQL workloads |
| `{env}-n-rds-afip-pgsql` | Aurora PostgreSQL 15.12 | 0.5–7 ACU | AFIP/ARCA service (higher max for tax API load) |
| `{env}-n-rds-paybook` | Aurora MySQL 8.0 | 0.5–3 ACU | Paybook banking integration |
| `{env}-rds-fusionauth` | Aurora PostgreSQL | 0.5–3 ACU | FusionAuth identity store (test/stg only) |

- Aurora Serverless v2 scales compute automatically (no fixed instance size)
- Writer + Reader separation in prod for read scaling
- Encrypted at rest, 12-day backup retention (prod)
- Auto-pause after 600s idle (non-prod)
- RDS credentials auto-generated by Terraform (`random_password`) and stored in Secrets Manager at `{cluster}/credentials`
- `inf_rds_auto_shutdown_startup_lambda` auto-stops non-prod clusters during off-hours (cost savings)
- `sas-colppy-cloudops-rdsrestoretostaging-lambda` restores prod snapshots to staging for data refresh

> **Migration status**: The main `colppy` schema has NOT been migrated from EC2 MySQL 5.6 to Aurora MySQL 8.0. The Aurora clusters exist but the legacy database remains the production source of truth for Frontera, Benjamin, and NestJS services.

### Cost Optimization

| Lambda | Purpose |
|---|---|
| `inf_eks_auto_shutdown_startup_lambda` | Auto-stops/starts non-prod EKS node groups on schedule |
| `inf_rds_auto_shutdown_startup_lambda` | Auto-stops/starts non-prod Aurora clusters on schedule |

These Lambdas significantly reduce non-prod AWS costs by shutting down compute during nights and weekends.

### Helm Charts: inf_helm_charts

Location: `colppy/inf_helm_charts/charts/`

| Chart | Service deployed |
|---|---|
| `svc_afip` | AFIP/ARCA integration service (NestJS) |
| `svc_backoffice` | Backoffice API (PHP/Laravel) |
| `svc_importer` | Data import service (PHP) |
| `svc_importer_data` | Import data processor |
| `svc_integracion_crm` | CRM integration service (PHP) |
| `svc_integracion_paybook` | Paybook integration service (PHP) |
| `svc_inventory` | Inventory service (NestJS) |
| `svc_mercado_pago` | Mercado Pago integration |
| `svc_reporter` | Reporting service (PHP) |
| `svc_sales` | Sales service (NestJS) |
| `svc_settings` | Settings/session service (NestJS) |
| `svc_utils` | Utilities service |
| `goldilocks` | Kubernetes resource right-sizing (VPA) |
| `newrelic` | New Relic Kubernetes integration |

- Charts are stored in S3: `s3://{env}-colppy-inf-helm-charts/{chart-name}/`
- Uses `helm-s3` plugin for S3-based Helm repos
- Per-environment `values.yaml-{env}` files with placeholder substitution (`ENV`, `ID`, `CERT`, `VERSION`)

### Docker Base Images: inf_docker_images

Location: `colppy/inf_docker_images/`

| Image | Purpose |
|---|---|
| `php_base_5.6` | PHP 5.6 base (legacy colppy-app) |
| `php_base_7.1` | PHP 7.1 base |
| `php_base_7.4` | PHP 7.4 base (most PHP services) |
| `php_base_8.2` | PHP 8.2 base (newer PHP services) |
| `node_base_21` | Node.js 21 base (NestJS services) |
| `node_base_tls` | Node.js with custom TLS config |
| `nginx_base` | Nginx reverse proxy base |
| `nginx_base_node` | Nginx + Node.js combo |
| `applicaciones_laravel` | Laravel application base |
| `applicaciones_nestjs` | NestJS application base |

---

## Key Infrastructure Repos

| Repo | Purpose |
|---|---|
| `inf_workflows` | Central reusable GitHub Actions workflows |
| `inf_terraform_aws` | Terraform IaC for all AWS accounts (prod, stg, test, sec, main) |
| `inf_terraform_testing` | Terraform testing/validation |
| `inf_helm_charts` | Helm charts for all EKS-deployed services |
| `inf_docker_images` | Base Docker images (PHP 5.6/7.1/7.4/8.2, Node 21, Nginx) |
| `inf_organizations_tf` | AWS Organizations Terraform |
| `inf_eks_auto_shutdown_startup_lambda` | Lambda to auto-start/stop EKS clusters (cost savings) |
| `inf_rds_auto_shutdown_startup_lambda` | Lambda to auto-start/stop RDS instances (cost savings) |
| `inf_SNSToSlack_lambda_lambda` | SNS-to-Slack notification Lambda |
| `inf_lt_colppyapp_userdata` | EC2 launch template user data scripts |
| `nr_terraform` | New Relic Terraform configuration |
| `cloudops-infra-policies` | CloudOps infrastructure policies (OPA/Sentinel) |
| `dockervm` | Local Docker development environment |
| `docker-recipes` | Shared Docker recipes/snippets |
| `sas-colppy-dockerfiles` | Additional Dockerfiles |
| `sas-colppy-infrastructure-cdk` | AWS CDK infrastructure (legacy/experimental) |
| `sas-colppy-github-pipelines-templates` | GitHub Actions pipeline templates |
| `sas-colppy-templates-circleci` | CircleCI templates (legacy, being migrated) |
| `sas-colppy-deploymentTools` | Deployment helper scripts |
| `sas-colppy-adminTools` | Admin/ops tooling |
| `sas-colppy-fusionauth` | FusionAuth configuration and setup |
| `sas-colppy-slackCommands` | Slack bot commands for ops |
| `sas-colppy-updateRundeckDNS` | Rundeck DNS update automation |
| `sas-colppy-cloudops-rdsrestoretostaging-lambda` | Lambda to restore RDS snapshots to staging |
| `sas-colppy-commandManagement-lambda` | Command management Lambda |
| `sas-colppy-auth-lambda` | Authentication Lambda |

See [Repo Directory](repo-directory.md) for the full listing including application repos.

---

## Local Development: dockervm

Location: `colppy/dockervm/`

### Quick Start

Run `bash setup-local.sh` from `dockervm/`. Use `--clone` to auto-clone missing repos. The script automates Docker images, DB loading, symlinks, certs, and stub endpoints. App is at **http://localhost:8080** (no /etc/hosts needed). One-click login: `http://localhost:8080/set-dev-cookie`. See `colppy/dockervm/README.md` for full instructions.

### Prerequisites

- Docker >= 20.0, Docker Compose >= 2.0
- pnpm (`npm install -g pnpm`)
- mkcert (optional, for HTTPS)
- Linux (Ubuntu/Debian) or macOS (OrbStack)
- SSH access to GitHub repos
- Estimated setup time: ~15-30 min (first run, with repos cloned)

### Repo Structure (sibling orgs)

`setup-local.sh` expects `colppy/` and `nubox-spa/` as **sibling directories**. It creates symlinks in `dockervm/code/` pointing to the actual repo paths. Repos do **not** need to be cloned into `code/` — the script symlinks them.

```
parent/  (e.g. github-jonetto/ or ~/colppy/)
├── colppy/                    # COLPPY_REPO
│   ├── dockervm/              # setup-local.sh lives here
│   ├── lib_ui/                # REQUIRED
│   ├── mfe_dashboard/
│   ├── colppy-vue/            # symlinked as code/mfe_vue
│   ├── svc_settings/
│   ├── svc_afip/
│   └── inf_docker_images/
└── nubox-spa/                 # NUBOX_REPO
    ├── colppy-app/            # REQUIRED
    ├── colppy-benjamin/
    ├── colppy-authentication-oauth-library/
    └── colppy-paypertic-sdk/
```

### Required Repos

| Repo | Path | Required |
|------|------|----------|
| colppy-app | `nubox-spa/colppy-app/` | Yes |
| lib_ui | `colppy/lib_ui/` | Yes |
| colppy-benjamin | `nubox-spa/colppy-benjamin/` | For full stack |
| mfe_dashboard | `colppy/mfe_dashboard/` | For dashboard MFE |
| svc_settings, svc_afip | `colppy/svc_*/` | For NestJS services |
| colppy-vue | `colppy/colppy-vue/` | For Vue frontend (symlinked as mfe_vue) |

### Docker Compose Services

| Service | Image/Base | IP (default subnet) | Local domain | Auto-start |
|---|---|---|---|---|
| `mysql` | `mysql:5.6` | `${MYSQL_IP}` (port 3306) | -- | Yes |
| `mysql-8` | `mysql:8.0.32` | `${MYSQL8_IP}` (port 3307) | -- | Yes |
| `redis` | `redis` | `${REDIS_IP}` (port 6379) | -- | Yes |
| `postgresql` | postgres | -- | -- | Yes |
| `colppy` + `colppy-lb` | PHP + Nginx LB | `172.18.0.151` | `local.colppy.com` | Yes |
| `benjamin2` + `benjamin2-lb` | Laravel + Nginx LB | `172.18.0.152` | `local.benjamin2.com` | Yes |
| `colppy-vue` | Node | -- | Served via colppy-lb | Yes |
| `reporter` | PHP | `172.18.0.154` | `local.reporter.com` | Yes |
| `importer` | PHP | `172.18.0.158` | `local.importer.com` | Yes |
| `integration-crm` | PHP | `172.18.0.159` | `local.integracioncrm.com` | Yes |
| `integration-paybook` + nginx | PHP | `172.18.0.161` | `local.integracionpaybook.com` | Yes |
| `backoffice` | PHP | `172.18.0.162` | `local.backoffice.com` | Yes |
| `fusionauth` | FusionAuth | `172.18.0.163` | `local.fusionauth.com` | Yes |
| `svc-afip-lb` + `svc-afip-node` | Nginx LB + Node | `172.18.0.164` | `local.arca.colppy.com` | LB yes, Node manual |
| `svc-settings-lb` + `svc-settings-node` | Nginx LB + Node | `172.18.0.165` | `local.settings.colppy.com` | LB yes, Node manual |
| `localstack` | LocalStack | -- | -- | Yes |
| `search` | Elasticsearch | -- | -- | Yes |

### /etc/hosts Entries

```
172.18.0.151    local.colppy.com
172.18.0.152    local.benjamin2.com
172.18.0.154    local.reporter.com
172.18.0.158    local.importer.com
172.18.0.159    local.integracioncrm.com
172.18.0.161    local.integracionpaybook.com
172.18.0.162    local.backoffice.com
172.18.0.163    local.fusionauth.com
172.18.0.164    local.arca.colppy.com
172.18.0.165    local.settings.colppy.com
```

### SSL Certificates

- Self-signed certs generated per service via `certificates/add-certificate.sh {name}`
- Stored in `dockervm/certificates/{service}/`
- Mounted into Nginx LB containers

### NestJS Services (Manual Start)

`svc_settings` and `svc_afip` are **not** auto-started by `docker compose up`. Start manually:

```bash
docker exec -it colppy-svc-settings-node-1 bash
cp .env.example .env
pnpm install
pnpm run migration:run
pnpm run start:dev
```

- The Nginx LB containers (`svc-settings-lb`, `svc-afip-lb`) **do** auto-start and proxy HTTPS to port 3000
- If running both simultaneously, change the port in one service's `.env`

---

## Environment Progression

Two deployment flows coexist. Repos are migrating from **Classic** to **GitLab Flow**.

### Classic Flow (most backend services, legacy SPAs)

```
local (dockervm)  -->  test (develop branch)  -->  stg (release/* branch)  -->  prod (master branch)
     |                      |                          |                           |
  Docker Compose       AWS Account               AWS Account                 AWS Account
  Self-signed SSL      828685354428              599636274800                185428918146
  MySQL 5.6/8.0        EKS test cluster          EKS stg cluster             EKS prod cluster
  LocalStack           Real AWS services         Real AWS services           Real AWS services
```

| Stage | Trigger | Deploy target | AWS Account | EKS Cluster |
|---|---|---|---|---|
| **local** | `docker compose up` | Local Docker | N/A | N/A |
| **test** | Push to `develop` or `feature/*` | EKS (test), S3+CF (MFE) | `828685354428` | `TEST-N-EKS-cluster` |
| **stg** | Push to `release/*` | EKS (stg), S3+CF (MFE) | `599636274800` | `STG-N-EKS-cluster` |
| **prod** | Push to `master` | EKS (prod), S3+CF (MFE) | `185428918146` | `PROD-N-EKS-cluster` |
| **develop** | Push to `migration/*` | EKS (develop) | `962781397405` | `DEVELOP-N-EKS-cluster` |

- `feature/*` branches build and scan only (no deploy to EKS, no S3 sync)
- Version is read from `composer.json` (PHP) or `package.json` (Node) -- no manual version bumping in CI
- `master` deploys auto-create a git tag `v{version}` (MFE/SPA repos)

### GitLab Flow (newer MFE/SPA repos)

Uses `spa-gitlab-flow.yml` or `mfe-gitlab-flow.yml`. Branch-to-environment mapping is different:

```
test branch  ──>  staging branch  ──>  master branch
     |                  |                    |
  test env          stg env             prod env
  828685354428     599636274800        185428918146
```

| Branch | Environment | Runner | CloudFront Distribution |
|---|---|---|---|
| `test` | `test` | `runner-test` | `ELHHSC3FWH5EO` |
| `staging` | `stg` | `runner-stg` | `EPVXXAC3PG2SY` |
| `master` | `prod` | `runner-prod` | `E191CN8OL6L6RY` |
| `migration/*` | `develop` | `develop` | `EJUMHQGE7UNE6` |
| `feature/*`, `bugfix/*`, `hotfix/*` | `test` (build validation only, no deploy) | `runner-test` | -- |

Promotion flow: PRs merge into `test`, then `test` is merged into `staging`, then `staging` into `master`. Feature/bugfix/hotfix branches trigger build validation on PR but only deploy when merged into `test`.

Repos using GitLab Flow: `mfe_authentication`, `mfe_onboarding`, `mfe_dashboard`, `mfe_vue`, `mfe_mercado_pago`, `svc_importer_data`, `app_root`, `app_backoffice` (check each repo for `gitlab_flow.yml`).

### Environment URLs (CloudFront Aliases)

| Service | Test (internal) | Staging | Production |
|---|---|---|---|
| **Main App (SPA)** | `app.test.internal.colppy.com` | `app.stg.colppy.com` | `app.colppy.com` |
| **MFE Shell** | `mfe.test.internal.colppy.com` | `mfe.stg.colppy.com` | `mfe.colppy.com` |
| **Legacy Vue** | `vue.test.internal.colppy.com` | `vue.stg.colppy.com` | `vue.colppy.com` |
| **Backoffice** | `backoffice.test.internal.colppy.com` | `backoffice.stg.internal.colppy.com` | `backoffice.prod.internal.colppy.com` |
| **Legacy PHP App** | `staging.colppy.com` (redirected from app.stg) | `staging.colppy.com` | `app.colppy.com` |
| **Auth API** | `api.test.internal.colppy.com/auth/` | -- | -- |

**Note**: Test environment uses `*.internal.colppy.com` domains (require VPN/internal network access). Staging uses `*.stg.colppy.com` (publicly accessible). After MFE login, the browser redirects to `staging.colppy.com` (legacy PHP app on EKS, not on CloudFront).

### S3 Bucket Naming

| Type | Pattern | Example (staging) |
|---|---|---|
| MFE assets | `{env}-colppy-mfe` | `stg-colppy-mfe` |
| SPA/Frontend | `{env}-colppy-frontend` | `stg-colppy-frontend` |
| Backoffice | `{env}-colppy-backoffice-frontend` | `stg-colppy-backoffice-frontend` |
| Vue legacy | `{env}-colppy-vue-frontend` | `stg-colppy-vue-frontend` |

MFEs deploy to `s3://{env}-colppy-frontend/{repo_name}/` (subdirectory per MFE). `app_root` deploys to the bucket root.

---

## Security Scanning

All Docker builds include two scan stages (both `continue-on-error: true`, non-blocking):

| Scanner | Type | What it checks |
|---|---|---|
| **Semgrep** | SAST (static code) | Source code in app directory, auto-configured rules |
| **Trivy** | Container image scan | OS packages, library vulns, embedded secrets |

- Results are uploaded as GitHub Actions artifacts (`security-scan-results-{run_id}`, 7-day retention)
- Summary tables appear in the GitHub Actions run summary
- Currently **advisory only** -- scans do not block the push to ECR

---

## Gotchas

- **dockervm repo structure**: `setup-local.sh` creates symlinks in `dockervm/code/` pointing to `colppy/` and `nubox-spa/` sibling directories. Repos can live in those sibling paths — they do not need to be cloned into `code/` directly.

- **Branch compatibility**: Some repos may require `feature/update-docker-services` for dockervm. Check each repo's README; `setup-local.sh` does not enforce branch checks.

- **PHP version varies by service**: Base images range across PHP 5.6, 7.1, 7.4, and 8.2. Check `inf_docker_images/` for which base a service uses. `colppy-app` (legacy) uses 5.6; most services use 7.4; newer services may use 8.2.

- **CircleCI templates still exist**: `sas-colppy-templates-circleci` remains in the org. Some repos may still have `.circleci/config.yml` files alongside `.github/workflows/`. The canonical CI/CD is now GitHub Actions via `inf_workflows`.

- **NestJS services require manual start locally**: `svc_settings` and `svc_afip` do not auto-start with `docker compose up`. You must `docker exec` into their node containers and run `pnpm run start:dev`. The Nginx LB containers that proxy HTTPS to them do auto-start.

- **Self-hosted runners per environment**: Workflows use self-hosted runners (`runner-prod`, `runner-stg`, `runner-test`). If a runner is down, the pipeline hangs indefinitely. The `develop` environment uses a runner literally named `develop`.

- **Helm values files are per-environment**: Each chart has `values.yaml-prod`, `values.yaml-stg`, `values.yaml-test`. The workflow renames the correct one to `values.yaml` and substitutes `ENV`, `ID`, `CERT`, `VERSION` placeholders via `sed`.

- **ECR login required for Docker builds**: Base images are stored in ECR, not Docker Hub. The build step logs into ECR before `docker build` to pull base images. If ECR creds expire or the runner loses IAM access, builds fail at the `FROM` stage.

- **S3 sync for special services**: `svc_backoffice` and `svc_afip` sync files from S3 (`s3://{env}-colppy-backoffice`, `s3://{env}-colppy-afip`) into a `storage/` directory before Docker build. Missing S3 data will cause runtime failures.

- **app_root vs other SPAs**: In `spa-build-and-deploy.yml`, `app_root` deploys to the S3 bucket root (`s3://{env}-colppy-frontend/`). All other SPAs deploy to a subdirectory (`s3://{env}-colppy-frontend/{repo}/`). Wrong naming breaks routing.

- **Five AWS accounts in use**: main, prod, stg, test, sec -- each with its own Terraform data directory in `inf_terraform_aws/data/`. Cross-account resources use Transit Gateway.

- **Two deployment flows coexist**: Some repos use Classic (develop/release/master), newer MFE repos use GitLab Flow (test/staging/master). When someone says "deployed to staging", check which flow the repo uses -- in GitLab Flow, PRs merge to `test` first, then promote to `staging`. In Classic, PRs merge to `develop` or `release/*`. The environment deployed depends on the branch, not the PR title.

- **Staging != Test in GitLab Flow repos**: For MFEs using `gitlab_flow.yml`, merging a PR into `test` deploys to the **test** environment (`*.test.internal.colppy.com`), NOT staging. To reach staging, `test` must be merged into the `staging` branch. This distinction matters for QA validation.

- **FusionAuth vs dev session**: `setup-local.sh` creates a dev session and cookie (`loginPasswordCookie`) to **bypass** the FusionAuth login flow. You can use the app immediately without configuring FusionAuth. For real login via FusionAuth: run the FusionAuth setup wizard, then `php artisan importar:usuarios` inside the Benjamin container.

- **Local database setup**: `setup-local.sh` loads `backup-database/colppy.sql` and `frontera2.sql` automatically. If missing, it downloads from `DB_BACKUP_BASE_URL` (set in `.env` for standalone setup). Manual: place dumps in `backup-database/` or `docker cp` into MySQL.

- **Version source differs by language**: PHP services read version from `composer.json`; Node services from `package.json`. If neither has a `version` field, the image version will be empty and the push/deploy will fail.

---

*Last updated: 2026-03-06*
