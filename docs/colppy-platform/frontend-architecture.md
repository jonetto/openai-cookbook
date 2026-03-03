# Frontend Architecture

> Colppy's frontend is a **single-spa** micro-frontend (MFE) shell with independently deployed React applications.
> Only two MFEs are currently mounted in production; the legacy Vue app still handles most post-login UX.

**Related docs:**
- [Auth and Sessions](auth-and-sessions.md) -- login flow, token lifecycle
- [Onboarding Wizard](onboarding-wizard.md) -- mfe_onboarding details
- [Repo Directory](repo-directory.md) -- full MFE repo listing
- [Deployment and Infra](deployment-and-infra.md) -- build/deploy pipeline
- [Backend Architecture](backend-architecture.md) -- API services consumed

---

## Architecture Overview

```
Browser
  |
  v
app_root (single-spa shell, Webpack, TypeScript)
  |-- SystemJS import map (injected at deploy time)
  |-- single-spa-layout router
  |
  |-- @colppy/mfe_authentication  (default route: /)
  |-- @colppy/mfe_onboarding      (route: /inicio)
  |
  +-- (6 additional MFEs exist in repos but are NOT mounted)
```

- **Module loader**: SystemJS 6.8.3 (loaded from CDN)
- **Layout engine**: `single-spa-layout` ^1.6.0
- **Org namespace**: `@colppy/`
- **Import map overrides**: `import-map-overrides` 2.2.0 (activate via `localStorage.setItem('devtools', true)`)

---

## app_root -- The Shell

| Property | Value |
|---|---|
| **Repo** | `colppy/app_root` |
| **Package name** | `@colppy/root-config` |
| **Bundler** | Webpack 5 (`webpack-config-single-spa-ts`) |
| **Language** | TypeScript 4.x |
| **Entry** | `src/colppy-root-config.ts` |
| **HTML template** | `src/index.ejs` (EJS, generates `index.html`) |
| **Layout** | `src/microfrontend-layout.html` |
| **Import map template** | `src/importmap-template.json` |
| **Dev server port** | 9000 |
| **Font** | Nunito Sans (Google Fonts) |
| **Analytics** | Google Tag Manager (`GTM-KQV2QTWJ`) |

### Root config entry point

```typescript
// colppy/app_root/src/colppy-root-config.ts
import { registerApplication, start } from "single-spa";
import {
  constructApplications,
  constructRoutes,
  constructLayoutEngine,
} from "single-spa-layout";
import microfrontendLayout from "./microfrontend-layout.html";

const routes = constructRoutes(microfrontendLayout);
const applications = constructApplications({
  routes,
  loadApp({ name }) {
    return System.import(name);
  },
});
const layoutEngine = constructLayoutEngine({ routes, applications });

applications.forEach(registerApplication);
layoutEngine.activate();
start();
```

### Layout definition

```html
<!-- colppy/app_root/src/microfrontend-layout.html -->
<single-spa-router>
  <main>
    <route default>
      <application name="@colppy/mfe_authentication"></application>
    </route>
    <route path="inicio">
      <application name="@colppy/mfe_onboarding"></application>
    </route>
  </main>
</single-spa-router>
```

### Import map injection

- The import map is **NOT** checked into source as a final JSON
- `src/importmap-template.json` contains only the MFE name list: `["mfe_authentication", "mfe_onboarding"]`
- At build time, `index.ejs` renders with `importMapUrl` parameter from Webpack env
- The actual SystemJS import map (mapping `@colppy/*` to S3/CloudFront URLs) is injected at deploy time per environment
- The `<script type="systemjs-importmap">` block in the HTML is where the resolved map lands

### Webpack config key parameters

```javascript
// colppy/app_root/webpack.config.js
templateParameters: {
  isLocal: webpackConfigEnv && webpackConfigEnv.isLocal,
  importMapUrl,     // injected per environment
  orgName,          // "colppy"
  hubspotId,
}
```

---

## MFE Inventory

