# Research: LLM Provider Abstraction Layer

**Date**: 2026-02-28
**Context**: ChefBot MVP — Python 3.12+ / FastAPI backend
**Relevant requirements**: FR-022 (retry logic), Principle II (Simplicity), Principle VII (Observability), Technology Constraints (provider-swappable interface)

---

## 1. Decision: Recommended Approach

**Use LiteLLM behind a thin application-owned Protocol interface.**

- **LiteLLM** handles provider-specific API differences (OpenAI, Anthropic, Ollama/local, etc.)
- **A project-owned `LLMProvider` Protocol** isolates all application code from LiteLLM, satisfying the constitution's mandate that "the underlying model can be swapped without changing application code"
- **A `ResilientLLMService` wrapper** owns retry logic, observability, and error translation — keeping provider implementations clean

---

## 2. Rationale

### Why LiteLLM + thin Protocol (not pure custom, not LangChain)

| Criterion | Custom from scratch | LiteLLM + Protocol | LangChain |
|---|---|---|---|
| Simplicity (Principle II) | Medium — must write/maintain per-provider clients | **High** — LiteLLM handles provider differences; Protocol is ~20 lines | Low — massive dependency graph, abstractions on abstractions |
| Provider swappability | Manual per provider | **Built-in** — change `model="gpt-4o"` to `model="claude-sonnet-4-20250514"` | Built-in but heavy |
| Async support | Must implement per SDK | **Built-in** (`litellm.acompletion`) | Built-in |
| Token/cost tracking | Must implement per provider | **Built-in** (`response.usage`, `litellm.completion_cost()`) | Built-in but complex |
| Structured output | Must implement per provider | **Pass-through** (`response_format`) | Built-in |
| Dependency weight | None | **~3 MB**, focused | ~50+ MB, 80+ transitive deps |
| Lock-in risk | None | **Low** — our Protocol isolates it; LiteLLM is swappable | High — LangChain idioms pervade app code |

**Key justification per constitution:**
- Principle II (Simplicity): "Prefer standard-library or well-known solutions over custom implementations." LiteLLM is well-known, focused, and does one thing.
- The Protocol layer (~20 lines of code) is justified by a concrete, present-day need: the constitution *explicitly mandates* provider swappability.
- LangChain violates "every abstraction MUST justify its existence" — ChefBot doesn't need chains, agents, vector stores, or memory abstractions in the MVP.

---

## 3. Alternatives Considered

### A. Pure custom abstraction (no library)

Write `OpenAIProvider`, `AnthropicProvider`, etc. directly using each SDK's async client.

- **Pro**: Zero external dependency beyond the SDKs themselves; full control.
- **Con**: Must handle each provider's API shape, auth, error types, streaming format, token counting, and cost calculation independently. This is significant ongoing maintenance for a small team.
- **Con**: Violates Simplicity — reimplements what LiteLLM already does well.
- **Verdict**: Rejected. The effort is not justified by a concrete need. LiteLLM already exists and is battle-tested.

### B. LangChain / LangChain Core

Full-featured LLM orchestration framework.

- **Pro**: Rich ecosystem — prompt templates, output parsers, chains, callbacks, tracing.
- **Con**: Massive dependency tree (~80+ transitive packages). Frequent breaking changes between versions. Abstractions are designed for complex agent workflows, not a focused chat-with-recipe use case.
- **Con**: Directly violates Principle II: "If a feature can be delivered with fewer moving parts, it MUST be."
- **Verdict**: Rejected. Over-engineered for ChefBot's needs.

### C. LiteLLM used directly (no Protocol wrapper)

Call `litellm.acompletion()` throughout the application code.

- **Pro**: Simplest possible approach — zero abstraction overhead.
- **Con**: Couples all application code to LiteLLM's API signature. If LiteLLM introduces breaking changes or we want to replace it, every call site must change.
- **Con**: Doesn't satisfy the constitution's mandate: "Abstracted behind a provider interface."
- **Verdict**: Rejected. The Protocol wrapper is a justified abstraction given the explicit architectural constraint.

### D. Instructor library (for structured output only)

Patches LLM clients to return Pydantic models directly. Could be used alongside LiteLLM.

