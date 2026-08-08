import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("API KEY FOUND:", os.getenv("XAI_API_KEY") is not None)

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

response = client.chat.completions.create(
    model="grok-4-fast-reasoning",
    messages=[
        {
            "role": "user",
            "content": "Say Hello from Grok AI!"
        }
    ]
)

print(response.choices[0].message.content)