| MFE | Repo | Version | Purpose | Tech Stack | Mount Route | Status |
|---|---|---|---|---|---|---|
| `mfe_authentication` | `nubox-spa/colppy-app/mfe_authentication` | 1.1.4 | Login, signup, password recovery | React 18 + TS + Vite + MUI 5 + Redux Toolkit + react-hook-form + yup | `/` (default) | **Active** |
| `mfe_onboarding` | `colppy/mfe_onboarding` | 1.0.8 | Post-signup onboarding wizard | React 18 + TS + Vite + MUI 7 + Redux Toolkit + react-hook-form | `/inicio` | **Active** |
| `mfe_dashboard` | `colppy/mfe_dashboard` | 1.0.0 | Home dashboard with charts | React 18 + TS + Vite + Redux Toolkit + chart.js | Not mounted | Inactive |
| `mfe_mercado_pago` | `colppy/mfe_mercado_pago` | 1.0.3 | Mercado Pago integration | React 18 + TS + Vite + Redux Toolkit + TanStack Table | Not mounted | Inactive |
| `mfe_sales` | `colppy/mfe_sales` | 0.0.1 | Sales module | React 18 + TS + Vite + Redux Toolkit | Not mounted | Inactive (archetype clone) |
| `mfe_vue` | `colppy/mfe_vue` | 2.5.12 | Legacy Vue components bridge | Vue 2.5 + Vuex 3 + Webpack 3 + Bootstrap 4 | Not mounted | Inactive (legacy) |
| `mfe_archetype` | `colppy/mfe_archetype` | 0.0.1 | Template for new MFEs (standalone Vite) | React 18 + TS + Vite | N/A | Template |
| `mfe_archetype_single_spa` | `colppy/mfe_archetype_single_spa` | 0.0.1 | Template for new MFEs (single-spa integrated) | React 18 + TS + Vite + single-spa-react | N/A | Template |

---

## Currently Active MFEs

### mfe_authentication

- **Location**: `nubox-spa/colppy-app/mfe_authentication/`
- **Mount**: Default route (`/`) -- catches all unmatched paths
- **single-spa integration**: `single-spa-react` ^6.0.1
- **Key dependencies**:
  - `@mui/material` ^5.15.11 + `@emotion/react`
  - `@reduxjs/toolkit` ^2.0.1 + `react-redux` ^9.0.4
  - `react-hook-form` ^7.50.1 + `yup` ^1.4.0 (form validation)
  - `i18next` ^23.7.12 + `react-i18next` ^14.0.0 (i18n)
  - `mixpanel-browser` ^2.71.0 (analytics)
  - `react-use-intercom` ^5.4.3 (support chat)
  - `sdk_interlink` ^1.0.2 (token cookie management)
  - `colppy-lib` ^1.0.26 (shared UI components)
  - `crypto-js` ^4.2.0 (password hashing)
- **See**: [Auth and Sessions](auth-and-sessions.md)

### mfe_onboarding

