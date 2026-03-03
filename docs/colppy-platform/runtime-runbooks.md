# Runtime Core Runbooks

> Operational quick cards for the 9 runtime core repos.
> Ownership metadata is not formally defined yet, so owner/on-call fields are placeholders.

---

## Runbook Cards

| Repo | Path | Start (Local) | Test/Smoke | Deploy Workflow | Owner | On-call |
|------|------|------|------|------|------|------|
| `app_root` | `colppy/app_root/` | `pnpm install && pnpm dev` (9000) | UI loads at `http://localhost:9000` | `spa-build-and-deploy.yml` | TBD | TBD |
| `mfe_authentication` | `nubox-spa/colppy-app/mfe_authentication/` | `pnpm install && pnpm dev` | Login page renders in shell or standalone dev URL | `mfe-build-and-deploy.yml` | TBD | TBD |
| `mfe_onboarding` | `colppy/mfe_onboarding/` | `pnpm install && pnpm dev` (9002 typical) | Wizard route `/inicio` loads and submits | `mfe-build-and-deploy.yml` | TBD | TBD |
| `svc_settings` | `colppy/svc_settings/` | `pnpm install && pnpm run start:dev` (3000) | `POST /login`, `GET /session-info`, `POST /finish-onboarding` | `build-and-push-dockerimage.yml` + `helm-chart-deploy.yml` | TBD | TBD |
| `colppy-app` | `nubox-spa/colppy-app/` | `docker-compose up` | Frontera call to `/lib/frontera2/service.php` returns expected envelope | legacy Docker/ops flow | TBD | TBD |
| `colppy-benjamin` | `nubox-spa/colppy-benjamin/` | project-specific Laravel startup | `GET /api/v1/*` returns with valid OAuth2 token | service Docker + Helm flow | TBD | TBD |
| `lib_ui` | `colppy/lib_ui/` | `pnpm install && pnpm storybook` | components render + package build succeeds | npm package publish workflow | TBD | TBD |
| `sdk_interlink` | `colppy/sdk_interlink/` | `pnpm install && pnpm build` | token/cookie helpers integrated in MFEs | package/library release workflow | TBD | TBD |
| `inf_workflows` | `colppy/inf_workflows/` | edit/reuse workflow files | validate via dependent repo pipeline run | N/A (this repo defines workflows) | TBD | TBD |

---

## Minimum Metadata To Fill Later

When ownership is ready, add these fields for each card:

- team owner
- technical owner
- escalation Slack channel
- severity-1 paging rotation

---

*Last updated: 2026-03-03*
