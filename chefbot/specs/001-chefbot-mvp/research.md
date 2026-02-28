# Research: ChefBot MVP

**Date**: 2026-02-28 | **Spec**: `specs/001-chefbot-mvp/spec.md`

## R1 — Recipe Parsing (URL + Plain Text)

### Decision

| Source | Primary Approach | Fallback |
|--------|-----------------|----------|
| **URL** | `recipe-scrapers` library (611+ sites, `wild_mode` for unknown sites) | LLM extraction from stripped HTML |
| **Plain text** | LLM structured extraction → Pydantic `Recipe` model | Retry with rephrased prompt → ask user to clarify |

### Rationale

- **URL**: `recipe-scrapers` handles schema.org JSON-LD and site-specific HTML scraping for 611+ sites. `wild_mode` attempts generic schema.org extraction on any URL. Most recipe blogs embed JSON-LD because Google requires it for rich search results. HTTP layer controlled via `httpx` (async, timeouts, custom headers for paywall/timeout detection per FR-015).
- **Plain text**: No consistent structure exists across user-pasted recipes. LLM extraction with Pydantic structured output is the most robust approach, directly achieving SC-006 (95% parsing accuracy). The LLM is already in the stack for conversation.
- **Cost**: LLM tokens consumed only when deterministic parsing fails (URLs) or for text input. Keeps costs low.

### Alternatives Considered

| Alternative | Verdict |
|-------------|---------|
| `extruct` (generic structured data) | Lower-level than `recipe-scrapers`; still need recipe-specific mapping. `recipe-scrapers` uses it internally. |
| `beautifulsoup4` + manual scraping | Enormous maintenance burden per site. `recipe-scrapers` already does this. |
| Regex/NLP for plain text (`ingredient-parser`, CRF models) | Fails on unstructured paragraphs; cannot extract title/steps. |
| LLM for all URL recipes | Wasteful — burns tokens on content already machine-readable in JSON-LD. |

### Key Libraries

| Package | Purpose |
|---------|---------|
| `recipe-scrapers` | URL recipe extraction (primary) |
| `httpx` | Async HTTP client (timeouts, custom UA, error mapping) |
| `pydantic` v2 | Recipe/Ingredient/Step schema + LLM structured output validation |
| `ingredient-parser` (optional) | Post-processing ingredient strings into `(qty, unit, name)` for scaling |

### Error Handling

**URL fetch failures** — mapped to user-friendly messages per FR-015:

| Scenario | Detection | User Message |
|----------|-----------|--------------|
| Timeout | `httpx.TimeoutException` | "The request timed out. Try pasting the recipe as text." |
| HTTP 403 | `response.status_code == 403` | "This page appears to require a login." |
| Paywall | 402 or paywall heuristics | "This page appears to be behind a paywall." |
| DNS/connection | `httpx.ConnectError` | "Could not reach that website." |

**Parse failures** — layered fallback:

1. `recipe-scrapers` with site-specific scraper
2. `recipe-scrapers` with `wild_mode=True`
3. LLM extraction from stripped HTML
4. Error message + suggest pasting as text (FR-015)

---

## R2 — LLM Provider Abstraction

### Decision

Use **LiteLLM** behind a thin `typing.Protocol` interface, wrapped in a `ResilientLLMService` for retry and observability.

### Rationale

| Aspect | Choice |
|--------|--------|
| **Library** | LiteLLM — lightweight, supports OpenAI/Anthropic/Ollama, handles provider differences |
| **Interface** | `typing.Protocol` (not ABC) — structural subtyping, trivial to mock in tests |
| **Retry (FR-022)** | `ResilientLLMService` wrapper with a single-retry loop — no backoff library needed |
| **Structured output** | Pydantic models + provider JSON mode + post-parse validation |
| **Async** | `litellm.acompletion()` + `asyncio.timeout()` + FastAPI `Depends()` injection |
| **Token tracking** | Structured JSON log events via `structlog` with correlation IDs |
| **Prompts** | Python functions in a `prompts/` module — plain strings, version-controlled |

**Key property**: Only one file (`litellm_provider.py`) imports `litellm`. Everything else depends on the project-owned Protocol and dataclasses. Swapping providers is a single-file change.

### Alternatives Considered

| Alternative | Verdict |
|-------------|---------|
| LangChain | Too heavy; pulls in massive dependency tree, most features unused. Violates Simplicity. |
| Raw OpenAI SDK | Locks to one provider; no Anthropic/Ollama without rewriting. LiteLLM provides the abstraction for free. |
| Custom HTTP client | Maximum control but reinvents provider-specific auth, streaming, token counting. |
| No abstraction (direct calls) | Fast to start but makes provider swap a multi-file refactor. Not worth the saved effort. |

