# My Life AI — Repository Audit & Refactor Plan

> **Purpose:** This document is the single source of truth for the current repository
> inconsistencies and the agreed remediation order. It is written so a future agent/model
> can resume work without re-discovering the problems.
>
> **Status:** Planning complete, implementation **not started**.
> **Last updated:** 2026-11-25
> **Owner:** Lead Architect (per `AGENTS.md`)

---

## 0. How to use this document

1. Read `AGENTS.md`, `ROADMAP.md`, `WORKLOG.md`, then this file.
2. Work top-to-bottom through **Phase 1 → Phase 5** unless a task is explicitly deferred.
3. Tick a task only after its **acceptance criteria** pass and verification commands run.
4. Keep changes scoped; do not commit unless the human explicitly asks.
5. Update `WORKLOG.md` when a phase is complete and update this file's status markers.

### Verification commands

```bash
# Backend (from repo root)
cd backend
python -m compileall -q app
python -c "import app.main; print('backend import OK')"
# ruff check .        # once deps installed
# mypy app            # once deps installed

# Frontend (from repo root)
cd frontend
npx tsc --noEmit        # current baseline: 84 errors (see §3.2)
npm run build           # after typecheck is green
```

> The current environment has `frontend/node_modules` installed, so `npx tsc --noEmit`
> works today. Backend dependencies may not be installed; `compileall` still works.

---

## 1. Executive summary

The project is feature-rich but the backend has **two parallel implementations of every
domain operation**: an unused, clean `app/services/*` layer and a 2,324-line god-object
`app/models/user.py` that the GraphQL schema actually calls. This causes:

- Massive duplication (event/category/memory/conversation/notification logic exists twice).
- Inconsistent DB session handling (models open their own sessions; the request session is wasted).
- Inconsistent data contracts (e.g. `recurrence_exceptions` is a `UUID[]` in the migration,
  `DateTime[]` in the model, and `UUID[]` in GraphQL).
- A frontend that does not type-check (84 TypeScript errors) and ships duplicate/stale
  GraphQL types, duplicate lockfiles, and broken auth refresh.

The fix is **not** a rewrite. It is a consolidation: make the services the single domain
layer, make the schema thin, centralise model→GraphQL serialization, standardise the DB
session and timezone handling, then repair the frontend type layer.

---

## 2. Target architecture (decide once, apply everywhere)

```
backend/app/
├── core/config.py              # settings only
├── db/session.py               # engine + ONE session factory + ONE get_db context manager
├── models/                     # pure SQLAlchemy ORM. NO business logic, NO GraphQL imports.
├── graphql/
│   ├── context.py              # request context: db session + authenticated user
│   ├── serializers.py          # NEW: single home for model -> GraphQL type conversion
│   ├── schema.py               # thin resolvers: auth guard + delegate to services
│   └── types/                  # strawberry types/inputs/enums/scalars only
├── services/                   # ALL domain logic; receives AsyncSession in __init__
└── workers/                    # Celery tasks; shared async helper in workers/utils.py
```

**Rules to enforce during refactor**

- Resolvers never contain business logic. They resolve `user`, then call a service method.
- Services take `AsyncSession` via constructor and use it for all reads/writes.
- Models must not import from `app.graphql.*` and must not import `get_db`.
- One conversion function per model lives in `graphql/serializers.py`.
- All timestamps are timezone-aware UTC: `datetime.now(timezone.utc)`; never `datetime.utcnow()`.
- Soft delete uses a single convention (`deleted_at` timestamp); hard delete only in maintenance tasks.
- GraphQL type name is the source of truth for enums; backend enums are the storage values.

---

## 3. Findings (audit)

Severity: **P0** = breaks correctness/security, **P1** = architectural inconsistency,
**P2** = maintainability/cleanup, **P3** = docs/nits.

### 3.1 Backend

