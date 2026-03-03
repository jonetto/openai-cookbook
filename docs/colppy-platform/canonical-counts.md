# Canonical Counts

> Single source of truth for count-sensitive values used across Colppy platform docs.

---

## Counts (As Of 2026-03-03)

| Metric | Canonical Value | Scope/Definition |
|------|------|------|
| Total repositories | 108 | `colppy/` + `nubox-spa/` combined |
| Runtime core repos | 9 | `app_root`, `mfe_authentication`, `mfe_onboarding`, `svc_settings`, `colppy-app`, `colppy-benjamin`, `lib_ui`, `sdk_interlink`, `inf_workflows` |
| MFE repos | 8 | Includes templates/archetypes |
| MFE repos mounted in `app_root` | 2 | `mfe_authentication`, `mfe_onboarding` |
| Provisiones top-level folders | 32 | 31 business Provisiones + `ColppyCommon` shared infra |
| Business Provisiones | 31 | Excludes `ColppyCommon` |
| Lambda repos (total) | 20 | 14 application + 6 infrastructure |
| MySQL tables in shared schema | 207 | `colppy` database |

---

## Update Rules

1. Update this file first when a count changes.
2. Then update any affected narrative docs.
3. Run `bash docs/colppy-platform/docs-check.sh` before commit/merge.

---

*Last updated: 2026-03-03*