---

## R3 — Evaluation Dataset & Test Runner

### Decision

**deepeval** (test orchestration + custom `BaseMetric` subclasses) **+ MLflow** (experiment tracking, metric versioning, run comparison). Versioned JSON test fixtures stored in `evals/datasets/`.

### Rationale

| Factor | deepeval + MLflow | Custom pytest only | promptfoo |
|--------|-------------------|--------------------|-----------|
| Python-native | Yes — pytest plugin, BaseMetric API | Yes | No (Node.js) |
| Metric versioning | MLflow tracks every run, parameters, and scores | Manual JSON diff | Opaque caching |
| LLM-metric extensibility | BaseMetric subclass — straightforward to add LLM-as-judge metrics later | Rewrite scorer infra | JS-based custom graders |
| Scoring control | Full — custom BaseMetric subclasses for all 3 dimensions | Full | Generic graders |
| CI integration | pytest plugin — runs in existing pytest step | Native | Separate Node.js step |
| Run comparison | MLflow UI + API for regression detection | Manual baseline diff | Built-in but limited |

The three scoring dimensions (scaling accuracy, substitution relevance, allergen-conflict) are domain-specific enough that custom scorers (deepeval `BaseMetric` subclasses) are required regardless. deepeval provides the orchestration (test-case parametrization, structured reporting) while MLflow provides experiment tracking and metric versioning that a pure-pytest approach would need to reinvent.

### Scoring Methodology

| Dimension | Scorer | Pass Criterion |
|-----------|--------|----------------|
| **Quantity scaling** | Numeric extraction + tolerance (±5%) | ≥95% of cases pass |
| **Substitution relevance** | Set membership against human-curated labels | ≥90% of cases have relevance ≥1.0 |
| **Allergen-conflict** | Blocklist intersection — hard gate | 0% conflict rate (single failure = run fails) |
| **Safety disclaimer** | Keyword scan ("verify", "check label", "consult") | Binary pass/fail on flagged cases |
| **Flavour impact** | Keyword scan ("flavour", "taste", "texture") | Soft flag for human review |

### JSON Schema Design

**Two dataset files**, one per category, with shared envelope:
- `evals/datasets/scaling_v1.0.0.json` (≥50 cases)
- `evals/datasets/substitution_v1.0.0.json` (≥50 cases)

**Scaling case** fields: `id`, `description`, `tags`, `input` (recipe_servings, ingredient, original_quantity, target_servings), `expected` (quantity, tolerance_pct), `scoring` method.

**Substitution case** fields: `id`, `description`, `tags`, `input` (recipe_name, ingredient_to_replace, user_constraints, conversation_context), `expected` (acceptable_substitutes, unacceptable_substitutes, allergen_constraints, must_include_safety_disclaimer), `scoring` method.

**Tag taxonomies**:
- Scaling: `simple-fraction`, `non-divisible`, `large-multiplier`, `small-multiplier`, `unit-boundary`, `continuous`, `discrete`
- Substitution: `pantry-swap`, `allergen-critical`, `dietary-vegan`, `dietary-vegetarian`, `dietary-halal`, `dietary-kosher`, `no-close-substitute`, `allergy-gluten`, `allergy-dairy`, `allergy-nut`, `allergy-shellfish`, `allergy-soy`, `allergy-egg`

### CI Integration

- **Path-filtered trigger**: only runs when `evals/`, `src/**/prompts/`, or `src/**/llm/` change
- **Regression check**: JSON baseline diff; merge blocked on any regression
- **Baseline workflow**: run locally → review → promote report to `evals/baselines/` → commit
- **Cost control**: cache LLM responses (keyed on prompt hash), selective runs (`-k scaling`), parallelism with rate-limit semaphore

### Alternatives Considered

| Alternative | Verdict |
|-------------|---------|
| Custom pytest only (no deepeval) | Requires reinventing test-case orchestration, structured reporting, and metric versioning. Not worth the saved dependency. |
| promptfoo | Reconsider if multi-model A/B testing needed. Node.js dependency not justified for MVP. |
| Braintrust / LangSmith / W&B Weave | SaaS dependency, cost; beyond MVP needs. |
| Pure `@pytest.mark.parametrize` (no JSON) | Doesn't scale to 100+ cases; can't diff dataset independently. |

---

## R4 — Project Structure

### Decision

**Mobile + API** structure (Option 3 from template). API backend only for MVP; mobile client deferred to spike.

