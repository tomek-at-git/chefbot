# Data Model: ChefBot MVP

**Date**: 2026-02-28 | **Spec**: `specs/001-chefbot-mvp/spec.md`

## Entity Relationship Diagram

```
┌─────────────────┐
│   UserProfile    │
├─────────────────┤        ┌───────────────────────┐
│ user_id (PK)    │        │  ConversationContext   │
│ constraints[]   │        ├───────────────────────┤
│ check_enabled   │◄───────│ user_id (FK)          │
└─────────────────┘        │ loaded_recipe         │──────┐
                           │ current_step_index    │      │
                           │ requested_servings    │      │
                           │ stated_allergies[]    │      │
                           └───────────────────────┘      │
                                                          │
                           ┌───────────────────────┐      │
                           │       Recipe          │◄─────┘
                           ├───────────────────────┤
                           │ title                 │
                           │ default_servings      │
                           │ source                │
                           │ source_type           │
                           │ ingredients[]         │──────┐
                           │ steps[]               │───┐  │
                           └───────────────────────┘   │  │
                                                       │  │
                           ┌──────────────────┐        │  │
                           │      Step        │◄───────┘  │
                           ├──────────────────┤           │
                           │ step_number      │           │
                           │ instruction_text │           │
                           └──────────────────┘           │
                                                          │
                           ┌──────────────────┐           │
                           │   Ingredient     │◄──────────┘
                           ├──────────────────┤
                           │ name             │
                           │ quantity         │
                           │ unit             │
                           └──────────────────┘

┌───────────────────────────┐
│   EvaluationDataset       │  (file-based, not DB)
├───────────────────────────┤
│ version                   │
│ category                  │
│ cases[]                   │
│   ├── id                  │
│   ├── description         │
│   ├── tags[]              │
│   ├── input {}            │
│   ├── expected {}         │
│   └── scoring             │
└───────────────────────────┘
```

## Entities

### Recipe

Represents a parsed dish loaded into the conversation.

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `title` | `str` | Yes | Non-empty, max 200 chars | Extracted from source |
| `default_servings` | `int` | Yes | ≥ 1 | Original serving count |
| `source` | `str` | Yes | Non-empty | Original text or URL |
| `source_type` | `Literal["text", "url"]` | Yes | Enum | How the recipe was loaded |
| `ingredients` | `list[Ingredient]` | Yes | ≥ 1 item | Ordered list |
| `steps` | `list[Step]` | Yes | ≥ 1 item | Ordered by step_number |

**Validation rules**:
- Must have at least one ingredient and one step to be considered a valid recipe.
- `title` is required — if LLM extraction cannot determine a title, it defaults to "Untitled Recipe".
- `default_servings` defaults to 1 if not determinable from source.

**State transitions**: None — Recipe is immutable once parsed. A new recipe replaces the old one.

---

### Ingredient

A single item used in a recipe.

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `name` | `str` | Yes | Non-empty, max 100 chars | Normalised to lowercase |
| `quantity` | `float \| None` | No | ≥ 0 if present | `None` for "to taste" items |
| `unit` | `str \| None` | No | Max 30 chars | `None` for unitless (e.g., "2 eggs") |

**Validation rules**:
- `name` is always required.
- `quantity` may be `None` for items specified as "to taste", "a pinch", etc.
- `unit` may be `None` for countable items (eggs, cloves, etc.).
- Quantities are stored as `float` to handle fractions (½ = 0.5).

---

### Step

An ordered instruction within a recipe.

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `step_number` | `int` | Yes | ≥ 1, sequential | 1-indexed |
| `instruction_text` | `str` | Yes | Non-empty | Full instruction text |

**Validation rules**:
- Steps must be sequentially numbered starting at 1.
- `instruction_text` is the full text — no truncation.

---

### ConversationContext

Runtime state of a user's active session. In-memory only (not persisted).

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `user_id` | `str` | Yes | Non-empty | Links to UserProfile |
| `loaded_recipe` | `Recipe \| None` | No | — | `None` if no recipe loaded |
| `current_step_index` | `int` | No | 0-indexed, within recipe bounds | `None` if no recipe loaded |
| `requested_servings` | `int \| None` | No | ≥ 1 if present | `None` = use default_servings |
| `stated_allergies` | `list[str]` | Yes | Defaults to `[]` | Allergies mentioned in conversation |

**Validation rules**:
- `current_step_index` must be within `[0, len(recipe.steps) - 1]` when a recipe is loaded.
- `stated_allergies` accumulates during conversation — never cleared unless recipe is replaced.
- `requested_servings` is set when the user asks for a different serving count.

**State transitions**:

```
No Recipe → Recipe Loaded (via load action)
Recipe Loaded → Navigating (via step question)
Navigating → Navigating (step forward/back/jump)
Recipe Loaded → Recipe Loaded (new recipe replaces old)
Any State → No Recipe (conversation ends)
```

---

### UserProfile

Persistent user preferences stored in SQLite.

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `user_id` | `str` | Yes | PK, non-empty | Unique identifier |
| `dietary_constraints` | `list[str]` | Yes | Defaults to `[]` | Allergies, intolerances, preferences |
| `dietary_check_enabled` | `bool` | Yes | Default `True` | Toggle for automatic checking |

**Validation rules**:
- `dietary_constraints` items are normalised to lowercase.
- `dietary_check_enabled` defaults to `True` on creation.
- Empty `dietary_constraints` with `check_enabled=True` is valid (no-op on check).

**State transitions**:

```
Not Exists → Created (during onboarding or first settings visit)
Created → Updated (add/remove constraints, toggle checking)
```

**Persistence**: SQLite table `user_profiles`:

```sql
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    dietary_constraints TEXT NOT NULL DEFAULT '[]',  -- JSON array
    dietary_check_enabled INTEGER NOT NULL DEFAULT 1  -- boolean
);
```

---

### EvaluationDataset (File-Based)

Not a database entity — versioned JSON files in `evals/datasets/`.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `version` | `str` | Yes | SemVer (e.g., "1.0.0") |
| `category` | `Literal["scaling", "substitution"]` | Yes | Dataset type |
| `created` | `str` | Yes | ISO date |
| `baseline_report` | `str \| None` | No | Path to last accepted baseline |
| `cases` | `list[ScalingCase \| SubstitutionCase]` | Yes | ≥ 50 items |

See [research.md](research.md) §R3 for full JSON schema of test cases.

---

## Cross-Entity Relationships

| Relationship | Type | Notes |
|--------------|------|-------|
| Recipe → Ingredient | 1:N (composition) | Ingredients belong to exactly one recipe |
| Recipe → Step | 1:N (composition) | Steps belong to exactly one recipe |
| ConversationContext → Recipe | 1:0..1 | Context may or may not have a loaded recipe |
| ConversationContext → UserProfile | 1:1 | Context always links to a user profile (even if empty) |
| UserProfile ←→ Recipe load | Checked on load | Profile constraints checked against recipe ingredients (FR-024) |
| UserProfile ←→ Substitution | Checked on suggest | Profile + in-conversation constraints filter suggestions (FR-016) |

## Constraint Merging Logic

When checking for allergen conflicts (on recipe load or substitution), the system merges two sources:

1. **UserProfile.dietary_constraints** — persistent, from onboarding/settings
2. **ConversationContext.stated_allergies** — transient, from current conversation

Merge rule: **union of both sets**, normalised to lowercase. Applied regardless of `dietary_check_enabled` for source (2) per FR-026.

```
effective_constraints = set(profile.dietary_constraints if profile.dietary_check_enabled else [])
                      | set(context.stated_allergies)
```
