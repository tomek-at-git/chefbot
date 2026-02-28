<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 (template) → 1.0.0
  Bump rationale: MAJOR — initial adoption of all principles and
  governance rules; first concrete version of the constitution.

  Modified principles:
    - [PRINCIPLE_1] → I. Test-First (NEW)
    - [PRINCIPLE_2] → II. Simplicity (NEW)
    - [PRINCIPLE_3] → III. Small Increments (NEW)
    - [PRINCIPLE_4] → IV. Quality Gates (NEW)
    - [PRINCIPLE_5] → V. Conversational UX First (NEW)
    - [PRINCIPLE_6] → VI. Learning-Driven Development (NEW)
    - [PRINCIPLE_7] → VII. Observability (NEW)

  Added sections:
    - Technology & Architecture Constraints
    - Development Workflow

  Removed sections: (none — template placeholders replaced)

  Templates requiring updates:
    - .specify/templates/plan-template.md          ✅ compatible (no changes needed)
    - .specify/templates/spec-template.md           ✅ compatible (no changes needed)
    - .specify/templates/tasks-template.md          ✅ compatible (no changes needed)
    - .specify/templates/checklist-template.md      ✅ compatible (no changes needed)

  Follow-up TODOs: none
-->

# ChefBot Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

- Every feature MUST follow the Red-Green-Refactor cycle:
  tests written → tests fail → implement → tests pass → refactor.
- No production code may be written without a corresponding
  failing test already in place.
- Test types by scope: unit tests for pure logic, integration
  tests for service boundaries, contract tests for API surfaces.
- Test coverage MUST NOT decrease with any change.

**Rationale**: Tests are the executable specification of ChefBot.
Writing them first forces clear thinking about behaviour before
implementation and prevents regressions in a rapidly evolving
codebase.

### II. Simplicity

- Start with the simplest solution that satisfies the current
  requirements. YAGNI (You Aren't Gonna Need It) applies.
- Every abstraction, dependency, or layer MUST justify its
  existence against a concrete, present-day need.
- Prefer standard-library or well-known solutions over custom
  implementations.
- If a feature can be delivered with fewer moving parts, it MUST
  be.

**Rationale**: ChefBot is a greenfield project built by a small
team. Premature complexity slows delivery and increases the
surface area for bugs.

### III. Small Increments

- Work MUST be decomposed into small, independently deliverable
  slices that can each be merged, tested, and (where applicable)
  demonstrated.
- A single increment SHOULD touch no more than one logical
  concern (one model, one endpoint, one UI screen, etc.).
- Pull requests MUST be small enough to review in a single
  sitting (target < 400 lines of diff).
- Each increment MUST leave the main branch in a deployable
  state.

**Rationale**: Small increments reduce integration risk, provide
frequent feedback points, and make it easy to identify which
change introduced a problem.

### IV. Quality Gates

- Pre-commit hooks MUST enforce linting, formatting, and type
  checking before any commit reaches the repository.
- CI MUST run the full test suite on every push and block merging
  on failure.
- Code formatting and style MUST be automated (no manual style
  debates).
- Dependency updates MUST pass the full gate before merging.

**Rationale**: Automated quality gates catch issues at the
earliest possible moment, keep the codebase consistently
formatted, and free developers from repetitive manual checks.

### V. Conversational UX First

- The primary user interface is a hands-free, voice-friendly
  chat experience for people actively cooking.
- Responses MUST be concise, actionable, and context-aware
  (remembering the current recipe and step).
- The system MUST gracefully handle ambiguous or incomplete
  user queries by asking short clarifying questions rather than
  failing silently.
- Latency for a conversational reply SHOULD stay below 2 seconds
  to maintain a natural dialogue flow.

**Rationale**: ChefBot's core value proposition is helping cooks
who have their hands occupied. Every design decision MUST be
evaluated through the lens of "Can a user interact with this
while cooking?"

### VI. Learning-Driven Development

- New tools, frameworks, or techniques MUST be evaluated via
  small, time-boxed spikes before committing to them in
  production code.
- Learnings and decisions MUST be documented (ADRs, spike
  summaries, or inline comments) so future contributors
  understand *why* a choice was made.
- Failure of a spike is a valid and valuable outcome — document
  what was learned and move on.

**Rationale**: The project is a learning vehicle as much as a
product. Capturing knowledge prevents repeated exploration of
dead ends and builds a durable decision log.

### VII. Observability

- All backend services MUST emit structured logs (JSON) with
  request correlation IDs.
- Errors MUST be logged with sufficient context to reproduce
  the issue (input, stack trace, user session ID).
- Health-check endpoints MUST be exposed for every deployed
  service.
- Key metrics (response latency, LLM token usage, error rate)
  MUST be tracked from day one, even if only via logs initially.

**Rationale**: A conversational AI system can fail in subtle
ways (hallucinated answers, slow responses). Without
observability, these failures are invisible until users
complain.

## Technology & Architecture Constraints

- **Backend**: Python 3.12+ with FastAPI. Async-first where I/O
  is involved.
- **Mobile client**: Technology to be determined via a spike
  (candidates: React Native, Flutter, or native Swift/Kotlin).
  Decision MUST be documented as an ADR before implementation
  begins.
- **LLM integration**: Abstracted behind a provider interface so
  the underlying model (OpenAI, Anthropic, local, etc.) can be
  swapped without changing application code.
- **Data storage**: Start with SQLite for local development;
  PostgreSQL for production. ORM usage is permitted but raw SQL
  MUST remain an option for performance-critical queries.
- **Dependency management**: Use `uv` for Python packaging.
  Lock files MUST be committed.
- **Containerisation**: Dockerfiles MUST be provided for every
  deployable service. Local development MAY run outside
  containers for speed.

## Development Workflow

- **Branching**: Trunk-based development. Short-lived feature
  branches (`<issue-number>-<slug>`) merged via pull request.
- **Commit messages**: Follow Conventional Commits
  (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`).
- **Pre-commit hooks**: Enforced via `pre-commit` framework.
  Hooks MUST include at minimum: formatter (ruff format), linter
  (ruff check), type checker (mypy or pyright), and test runner
  (pytest — fast unit tests only).
- **Code review**: Every PR MUST be reviewed against the
  constitution principles before merge. A constitution
  compliance note is encouraged in PR descriptions.
- **CI pipeline**: GitHub Actions. Stages: lint → type-check →
  test → build. All stages MUST pass for merge.

## Governance

- This constitution supersedes all other development practices.
  When in conflict, the constitution wins.
- **Amendments**: Any principle may be added, removed, or
  modified. Each amendment MUST include:
  1. A rationale explaining why the change is needed.
  2. An updated version number following SemVer (MAJOR for
     removals/redefinitions, MINOR for additions, PATCH for
     clarifications).
  3. A review of dependent templates and docs for consistency.
- **Compliance**: All PRs and code reviews MUST verify adherence
  to these principles. Violations MUST be flagged and resolved
  before merge.
- **Complexity justification**: Any deviation from the Simplicity
  principle MUST be documented in the PR with a concrete
  justification.

**Version**: 1.0.0 | **Ratified**: 2026-02-28 | **Last Amended**: 2026-02-28
