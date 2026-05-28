import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free"
]

def ask_openrouter(prompt):

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kokai-ai.onrender.com",
        "X-Title": "KOKAI_AI"
    }

    last_error = ""

    for model in MODELS:

        try:

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=60
            )

            data = response.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

            last_error = str(data)

        except Exception as e:
            last_error = str(e)

    return f"KOKAI_AI Gateway Failure\n\n{last_error}"