- **Pro**: Elegant structured output — `client.chat.completions.create(..., response_model=Recipe)`.
- **Con**: Another dependency. LiteLLM already supports `response_format` pass-through.
- **Verdict**: Deferred. Start with LiteLLM's native `response_format` + Pydantic validation. Adopt Instructor only if structured output handling becomes a pain point.

---

## 4. Key Design Patterns

### 4.1 Protocol-based type contract

Use `typing.Protocol` (not ABC) for the provider interface. This is more Pythonic, supports structural subtyping, and makes testing trivial (any object matching the shape works as a mock).

```python
from typing import Protocol
from dataclasses import dataclass

@dataclass(frozen=True)
class LLMRequest:
    """Provider-agnostic request."""
    messages: list[dict[str, str]]
    model: str
    temperature: float = 0.7
    max_tokens: int = 1024
    response_format: dict | None = None  # for structured output

@dataclass(frozen=True)
class LLMResponse:
    """Provider-agnostic response."""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float

class LLMProvider(Protocol):
    """Contract for any LLM provider implementation."""
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
```

**Why Protocol over ABC**: 
- ABC requires `class MyProvider(LLMProvider)` — inheritance coupling.
- Protocol allows any class with a matching `async def complete(self, request: LLMRequest) -> LLMResponse` to satisfy the type checker, without inheriting anything.
- For testing, `unittest.mock.AsyncMock` or a simple stub class works without inheriting from the base.
- Python 3.12+ has mature Protocol support with full mypy/pyright enforcement.

ABC is better when you have shared implementation in the base class (Template Method pattern). But here, shared logic (retry, logging) belongs in the `ResilientLLMService` wrapper, not in the provider interface itself. Providers should be thin — just call the API.

### 4.2 Retry-once with error translation (FR-022)

Implement as a service wrapper, not inside each provider. This keeps providers focused on API communication and centralizes resilience logic.

```python
class ResilientLLMService:
    """Wraps any LLMProvider with retry, logging, and error translation."""

    def __init__(self, provider: LLMProvider, logger: structlog.BoundLogger):
        self._provider = provider
        self._logger = logger

    async def complete(self, request: LLMRequest, correlation_id: str) -> LLMResponse:
        for attempt in range(2):  # attempt 0 = first try, attempt 1 = retry
            try:
                response = await self._provider.complete(request)
                self._log_success(request, response, correlation_id, attempt)
                return response
            except Exception as exc:
                if attempt == 0:
                    self._logger.warning(
                        "llm_call_failed_retrying",
                        correlation_id=correlation_id,
                        model=request.model,
                        error=str(exc),
                    )
                    continue
                self._logger.error(
                    "llm_call_failed_after_retry",
                    correlation_id=correlation_id,
                    model=request.model,
                    error=str(exc),
                    exc_info=True,
                )
                raise UserFriendlyError(
                    "I'm having trouble thinking right now — please try again in a moment."
                ) from exc

        # Unreachable, but satisfies type checker
        raise UserFriendlyError("Unexpected error")
```

**Why this pattern**:
- FR-022 specifies exactly "retry once silently" — this is a `range(2)` loop, not exponential backoff.
- The first failure is logged at `warning` level (silent to user, visible in logs).
- The second failure is logged at `error` level with full context.
- The `UserFriendlyError` is caught by FastAPI exception handlers and returned as a friendly message.
- Conversation context is preserved because the error doesn't destroy any state — it's handled at the response level.
- No need for `tenacity` or `backoff` libraries — the logic is 2 attempts with no delay. Adding a library would violate Simplicity.

### 4.3 Observability integration (Principle VII)

Every LLM call logs a structured JSON event with:

```python
def _log_success(self, request, response, correlation_id, attempt):
    self._logger.info(
        "llm_call_completed",
        correlation_id=correlation_id,
        model=response.model,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        total_tokens=response.total_tokens,
        latency_ms=response.latency_ms,
        retried=attempt > 0,
    )
```

Use `structlog` for structured JSON logging. It integrates cleanly with Python's standard `logging` and produces JSON output. The correlation ID flows from FastAPI middleware → service → LLM call.

Cost tracking can be derived from token counts + model in log aggregation, or computed inline using LiteLLM's `completion_cost()` and added to the log event.

### 4.4 Structured output parsing

ChefBot needs structured output for recipe parsing (FR-003: title, ingredients, steps). Pattern:

```python
from pydantic import BaseModel

class ParsedRecipe(BaseModel):
    title: str
    default_servings: int
    ingredients: list[Ingredient]
    steps: list[Step]

# In the recipe parsing service:
request = LLMRequest(
    messages=[
        {"role": "system", "content": RECIPE_PARSE_SYSTEM_PROMPT},
        {"role": "user", "content": raw_recipe_text},
    ],
    model=settings.llm_model,
    response_format={"type": "json_object"},
)
response = await self._llm_service.complete(request, correlation_id)
parsed = ParsedRecipe.model_validate_json(response.content)
```

**Key points**:
- Define output schemas as Pydantic models — they serve as documentation, validation, and type safety.
- Use the provider's native JSON mode (`response_format={"type": "json_object"}`) to get reliable JSON.
- Always validate with Pydantic after parsing — don't trust the LLM output blindly.
- If validation fails, this counts as a provider error and triggers the retry-once logic.
- OpenAI's newer "structured outputs" feature (`response_format={"type": "json_schema", "json_schema": ...}`) guarantees schema compliance — use when available; fall back to JSON mode + validation for other providers.

### 4.5 Async patterns for FastAPI

```python
# FastAPI endpoint — fully async
@router.post("/chat")
async def chat(
    body: ChatRequest,
    llm_service: ResilientLLMService = Depends(get_llm_service),
    correlation_id: str = Depends(get_correlation_id),
) -> ChatResponse:
    response = await llm_service.complete(
        LLMRequest(messages=body.messages, model=settings.llm_model),
        correlation_id=correlation_id,
    )
    return ChatResponse(message=response.content)
```

**Key patterns**:
- All LLM calls use `async/await` — never block the event loop with synchronous SDK calls.
- LiteLLM's `acompletion()` is natively async (uses `httpx` under the hood).
- Use FastAPI's `Depends()` for injecting the LLM service — enables easy testing via dependency override.
- Apply `asyncio.timeout()` (Python 3.11+) or `asyncio.wait_for()` for the 2-second / 5-second latency targets.
- Streaming (SSE) is a future consideration for long responses but not needed in MVP — responses should be concise per Principle V.

**Timeout enforcement**:

```python
import asyncio

async def complete(self, request: LLMRequest, correlation_id: str) -> LLMResponse:
    for attempt in range(2):
        try:
            async with asyncio.timeout(4.0):  # leave margin within 5s budget
                response = await self._provider.complete(request)
            ...
```

### 4.6 Prompt template management

Start with the simplest approach that works: **Python functions in a dedicated `prompts/` module**.

```
app/
  prompts/
    __init__.py
    recipe_parsing.py    # RECIPE_PARSE_SYSTEM_PROMPT, format_parse_request()
    conversation.py      # CHAT_SYSTEM_PROMPT, format_chat_context()
    substitution.py      # SUBSTITUTION_SYSTEM_PROMPT
```

```python
# prompts/recipe_parsing.py

SYSTEM_PROMPT = """\
You are a recipe parser. Extract structured data from the recipe below.
Return valid JSON matching this schema: {schema}
..."""

def format_parse_request(raw_text: str, schema: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(schema=schema)},
        {"role": "user", "content": raw_text},
    ]
```

**Why this approach**:
- Prompts are version-controlled alongside code (mandatory per FR-020, SC-009 — prompt changes must be gate-checked).
- Plain Python strings are greppable, debuggable, and require zero additional dependencies.
- Functions encapsulate formatting logic and parameter injection.
- Type-safe: the function signature documents what parameters a prompt needs.
- Easy to test: unit-test the formatting function, integration-test the full LLM call.
- Migrate to Jinja2 only if prompts grow conditionals/loops complex enough to warrant it.

---

## 5. Specific Implementation Recommendations

### 5.1 Project structure

```
app/
  llm/
    __init__.py
    models.py          # LLMRequest, LLMResponse, UserFriendlyError
    protocol.py        # LLMProvider Protocol definition
    providers/
      __init__.py
      litellm_provider.py   # LiteLLMProvider (the one concrete impl)
    service.py         # ResilientLLMService (retry, logging, metrics)
  prompts/
    __init__.py
    recipe_parsing.py
    conversation.py
    substitution.py
```

### 5.2 Dependency injection via FastAPI

