# Contributing to AdTicks

This guide covers everything you need to contribute to AdTicks — from setting up your local environment to getting a pull request merged.

---

## Table of Contents

- [Local Environment Setup](#local-environment-setup)
- [Project Structure Quick Reference](#project-structure-quick-reference)
- [Git Workflow](#git-workflow)
- [Branch Naming Conventions](#branch-naming-conventions)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Code Review Checklist](#code-review-checklist)
- [Python Coding Standards](#python-coding-standards)
- [TypeScript & React Coding Standards](#typescript--react-coding-standards)
- [Testing Requirements](#testing-requirements)
- [Database Migration Workflow](#database-migration-workflow)
- [Running the Full Test Suite](#running-the-full-test-suite)
- [CI / Pre-merge Gates](#ci--pre-merge-gates)

---

## Local Environment Setup

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | 24+ | https://docs.docker.com/desktop/ |
| Node.js | 20 LTS | https://nodejs.org or `nvm install 20` |
| Python | 3.11+ | https://python.org or `pyenv install 3.11` |
| Git | 2.40+ | system package manager |
| Make | any | system package manager |

### First-time setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/adticks.git
cd adticks

# 2. Copy environment files
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local

# 3. Fill in the required variables in .env
#    At minimum:
#      OPENAI_API_KEY=sk-...
#      ANTHROPIC_API_KEY=sk-ant-...
#    Everything else has safe defaults for local development.

# 4. Start all services (Postgres, Redis, backend, frontend, Celery)
make dev

# 5. Apply database migrations
make migrate

# 6. (Optional) Seed demo data
make seed
```

### Verifying your setup

Once `make dev` is running, open:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |
| Celery Flower | http://localhost:5555 |
| pgAdmin (optional) | http://localhost:5050 |

Create an account at http://localhost:3000/signup and run a quick scan to confirm the Celery worker pipeline is functional.

### Stopping and cleaning up

```bash
make stop        # Stop containers (preserves volumes)
make clean       # Stop containers and remove volumes (wipes DB)
```

---

## Project Structure Quick Reference

```
adticks/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI routers — one file per feature domain
│   │   ├── core/            # Config, security, celery_app
│   │   ├── db/              # Engine, session, Base
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # Business logic (stateless functions)
│   ├── alembic/versions/    # Migration files (auto-generated + reviewed)
│   └── tests/
├── frontend/
│   ├── app/                 # Next.js App Router
│   │   ├── (auth)/          # Login, signup pages
│   │   └── (dashboard)/     # All authenticated pages
│   ├── components/
│   │   ├── layout/          # Sidebar, Header, DashboardLayout
│   │   ├── dashboard/       # Dashboard widgets
│   │   └── ui/              # Generic design system components
│   ├── hooks/               # React Query data hooks
│   ├── lib/                 # API client, auth helpers, utils
│   └── types/               # TypeScript interfaces
├── docs/                    # This documentation suite
├── scripts/                 # deploy.sh and other shell utilities
├── docker-compose.yml       # Development stack
├── docker-compose.prod.yml  # Production stack
└── Makefile
```

---

## Git Workflow

AdTicks uses a **trunk-based development** model with short-lived feature branches.

```
main  ──────────●──────────────────●──────────────●──────────
                │                  ↑              ↑
                └─► feature/xxx ───┘   fix/yyy ───┘
```

- `main` is always deployable. CI runs on every push.
- Feature branches live for **≤ 3 days** wherever possible.
- Never commit directly to `main` (branch protection is enforced).
- Rebase onto `main` before opening a PR — do not merge `main` into your branch.

### Typical contribution flow

```bash
# 1. Pull latest main
git checkout main && git pull

# 2. Create your branch
git checkout -b feature/add-backlinks-table

# 3. Make changes, commit often
git add -p   # Stage hunks interactively — avoid "git add ."
git commit -m "feat(seo): add backlinks table ORM model"

# 4. Rebase before pushing
git fetch origin && git rebase origin/main

# 5. Push and open PR
git push -u origin feature/add-backlinks-table
```

---

## Branch Naming Conventions

```
<type>/<short-description>
```

| Type | When to use |
|------|------------|
| `feature/` | New user-facing capability |
| `fix/` | Bug fix |
| `refactor/` | Internal restructure, no behaviour change |
| `docs/` | Documentation only |
| `chore/` | Tooling, CI, dependencies |
| `test/` | Adding or fixing tests |

**Examples:**
```
feature/ai-visibility-perplexity-model
fix/gsc-oauth-callback-state-mismatch
refactor/celery-task-error-handling
docs/add-contributing-guide
chore/upgrade-nextjs-14-to-15
test/keyword-clustering-service
```

Branch names must be **kebab-case**, **lowercase**, and contain no slashes beyond the type prefix.

---

## Commit Message Format

AdTicks uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short imperative summary>

[optional body — wrap at 72 characters]

[optional footer: BREAKING CHANGE or Closes #issue]
```

### Types

| Type | Meaning |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that is neither a fix nor a feature |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `chore` | Maintenance (deps, CI, config) |
| `perf` | Performance improvement |
| `style` | Formatting, whitespace (no logic change) |

### Scopes

Use the feature domain: `auth`, `seo`, `ai`, `gsc`, `ads`, `scoring`, `celery`, `frontend`, `db`, `api`, `infra`.

### Examples

```
feat(ai): add Perplexity model to visibility scan pipeline

Adds PerplexityClient alongside existing OpenAI/Anthropic/Gemini
clients. The scan task now fans out to all four models in parallel
using asyncio.gather().

Closes #142
```

```
fix(gsc): handle missing OAuth state cookie on callback

State cookie was not being set when the user had third-party cookies
blocked. Fallback to session storage for state validation.
```

```
feat(frontend)!: redesign sidebar navigation

BREAKING CHANGE: Sidebar now requires the `collapsed` prop from
DashboardLayout context. Update any layout wrappers that render
Sidebar directly.
```

### Rules

- Summary line ≤ 72 characters.
- Use the **imperative mood**: "add feature" not "added feature" or "adds feature".
- Do not end the summary line with a period.
- Reference issues in the footer, not the summary.

---

## Pull Request Process

### Before opening a PR

- [ ] All new code has tests (see [Testing Requirements](#testing-requirements))
- [ ] `make lint` passes (zero warnings)
- [ ] `make test` passes locally
- [ ] If schema changed: migration file is included and reviewed
- [ ] Branch is rebased onto latest `main`
- [ ] PR description is filled out using the template

### PR description template

```markdown
## What & Why
<!-- One paragraph describing the change and the motivation behind it -->

## How
<!-- Key implementation decisions, data flow changes, anything non-obvious -->

## Testing
<!-- How did you verify this works? What edge cases did you consider? -->

## Screenshots / Recordings
<!-- For any UI changes, include before/after screenshots or a screen recording -->

## Checklist
- [ ] Tests added / updated
- [ ] Linting passes (`make lint`)
- [ ] Migration included (if schema changed)
- [ ] Docs updated (if adding new endpoints or config vars)
```

### Review process

1. Open the PR targeting `main`.
2. At least **one approval** is required before merging.
3. CI must be green (lint + tests).
4. The PR author merges after approval (not the reviewer).
5. Use **Squash and Merge** for feature branches to keep `main` history clean.
6. Use **Rebase and Merge** for chore/docs commits where individual commits are meaningful.
7. Delete the branch after merging (GitHub auto-delete is enabled).

### Keeping your PR small

PRs that touch > 400 lines of production code should be split if possible. Large PRs are harder to review well and delay merging. If a large change is unavoidable, leave a tour comment on the PR explaining where to start reading.

---

## Code Review Checklist

When reviewing someone else's PR, check for:

**Correctness**
- [ ] Does the logic match the stated intent?
- [ ] Are error cases handled (network failures, empty responses, auth errors)?
- [ ] Are edge cases considered (empty arrays, null values, concurrent requests)?

**Security**
- [ ] Is user input validated before use?
- [ ] Are new endpoints protected by `get_current_user` dependency?
- [ ] Are secrets accessed only via `settings.*` (not hardcoded)?

**Performance**
- [ ] Are N+1 database queries avoided? (Use `selectinload`/`joinedload` for relationships)
- [ ] Are expensive operations in Celery tasks, not in request handlers?
- [ ] Is pagination applied on list endpoints?

**Maintainability**
- [ ] Is the function/component doing one clear thing?
- [ ] Are magic numbers replaced with named constants?
- [ ] Would a new contributor understand this without reading the PR description?

**Tests**
- [ ] Do tests cover the happy path and at least one failure path?
- [ ] Are tests deterministic (no flakiness from time, randomness, or network)?

---

## Python Coding Standards

### Formatter & linter: Ruff

AdTicks uses [Ruff](https://docs.astral.sh/ruff/) for both formatting and linting (replaces Black + isort + Flake8).

```bash
# Format all Python files
make fmt-backend
# Equivalent: ruff format backend/

# Lint and auto-fix
make lint-backend
# Equivalent: ruff check backend/ --fix
```

`ruff.toml` (in `backend/`):

```toml
line-length = 100
target-version = "py311"

[lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "TCH"]
ignore = ["E501"]   # line length handled by formatter

[lint.isort]
known-first-party = ["app"]
```

### Type annotations

All function signatures must have full type annotations:

```python
# ✅ Good
async def get_project(project_id: UUID, db: AsyncSession) -> Project:
    ...

# ❌ Bad — missing annotations
async def get_project(project_id, db):
    ...
```

Use `from __future__ import annotations` at the top of files to enable forward references without string quoting.

### Async patterns

- Route handlers that interact with the database must be `async def`.
- Long-running work (AI calls, external HTTP requests) must be dispatched to Celery — never `await` them inside a route handler where the latency would time out an HTTP client.
- Use `asyncio.gather()` for parallel async calls within a service.

```python
# ✅ Parallel AI model calls
async def scan_all_models(prompt_text: str) -> list[str]:
    results = await asyncio.gather(
        openai_client.complete(prompt_text),
        anthropic_client.complete(prompt_text),
        gemini_client.complete(prompt_text),
    )
    return list(results)
```

### Error handling

Use FastAPI's `HTTPException` for API errors. Do not let raw SQLAlchemy or `boto3` exceptions bubble up to the client.

```python
from fastapi import HTTPException, status

async def get_project_or_404(project_id: UUID, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
```

### Dependency injection

Always inject the database session and current user via FastAPI `Depends()` — never import them as globals.

```python
@router.get("/{project_id}", response_model=ProjectRead)
async def read_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    ...
```

### Naming

- **Modules**: snake_case (`keyword_service.py`)
- **Classes**: PascalCase (`KeywordService`)
- **Functions / variables**: snake_case (`get_keyword_clusters`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_CONCURRENT_SCANS = 10`)
- **Private helpers**: leading underscore (`_parse_mention_from_text`)

---

## TypeScript & React Coding Standards

### Linter: ESLint + Prettier

```bash
# Lint frontend
make lint-frontend
# Equivalent: cd frontend && npm run lint

# Format frontend
make fmt-frontend
# Equivalent: cd frontend && npm run format
```

### TypeScript strictness

`tsconfig.json` enforces `"strict": true`. All new code must compile cleanly with no `// @ts-ignore` suppressions.

- Always define explicit return types on exported functions and React components.
- Use `interface` for object shapes that may be extended; `type` for unions, intersections, and aliases.
- Never use `any` — use `unknown` and narrow it with type guards, or use a proper interface.

### React component patterns

**File structure for a new component:**

```tsx
// components/dashboard/MyWidget.tsx

"use client";   // only if this component uses browser APIs or hooks

import { useState } from "react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────

interface MyWidgetProps {
  title: string;
  value: number;
  className?: string;
}

// ─── Component ────────────────────────────────────────────────────────────

function MyWidget({ title, value, className }: MyWidgetProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={cn("rounded-xl border border-white/[0.06] bg-surface2 p-4", className)}>
      <p className="text-sm text-zinc-400">{title}</p>
      <p className="text-2xl font-semibold text-zinc-100">{value}</p>
    </div>
  );
}

export default MyWidget;
export { MyWidget };
```

Rules:
- Use **named function declarations** (`function MyWidget()`), not arrow function assignments for components.
- Export both `default` and named export for layout-level components (enables both import styles).
- Co-locate component-specific types at the top of the file, not in a separate `types/` file (unless shared).
- Use `cn()` (from `@/lib/utils`) for all `className` concatenation — never template literals for conditional classes.

### Data fetching

All server data must go through React Query hooks in `hooks/`. Page components import hooks — they do not call `fetch` directly.

```tsx
// ✅ Good — page uses a hook
import { useScores } from "@/hooks/useScores";

export default function OverviewPage() {
  const { data: scores, isLoading } = useScores(projectId);
  ...
}

// ❌ Bad — direct fetch in component
export default function OverviewPage() {
  const [scores, setScores] = useState(null);
  useEffect(() => { fetch("/api/scores").then(...).then(setScores); }, []);
  ...
}
```

### Naming

- **Components**: PascalCase (`VisibilityScore.tsx`)
- **Hooks**: `use` prefix camelCase (`useKeywordClusters.ts`)
- **Utilities**: camelCase (`formatCurrency.ts`)
- **Types/interfaces**: PascalCase, no `I` prefix (`ProjectResponse`, not `IProjectResponse`)
- **Constants**: UPPER_SNAKE_CASE in the file, or PascalCase arrays/objects (`NAV_SECTIONS`, `PRIORITY_CONFIG`)

### CSS / Tailwind

- Use Tailwind utility classes exclusively — no inline `style` objects except for values that cannot be expressed in Tailwind (e.g. dynamic `radial-gradient` backgrounds, `scaleX` animation driven by JS state).
- Custom CSS goes in `globals.css`, not in component files.
- Use the semantic color aliases defined in `tailwind.config.ts` (`surface2`, `text-primary`, etc.) rather than raw Zinc values where a semantic name exists.

---

## Testing Requirements

### Backend (Python / pytest)

**Minimum coverage gate: 80% line coverage** on `backend/app/`.

Every PR that adds a new route, service function, or Celery task must include tests for:

1. **Happy path** — the expected successful outcome
2. **Auth failure** — unauthenticated request returns 401
3. **Not found** — missing resource returns 404
4. **Validation error** — malformed request body returns 422

#### Test file placement

```
backend/tests/
├── conftest.py          # Shared fixtures (async DB session, test client, test user)
├── api/
│   └── test_projects.py # One test file per router
├── services/
│   └── test_seo_service.py
└── tasks/
    └── test_scan_tasks.py
```

#### Test conventions

```python
# backend/tests/api/test_projects.py

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient, auth_headers: dict):
    payload = {"brand_name": "TestCo", "domain": "testco.io"}
    response = await client.post("/api/projects/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["brand_name"] == "TestCo"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_project_unauthenticated(client: AsyncClient):
    response = await client.post("/api/projects/", json={"brand_name": "X", "domain": "x.io"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get(f"/api/projects/{uuid4()}", headers=auth_headers)
    assert response.status_code == 404
```

#### Running backend tests

```bash
make test              # Run all tests
make test-cov          # Run with HTML coverage report (opens in browser)
make test-watch        # Re-run on file change (requires pytest-watch)

# Run a single test file
docker-compose exec backend pytest tests/api/test_projects.py -v

# Run a single test by name
docker-compose exec backend pytest tests/ -k "test_create_project_success" -v
```

### Frontend (Jest + React Testing Library)

**Minimum coverage gate: 70% line coverage** on `frontend/components/` and `frontend/hooks/`.

Every PR that adds a new component or hook must include tests for:

1. **Renders without crashing** — snapshot or basic `screen.getByText` assertion
2. **Loading state** — skeleton or spinner shown while data is pending
3. **Error state** — error message shown when the hook returns an error
4. **User interaction** — button clicks, form submissions trigger the correct handler

#### Test file placement

Co-locate test files with the component:

```
frontend/
└── components/
    └── dashboard/
        ├── VisibilityScore.tsx
        └── VisibilityScore.test.tsx
```

#### Test conventions

```tsx
// frontend/components/dashboard/VisibilityScore.test.tsx

import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import VisibilityScore from "./VisibilityScore";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>
    {children}
  </QueryClientProvider>
);

describe("VisibilityScore", () => {
  it("renders the score value", () => {
    render(<VisibilityScore score={73} />, { wrapper });
    expect(screen.getByText("73")).toBeInTheDocument();
  });

  it("shows 'Good' label for scores between 60 and 79", () => {
    render(<VisibilityScore score={73} />, { wrapper });
    expect(screen.getByText("Good")).toBeInTheDocument();
  });

  it("shows 'Excellent' label for scores ≥ 80", () => {
    render(<VisibilityScore score={85} />, { wrapper });
    expect(screen.getByText("Excellent")).toBeInTheDocument();
  });
});
```

#### Running frontend tests

```bash
make test-frontend           # Run all Jest tests
make test-frontend-watch     # Watch mode
make test-frontend-cov       # With coverage report

# From inside the frontend directory
cd frontend
npm test                     # Run once
npm test -- --watch          # Watch mode
npm test -- --coverage       # Coverage
```

---

## Database Migration Workflow

**Every schema change must go through an Alembic migration.** Never alter the database schema with raw SQL.

### Creating a migration

```bash
# 1. Make your model change in backend/app/models/my_model.py
# 2. Import the model in backend/app/models/__init__.py
# 3. Import the model in backend/alembic/env.py

# 4. Auto-generate the migration
make migration msg="add backlinks table"
# Equivalent: docker-compose exec backend alembic revision --autogenerate -m "add backlinks table"
```

### Reviewing the generated file

**Always review** the generated file in `backend/alembic/versions/` before applying. Autogenerate misses:

- Column renames (generates drop + add instead of rename — data loss risk)
- Custom constraints and check constraints
- Partial indexes
- Server-side defaults with complex expressions

If autogenerate got something wrong, edit the migration file manually. Add a comment explaining the manual change.

### Applying migrations

```bash
make migrate
# Equivalent: docker-compose exec backend alembic upgrade head
```

### Rollback

```bash
make downgrade
# Equivalent: docker-compose exec backend alembic downgrade -1
```

### Rules for migration files

- Migration files are **committed alongside the model changes** in the same PR.
- Do not squash or edit migration files that are already merged to `main` — create a new migration to fix forward.
- Migration filenames are auto-generated (`<timestamp>_<slug>.py`) — do not rename them.
- Add a docstring to the `upgrade()` function explaining what it does if the intent isn't obvious from the filename.

---

## Running the Full Test Suite

To run everything in the same way CI does:

```bash
# Backend: lint + tests + coverage
make lint-backend
make test-cov

# Frontend: lint + tests + type-check
make lint-frontend
make test-frontend
make typecheck-frontend

# Or run everything in one command
make ci
```

The `make ci` target runs all checks in sequence and exits non-zero if any step fails. This is what GitHub Actions runs on every PR.

---

## CI / Pre-merge Gates

GitHub Actions runs the following on every push and PR:

| Check | Command | Must pass |
|-------|---------|-----------|
| Backend lint | `ruff check backend/` | ✅ |
| Backend format | `ruff format --check backend/` | ✅ |
| Backend tests | `pytest tests/ --cov=app --cov-fail-under=80` | ✅ |
| Frontend lint | `next lint` | ✅ |
| Frontend type-check | `tsc --noEmit` | ✅ |
| Frontend tests | `jest --coverage --coverageThreshold='{"global":{"lines":70}}'` | ✅ |
| Docker build | `docker build ./backend && docker build ./frontend` | ✅ |

A PR cannot be merged until all checks are green. If CI fails on your branch, fix it before requesting review — do not ask a reviewer to look at a failing PR.

### Fixing a flaky test

If a test is intermittently failing (not related to your change), open a separate `fix/` branch immediately. Flaky tests erode trust in CI and should be treated as bugs. Do not merge PRs with known-flaky tests.

---

## Getting Help

- **Slack** `#adticks-dev` — day-to-day questions, PR review requests
- **GitHub Issues** — bugs and feature requests (use the issue templates)
- **Architecture questions** — read `docs/ARCHITECTURE.md` first, then ask in `#adticks-dev`

When asking for help, always include: what you tried, what you expected, what actually happened, and the relevant error output. A minimal reproduction is worth a thousand words.
