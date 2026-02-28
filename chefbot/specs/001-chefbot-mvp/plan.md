# Implementation Plan: ChefBot MVP — Chat With Your Recipe

**Branch**: `001-chefbot-mvp` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-chefbot-mvp/spec.md`

## Summary

ChefBot is a hands-free recipe assistant that lets cooks ask questions while cooking. The MVP supports loading recipes (text or URL), step-by-step navigation, quantity scaling, and ingredient substitutions — with health-safety evaluation gates for the latter two. The backend is a Python 3.12+ / FastAPI API server; mobile client is deferred to a spike.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI, httpx, pydantic v2, litellm, recipe-scrapers, structlog, aiosqlite, deepeval, mlflow
**Storage**: SQLite (dev/MVP) → PostgreSQL (production). UserProfile persisted; Recipe/ConversationContext in-memory.
**Testing**: pytest, ruff (format + lint), pyright (type checking). deepeval + MLflow for health-critical eval tracking.
**Target Platform**: API server (Linux/macOS) consumed by a mobile client (TBD via spike)
**Project Type**: Mobile + API (API-only for MVP)
**Performance Goals**: <5s recipe load (SC-001), <2s conversational queries (SC-002/FR-021)
**Constraints**: 0% allergen-conflict (SC-007), ≥95% scaling accuracy (SC-003), ≥90% substitution relevance (SC-005), ≥100 eval test cases (SC-008)
**Scale/Scope**: Single-user MVP, one recipe at a time (FR-010)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-First (NON-NEGOTIABLE) | ✅ PASS | Eval dataset (US4) is P1 prerequisite for health-critical features. All stories require tests-first. Red-Green-Refactor enforced. |
| II. Simplicity | ✅ PASS | One recipe at a time (FR-010), no accounts, no image input, no unit conversion, SQLite for 1 table, LiteLLM (thin wrapper) over LangChain. |
| III. Small Increments | ✅ PASS | 6 user stories with clear priorities and dependency chain. Each independently deliverable. |
| IV. Quality Gates | ✅ PASS | Pre-commit hooks (ruff, pyright, pytest), CI pipeline, eval dataset gates health-critical merges (FR-019, SC-009). |
| V. Conversational UX First | ✅ PASS | FR-008 (concise language), FR-009 (clarifying questions), FR-021 (<2s target), FR-013 (off-topic redirect). |
| VI. Learning-Driven Development | ✅ PASS | Mobile client requires spike + ADR. LLM provider choice documented. |
| VII. Observability | ✅ PASS | structlog with JSON + correlation IDs (research R2), health-check endpoint (contract), latency tracking from day one. |

**Gate result**: PASS — no violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-chefbot-mvp/
├── plan.md              # This file
├── research.md          # Phase 0 output — 5 research decisions
├── data-model.md        # Phase 1 output — 6 entities with fields, validation, state transitions
├── quickstart.md        # Phase 1 output — developer setup guide
├── contracts/           # Phase 1 output — API contracts
│   ├── chat.md          #   POST /chat (primary conversational endpoint)
│   ├── recipe.md        #   POST /recipe/load
│   ├── profile.md       #   CRUD /profile + allergen list
│   └── health.md        #   GET /health
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
api/
├── src/
│   ├── models/          # Pydantic domain models (Recipe, Ingredient, Step, ConversationContext, UserProfile)
│   ├── services/        # Business logic
│   │   ├── recipe_parser.py       # Plain text → Recipe (LLM extraction)
│   │   ├── url_fetcher.py         # URL → HTML → recipe-scrapers → Recipe
│   │   ├── dietary_checker.py     # Ingredient vs constraint matching
│   │   ├── step_navigator.py      # Next/prev/current/jump step logic
│   │   ├── chat_orchestrator.py   # Intent classification, routing, context management
│   │   ├── quantity_scaler.py     # Serving ratio scaling
│   │   ├── substitution_service.py # LLM-powered substitution with allergen filtering
│   │   ├── allergen_detector.py   # Blocklist-based allergen conflict detection
│   │   └── user_profile_service.py # CRUD for dietary profile
│   ├── routers/         # FastAPI route handlers
│   │   ├── chat.py      # POST /chat
│   │   ├── recipe.py    # POST /recipe/load
│   │   └── profile.py   # GET/POST/PUT/PATCH /profile
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (env vars)
│   │   ├── logging.py           # structlog JSON setup + correlation ID middleware
│   │   ├── llm_provider.py      # typing.Protocol for LLM interface
│   │   ├── litellm_provider.py  # LiteLLM concrete implementation
│   │   ├── errors.py            # Error handling middleware, user-friendly messages
│   │   ├── prompts.py           # Prompt templates (step nav, scaling, substitution, extraction)
│   │   └── database.py          # aiosqlite connection + UserProfile table
│   └── main.py          # FastAPI app, middleware, router mounting, health endpoint
├── tests/
│   ├── unit/            # No I/O, no LLM calls
│   ├── integration/     # Mocked LLM, real DB
│   └── contract/        # API surface validation
├── pyproject.toml       # uv project config + tool settings
└── Dockerfile

evals/
├── datasets/
│   ├── scaling_v1.0.0.json       # ≥50 quantity scaling test cases
│   └── substitution_v1.0.0.json  # ≥50 substitution test cases (incl. allergen)
├── metrics/                       # Custom deepeval BaseMetric subclasses
│   ├── numeric_tolerance.py       # Quantity scaling scorer
│   ├── set_membership.py          # Substitution relevance scorer
│   └── allergen_gate.py           # Allergen conflict hard gate
├── conftest.py                    # pytest fixtures + MLflow experiment setup
├── test_scaling_eval.py           # deepeval test cases for scaling
└── test_substitution_eval.py      # deepeval test cases for substitutions

docs/
├── adr/                # Architecture Decision Records
└── quickstart.md       # Developer setup guide (symlink or copy from specs)
```