| # | Sev | Finding | Location |
|---|-----|---------|----------|
| B1 | P0 | **God object** `User` contains ~2,000 lines duplicating every service (events, categories, conversations, memory, notifications, settings, AI proposals). Schema calls `user.<method>` instead of services. | `backend/app/models/user.py` (2,324 lines), `backend/app/graphql/schema.py` |
| B2 | P0 | **Two DB-session patterns.** Schema/context opens one session; every `User.*` method opens another via `get_db()` and commits independently. Request session is effectively unused; transactions are split. | `app/models/user.py`, `app/db/session.py`, `app/graphql/context.py` |
| B3 | P0 | **CORS config ignored.** `main.py` passes `settings.CORS_ORIGINS` (a raw comma string) instead of `settings.cors_origins_list`; same for methods/headers. Browser CORS will not behave as configured. | `app/main.py` (`create_app`) |
| B4 | P0 | **`recurrence_exceptions` type mismatch.** Model: `ARRAY(DateTime(timezone=True))`. Migration: `ARRAY(UUID)`. GraphQL: `List[UUID]`. Services append either event IDs or `datetime.utcnow()`. Recurring exceptions cannot work. | `models/event.py`, `migrations/versions/001_initial_schema.py`, `graphql/types/event.py`, `services/event.py` |
| B5 | P0 | **Refresh token flow broken.** `AuthPayload` exposes only `token`; refresh token is generated then discarded. Frontend sends refresh token in `Authorization` while backend reads `X-Refresh-Token`. | `services/auth.py`, `graphql/types/payloads.py`, `frontend/src/store/authStore.ts`, `graphql/context.py` |
| B6 | P1 | **Services are dead code** relative to the API. They are implemented but never wired to resolvers (except `AuthService`). | `app/services/*` vs `app/graphql/schema.py` |
| B7 | P1 | **Serialization duplicated** in `User.*`, `services/*._x_to_gql`, and inline. Same event→GQL mapping appears ≥6 times. | `models/user.py`, `services/event.py`, `services/category.py`, etc. |
| B8 | P1 | **Duplicate `NotificationFilterInput`.** Imported from `types.inputs` then redefined at module scope in the schema, shadowing the import. | `graphql/schema.py` |
| B9 | P1 | **Unused context class.** `GraphQLContext` is constructed but never passed; `get_context` yields a dict. Refresh-token plumbing uses `request.state` and then ignores it. | `graphql/context.py` |
| B10 | P1 | **Schema resolver drift.** e.g. service `update_recurring_series` returns `List[Event]` while the GraphQL mutation declares `Event`. | `services/event.py`, `graphql/schema.py` |
| B11 | P1 | **Timezone correctness.** Widespread `datetime.utcnow()` (naive) written into `TIMESTAMP WITH TIME ZONE` columns; comparisons vs `now()` and user timezones are unreliable. | `models/user.py`, `services/*`, `workers/tasks/*` |
| B12 | P1 | **`init_db()` uses `create_all` + debug `print`s + env-var once-guard**, bypassing Alembic. Diverges from migrations and is not production-safe. | `app/db/session.py`, `app/main.py` |
| B13 | P1 | **Docker/DB wiring.** Compose mounts `backend/migrations` into `/docker-entrypoint-initdb.d` (only `.sql/.sh` are executed; Alembic `.py` files are ignored). Dockerfile copies `alembic.ini` to a non-existent `migrations/alembic.ini`. | `docker-compose.yml`, `backend/Dockerfile` |
| B14 | P1 | **Two `alembic.ini` files** with identical content (`backend/alembic.ini`, `backend/migrations/alembic.ini`). | backend root + migrations |
| B15 | P2 | **Bare `except:` / swallowed exceptions** (`except: pass`) hide failures. | `models/user.py`, `services/*` |
| B16 | P2 | `__import__('strawberry').asdict(...)` hack instead of a normal import. | `models/user.py` (multiple) |
| B17 | P2 | Duplicated `run_async` helper + trailing `import asyncio` in three worker modules; `print()` instead of structured logging. | `workers/tasks/{reminders,notifications,maintenance}.py` |
| B18 | P2 | `get_db` and `get_db_context` are identical; unused imports (`Depends`, `get_db`) and duplicate `text` imports. | `db/session.py`, `main.py` |
| B19 | P2 | `category._soft_delete_children` assigns `func.now()` (a SQL expression) to a Python attribute instead of a datetime. | `services/category.py` |
| B20 | P2 | `event._expand_recurring_event` never actually filters `recurrence_exceptions` (placeholder `pass`). | `services/event.py` |
| B21 | P2 | Dockerfile installs editable project (`uv pip install -e ".[dev]"`) **before** `COPY ./app`, so setuptools may discover no package at install time. | `backend/Dockerfile` |
| B22 | P3 | `pyproject.toml` uses legacy top-level Ruff `select`/`ignore` (moved to `[tool.ruff.lint]` in modern Ruff). | `backend/pyproject.toml` |
| B23 | P3 | No backend tests despite `testpaths=["tests"]` and an empty `app/tests/` directory. | `backend/` |

