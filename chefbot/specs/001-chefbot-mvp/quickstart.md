# Quickstart: ChefBot MVP

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- An LLM API key (OpenAI, Anthropic, or any LiteLLM-supported provider)

## Setup

```bash
# Clone and enter the project
git clone <repo-url>
cd chefbot

# Install dependencies
cd api
uv sync

# Configure environment
cp .env.example .env
# Edit .env and set:
#   LLM_API_KEY=sk-...
#   LLM_MODEL=gpt-4o-mini   (or any LiteLLM-supported model)
```

## Run

```bash
# Start the API server
uv run uvicorn src.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Test

```bash
# Run all tests (unit + integration)
uv run pytest

# Run only unit tests (fast, no LLM calls)
uv run pytest tests/unit/

# Run evaluation suite (requires LLM API key)
uv run pytest ../evals/
```

## Pre-commit Hooks

```bash
# Install pre-commit hooks (one-time)
uv run pre-commit install

# Hooks run automatically on commit:
#   - ruff format (formatter)
#   - ruff check (linter)
#   - pyright (type checker)
#   - pytest tests/unit/ (fast unit tests)
```

## Project Structure

```
api/
├── src/
│   ├── models/       # Pydantic domain models (Recipe, Ingredient, Step, etc.)
│   ├── services/     # Business logic (parser, scaler, substitution, chat orchestrator)
│   ├── routers/      # FastAPI route handlers (chat, recipe, profile)
│   ├── core/         # Cross-cutting (config, logging, LLM provider, errors, prompts)
│   └── main.py       # FastAPI application entry point
└── tests/
    ├── unit/         # Pure logic tests (no I/O, no LLM)
    ├── integration/  # Service boundary tests (mocked LLM)
    └── contract/     # API surface tests

evals/
├── datasets/         # Versioned JSON test fixtures (scaling, substitutions)
├── baselines/        # Accepted baseline reports
└── ...               # Scorers, reporter, regression checker

docs/
├── adr/              # Architecture Decision Records
└── quickstart.md     # This file
```

## Quick Smoke Test

After starting the server, try loading a recipe:

```bash
curl -X POST http://localhost:8000/api/v1/recipe/load \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "source": "Scrambled Eggs\nServes 2\n\nIngredients:\n- 4 eggs\n- 1 tbsp butter\n- Salt to taste\n\nSteps:\n1. Beat eggs in a bowl.\n2. Melt butter in a pan over medium heat.\n3. Pour in eggs and stir gently.\n4. Season with salt and serve.",
    "source_type": "text"
  }'
```

Then ask a question:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "message": "What comes next after beating the eggs?"
  }'
```

## Key Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_API_KEY` | Yes | — | API key for the LLM provider |
| `LLM_MODEL` | No | `gpt-4o-mini` | Model identifier (LiteLLM format) |
| `LLM_TIMEOUT` | No | `10` | LLM call timeout in seconds |
| `DATABASE_URL` | No | `sqlite:///chefbot.db` | SQLite path (dev) or PostgreSQL URL (prod) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
