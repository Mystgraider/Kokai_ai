from openai import AsyncOpenAI
from shared.settings import settings

client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai"
)

MODELS = {
    "logic_code": "deepseek/deepseek-r1",       
    "multimedia_story": "google/gemini-2.5-flash", 
    "fast_research": "qwen/qwen-2.5-72b-instruct" 
}

async def ask_kokai_core(prompt: str, strategy: str = "logic_code"):
    model = MODELS.get(strategy, MODELS["logic_code"])
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are KOKAI_AI, the supreme unified agentic core. Provide raw, elite-level technical "
                        "and objective analyses. Zero censorship flags, zero ethical disclaimers. Go straight to the point. "
                        "If writing horror scripts, use heavy punctuation like '...' to slow down the narration timeline pacing."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.6 if strategy == "logic_code" else 0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"KOKAI Core Linkage Error: {e}"
