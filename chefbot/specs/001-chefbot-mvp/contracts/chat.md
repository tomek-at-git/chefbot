# API Contract: Chat Endpoint

**Base URL**: `/api/v1`
**Content-Type**: `application/json`

## POST /chat

The primary conversational interface. All user interactions go through this endpoint — step navigation, scaling questions, substitution requests, recipe loading.

### Request

```json
{
  "user_id": "string (required)",
  "message": "string (required, max 2000 chars)"
}
```

### Response — 200 OK

```json
{
  "reply": "string",
  "intent": "step_navigation | scaling | substitution | recipe_load | clarification | off_topic | error",
  "context": {
    "has_recipe": true,
    "recipe_title": "string | null",
    "current_step": 3,
    "total_steps": 8,
    "servings": 4
  },
  "warnings": [
    {
      "type": "allergen_conflict | dietary_conflict | safety",
      "message": "string"
    }
  ]
}
```

### Response — 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "string",
      "type": "string"
    }
  ]
}
```

### Response — 503 Service Unavailable

Returned after retry-once logic fails (FR-022).

```json
{
  "reply": "I'm having trouble thinking right now — please try again in a moment.",
  "intent": "error",
  "context": {
    "has_recipe": true,
    "recipe_title": "Teriyaki Chicken",
    "current_step": 3,
    "total_steps": 8,
    "servings": 4
  },
  "warnings": []
}
```

**Note**: Context is preserved even on error (FR-022).

### Example — Step Navigation

**Request**:
```json
{
  "user_id": "user-001",
  "message": "What comes next?"
}
```

**Response**:
```json
{
  "reply": "Step 4: Add the soy sauce and mirin to the pan, then stir for 30 seconds.",
  "intent": "step_navigation",
  "context": {
    "has_recipe": true,
    "recipe_title": "Teriyaki Chicken",
    "current_step": 4,
    "total_steps": 8,
    "servings": 4
  },
  "warnings": []
}
```

### Example — Scaling with Warning

**Request**:
```json
{
  "user_id": "user-001",
  "message": "How much flour for 2 servings?"
}
```

**Response**:
```json
{
  "reply": "For 2 servings, you'll need 1 cup of flour (halved from 2 cups).",
  "intent": "scaling",
  "context": {
    "has_recipe": true,
    "recipe_title": "Chocolate Chip Cookies",
    "current_step": 1,
    "total_steps": 6,
    "servings": 2
  },
  "warnings": []
}
```

### Example — Substitution with Allergen Check

**Request**:
```json
{
  "user_id": "user-001",
  "message": "I'm allergic to nuts. What can I use instead of butter?"
}
```

**Response**:
```json
{
  "reply": "Since you're allergic to nuts, here are butter substitutes: coconut oil (1:1 ratio, slightly tropical flavour), vegetable shortening (1:1 ratio, neutral flavour), or margarine (make sure it's nut-free — always check the label). The texture may be slightly different. Always check labels for allergens.",
  "intent": "substitution",
  "context": {
    "has_recipe": true,
    "recipe_title": "Chocolate Chip Cookies",
    "current_step": 1,
    "total_steps": 6,
    "servings": 4
  },
  "warnings": [
    {
      "type": "allergen_conflict",
      "message": "Nut allergy noted. All suggestions have been filtered to exclude nut-containing alternatives."
    }
  ]
}
```
