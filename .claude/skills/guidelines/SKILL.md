---
name: easy-dev-guidelines
description: Enforces seeErp's development guidelines (FastAPI + Jinja2 + Vanilla JS/CSS + MariaDB ERP project) — backend rules (common-code/Enum instead of hardcoded status values, parameterized query functions instead of near-duplicate ones, one APIRouter per domain, mandatory 5-field audit mixin with logical delete only), frontend rules (layout.html inheritance, component partials, no inline scripts, the fixed CSS-variable color palette, Pretendard/Inter fonts, 8px spacing grid, required toast/snackbar feedback on create/update/delete), and git branch/commit conventions. Use this any time you are writing, generating, reviewing, or refactoring code (Python/FastAPI, SQLAlchemy models, Pydantic schemas, Jinja2 templates, CSS, or JS) inside the seeErp repository, or planning a new module/table/endpoint/page for it — even if the user's request doesn't mention "guidelines" explicitly.
---

# seeErp Development Guidelines

These rules come from `guide/DEVELOPMENT_GUIDELINES.md` (the project's own guide, in Korean) and exist to keep a server-rendered, no-framework-frontend ERP codebase consistent across many small feature additions over time. Apply them whenever you touch backend or frontend code in this repo — not just when the user explicitly asks about style.

The core philosophy behind all of it: no over-engineering (simplest structure that satisfies the current requirement), strict frontend/backend separation (they only talk through the REST API), no duplicated functions/components/queries, and no hardcoded business values. When a rule below seems to conflict with expedience, these four principles are the tiebreaker.

## Architecture reference

```
Browser → Jinja2 Templates → Vanilla JS (fetch) → FastAPI Router → MariaDB
```

```
app/
├── api/        # one router file per domain (users.py, inventory.py, orders.py...)
├── core/       # config, security, error handling
├── crud/       # DB access/query logic
├── models/     # SQLAlchemy ORM models
├── schemas/    # Pydantic validation schemas
├── static/{css,js}/
├── templates/
│   ├── components/  # reusable partials/macros
│   ├── pages/
│   └── layout.html
└── main.py
```

If `app/` doesn't exist yet, this is the layout to create it in — don't invent a different structure.

## Project setup & documentation

**At the start of any new project (or the first time this skill touches a repo without one), create a `guide/` folder** at the project root. Use it to keep the project's living documentation:
- Development plans (what's being built, in what order)
- History/changelog of major decisions and completed work
- The existing `guide/DEVELOPMENT_GUIDELINES.md` and `guide/SCHEMA_DESIGN.md` referenced above also live here

Update `guide/` as work progresses — a plan file that's written once and never touched again isn't serving its purpose. When a feature is completed or a significant decision is made, log it there rather than letting that context live only in chat history or commit messages.

**`CLAUDE.md` at the project root must index these paths**, so future sessions (or other contributors) can find them without re-deriving the project structure from scratch. At minimum, `CLAUDE.md` should list and briefly describe:
- `guide/DEVELOPMENT_GUIDELINES.md` — this project's dev guidelines
- `guide/SCHEMA_DESIGN.md` — DB schema reference
- Any plan/history files under `guide/` (e.g. `guide/PLAN.md`, `guide/HISTORY.md`, or however they end up named)
- Key `app/` subfolder paths (`app/api/`, `app/crud/`, `app/models/`, etc.) if `CLAUDE.md` doesn't already cover them elsewhere

If `CLAUDE.md` doesn't exist yet, create it with this index. If it exists, add/update the relevant section rather than duplicating or overwriting unrelated content in it.

## Backend rules

**Never hardcode classification or status values** ('대기', '진행중', '남자', '여자', etc.) in Python or in templates. Route them through the common-code tables (`common_code_groups` / `common_codes`, see `guide/SCHEMA_DESIGN.md`) or a backend `Enum`. This is the project's main defense against the kind of scattered magic-string bugs that show up once a status list needs a new value — a change should happen in one place, not at every call site.

**Don't fork query/CRUD functions for each filter combination.** If you're about to write `get_active_users()` next to an existing `get_users()`, stop — add an optional parameter instead (`get_users(gender=None, is_active=None)`) and filter dynamically. The smell to watch for: two functions in the same module whose bodies differ only in a WHERE clause.

**One APIRouter per domain**, under `app/api/`. Don't add endpoints to `main.py` directly or let one router file accumulate unrelated domains — a users endpoint doesn't belong in `inventory.py`.

**Every table needs 5 audit columns**, applied via a shared SQLAlchemy mixin so models inherit them automatically rather than redeclaring them:
- `created_by`, `created_at`, `updated_by`, `updated_at`, `is_active`

`is_active` means deletes in this system are always logical (flip the flag), never physical `DELETE FROM`. If you're implementing a "delete" endpoint or CRUD method, it should update `is_active`, not remove the row. Note `guide/SCHEMA_DESIGN.md` omits these 5 fields from its individual table specs for brevity — they still apply to every table there.

## Frontend rules (Jinja2 + Vanilla JS/CSS)

**Every page extends the base layout.** `layout.html` defines Header / Left Sidebar / Body / Footer; individual pages use `{% extends "layout.html" %}` rather than reimplementing the shell. Repeated UI fragments go in `templates/components/` via `{% include %}` or `{% macro %}` — if you find yourself copy-pasting a card or table-row block across two page templates, that's a signal to extract it there instead.

**No inline `<script>` blocks.** Client logic lives in `static/js/`, one file per feature/module, using `fetch` to talk to FastAPI. Keep DOM control and async calls in vanilla JS — no framework.

**Use the fixed color palette via CSS variables**, defined once in `static/css/style.css`:
```css
:root {
  --color-dark: #354649;      /* primary text / key elements */
  --color-secondary: #6C7A89; /* secondary text / borders */
  --color-accent: #A3C6C4;    /* highlights / accent points */
  --color-light: #E0E7E9;     /* backgrounds / card areas */
}
```
Don't introduce new one-off hex values in templates or component CSS — extend the variable set instead if a genuinely new color is needed.

**Typography**: Pretendard for Korean/body text, Inter for numeric/tabular data (dashboards, tables). Both are OFL-licensed — don't substitute a font with unclear commercial licensing.

**Spacing**: keep margins/padding on an 8px-multiple grid, with smooth hover/transition effects on interactive elements. Icons should stay simple — avoid decorative or overly detailed iconography.

**Any create/update/delete triggered by user action must show a visible success/failure notification** (toast, snackbar, or alert). This is a UX requirement, not optional polish — a silent failed save is the specific failure mode it's guarding against.

**Keep UI/document text emoji-free** and professional in tone; avoid emoji as a stylistic default.

## Git conventions

- Branches: `main` (deployable), `develop` (integration), `feature/<feature-name>` (per-feature work).
- Commit prefixes: `feat:`, `fix:`, `refactor:`, `style:`, `chore:` — match the change type, e.g. a pure formatting change is `style:` even if it touches business logic files, and a dedup/cleanup with no behavior change is `refactor:` not `fix:`.

## When rules and requests conflict

If a user request would violate one of these (e.g., "just hardcode the status for now," or a request to add a redundant `get_pending_orders()` next to `get_orders()`), implement it the compliant way by default and briefly note why, rather than silently picking one or the other. If they push back after that, defer to them — these are project conventions, not hard constraints on what's technically possible.
