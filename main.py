from ollama import chat
from ollama import ChatResponse

def main():
    response: ChatResponse = chat(model='qwen2.5:3b', messages=[
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
])
    print(response["message"]["content"])


if __name__ == "__main__":
    main()
