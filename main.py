from ollama import chat
from ollama import ChatResponse
from pathlib import Path

def main():
    recipe = Path('./recipes_md/coleslaw_chefkoch.md').read_text(encoding='utf-8')
    print(recipe)
    print("#" * 50)
    response: ChatResponse = chat(model='qwen2.5:3b', messages=[
  {
    'role': 'system',
    'content': 'Du bist ein Experte der Fragen zu dem folgenden Rezept {recipe} beantwortet.'.format(recipe=recipe),
  },
  {
    'role': 'user',
    'content': 'Wie viel Zucker benötige ich?',
  },
])
    print(response["message"]["content"])


if __name__ == "__main__":
    main()
