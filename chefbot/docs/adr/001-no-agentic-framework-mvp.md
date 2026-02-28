# ADR 001: No Agentic Framework for MVP

**Status**: Accepted
**Date**: 2026-02-28
**Context**: ChefBot MVP (`001-chefbot-mvp`)

## Decision

Use deterministic intent classification and service routing in the chat orchestrator for the MVP. Do not adopt PydanticAI, LangChain agents, or any tool-use / function-calling pattern where the LLM decides which capabilities to invoke.

## Context

ChefBot's chat orchestrator routes user messages to the appropriate service (step navigation, quantity scaling, substitution, recipe loading, off-topic redirect). An agentic tool-use pattern — where the LLM selects from registered tools — was considered as an alternative to manual intent classification.

PydanticAI is the most natural candidate: it is Pydantic-native, async-first, and lightweight — a good fit for the existing stack.

## Reasons Against (for MVP)

### 1. Health-Safety Determinism

Allergen checking (FR-016, SC-007) requires a **0% conflict rate** — no substitution may suggest an ingredient contradicting a stated allergy. In the current design, allergen checking is a hardcoded step in the substitution service pipeline: every substitution request unconditionally passes through the allergen detector.

In a tool-use pattern, the LLM decides which tools to call. If the model skips `check_allergen` on a substitution — even once — that is a health-safety failure. Making a safety-critical step dependent on probabilistic tool selection is an unacceptable risk for the MVP.

### 2. Eval Reproducibility

The evaluation dataset (US4, ≥100 cases) scores system outputs against expected answers. Deterministic orchestration means the same input always follows the same code path, making eval results reproducible and regressions attributable to specific code changes.

Agentic routing can produce different tool-call sequences for the same input across runs, undermining eval stability.

### 3. Simplicity (Constitution §II)

The MVP has exactly 5 intents. A simple orchestrator that classifies intent (via LLM or keyword heuristics) and routes to the correct service is approximately 50 lines of code. An agentic framework adds:
- A new dependency
- A tool registration system
- A tool-call parsing layer
- A new abstraction to understand and debug

This complexity is not justified by the current scope.

## When to Revisit

Adopt PydanticAI tool-use when **any** of these conditions is met:

- **Intent count exceeds ~8–10**: Manual routing becomes a growing if/elif chain. Tool registration is simpler.
- **Multi-step interactions emerge**: A user request requires chaining tool A → tool B (e.g., "substitute butter and recalculate for 2 servings"). The orchestrator would need to become a state machine — at that point, an agent loop is simpler.
- **New capability cost**: Adding a new capability takes more effort than writing a tool function and registering it.

Likely triggers: technique swaps, timer management, multi-recipe coordination, meal planning, image-based input.

## Migration Path

The architecture is designed for this transition:

1. **Per-service design**: Each service (`quantity_scaler`, `substitution_service`, `step_navigator`, etc.) is a standalone module with a clear input/output contract. These become PydanticAI tool functions with no internal rewrite.
2. **Protocol-based LLM interface**: The `typing.Protocol` in `llm_provider.py` is compatible with PydanticAI's model abstraction.
3. **Scope of change**: Only `chat_orchestrator.py` is rewritten. Services, models, routers, and tests remain unchanged.
4. **Safety gate preservation**: Allergen checking can be implemented as a PydanticAI result validator or a mandatory post-tool-call hook, preserving the unconditional safety check.

## Alternatives Considered

| Alternative | Verdict |
|-------------|---------|
| **PydanticAI** | Best future candidate. Pydantic-native, async, lightweight. Not justified for 5 intents with a 0% allergen-conflict hard gate. |
| **LangChain agents** | Heavy, large dependency tree. Not warranted even post-MVP when PydanticAI exists. |
| **Custom function calling** | Lighter than a framework but still delegates routing to the LLM — same safety concern. |
| **Semantic Kernel** | Microsoft ecosystem; adds abstractions misaligned with Python-async-first. |

## Consequences

- **Positive**: Simpler codebase, deterministic safety checks, reproducible evals, fewer dependencies.
- **Negative**: Manual orchestrator needs updating for each new intent. Becomes tedious past ~8 intents.
- **Accepted risk**: If the product rapidly expands capabilities, the orchestrator refactor will be needed sooner. The per-service architecture limits the blast radius of that refactor.