```python
# app/dependencies.py
from functools import lru_cache

@lru_cache
def get_llm_provider() -> LLMProvider:
    return LiteLLMProvider(default_model=settings.llm_model)

def get_llm_service(
    provider: LLMProvider = Depends(get_llm_provider),
    logger: BoundLogger = Depends(get_logger),
) -> ResilientLLMService:
    return ResilientLLMService(provider=provider, logger=logger)
```

In tests, override with `app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()`.

### 5.3 Configuration via environment variables

```python
# app/config.py
from pydantic_settings import BaseSettings

class LLMSettings(BaseSettings):
    llm_model: str = "gpt-4o-mini"               # default model
    llm_timeout_seconds: float = 4.0               # per-call timeout
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024

    model_config = {"env_prefix": "CHEFBOT_"}
```

Model swapping is then a config change (`CHEFBOT_LLM_MODEL=claude-sonnet-4-20250514`), not a code change.

### 5.4 LiteLLM provider implementation

```python
# app/llm/providers/litellm_provider.py
import time
import litellm

class LiteLLMProvider:
    """Thin wrapper that adapts litellm to our LLMProvider Protocol."""

    def __init__(self, default_model: str):
        self._default_model = default_model

    async def complete(self, request: LLMRequest) -> LLMResponse:
        start = time.monotonic()
        response = await litellm.acompletion(
            model=request.model or self._default_model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content,
            model=response.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=round(elapsed_ms, 1),
        )
```

This is the **only place** in the codebase that imports `litellm`. If we ever need to replace it, this one file changes. Everything else depends on `LLMProvider` Protocol and `LLMRequest/LLMResponse` data classes.

### 5.5 Correlation ID flow

```python
# app/middleware.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

The correlation ID is threaded through `Depends(get_correlation_id)` → service → LLM call → log events. Every log entry for a single user request shares the same ID.

### 5.6 Token usage and cost tracking

Start with structured log events (Principle VII: "even if only via logs initially"):

```json
{
  "event": "llm_call_completed",
  "correlation_id": "abc-123",
  "model": "gpt-4o-mini",
  "prompt_tokens": 842,
  "completion_tokens": 156,
  "total_tokens": 998,
  "latency_ms": 1423.7,
  "estimated_cost_usd": 0.00032,
  "retried": false,
  "timestamp": "2026-02-28T14:30:00Z"
}
```

Aggregate cost/usage via log analysis tooling. Add a dedicated metrics store (Prometheus counters, database table) only when log-based tracking becomes insufficient — that's a future increment, not an MVP need.

### 5.7 Testing strategy

| Layer | Test type | What's tested |
|---|---|---|
| `LiteLLMProvider` | Integration test (with real API, gated) | Actual LLM calls work end-to-end |
| `ResilientLLMService` | Unit test (with fake provider) | Retry logic, logging, error translation |
| Prompt functions | Unit test | Correct message formatting |
| FastAPI endpoints | Unit test (with mock service) | Request/response handling |
| Pydantic output models | Unit test | Validation of LLM response shapes |

The fake provider for unit tests:

```python
class FakeProvider:
    def __init__(self, responses: list[LLMResponse | Exception]):
        self._responses = iter(responses)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        result = next(self._responses)
        if isinstance(result, Exception):
            raise result
        return result
```

This satisfies the `LLMProvider` Protocol without inheriting from anything.

---

## Summary

| Aspect | Recommendation |
|---|---|
| Library choice | LiteLLM (focused, lightweight, supports all target providers) |
| Interface pattern | `typing.Protocol` — structural subtyping, no inheritance |
| Retry logic | `ResilientLLMService` wrapper, `range(2)` loop, no extra library |
| Structured output | Pydantic models + provider JSON mode + post-validation |
| Async pattern | `litellm.acompletion()` + `asyncio.timeout()` + FastAPI `Depends` |
| Token tracking | Structured log events via `structlog`, cost derived from token counts |
| Prompt management | Python functions in `prompts/` module, plain strings |
| Observability | `structlog` JSON logs with correlation IDs on every LLM call |

**One dependency added** (`litellm`), **one interface defined** (`LLMProvider` Protocol), **one wrapper** for cross-cutting concerns (`ResilientLLMService`). Everything else is standard Python / FastAPI / Pydantic.