### 3.2 Frontend

Baseline: `cd frontend && npx tsc --noEmit` → **84 errors** (2 exit).

| # | Sev | Finding | Location |
|---|-----|---------|----------|
| F1 | P0 | **Type-check fails** (84 errors): unused imports/vars, implicit `any`, invalid AntD icon names, `import.meta.env` typing missing. | multiple (see below) |
| F2 | P0 | **`themeStore.applyTheme` not declared** on `ThemeState`, yet used by `setTheme`, `initializeTheme`, `onRehydrateStorage`. | `store/themeStore.ts` |
| F3 | P0 | **Missing Vite env types**: `Property 'env' does not exist on type 'ImportMeta'` (no `vite-env.d.ts` / `vite/client` type). | `LoginPage`, `RegisterPage`, `utils/graphqlClient.ts`, `tsconfig.json` |
| F4 | P1 | **Stale/duplicate generated GraphQL types.** `src/graphql/generated/*` (gql.ts with empty `documents`, graphql.ts, schema.ts) duplicates hand-written `src/types/graphql.ts`; generated `gql.ts` itself fails strict TS. Nothing uses the generated documents. | `src/graphql/generated/`, `src/types/graphql.ts`, `codegen.ts` |
| F5 | P1 | **Duplicate package manager artifacts**: `package-lock.json` + `pnpm-lock.yaml` + `pnpm-workspace.yaml`; Dockerfile uses npm. | `frontend/` |
| F6 | P1 | **Refresh flow bug** (mirror of B5): refresh token stored but sent as bearer; `AuthPayload` has no refresh token. | `store/authStore.ts` |
| F7 | P1 | **Duplicate GraphQL operation strings** scattered across stores/pages/components; no central operations module. | `store/*.ts`, `pages/*`, `components/categories/CategoryManagement.tsx` |
| F8 | P2 | `graphqlClient.ts` uses `any` for variables/WS messages; unused `error` binding; WS URL hard-coded via string replace. | `utils/graphqlClient.ts` |
| F9 | P2 | `dateUtils.ts` exports dozens of thin one-line wrappers (`addDaysSafe`, `isSameDaySafe`, …) around `date-fns` — pure indirection; unused import `format`, unused `timezone` param. | `utils/dateUtils.ts` |
| F10 | P2 | Settings/Calendar/Planner/Notifications pages contain dead handlers, dead query constants, and implicit-`any` subcomponents. | pages |
| F11 | P3 | `RegisterPage` passes `type="submit"` to AntD `Button` (invalid; use `htmlType`). | `pages/RegisterPage.tsx` |
| F12 | P3 | Invalid AntD icons: `IndentOutlined`, `OutdentOutlined`, `IndentedOutlined`. | `pages/SettingsPage.tsx` |
| F13 | P3 | `package.json` defines `lint` (ESLint) but there is **no ESLint config**, so `npm run lint` fails. | `frontend/package.json` |
| F14 | P3 | `tsconfig` `noUnusedLocals`/`noUnusedParameters` are on, which is good, but the codebase violates them everywhere — fix code, don't disable. | `tsconfig.json` |

### 3.3 Repo / docs / config

| # | Sev | Finding |
|---|-----|---------|
| R1 | P2 | `README.md` references `docs/decisions` and `docs/features` that exist but are empty; acceptable, note only. |
| R2 | P2 | `WORKLOG.md`/`CHANGELOG.md` claim things that are not true (e.g. “GraphQL codegen generated 20 queries…” — generated documents array is empty). Update after refactor. |
| R3 | P3 | `.env` files are correctly git-ignored (verified), keep it that way. |
| R4 | P3 | `backend/app/tests/` is empty; `pyproject` points tests at `tests/` (mismatch). |

---

## 4. Remediation plan (ordered, with acceptance criteria)

> Work phases in order. Phase 1 unblocks everything else. Do **not** delete `user.py`
> methods until their service equivalents are wired and verified.

### Phase 1 — Backend foundation (no behaviour change yet)

- [x] **1.1 Consolidate DB session layer** (`app/db/session.py`)
  - Remove `get_db_context` (or make `get_db` the only public manager).
  - Remove `print()` debugging from `init_db`; remove duplicate `text` import.
  - Decide `init_db` policy: keep `create_all` **only** for dev bootstrap or remove it in
    favour of `alembic upgrade head` in the entrypoint. Document the choice in WORKLOG.
  - Acceptance: `grep -rn "get_db_context" app` returns only the context usage you keep;
    `python -c "import app.db.session"` passes.

