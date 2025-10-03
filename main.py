from ollama import chat
from ollama import ChatResponse
from pathlib import Path

MODEL = "qwen3:4b"


def main():
    recipe = Path("./recipes_md/coleslaw_chefkoch.md").read_text(encoding="utf-8")
    print(recipe)
    print("#" * 50)
    response: ChatResponse = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Du bist ein Experte der Fragen zu dem folgenden Rezept {recipe} beantwortet.".format(
                    recipe=recipe
                ),
            },
            {
                "role": "user",
                "content": "Wie viel Zucker benötige ich?",
            },
        ],
    )
    print(response["message"]["content"])


if __name__ == "__main__":
    main()
