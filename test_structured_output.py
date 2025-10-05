import json
from pydantic import BaseModel
from pathlib import Path
import ollama

RECIPES = Path("recipes_md")
MODEL = "qwen3:4b"


class Recipe(BaseModel):
    title: str
    ingredients: list[str]
    steps: list[str]


class Ingredient(BaseModel):
    ingredient_name: str
    amount: str
    unit: str


with open(RECIPES / "coleslaw_chefkoch.md", "r", encoding="utf-8") as f:
    recipe_text = f.read()

prompt = f"""
Extract the recipe from the following markdown and return it strictly as JSON
that matches this schema:

{{
  "title": "string",
  "ingredients": ["string", "string", ...],
  "steps": ["string", "string", ...]
}}

Markdown recipe:
{recipe_text}
"""

prompt = f"""
Analyse the amount of sugar from the following markdown.

Return it strictly as JSON that matches this schema:

{{
  "ingredient_name": "string",
  "amount": "string"
  "unit": "string"
}}

Markdown recipe:
{recipe_text}
"""

# Use ollama.generate for single-shot structured output
response = ollama.generate(
    model=MODEL,  # or any other small model you installed
    prompt=prompt,
    format="json",  # tell Ollama we expect JSON
)

# Ollama returns a dict with 'response' containing the text
raw_json = response["response"]

print(raw_json)

# Parse and validate with Pydantic
# output = Ingredient.model_validate_json(raw_json)
#
# print(output)