- [x] **1.2 Fix context + session ownership** (`app/graphql/context.py`)
  - Use one request-scoped session; pass it to services.
  - Keep the yielded dict shape `{request, db, user, refresh_token, settings}` (schema already
    reads `info.context["db"]` / `["user"]`).
  - Remove unused `GraphQLContext` class **or** make it the actual yielded object and update
    resolvers consistently. Prefer the dict to avoid churn.
  - Acceptance: no resolver creates its own session; all `get_db()` usage outside
    workers/entrypoints is gone.

- [x] **1.3 Create `app/graphql/serializers.py`** (new file)
  - Add: `category_to_gql`, `reminder_to_gql`, `event_to_gql`, `message_to_gql`,
    `conversation_to_gql`, `memory_to_gql`, `notification_to_gql`, `settings_to_gql`,
    `user_to_gql`.
  - Move the current `_event_to_gql`, `_category_to_gql`, `_memory_to_gql`,
    `_notification_to_gql`, `_conversation_to_gql`, `_message_to_gql`, `_settings_to_gql`,
    `_user_to_gql` bodies here (deduplicated).
  - Services should import these; delete their private duplicates.
  - Acceptance: exactly one definition of each mapping (`grep -c "GQLEvent(" app` etc.).

- [x] **1.4 Standardise timezone handling**
  - Replace every `datetime.utcnow()` with `datetime.now(timezone.utc)`.
  - Ensure naive incoming datetimes are coerced to UTC at the service boundary.
  - Acceptance: `grep -rn "utcnow" app` → 0.

### Phase 2 — Wire the API to services and delete the god object

- [x] **2.1 Fix `AuthPayload` + refresh flow (B5)**
  - Add `refresh_token: str` to `graphql/types/payloads.py`.
  - `AuthService.register/login` return both tokens.
  - `refresh_token` mutation reads the refresh token from `X-Refresh-Token`
    (or better: accept it as an explicit argument) and returns a new access token.
  - Acceptance: register/login response contains `refreshToken`; refresh works end-to-end.

- [x] **2.2 Rewrite `app/graphql/schema.py` to delegate**
  - Add a small `require_user(info)` helper (raises `GraphQLError`/`Exception` consistently).
  - Each resolver: `db = info.context["db"]`, `user = require_user(info)`, then
    `return await SomeService(db).method(user.id, ...)`.
  - Remove the duplicate `NotificationFilterInput` class (use the one from `types.inputs`).
  - Remove unused imports; keep subscriptions as explicit stubs (they currently `yield None`
    against non-optional types — mark with `# TODO` and keep schema valid, or remove from
    schema until implemented).
  - Acceptance: `schema.py` contains no SQLAlchemy queries and no manual GQL type construction.

- [x] **2.3 Fix service contract drift (B10, B19, B20)**
  - `EventService.update_recurring_series` → return a single `Event`.
  - `CategoryService._soft_delete_children` → assign `datetime.now(timezone.utc)`.
  - `EventService._expand_recurring_event` → actually skip occurrences matching
    `recurrence_exceptions` (datetime comparison), and preserve instance IDs sensibly.
  - Acceptance: GraphQL schema builds (`python -c "import app.graphql.schema"`), and recurring
    helpers have no `pass` placeholders for core logic.

- [x] **2.4 Fix `recurrence_exceptions` contract (B4) — choose timestamps**
  - Model: `ARRAY(DateTime(timezone=True))` (already).
  - GraphQL type: `recurrence_exceptions: List[DateTime]`.
  - Migration `001_initial_schema.py`: `postgresql.ARRAY(sa.DateTime(timezone=True))`
    with default `ARRAY[]::timestamptz[]` (add a follow-up migration if the initial one has
    already been applied in any shared environment).
  - Services append datetimes, not event IDs (`create_recurring_exception`).
  - Acceptance: no `ARRAY(...UUID...)` for this column; grep shows consistent datetime use.

- [x] **2.5 Delete business logic from `User` model (B1, B2, B7, B16)**
  - Reduce `models/user.py` to the ORM model + relationships + `__repr__` (~120 lines).
  - Remove `to_gql` (use `serializers.user_to_gql`).
  - Acceptance: `wc -l models/user.py` < 200; `grep -n "from app.graphql" models/user.py` empty;
    all queries/mutations still resolve through services.

