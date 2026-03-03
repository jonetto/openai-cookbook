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

### Prerequisites

- Docker >= 20.0, Docker Compose >= 2.0
- Linux (Ubuntu/Debian preferred)
- Node.js >= 16
- SSH access to GitHub repos
- Estimated setup time: ~45-60 minutes (first run)

### Required Repos (cloned into `dockervm/code/`)

```
dockervm/code/
  colppy-app/                 # Main PHP app (nubox-spa org)
  colppy-benjamin/            # Benjamin API (nubox-spa org, Laravel)
  mfe_vue/                    # Vue MFE
  svc_importer/               # Importer service
  svc_integracion_crm/        # CRM integration
  svc_backoffice/             # Backoffice service
  app_backoffice/             # Backoffice frontend
  svc_integracion_paybook/    # Paybook integration
  svc_reporter/               # Reporter service
  svc_settings/               # Settings service (NestJS)
  svc_afip/                   # AFIP/ARCA service (NestJS)
  paypertic-sdk/              # PayPerTic SDK
  authentication-oauth-library/  # OAuth library
```

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

- **dockervm requires repos in `code/` subdirectory**: All repos must be cloned into `dockervm/code/`. The Docker Compose volume mounts expect this structure. Cloning repos elsewhere will cause mount failures.

- **Required branch for local dev**: `mfe_vue`, `colppy-app`, `colppy-benjamin`, and `svc_settings` must be on `feature/update-docker-services` branch for dockervm compatibility.

- **PHP version varies by service**: Base images range across PHP 5.6, 7.1, 7.4, and 8.2. Check `inf_docker_images/` for which base a service uses. `colppy-app` (legacy) uses 5.6; most services use 7.4; newer services may use 8.2.

- **CircleCI templates still exist**: `sas-colppy-templates-circleci` remains in the org. Some repos may still have `.circleci/config.yml` files alongside `.github/workflows/`. The canonical CI/CD is now GitHub Actions via `inf_workflows`.

- **NestJS services require manual start locally**: `svc_settings` and `svc_afip` do not auto-start with `docker compose up`. You must `docker exec` into their node containers and run `pnpm run start:dev`. The Nginx LB containers that proxy HTTPS to them do auto-start.

- **Self-hosted runners per environment**: Workflows use self-hosted runners (`runner-prod`, `runner-stg`, `runner-test`). If a runner is down, the pipeline hangs indefinitely. The `develop` environment uses a runner literally named `develop`.

- **Helm values files are per-environment**: Each chart has `values.yaml-prod`, `values.yaml-stg`, `values.yaml-test`. The workflow renames the correct one to `values.yaml` and substitutes `ENV`, `ID`, `CERT`, `VERSION` placeholders via `sed`.

- **ECR login required for Docker builds**: Base images are stored in ECR, not Docker Hub. The build step logs into ECR before `docker build` to pull base images. If ECR creds expire or the runner loses IAM access, builds fail at the `FROM` stage.

- **S3 sync for special services**: `svc_backoffice` and `svc_afip` sync files from S3 (`s3://{env}-colppy-backoffice`, `s3://{env}-colppy-afip`) into a `storage/` directory before Docker build. Missing S3 data will cause runtime failures.

- **app_root vs other SPAs**: In `spa-build-and-deploy.yml`, `app_root` deploys to the S3 bucket root (`s3://{env}-colppy-frontend/`). All other SPAs deploy to a subdirectory (`s3://{env}-colppy-frontend/{repo}/`). Wrong naming breaks routing.

- **Five AWS accounts in use**: main, prod, stg, test, sec -- each with its own Terraform data directory in `inf_terraform_aws/data/`. Cross-account resources use Transit Gateway.

- **FusionAuth import required for local login**: After setting up FusionAuth locally, you must run `php artisan importar:usuarios` inside the Benjamin container. Without this, no users exist and login fails silently.

- **Local database setup is manual**: You must `docker cp` SQL dumps into the MySQL container and import them. There is no automated migration or seed for the local MySQL databases (`colppy`, `frontera2`).

- **Version source differs by language**: PHP services read version from `composer.json`; Node services from `package.json`. If neither has a `version` field, the image version will be empty and the push/deploy will fail.

---

*Last updated: 2026-03-03*
