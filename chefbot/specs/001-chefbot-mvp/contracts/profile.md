# API Contract: Profile Endpoint

**Base URL**: `/api/v1`
**Content-Type**: `application/json`

## GET /profile/{user_id}

Retrieve the user's dietary profile.

### Response — 200 OK

```json
{
  "user_id": "user-001",
  "dietary_constraints": ["tree nut allergy", "lactose intolerance"],
  "dietary_check_enabled": true
}
```

### Response — 404 Not Found

```json
{
  "detail": "No profile found. Complete onboarding to set up your dietary preferences."
}
```

---

## POST /profile

Create a new user profile (during onboarding).

### Request

```json
{
  "user_id": "string (required)",
  "dietary_constraints": ["string"] ,
  "dietary_check_enabled": true
}
```

`dietary_constraints` accepts both predefined values and free-text entries.

**Predefined allergen list**: `"gluten"`, `"dairy"`, `"tree nut"`, `"peanut"`, `"shellfish"`, `"soy"`, `"egg"`, `"fish"`, `"sesame"`, `"wheat"`

**Predefined dietary preferences**: `"vegan"`, `"vegetarian"`, `"halal"`, `"kosher"`, `"pescatarian"`

### Response — 201 Created

```json
{
  "user_id": "user-001",
  "dietary_constraints": ["tree nut allergy"],
  "dietary_check_enabled": true,
  "message": "Profile created. Your dietary preferences will be checked automatically when loading recipes."
}
```

### Response — 409 Conflict

```json
{
  "detail": "Profile already exists. Use PUT /profile/{user_id} to update."
}
```

---

## PUT /profile/{user_id}

Update the user's dietary constraints.

### Request

```json
{
  "dietary_constraints": ["tree nut allergy", "vegan"]
}
```

### Response — 200 OK

```json
{
  "user_id": "user-001",
  "dietary_constraints": ["tree nut allergy", "vegan"],
  "dietary_check_enabled": true,
  "message": "Profile updated. Changes take effect on next recipe load."
}
```

---

## PATCH /profile/{user_id}/toggle

Toggle automatic dietary checking on or off.

### Request

```json
{
  "dietary_check_enabled": false
}
```

### Response — 200 OK

```json
{
  "user_id": "user-001",
  "dietary_check_enabled": false,
  "message": "Automatic dietary checks disabled. You can still mention allergies during conversation and they will be honoured."
}
```

---

## GET /profile/allergens

Returns the predefined list of allergens and dietary preferences for the onboarding UI.

### Response — 200 OK

```json
{
  "allergens": [
    "gluten", "dairy", "tree nut", "peanut", "shellfish",
    "soy", "egg", "fish", "sesame", "wheat"
  ],
  "dietary_preferences": [
    "vegan", "vegetarian", "halal", "kosher", "pescatarian"
  ]
}
```