- [x] **2.6 Clean CORS + app wiring (B3, B18)**
  - `main.py`: use `settings.cors_origins_list`, `cors_allow_methods_list`,
    `cors_allow_headers_list`; remove unused `Depends`/`get_db` import.
  - Acceptance: CORS middleware receives lists (inspect once at startup / unit test helper).

- [x] **2.7 Workers cleanup (B17)**
  - Create `app/workers/utils.py` with a single `run_async`.
  - Remove trailing `import asyncio`, duplicate helpers, and `print()`; use `structlog`.
  - Ensure all task datetime math is UTC-aware.
  - Acceptance: `grep -rn "def run_async" app/workers` → 1; `grep -rn "print(" app/workers` → 0.

### Phase 3 — Backend deployment/config consistency

- [x] **3.1 Single Alembic config**
  - Keep `backend/alembic.ini`; delete `backend/migrations/alembic.ini`.
  - Dockerfile: remove the bogus `COPY ./alembic.ini ./migrations/alembic.ini`; copy
    `alembic.ini` to `/app/alembic.ini` and keep `script_location = migrations`.
  - Acceptance: `alembic -c alembic.ini history` works from `backend/`.

- [x] **3.2 Compose fixes**
  - Remove `./backend/migrations:/docker-entrypoint-initdb.d:ro` (it does nothing).
  - Fix Celery beat: mount a dedicated dir, e.g. `celery_beat_schedule:/data` and
    `--schedule=/data/celerybeat-schedule`; do **not** mount a volume over `/app`
    (it hides application code).
  - Add `command`/entrypoint that runs `alembic upgrade head` before uvicorn if that is the
    chosen strategy.
  - Acceptance: `docker compose config` is valid; beat container does not shadow `/app`.

- [x] **3.3 Backend Dockerfile**
  - Copy `pyproject.toml` (+ lockfile if used) and `app/` **before** editable install, or
    install dependencies without `-e .` and set `PYTHONPATH=/app`.
  - Remove duplicate `COPY` lines; ensure `uv.lock` is either committed or not referenced
    (currently `.gitignore` ignores `backend/uv.lock`, so `uv.lock*` will be empty — that is
    fine, but be explicit).
  - Acceptance: clean `docker build --target development ./backend` succeeds.

- [x] **3.4 `pyproject.toml`**
  - Move Ruff `select`/`ignore`/`per-file-ignores` under `[tool.ruff.lint]`.
  - Align pytest `testpaths` with where tests will live (`tests` at backend root).
  - Acceptance: `ruff check .` runs without config deprecation warnings.

### Phase 4 — Frontend correctness

- [x] **4.1 Add Vite env types (F3)**
  - Add `frontend/src/vite-env.d.ts` with `/// <reference types="vite/client" />`.
  - Acceptance: `import.meta.env` errors gone.

- [x] **4.2 Fix `themeStore` (F2)**
  - Add `applyTheme: (theme: Theme) => void` to `ThemeState`.
  - Fix unused `e` param; ensure the system-preference listener is cleaned up.
  - Remove the duplicate `initializeTheme()` call (currently in `main.tsx` **and** at the
    bottom of the store module).
  - Acceptance: theme toggle + system change works; no TS errors in the file.

- [x] **4.3 Fix auth refresh (F6)**
  - Add `refreshToken` to the local `AuthPayload` type (and generated schema once B5 lands).
  - Store it; send it via `X-Refresh-Token` header (add header support to
    `graphqlRequest`) instead of `Authorization`.
  - Acceptance: expired access token refreshes and retries once.

- [x] **4.4 Remove stale generated types / pick one source of truth (F4)**
  - Recommended: delete `frontend/src/graphql/generated/*`, delete `src/types/index.ts`,
    keep `src/types/graphql.ts` as the canonical hand-authored contract.
  - Update `codegen.ts` to emit a single file (e.g. `src/graphql/generated.ts`) and add it to
    `.gitignore` so it is generated on demand, not committed.
  - Do **not** import generated types until codegen is re-run against the fixed backend.
  - Acceptance: `npx tsc --noEmit` no longer reports generated-file errors; one type source.

