# Tasks: ChefBot MVP — Chat With Your Recipe

**Input**: Design documents from `/specs/001-chefbot-mvp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included per Constitution Principle I (Test-First NON-NEGOTIABLE). Tests are written FIRST and must FAIL before implementation begins (Red-Green-Refactor).

**Organization**: Tasks grouped by user story following plan.md phase structure. Each story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story the task belongs to (US1–US6)
- All file paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, tooling, CI configuration

- [ ] T001 Create project directory structure per plan.md (`api/src/models/`, `api/src/services/`, `api/src/routers/`, `api/src/core/`, `api/tests/unit/`, `api/tests/integration/`, `api/tests/contract/`, `evals/datasets/`, `evals/metrics/`, `evals/baselines/`, `evals/reports/`, `docs/adr/`)
- [ ] T002 Initialize uv project with all dependencies and ruff config in `api/pyproject.toml` (FastAPI, httpx, pydantic v2, litellm, recipe-scrapers, structlog, aiosqlite; dev: pytest, ruff, pyright, deepeval, mlflow, pre-commit)
- [ ] T003 [P] Configure pyright strict mode in `api/pyrightconfig.json`
- [ ] T004 [P] Configure pre-commit hooks (ruff check, ruff format, pyright, pytest unit tests) in `.pre-commit-config.yaml`
- [ ] T005 [P] Set up GitHub Actions CI workflow (lint → type-check → test → build) in `.github/workflows/ci.yml`
- [ ] T006 [P] Create API Dockerfile in `api/Dockerfile`

**Checkpoint**: Toolchain ready — `uv sync`, `uv run ruff check .`, `uv run pyright`, `uv run pytest` all run (even if no tests yet).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain models, LLM abstraction, config, logging, error handling, database, and FastAPI skeleton

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests (write first, must fail) ⚠️

- [ ] T007 [P] Write unit tests for Recipe, Ingredient, Step model validation in `api/tests/unit/test_models_recipe.py`
- [ ] T008 [P] Write unit tests for UserProfile and ConversationContext models in `api/tests/unit/test_models_context.py`
- [ ] T009 [P] Write contract test for GET /health endpoint in `api/tests/contract/test_health.py`

### Domain Models

- [ ] T010 [P] Create Recipe, Ingredient, Step Pydantic models in `api/src/models/recipe.py`
- [ ] T011 [P] Create UserProfile Pydantic model in `api/src/models/user_profile.py`
- [ ] T012 Create ConversationContext model with state management in `api/src/models/context.py`
- [ ] T013 Create models package with public exports in `api/src/models/__init__.py`

### Core Infrastructure

- [ ] T014 Create Pydantic Settings config (env vars: LLM provider, model, DB path, log level) in `api/src/core/config.py`
- [ ] T015 [P] Create structlog JSON logging with correlation ID middleware in `api/src/core/logging.py`
- [ ] T016 Create LLM provider Protocol interface (complete, send_structured) in `api/src/core/llm_provider.py`
- [ ] T017 Create LiteLLM concrete implementation with retry-once logic (FR-022) in `api/src/core/litellm_provider.py`
- [ ] T018 [P] Create error handling middleware with user-friendly messages in `api/src/core/errors.py`
- [ ] T019 [P] Create base prompt templates module (structure only) in `api/src/core/prompts.py`
- [ ] T020 Create aiosqlite database module with user_profiles table DDL in `api/src/core/database.py`

### App Skeleton

- [ ] T021 Create FastAPI app with middleware (logging, errors, CORS), router mounting, and GET /health endpoint in `api/src/main.py`

**Checkpoint**: Foundation ready — all model tests pass, health endpoint responds, `uv run pytest` green. User story implementation can begin.

---

## Phase 3: US5 — Load Recipe (Priority: P1) 🎯 MVP

**Goal**: User pastes plain text or sends a URL → ChefBot parses the recipe, confirms title/step count/servings, and flags dietary conflicts from conversation-stated allergies.

**Independent Test**: Paste a recipe as plain text → system confirms recipe name, number of steps, and default serving count.

### Tests (write first, must fail) ⚠️

- [ ] T022 [P] [US5] Write contract test for POST /recipe/load (text + URL + error cases) in `api/tests/contract/test_recipe.py`
- [ ] T023 [P] [US5] Write unit tests for recipe text parser (LLM extraction → Recipe) in `api/tests/unit/test_recipe_parser.py`
- [ ] T024 [P] [US5] Write unit tests for URL fetcher (httpx → recipe-scrapers fallback chain) in `api/tests/unit/test_url_fetcher.py`

### Implementation

- [ ] T025 [P] [US5] Implement recipe text parser with LLM extraction prompt in `api/src/services/recipe_parser.py`
- [ ] T026 [P] [US5] Implement URL fetcher (httpx + recipe-scrapers + wild_mode + LLM fallback) in `api/src/services/url_fetcher.py`
- [ ] T027 [US5] Implement dietary checker (constraint list × ingredient list → warnings) in `api/src/services/dietary_checker.py`
- [ ] T028 [US5] Implement POST /recipe/load router with request/response schemas and dietary warnings in `api/src/routers/recipe.py`

**Checkpoint**: User can load a recipe via text or URL. Dietary checker works with conversation-stated allergies (profile integration comes in Phase 6).

---

## Phase 4: US1 — Step-by-Step Navigation (Priority: P1) 🎯 MVP

**Goal**: User asks "What comes next?" and ChefBot replies with the correct step in concise language. Supports next/prev/current/jump and off-topic redirect.

**Independent Test**: Load any recipe, advance to a middle step, ask "What comes next?" — system returns the correct next step.

### Tests (write first, must fail) ⚠️

- [ ] T029 [P] [US1] Write contract test for POST /chat (step navigation + off-topic intents) in `api/tests/contract/test_chat_navigation.py`
- [ ] T030 [P] [US1] Write unit tests for step navigator (next/prev/current/jump/boundary) in `api/tests/unit/test_step_navigator.py`
- [ ] T031 [P] [US1] Write unit tests for chat orchestrator intent classification and routing in `api/tests/unit/test_chat_orchestrator.py`

### Implementation

- [ ] T032 [US1] Implement step navigator service (next/prev/current/jump, boundary handling) in `api/src/services/step_navigator.py`
- [ ] T033 [US1] Implement chat orchestrator with intent classification, service routing, and context management in `api/src/services/chat_orchestrator.py`
- [ ] T034 [US1] Implement POST /chat router with request/response schemas in `api/src/routers/chat.py`
- [ ] T035 [US1] Add step navigation, intent classification, and off-topic redirect prompt templates to `api/src/core/prompts.py`

**Checkpoint**: Full recipe walkthrough works — load recipe → navigate all steps → finish. MVP is functional (SC-004).

---

## Phase 5: US4 — Evaluation Dataset (Priority: P1) ⚠️ HEALTH-CRITICAL

**Goal**: Curate ≥100 test cases (≥50 scaling, ≥50 substitution) with automated scoring via deepeval custom metrics and MLflow experiment tracking. This is the regression gate for health-critical features.

**Independent Test**: Run `uv run pytest ../evals/` — test runner produces a structured pass/fail report with per-case scores.

**Can run in parallel with Phases 3–4.**

### Datasets

- [ ] T036 [P] [US4] Create scaling eval dataset (≥50 cases: fractions, non-divisible, edge multipliers) in `evals/datasets/scaling_v1.0.0.json`
- [ ] T037 [P] [US4] Create substitution eval dataset (≥50 cases: allergens, dietary, pantry swaps, safety) in `evals/datasets/substitution_v1.0.0.json`

### Custom Metrics (deepeval BaseMetric subclasses)

- [ ] T038 [P] [US4] Implement NumericTolerance metric (±5% for continuous, exact for discrete) in `evals/metrics/numeric_tolerance.py`
- [ ] T039 [P] [US4] Implement SetMembership metric (substitution relevance vs human-curated labels) in `evals/metrics/set_membership.py`
- [ ] T040 [P] [US4] Implement AllergenGate metric (blocklist intersection, hard fail on any conflict) in `evals/metrics/allergen_gate.py`

### Test Runner

- [ ] T041 [US4] Create pytest fixtures and MLflow experiment setup in `evals/conftest.py`
- [ ] T042 [US4] Implement scaling eval test runner with deepeval test cases in `evals/test_scaling_eval.py`
- [ ] T043 [US4] Implement substitution eval test runner with deepeval test cases in `evals/test_substitution_eval.py`
- [ ] T044 [US4] Add eval suite to CI workflow with path-filtered trigger (evals/, prompts/, llm/) in `.github/workflows/ci.yml`

### Parsing Accuracy (SC-006)

- [ ] T044a [P] [US4] Create parsing eval dataset (≥30 cases: plain text + URL, varied formats, edge cases) in `evals/datasets/parsing_v1.0.0.json`
- [ ] T044b [US4] Implement parsing accuracy scorer (title, servings, ingredient count, step count match) in `evals/metrics/parsing_accuracy.py`
- [ ] T044c [US4] Implement parsing eval test runner with deepeval test cases in `evals/test_parsing_eval.py`

**Checkpoint**: Eval suite runs end-to-end on sample data. MLflow logs experiments. CI runs evals on relevant changes. Gate thresholds configured (≥95% scaling, ≥90% substitution, 0% allergen, ≥95% parsing accuracy).

---

## Phase 6: US6 — Dietary Profile (Priority: P2) ⚠️ HEALTH-CRITICAL

**Goal**: User sets up dietary constraints during onboarding (or via settings). Constraints are persisted and automatically applied on recipe load and substitution requests. Toggle on/off supported.

**Independent Test**: Create profile with nut allergy → load recipe with walnuts → system flags conflict. Disable checking → load same recipe → no warning.

**Can run in parallel with Phases 3–5.**

### Tests (write first, must fail) ⚠️

- [ ] T045 [P] [US6] Write contract tests for profile CRUD endpoints (GET/POST/PUT/PATCH + allergen list) in `api/tests/contract/test_profile.py`
- [ ] T046 [P] [US6] Write unit tests for user profile service (CRUD, constraint normalisation) in `api/tests/unit/test_user_profile_service.py`
- [ ] T047 [P] [US6] Write integration test for profile-aware recipe loading in `api/tests/integration/test_profile_recipe_load.py`

### Implementation

- [ ] T048 [US6] Implement user profile service (create, read, update, toggle, allergen list) in `api/src/services/user_profile_service.py`
- [ ] T049 [US6] Implement profile router (GET/POST/PUT/PATCH /profile, GET /profile/allergens) in `api/src/routers/profile.py`
- [ ] T050 [US6] Integrate profile constraints into dietary checker on recipe load (constraint merging logic) in `api/src/services/dietary_checker.py`
- [ ] T051 [US6] Integrate profile constraints into chat orchestrator context for substitution filtering in `api/src/services/chat_orchestrator.py`

**Checkpoint**: Profile CRUD works. Recipe load merges profile + conversation constraints. Toggle disables profile checks but conversation-stated allergies still honoured (FR-026).

---

## Phase 7: US2 — Quantity Scaling (Priority: P2) ⚠️ HEALTH-CRITICAL

**Goal**: User asks "How much flour for 2 servings?" and ChefBot returns the correctly scaled quantity with rounding explanations for non-divisible items.

**Independent Test**: Load recipe for 4 servings, ask "How much flour for 2 servings?" — system returns correctly halved amount.

**Depends on**: Phase 3 (US5 — recipe must be loaded), Phase 5 (US4 — eval gate required)

### Tests (write first, must fail) ⚠️

- [ ] T052 [P] [US2] Write unit tests for quantity scaler (fractions, non-divisible, edge multipliers) in `api/tests/unit/test_quantity_scaler.py`
- [ ] T053 [P] [US2] Write contract test for POST /chat (scaling intent) in `api/tests/contract/test_chat_scaling.py`

### Implementation

- [ ] T054 [US2] Implement quantity scaler service with rounding logic and scaling prompt in `api/src/services/quantity_scaler.py`
- [ ] T055 [US2] Integrate quantity scaler into chat orchestrator (scaling intent → scaler service) in `api/src/services/chat_orchestrator.py`
- [ ] T056 [US2] Run scaling eval suite, establish baseline, and verify ≥95% accuracy gate (SC-003) in `evals/baselines/`

**Checkpoint**: Scaling works end-to-end via chat. Eval baseline established and meets SC-003 threshold.

---

## Phase 8: US3 — Ingredient Substitutions (Priority: P2) ⚠️ HEALTH-CRITICAL

**Goal**: User asks "What can I use instead of Mirin?" and ChefBot suggests alternatives with flavour impact notes, safety disclaimers, and allergen filtering against profile + conversation constraints.

**Independent Test**: Load recipe with Mirin, ask for a substitute — system suggests at least one viable alternative with explanation.

**Depends on**: Phase 3 (US5), Phase 5 (US4 — eval gate), Phase 6 (US6 — profile constraints)

### Tests (write first, must fail) ⚠️

- [ ] T057 [P] [US3] Write unit tests for allergen detector (blocklist intersection, edge cases) in `api/tests/unit/test_allergen_detector.py`
- [ ] T058 [P] [US3] Write unit tests for substitution service (suggestions, safety disclaimers, filtering) in `api/tests/unit/test_substitution_service.py`
- [ ] T059 [P] [US3] Write contract test for POST /chat (substitution intent with allergen warnings) in `api/tests/contract/test_chat_substitution.py`

### Implementation

- [ ] T060 [US3] Implement blocklist-based allergen detector in `api/src/services/allergen_detector.py`
- [ ] T061 [US3] Implement substitution service with LLM suggestions, allergen filtering, and safety disclaimers in `api/src/services/substitution_service.py`
- [ ] T062 [US3] Integrate substitution service into chat orchestrator (substitution intent → allergen check → suggest) in `api/src/services/chat_orchestrator.py`
- [ ] T063 [US3] Run substitution eval suite, establish baseline, and verify ≥90% relevance + 0% allergen-conflict gates (SC-005, SC-007) in `evals/baselines/`

**Checkpoint**: Substitutions work end-to-end. Allergen gate passes at 0% conflict rate. Eval baseline established and meets SC-005 + SC-007 thresholds.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, performance verification, security review, full regression baseline

- [ ] T064 [P] Generate API documentation from contracts in `docs/api.md`
- [ ] T065 [P] Copy and verify quickstart guide in `docs/quickstart.md`
- [ ] T066 Performance verification: <5s recipe load (SC-001), <2s conversational queries (SC-002) across all endpoints
- [ ] T067 Security review: input validation limits, prompt injection mitigation, error message leakage
- [ ] T068 Run full eval suite, commit final baseline, and validate no regressions (SC-009) in `evals/baselines/`

**Checkpoint**: All success criteria met. Documentation complete. Ready for deployment.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational ←── BLOCKS all user stories
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

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|-----------|-------------------|
| US5 Load Recipe (P1) | Foundational only | US4, US6 |
| US1 Step Navigation (P1) | US5 (needs loaded recipe) | US4, US6 |
| US4 Eval Dataset (P1) | Foundational only | US5, US1, US6 |
| US6 Dietary Profile (P2) | Foundational only | US5, US1, US4 |
| US2 Quantity Scaling (P2) | US5 + US4 (eval gate) | — |
| US3 Substitutions (P2) | US5 + US4 + US6 (eval gate + profile) | — |

### Within Each User Story

1. Tests written FIRST → must FAIL (Red)
2. Models before services
3. Services before routers
4. Core implementation before integration
5. All tests pass (Green)
6. Refactor if needed

---

## Parallel Execution Examples

### Phase 2: Foundational

```
# Parallel batch 1 — Tests (all different files):
T007: Unit tests for Recipe/Ingredient/Step models
T008: Unit tests for UserProfile/ConversationContext models
T009: Contract test for GET /health

