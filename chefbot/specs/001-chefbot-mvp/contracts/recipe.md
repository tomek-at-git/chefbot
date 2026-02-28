# API Contract: Recipe Endpoint

**Base URL**: `/api/v1`
**Content-Type**: `application/json`

## POST /recipe/load

Load a recipe into the conversation by providing plain text or a URL.

### Request

```json
{
  "user_id": "string (required)",
  "source": "string (required, max 50000 chars)",
  "source_type": "text | url (required)"
}
```

### Response — 200 OK

```json
{
  "recipe": {
    "title": "string",
    "default_servings": 4,
    "source_type": "text | url",
    "ingredient_count": 12,
    "step_count": 8,
    "ingredients": [
      {
        "name": "string",
        "quantity": 2.0,
        "unit": "cups"
      }
    ],
    "steps": [
      {
        "step_number": 1,
        "instruction_text": "string"
      }
    ]
  },
  "dietary_warnings": [
    {
      "ingredient": "almonds",
      "constraint": "tree nut allergy",
      "message": "⚠️ This recipe contains almonds — you have a tree nut allergy listed in your profile."
    }
  ],
  "confirmation_message": "Loaded \"Teriyaki Chicken\" — 8 steps, serves 4. Ready for questions!"
}
```

### Response — 422 Parse Failure

```json
{
  "detail": "I couldn't parse a recipe from that text. Could you paste just the ingredients and steps?",
  "suggestion": "Try formatting with ingredients listed first, then numbered steps."
}
```

### Response — 422 URL Fetch Failure

```json
{
  "detail": "This page appears to require a login. Try pasting the recipe as plain text instead.",
  "error_type": "paywall | timeout | connection_error | parse_failure | unsupported_format",
  "suggestion": "You can copy the recipe from the page and paste it as text."
}
```

### Example — Text Load

**Request**:
```json
{
  "user_id": "user-001",
  "source": "Teriyaki Chicken\nServes 4\n\nIngredients:\n- 2 chicken breasts\n- 3 tbsp soy sauce\n- 2 tbsp mirin\n- 1 tbsp sugar\n\nSteps:\n1. Slice chicken into strips.\n2. Mix soy sauce, mirin, and sugar.\n3. Cook chicken in a pan for 5 minutes.\n4. Add sauce and stir for 2 minutes.",
  "source_type": "text"
}
```

**Response**:
```json
{
  "recipe": {
    "title": "Teriyaki Chicken",
    "default_servings": 4,
    "source_type": "text",
    "ingredient_count": 4,
    "step_count": 4,
    "ingredients": [
      { "name": "chicken breasts", "quantity": 2.0, "unit": null },
      { "name": "soy sauce", "quantity": 3.0, "unit": "tbsp" },
      { "name": "mirin", "quantity": 2.0, "unit": "tbsp" },
      { "name": "sugar", "quantity": 1.0, "unit": "tbsp" }
    ],
    "steps": [
      { "step_number": 1, "instruction_text": "Slice chicken into strips." },
      { "step_number": 2, "instruction_text": "Mix soy sauce, mirin, and sugar." },
      { "step_number": 3, "instruction_text": "Cook chicken in a pan for 5 minutes." },
      { "step_number": 4, "instruction_text": "Add sauce and stir for 2 minutes." }
    ]
  },
  "dietary_warnings": [],
  "confirmation_message": "Loaded \"Teriyaki Chicken\" — 4 steps, serves 4. Ready for questions!"
}
```

### Example — URL Load with Dietary Warning

**Request**:
```json
{
  "user_id": "user-001",
  "source": "https://www.allrecipes.com/recipe/228293/thai-peanut-noodles/",
  "source_type": "url"
}
```

**Response**:
```json
{
  "recipe": {
    "title": "Thai Peanut Noodles",
    "default_servings": 6,
    "source_type": "url",
    "ingredient_count": 10,
    "step_count": 5,
    "ingredients": ["..."],
    "steps": ["..."]
  },
  "dietary_warnings": [
    {
      "ingredient": "peanut butter",
      "constraint": "peanut allergy",
      "message": "⚠️ This recipe contains peanut butter — you have a peanut allergy listed in your profile."
    }
  ],
  "confirmation_message": "Loaded \"Thai Peanut Noodles\" — 5 steps, serves 6. ⚠️ 1 dietary warning found."
}
```