- [x] **4.5 Fix all TypeScript errors (F1, F10–F12)**
  - Work file-by-file in this order: `utils/*` → `store/*` → `components/layout` →
    `components/categories` → `pages/Login|Register` → `pages/Notifications` →
    `pages/Planner` → `pages/Calendar` → `pages/Settings`.
  - Remove dead handlers/constants; type the inline subcomponents in `CalendarPage`;
    replace invalid icons (`IndentOutlined`/`OutdentOutlined`/`IndentedOutlined` → valid
    AntD icons such as `MenuFoldOutlined`/`MenuUnfoldOutlined`/`VerticalAlignMiddleOutlined`);
    use `htmlType="submit"` instead of `type="submit"`.
  - Acceptance: `npx tsc --noEmit` → exit 0; `npm run build` succeeds.

- [x] **4.6 Remove lockfile ambiguity (F5)**
  - Keep npm (`package-lock.json`); delete `pnpm-lock.yaml` and `pnpm-workspace.yaml`.
  - Acceptance: `grep -rn "pnpm" frontend --exclude-dir=node_modules` → 0.

- [x] **4.7 Centralise GraphQL operations (F7, optional but recommended)**
  - Move inline operation strings to `src/graphql/operations.ts` (or per-domain files).
  - Stores/pages import from there. This is the biggest remaining duplication.
  - Acceptance: each operation string appears once.

- [x] **4.8 ESLint config (F13)**
  - Either add a minimal `.eslintrc.cjs` compatible with ESLint 8 + TS + react-hooks, or
    remove the `lint` script and document `typecheck` as the gate.
  - Acceptance: `npm run lint` exits 0 (or script removed deliberately).

### Phase 5 — Tests & documentation

- [x] **5.1 Add minimal backend tests** (B23)
  - `backend/tests/` with: auth register/login, event CRUD, category tree, notification unread
    count, recurring exception contract. Use `pytest-asyncio` + a disposable Postgres (or
    SQLite only where Postgres-specific ARRAY/JSONB is not required).
  - Acceptance: `pytest` green in CI-like environment.

- [x] **5.2 Update docs**
  - `WORKLOG.md`: record the consolidation + verification evidence.
  - `CHANGELOG.md`: correct false claims (codegen documents, migrations).
  - `docs/database/schema.md` / `docs/api/graphql-schema.md`: align with the
    `recurrence_exceptions` decision and refresh-token payload.
  - Acceptance: docs match code.

---

## 5. Key decisions to record (ADRs)

Create short ADRs in `docs/decisions/` before/while implementing:

1. **ADR: Services own domain logic; models are persistence-only.**
2. **ADR: `recurrence_exceptions` stores occurrence timestamps (`timestamptz[]`), not IDs.**
3. **ADR: Refresh token transport** — pick `X-Refresh-Token` header (current backend) or an
   explicit mutation argument; document and apply on both ends.
4. **ADR: Generated GraphQL types are build artifacts, not committed; hand-authored
   `src/types/graphql.ts` is canonical until codegen is re-enabled.**
5. **ADR: Database schema is managed exclusively by Alembic** (remove `create_all` from
   request/runtime path or gate it strictly to dev bootstrap).

---

## 6. Explicitly deferred (do not do in this refactor)

- Implementing real WebSocket subscriptions (stubs stay stubs; keep schema valid).
- Email/push delivery (keep TODOs in workers).
- pgvector semantic search (text search stays as the interim implementation).
- Rewriting the AI provider layer (`services/ai.py` is large but functional; only clean
  imports/prints if touched).
- UI redesign; this plan only fixes correctness/types and removes dead code.

---

## 7. Definition of done

- [x] `cd backend && python -m compileall -q app && python -c "import app.main"` passes.
- [x] No `User` domain methods remain; `models/user.py` < 200 lines.
- [x] Exactly one model→GraphQL serializer per type.
- [x] No `datetime.utcnow`, no bare `except:`, no `print(` in `app/` (workers included).
- [x] `recurrence_exceptions` is `timestamptz[]` in model, migration, GraphQL, and services.
- [x] Refresh-token login→refresh round-trip works.
- [x] `docker compose config` valid; backend development image builds.
- [x] `cd frontend && npx tsc --noEmit` exits 0 and `npm run build` succeeds.
- [x] One lockfile, one set of GraphQL types, one `alembic.ini`.
- [x] `WORKLOG.md` and `CHANGELOG.md` reflect reality.

---

## 8. Resume checklist for the next agent

1. Run the verification commands in §0 and record the baseline.
2. Confirm no one else is editing (check `git status`; per `AGENTS.md`, coordinate).
3. Start at the first unchecked Phase 1 task; do not jump ahead.
4. After each task, re-run its acceptance check and tick the box here.
5. If a decision changes, update §5 ADRs and this plan before continuing.