- **Location**: `colppy/mfe_onboarding/`
- **Mount**: `/inicio`
- **single-spa integration**: `single-spa-react` ^6.0.1
- **Vite output format**: SystemJS (`format: 'system'` in rollup options)
- **Entry point**: `src/mfe-single-spa.tsx`
- **Build base path**: `/${MFE_NAME}` in prod, `http://localhost:9002` in dev
- **Key dependencies**:
  - `@mui/icons-material` ^7.0.2 (note: MUI 7, differs from authentication's MUI 5)
  - `@reduxjs/toolkit` ^2.0.1
  - `react-hook-form` ^7.56.1
  - `react-router-dom` ^7.5.1 (note: v7, differs from authentication's v6)
  - `react-responsive` ^10.0.1 + `@theme-ui/match-media` (responsive layouts)
  - `sdk_interlink` ^1.0.2
  - `colppy-lib` ^1.0.27
- **See**: [Onboarding Wizard](onboarding-wizard.md)

### Vite config pattern (shared by all React MFEs)

```typescript
// colppy/mfe_onboarding/vite.config.ts (representative)
build: {
  outDir: 'dist',
  rollupOptions: {
    input: 'src/mfe-single-spa.tsx',
    output: {
      format: 'system',          // SystemJS module format
      entryFileNames: '[name].js',
      chunkFileNames: '[name].js',
      assetFileNames: '[name].[ext]'
    },
    preserveEntrySignatures: 'strict'
  }
}
```

---

## Shared Libraries

### lib_ui (`colppy-lib` on npm)

| Property | Value |
|---|---|
| **Repo** | `colppy/lib_ui` |
| **npm package** | `colppy-lib` ^1.0.27 |
| **Bundler** | Rollup |
| **Storybook** | v7.6 (port 6006) |
| **Deploy Storybook** | `storybook-to-ghpages` |
| **Exports** | `dist/index.js` (ESM), `dist/src/index.es.js` |

**Exported modules:**
- `inputs/` -- button, calendar, dropdown, input-text
- `atoms/` -- badges, button-tab, modal, tooltip, typography
- `theme/config` -- shared theme configuration

**Peer dependencies** (consumers must provide):
- `@emotion/react` >= 11.11.4
- `@emotion/styled` >= 11.11.5
- `@mui/material` >= 5.15.11
- `@mui/icons-material` >= 5.15.11
- `react` >= 18.2.0
- `theme-ui` >= 0.16.1

### sdk_interlink

| Property | Value |
|---|---|
| **Repo** | `colppy/sdk_interlink` |
| **npm package** | `sdk_interlink` ^1.0.3 |
| **Bundler** | Rollup |
| **Exports** | ESM (`dist/index.js`), UMD/global (`dist/index.global.js` via `./cdn`) |
| **Purpose** | Cross-MFE authentication via shared cookies |

**Key functions:**

```typescript
// sdk_interlink/src/auth.ts

// Sets token cookie on .colppy.com domain, 1h expiry
setTokenAuthentication(token: string): void

// Clears token cookie
clearTokenAuthentication(): void

// Fetches user session data from backend (promise or callback style)
getUserData(url: string, callback?: (err, data?) => void): Promise<any> | void
```

- Token cookie: `token=<jwt>; domain=.colppy.com; Secure; SameSite=Lax`
- Session endpoint: `GET ${url}session-info` with `credentials: 'include'`
- CDN build (`index.global.js`) allows consumption by the legacy Vue app without npm install

---

## Common Tech Stack Per MFE

| Layer | Library | Version Range |
|---|---|---|
| **UI framework** | React | ^18.2.0 |
| **Language** | TypeScript | ^5.2.2 |
| **Bundler** | Vite | ^5.0.8 |
| **Module format** | SystemJS (single-spa) | -- |
| **State management** | Redux Toolkit | ^2.0.1 |
| **Component library** | MUI (Material UI) | ^5.15.x (auth, dashboard) / ^7.0.x (onboarding) |
| **Forms** | react-hook-form | ^7.50+ |
| **Validation** | yup (auth) / native (onboarding) | ^1.4.0 |
| **Internationalization** | i18next + react-i18next | ^23 / ^14 |
| **Analytics** | mixpanel-browser | ^2.55+ |
| **Support** | react-use-intercom | ^5.4.x |
| **Theme** | theme-ui | ^0.16.1 |
| **Testing** | Vitest + @testing-library/react | ^1.1.0 / ^14.1.2 |
| **Linting** | ESLint + Prettier | ^8 / ^3 |
| **Git hooks** | Husky | ^8.0.3 |
| **API mocking** | MSW (Mock Service Worker) | ^2.0.11 |

---

## Build and Deploy Pipeline

### MFE build flow

```
git push to branch
  |
  v
GitHub Actions: mfe-build-and-deploy.yml (reusable workflow)
  |
  |-- Determines environment from branch:
  |     master   -> prod
  |     release/ -> stg
  |     develop  -> test
  |     feature/ -> test (build only, no deploy)
  |
  |-- Fetches secrets from AWS Secrets Manager -> .env
  |-- Docker (node:21): pnpm install && pnpm run build
  |-- aws s3 sync ./dist/ s3://{env}-colppy-mfe/{repo_name}
  |-- aws cloudfront create-invalidation --paths '/*'
  |-- (master only) git tag v{version} from package.json
```

### app_root (shell) build flow

```
GitHub Actions: spa-build-and-deploy.yml
  |
  |-- Same branch -> env mapping
  |-- Docker (node:21): pnpm install && pnpm run build (Webpack)
  |-- app_root uploads to s3://{env}-colppy-frontend/ (root, no subfolder)
  |-- Other SPAs upload to s3://{env}-colppy-frontend/{repo_name}/
  |-- CloudFront invalidation
```

### S3 bucket structure

| Bucket | Contents |
|---|---|
| `{env}-colppy-frontend` | app_root shell (index.html + root-config bundle) |
| `{env}-colppy-mfe` | MFE bundles, one folder per MFE (`/mfe_authentication/`, `/mfe_onboarding/`) |

### CloudFront distributions (per environment)

| Environment | SPA Distribution | MFE Distribution |
|---|---|---|
| prod | `E191CN8OL6L6RY` | `EC52L3VE8AC9N` |
| stg | `EPVXXAC3PG2SY` | `E1EDIHAIM6AIO9` |
| test | `ELHHSC3FWH5EO` | `E2NXO4UGJD0960` |
| develop | `EJUMHQGE7UNE6` | `E1PH3BRXLPLKDO` |

---

## MFE Creation Workflow

New MFEs are created via GitHub Actions workflow `mfe_archetype-createrepo.yml`:

1. Choose archetype: `mfe_archetype` (standalone) or `mfe_archetype_single_spa` (single-spa integrated)
2. Provide MFE name (alphanumeric + underscores only)
3. Workflow creates `colppy/mfe_{name}` repo from template
4. Sets branch protection rules (develop + master require PR + 1 approval + CI pass)
5. Assigns `developers` (write) and `tech-leaders` (maintain) team permissions
6. Makes repo private

---

## Gotchas

- **Import map is NOT in source control.** The `importmap-template.json` only lists MFE names. The actual SystemJS import map (with full S3/CloudFront URLs) is injected at deploy time by the CI pipeline. You will not find a complete import map JSON in any repo.

- **Only 2 of 8 MFEs are mounted.** The `microfrontend-layout.html` only registers `mfe_authentication` (default) and `mfe_onboarding` (/inicio). The other 6 MFEs (dashboard, mercado_pago, sales, vue, and 2 archetypes) exist as repos but are not wired into the layout.

- **Legacy Vue app handles most post-login UX.** After login, users are redirected to the legacy PHP + Vue monolith (`colppy-vue`). The MFE architecture currently only covers authentication and onboarding. Dashboard, invoicing, reports, etc. are all still in the legacy app.

- **MUI version mismatch across MFEs.** `mfe_authentication` uses MUI 5.15.x while `mfe_onboarding` uses MUI 7.0.x. The shared `colppy-lib` has peer dependency on MUI >= 5.15.11, so it works with both, but component behavior may differ.

- **react-router-dom version mismatch.** `mfe_authentication` uses v6.22.x, `mfe_onboarding` uses v7.5.x. These have different APIs (v7 introduced breaking changes).

- **mfe_vue is Vue 2.5 with Webpack 3.** This is extremely legacy (2018-era). It exists as a bridge to embed Vue components in the single-spa shell but is not currently mounted.

- **mfe_sales package.json still has archetype name.** Its `name` field is `"mfe-archetype-application"` (never renamed from the template), indicating it was scaffolded but not actively developed.

- **colppy-lib Storybook may not reflect latest.** The lib builds via Rollup but Storybook is v7.6 -- verify deployed Storybook matches the latest published npm version.

- **CSP policies differ between local and non-local.** The `index.ejs` template has separate `Content-Security-Policy` meta tags. Local mode is more permissive (labeled "POLITICAS PARA PROD" in the comment, but this comment is misleading -- it is actually the local/dev policy).

- **sdk_interlink token expiry is hardcoded to 1 hour.** The `setTokenAuthentication` function sets `expires = new Date(Date.now() + 3600 * 1000)`. There is a code comment `// ver si el token expira` suggesting this may not match the actual JWT TTL.

- **Two separate S3 buckets and CloudFront distributions.** The shell (`app_root`) deploys to `{env}-colppy-frontend` while MFEs deploy to `{env}-colppy-mfe`. These are different CloudFront distributions with different distribution IDs.

- **No shared dependency externalization.** Each MFE bundles its own copy of React, Redux, MUI, etc. There is no SystemJS shared dependency map. This increases total bundle size but simplifies independent deployment.

- **Dev server ports are not standardized.** `app_root` runs on 9000, `mfe_onboarding` on 9002. Each MFE picks its own port. Check `vite.config.ts` or `package.json` scripts for the specific port.

---

## Quick Reference: Local Development

```bash
# 1. Start the shell
cd colppy/app_root
pnpm install
pnpm dev          # http://localhost:9000

# 2. Start an MFE (in separate terminal)
cd colppy/mfe_onboarding
pnpm install
pnpm dev          # http://localhost:9002

# 3. Override import map in browser
#    Open http://localhost:9000
#    localStorage.setItem('devtools', true)
#    Refresh -- import-map-overrides UI appears at bottom
#    Override @colppy/mfe_onboarding -> http://localhost:9002/src/mfe-single-spa.tsx
```