# Parallel batch 2 — Models (independent files):
T010: Recipe, Ingredient, Step models
T011: UserProfile model

# Sequential (depends on T010, T011):
T012: ConversationContext model (references Recipe, UserProfile)

# Parallel batch 3 — Core infrastructure:
T014: Config
T015: Logging
T016: LLM Protocol
T018: Error middleware
T019: Prompt templates

# Sequential:
T017: LiteLLM implementation (depends on T016 Protocol)
T020: Database module
T021: FastAPI app skeleton (depends on all core modules)
```

### Phases 3–6: Parallel Stories

```
# With two developers after Phase 2 completes:

Developer A (critical path):        Developer B (parallel):
Phase 3: US5 Load Recipe            Phase 5: US4 Eval Dataset
    ↓                                   (T036-T044, independent)
Phase 4: US1 Step Navigation
    ↓                               Phase 6: US6 Dietary Profile
Phase 7: US2 Quantity Scaling           (T045-T051, independent)
    ↓
Phase 8: US3 Substitutions
```

### Phase 5: US4 Eval Dataset (all metrics parallel)

```
# Parallel batch — datasets:
T036: Scaling dataset JSON
T037: Substitution dataset JSON

# Parallel batch — metrics (all independent files):
T038: NumericTolerance metric
T039: SetMembership metric
T040: AllergenGate metric

