# Design: Colppy Platform Documentation for AI Agents

**Date**: 2026-03-03
**Status**: Draft
**Location**: `docs/colppy-platform/` (inside openai-cookbook)
**Audience**: AI agents (Claude, Cursor, MCP tools)
**Source codebase**: `/Users/virulana/github-jonetto/` (108 repos)

---

## Problem

AI agents working on Colppy tasks (ARCA integration, wizard changes, HubSpot enrichment, reconciliation) lack fast-loading context about the platform's architecture, service boundaries, and code locations. Each session starts with expensive codebase exploration that repeats the same discoveries.

The `github-jonetto/` workspace already has 5 high-level docs (`APP_SYSTEM_MAP.md`, `CORE_DEPENDENCY_GRAPH.md`, etc.) but they are:
- Not structured for AI agent consumption (narrative-heavy, lack file paths)
- Located outside the AI workspace (agents must know to look in github-jonetto/)
- Missing depth on key areas: Provisiones system, auth flow, database schema, deployment

## Solution

Create **10 AI-optimized reference files** in `openai-cookbook/docs/colppy-platform/` that provide navigation-map-style documentation. Each file is self-contained, 200-400 lines, with explicit file paths into `github-jonetto/`.

## File Inventory

| # | File | Purpose | Key Sections |
|---|------|---------|-------------|
| 1 | `README.md` | Master index + architecture diagram | System layers, service map table, cross-references |
| 2 | `frontend-architecture.md` | MFE system | app_root shell, single-spa routing, MFE list, lib_ui, sdk_interlink, login flow |
| 3 | `backend-architecture.md` | Server-side services | Frontera 2.0 gateway, Benjamin Laravel API, NestJS microservices, Lambda functions |
| 4 | `database-schema.md` | Data layer | 207 tables by domain, key relationships, migrations, shared DB pattern |
| 5 | `api-reference.md` | API contracts | Frontera envelope format, Benjamin REST endpoints, request/response examples |
| 6 | `auth-and-sessions.md` | Authentication | FusionAuth + legacy dual system, JWT tokens, session lifecycle, encryption |
| 7 | `onboarding-wizard.md` | Wizard flow | MFE steps, svc_settings orchestration, Frontera setup calls, skip behavior |
| 8 | `provisiones-reference.md` | Business modules | 36+ provisions map, delegate pattern, DAO pattern, ColppyCommon shared code |
| 9 | `deployment-and-infra.md` | CI/CD & infrastructure | inf_workflows hub, Docker, AWS, deployment per service type |
| 10 | `repo-directory.md` | Repository catalog | 108 repos categorized: frontend, auth, core, domains, integrations, infra |

## Format Conventions

Each file follows this template:

```markdown
# [Title]

> One-line purpose statement

## Overview
2-3 sentences of context.

## [Domain-Specific Sections]
- Tables with file paths (relative to github-jonetto/)
- Decision trees where applicable
- Code snippets for patterns (envelope format, auth flow)

## Gotchas
- Bullet list of non-obvious behaviors

## Cross-References
- Links to related docs in this directory
- Links to source files in github-jonetto/
```

Rules:
- **File paths** always relative to `github-jonetto/` root
- **No narrative prose** — use tables, bullets, code blocks
- **Gotchas section mandatory** — the highest-value content for AI agents
- **200-400 lines per file** — loadable in a single Read call
- **No duplication** — each fact lives in exactly one file, others cross-reference

## What This Does NOT Cover

- openai-cookbook's own tools and plugins (already documented via plugin READMEs)
- How-to guides for developers (this is reference material, not tutorials)
- Runtime configuration values (no secrets, no .env contents)

## Dependencies

- Read access to `/Users/virulana/github-jonetto/` (additional working directory)
- Existing docs in `github-jonetto/` as source material: `APP_SYSTEM_MAP.md`, `CORE_DEPENDENCY_GRAPH.md`, `APP_REQUEST_PATHS.md`, `REPO_CONTEXT_INDEX.md`, `REPO_OPERATING_SHEET.md`

## Implementation Order

Files should be written in dependency order (later files may reference earlier ones):

1. `README.md` — establishes the architecture frame
2. `repo-directory.md` — catalogs all 108 repos (referenced by everything)
3. `backend-architecture.md` — Frontera + Benjamin + NestJS (core understanding)
4. `provisiones-reference.md` — 36+ business modules (depends on backend)
5. `database-schema.md` — 207 tables (depends on provisiones context)
6. `api-reference.md` — Envelope format + REST (depends on backend)
7. `auth-and-sessions.md` — Dual auth system (depends on backend + API)
8. `frontend-architecture.md` — MFE system (depends on auth flow)
9. `onboarding-wizard.md` — End-to-end flow (depends on frontend + backend + auth)
10. `deployment-and-infra.md` — CI/CD (standalone, but last since it wraps everything)