**Structure Decision**: Mobile + API (Option 3). API backend only for MVP — mobile directory created after spike ADR. `evals/` is a sibling of `api/` because eval datasets are project-level artifacts, not API-specific.

## Complexity Tracking

No violations found — no complexity justifications required.

## Research Decisions (Phase 0)

See [research.md](research.md) for full details. Summary:

| # | Decision | Choice | Key Rationale |
|---|----------|--------|---------------|
| R1 | Recipe parsing | `recipe-scrapers` for URLs, LLM extraction for text | 611+ sites covered; LLM only used when deterministic parsing fails |
| R2 | LLM abstraction | LiteLLM behind `typing.Protocol` | Single-file swap; supports all major providers; retry built into wrapper |
| R3 | Eval framework | deepeval (test runner + custom metrics) + MLflow (experiment tracking) | Metric versioning, run comparison, and LLM-metric extensibility out of the box; custom scorers as BaseMetric subclasses |
| R4 | Project structure | `api/` + `evals/` + `docs/` | API-only MVP; mobile deferred to spike |
| R5 | UserProfile storage | SQLite via `aiosqlite`, raw SQL | One table, 3 columns; ORM is overkill |

## Design Artifacts (Phase 1)

| Artifact | Path | Content |
|----------|------|---------|
| Data model | [data-model.md](data-model.md) | 6 entities: Recipe, Ingredient, Step, ConversationContext, UserProfile, EvaluationDataset. Fields, types, validation, state transitions, constraint merging logic. |
| Chat contract | [contracts/chat.md](contracts/chat.md) | POST /chat — primary conversational endpoint with intent classification, context tracking, warnings. |
| Recipe contract | [contracts/recipe.md](contracts/recipe.md) | POST /recipe/load — text and URL loading with dietary warnings. |
| Profile contract | [contracts/profile.md](contracts/profile.md) | CRUD endpoints for dietary profile + predefined allergen list. |
| Health contract | [contracts/health.md](contracts/health.md) | GET /health — service health check (Constitution §VII). |
| Quickstart | [quickstart.md](quickstart.md) | Developer setup, run, test, smoke test commands. |

## Implementation Phases

### Phase 1: Setup
Project initialisation, tooling configuration (uv, ruff, pyright, pre-commit, CI, Docker).

### Phase 2: Foundational
Core models (Recipe, Ingredient, Step, ConversationContext, UserProfile), LLM provider interface + LiteLLM implementation, config, logging, error handling, FastAPI app skeleton.

**⚠️ BLOCKS all user stories.**

### Phase 3: US5 — Load Recipe (P1)
Recipe text parser, URL fetcher, dietary constraint checker, load endpoint.

### Phase 4: US1 — Step Navigation (P1)
Step navigator, chat orchestrator, chat endpoint, prompt templates.

### Phase 5: US4 — Eval Dataset (P1)
Dataset creation (≥100 cases), test runner, regression checker, CI integration.

**Can run in parallel with Phases 3–4.**

### Phase 6: US6 — Dietary Profile (P2)
Profile service, onboarding/settings endpoints, integration with dietary checker.

**Can run in parallel with Phases 3–5.**

### Phase 7: US2 — Quantity Scaling (P2) ⚠️ HEALTH-CRITICAL
Scaling service, orchestrator integration. **Must pass eval gate (≥95%).**

### Phase 8: US3 — Substitutions (P2) ⚠️ HEALTH-CRITICAL
Substitution service, allergen detector, orchestrator integration. **Must pass eval gate (≥90% relevance, 0% allergen-conflict).**

### Phase 9: Polish
API docs, performance verification, security review, full eval baseline, ADRs.

## Dependency Graph

```
Phase 1: Setup
    ↓
Phase 2: Foundational
    ↓
    ├── Phase 3: US5 Load Recipe (P1)
    │       ↓
    │   Phase 4: US1 Step Navigation (P1)
    │
    ├── Phase 5: US4 Eval Dataset (P1)        ← parallel with 3/4
    │
    └── Phase 6: US6 Dietary Profile (P2)     ← parallel with 3/4/5
            ↓
        Phase 7: US2 Quantity Scaling (P2)     ← needs US5 + US4
            ↓
        Phase 8: US3 Substitutions (P2)        ← needs US5 + US4 + US6
            ↓
        Phase 9: Polish
```

## MVP Scope

**Minimum viable product** = Phases 1–4 (Setup + Foundational + US5 + US1):
- User can paste a recipe and navigate it step-by-step via chat
- Achievable before health-critical features require eval dataset

**Next**: Run `/speckit.tasks` to generate the detailed task breakdown in `tasks.md`.
