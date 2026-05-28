@app.post("/chat")
async def chat(body: RequestBody):

    import os
    import requests

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    MODELS = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free"
    ]

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
                            "content": body.prompt
                        }
                    ]
                },
                timeout=60
            )

            data = response.json()

            if "choices" in data:

                ai_response = data["choices"][0]["message"]["content"]

                return {
                    "response": ai_response
                }

            last_error = str(data)

        except Exception as e:
            last_error = str(e)

    return {
        "response": f"KOKAI_AI Gateway Failure\n\n{last_error}"
    }