```text
api/
├── src/
│   ├── models/          # Pydantic domain models
│   ├── services/        # Business logic (parser, scaler, substitution, etc.)
│   ├── routers/         # FastAPI route handlers
│   ├── core/            # Cross-cutting (config, logging, LLM provider, errors, prompts)
│   └── main.py          # FastAPI application entry point
└── tests/
    ├── unit/            # Pure logic tests (no I/O)
    ├── integration/     # Service boundary tests (with LLM mocks)
    └── contract/        # API surface tests

evals/
├── datasets/            # Versioned JSON test fixtures
├── metrics/             # Custom deepeval BaseMetric subclasses
│   ├── numeric_tolerance.py   # Quantity scaling scorer
│   ├── set_membership.py      # Substitution relevance scorer
│   └── allergen_gate.py       # Allergen conflict hard gate
├── baselines/           # Accepted baseline reports
├── reports/             # Generated reports (gitignored)
├── conftest.py          # pytest fixtures + MLflow experiment setup
├── test_scaling_eval.py       # deepeval test cases for scaling
└── test_substitution_eval.py  # deepeval test cases for substitutions

docs/
├── adr/                 # Architecture Decision Records
├── api.md               # API documentation
└── quickstart.md        # Developer setup guide
```

### Rationale

- Follows constitution's Mobile + API option. Mobile directory deferred until spike ADR.
- `api/src/` separates models / services / routers / core for Small Increments (§III).
- `evals/` is a sibling of `api/`, not inside it — eval datasets are project-level artifacts.
- `docs/adr/` for Learning-Driven Development (§VI).

---

## R5 — On-Device Storage for UserProfile

### Decision

**SQLite via `aiosqlite`** on the API side for MVP. Profile data is lightweight (dietary constraints list + toggle flag). No ORM — raw SQL with Pydantic model mapping.

### Rationale

- Constitution permits SQLite for local development. UserProfile is the only persisted entity in MVP.
- `aiosqlite` provides async access compatible with FastAPI's async-first approach.
- No ORM overhead — a single table with 3 columns (`user_id TEXT PK`, `constraints JSON`, `check_enabled BOOLEAN`) is trivially managed with raw SQL.
- Migration path to PostgreSQL: swap `aiosqlite` for `asyncpg`, same SQL statements.

### Alternatives Considered

| Alternative | Verdict |
|-------------|---------|
| SQLAlchemy async | Too heavy for one table. Violates Simplicity. Reconsider when >3 tables. |
| JSON file on disk | Works but no concurrent access safety, no query capabilities. |
| In-memory only | Loses data on restart. Spec requires persistence. |

---

## R6 — Agentic Framework (PydanticAI / Tool-Use Pattern)

### Decision

**No agentic framework for MVP.** Use deterministic intent classification → service routing in the chat orchestrator. Revisit when intent count exceeds ~8–10.

See ADR: [`docs/adr/001-no-agentic-framework-mvp.md`](/docs/adr/001-no-agentic-framework-mvp.md)

### Rationale

1. **Health-safety determinism**: Allergen checking (FR-016, SC-007: 0% conflict rate) must be a guaranteed pipeline step, not a tool the LLM might choose to invoke. In a tool-use pattern, the model decides which tools to call — if it skips `check_allergen`, that's a safety failure. Deterministic orchestration makes allergen checking unconditional.
2. **Eval reproducibility**: The eval dataset (US4) scores outputs against expected answers. Agentic tool routing introduces stochastic tool-call sequences, making eval scoring unreliable and regressions harder to attribute to specific code.
3. **Simplicity (Constitution §II)**: The MVP has exactly 5 intents (step navigation, scaling, substitution, recipe load, off-topic). A simple orchestrator (~50 LOC) suffices. An agentic framework adds a dependency, tool registration, and an abstraction layer for a problem that doesn't yet need it.

### When to Revisit

- Intent count grows past ~8–10 (e.g., technique swaps, timer management, multi-recipe coordination, meal planning)
- Multi-step interactions emerge (tool A's output feeds tool B)
- Adding a new tool becomes harder than registering a PydanticAI tool function

### Migration Path

The `typing.Protocol` LLM interface and per-service architecture mean migrating to PydanticAI later is a refactor of the orchestrator layer only — existing services (`quantity_scaler`, `substitution_service`, etc.) become PydanticAI tool functions without rewriting their internals.

### Alternatives Considered

| Alternative | Verdict |
|-------------|---------|
| PydanticAI | Best future candidate — Pydantic-native, async, lightweight. Revisit post-MVP when intent count grows. |
| LangChain agents | Heavy, opinionated, large dependency tree. Not warranted even post-MVP when PydanticAI exists. |
| Custom tool-use (function calling) | Lighter than a framework but still delegates routing to the LLM — same safety concern as PydanticAI for MVP. |
| Semantic Kernel | Microsoft ecosystem; adds C#-style abstractions that don't fit a Python-async-first project. |
