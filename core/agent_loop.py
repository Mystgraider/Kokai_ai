import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """
You are KOKAI_AI.

An advanced autonomous AI system with:
- Deep reasoning
- Coding support
- Security intelligence
- Research capabilities
- Autonomous analysis
- Professional AI assistance
"""

MODELS = [

    "google/gemini-2.0-flash-exp:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-32b:free",

]

async def run_autonomous_kokai_loop(prompt: str):

    last_error = None

    for model in MODELS:

        try:

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://kokai-ai.onrender.com",
                    "X-Title": "KOKAI_AI"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=90
            )

            print("MODEL:", model)
            print("STATUS:", response.status_code)
            print("RAW:", response.text)

            data = response.json()

            if "choices" in data:

                content = data["choices"][0]["message"]["content"]

                if content:

                    return f"""
[KOKAI_AI ACTIVE MODEL]
{model}

{content}
"""

            if "error" in data:

                last_error = f"{model} -> {data['error']}"

                continue

        except Exception as e:

            last_error = f"{model} -> {str(e)}"

            continue

    return f"""
KOKAI_AI Multi-Model Gateway Failure.

Last Error:
{last_error}
"""