# Sequential:
T041: conftest.py (depends on metrics)
T042: Scaling test runner
T043: Substitution test runner
T044: CI integration
```

---

## Implementation Strategy

### MVP First (Phases 1–4: Setup + Foundational + US5 + US1)

1. Complete Phase 1: Setup → toolchain works
2. Complete Phase 2: Foundational → models, LLM, core infra
3. Complete Phase 3: US5 Load Recipe → user can provide recipes
4. Complete Phase 4: US1 Step Navigation → user can navigate recipes via chat
5. **STOP and VALIDATE**: Full recipe walkthrough works (SC-004)
6. Deploy/demo MVP

### Incremental Delivery

| Increment | Stories | What It Delivers |
|-----------|---------|-----------------|
| MVP | US5 + US1 | Load recipe, navigate steps via chat |
| +Eval | US4 | Automated safety regression gate |
| +Profile | US6 | Persistent dietary preferences |
| +Scaling | US2 | Quantity adjustment (eval-gated) |
| +Substitutions | US3 | Ingredient swaps with allergen safety (eval-gated) |
| Polish | — | Docs, perf, security |

### Health-Critical Gate (US2, US3)

Before merging any health-critical feature:
1. Eval dataset must exist and pass CI (US4 prerequisite)
2. Feature must pass its eval threshold (≥95% scaling, ≥90% substitution, 0% allergen)
3. Baseline committed to `evals/baselines/`
4. No regression on any other eval metric (SC-009)

---

## Summary

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|----------|
| 1. Setup | — | T001–T006 (6) | T003–T006 |
| 2. Foundational | — | T007–T021 (15) | T007–T009, T010–T011, T014–T016+T018–T019 |
| 3. US5 Load Recipe | P1 | T022–T028 (7) | T022–T024, T025–T026 |
| 4. US1 Step Navigation | P1 | T029–T035 (7) | T029–T031 |
| 5. US4 Eval Dataset | P1 | T036–T044c (12) | T036–T037+T044a, T038–T040 |
| 6. US6 Dietary Profile | P2 | T045–T051 (7) | T045–T047 |
| 7. US2 Scaling | P2 | T052–T056 (5) | T052–T053 |
| 8. US3 Substitutions | P2 | T057–T063 (7) | T057–T059 |
| 9. Polish | — | T064–T068 (5) | T064–T065 |
| **Total** | | **71** | |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks within the same batch
- [Story] label maps each task to its user story for traceability
- Constitution Principle I: ALL tests written before implementation — verify they fail first
- Eval gates (SC-003, SC-005, SC-007, SC-009) are merge-blocking for health-critical features
- Commit after each task or logical group using Conventional Commits
- Stop at any checkpoint to validate the story independently
- `research.md` R3 notes: use deepeval BaseMetric subclasses + MLflow per plan.md
