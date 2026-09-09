import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print("\n=== CareerCraft AI — Groq Chat Test ===\n")

if not api_key:
    print("GROQ_API_KEY was NOT found.")
    raise SystemExit(1)

print("GROQ_API_KEY: Found")
print("Key length:", len(api_key))

try:
    client = Groq(
        api_key=api_key,
        timeout=60.0,
        max_retries=2
    )

    print("\nTesting openai/gpt-oss-120b...\n")

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: CareerCraft Groq is working."
            }
        ],
        temperature=0,
        max_tokens=30
    )

    reply = response.choices[0].message.content

    print("Chat completion: OK")
    print("AI reply:", reply)
    print("\nRESULT: GROQ CHAT IS WORKING CORRECTLY.")

except Exception as e:
    print("\nRESULT: GROQ CHAT TEST FAILED")
    print("Error type:", type(e).__name__)
    print("Error:", repr(e))
    print("\nDo NOT paste your GROQ API key here.")