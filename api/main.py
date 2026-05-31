import os
import time
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="KOKAI_AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# RATE LIMIT
# =========================
RATE_LIMIT_STORE = {}
MAX_REQUESTS_PER_MINUTE = 20

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    if client_ip not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[client_ip] = []
    RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if current_time - t < 60]
    if len(RATE_LIMIT_STORE[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        return JSONResponse(status_code=429, content={"error": "Rate limit exceeded. Try again later."})
    RATE_LIMIT_STORE[client_ip].append(current_time)
    return await call_next(request)

# =========================
# MODELS
# =========================
class ChatRequest(BaseModel):
    prompt: str

class ScriptRequest(BaseModel):
    topic: str
    mode: str = "normal"       # normal | horror | news | educational
    language: str = "filipino" # filipino | english | both
    duration: int = 60         # seconds: 60 | 120 | 180

class ReportRequest(BaseModel):
    report_type: str
    case_title: str
    prepared_by: str
    station: Optional[str] = ""
    location: Optional[str] = ""
    incident_date: Optional[str] = ""
    incident_time: Optional[str] = ""
    details: str

# =========================
# HELPERS
# =========================
OPENROUTER_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-4-maverick:free",
    "meta-llama/llama-4-scout:free",
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-v3-base:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

def call_openrouter(prompt: str, system: str = "") -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "ERROR: OPENROUTER_API_KEY not set"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://kokai-ai.onrender.com",
        "X-Title": "KOKAI_AI"
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error = ""
    for model in OPENROUTER_MODELS:
        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={"model": model, "messages": messages},
                timeout=90
            )
            data = res.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            last_error = str(data)
        except Exception as e:
            last_error = str(e)
    return f"ERROR: {last_error}"

# =========================
# ROUTES
# =========================
@app.get("/")
async def root():
    return {"status": "KOKAI_AI ONLINE", "version": "3.0.0", "message": "Render deployment successful"}

@app.post("/chat")
async def chat(body: ChatRequest):
    result = call_openrouter(body.prompt)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=502, content={"error": result})
    return {"response": result}

@app.post("/generate-script")
async def generate_script(body: ScriptRequest):
    scenes_count = max(4, min(10, body.duration // 15))

    lang_instruction = {
        "filipino": "Isulat lahat sa Filipino/Tagalog.",
        "english": "Write everything in English.",
        "both": "Write narration in Filipino but image prompts in English."
    }.get(body.language, "Write in Filipino.")

    mode_instructions = {
        "horror": f"""You are a Filipino horror storyteller. Create a terrifying, atmospheric horror story.
            Use Filipino horror elements: aswang, multo, manananggal, tiyanak, kapre, white lady.
            Make it genuinely scary with vivid descriptions. {lang_instruction}
            Image prompts must be dark, cinematic horror: 'dark horror photography, supernatural creature, eerie lighting, fog, Filipino horror, 8k cinematic'""",

        "normal": f"""You are a creative Filipino storyteller. Create an engaging, interesting story or topic.
            Keep it entertaining and informative. {lang_instruction}
            Image prompts must be beautiful, cinematic, professional photography.""",

        "news": f"""You are a professional Filipino news anchor. Create a factual, professional news report style video.
            Use formal language. {lang_instruction}
            Image prompts must be photojournalistic, realistic, professional.""",

        "educational": f"""You are a Filipino educational content creator. Create an informative, easy to understand educational video.
            Use simple language. {lang_instruction}
            Image prompts must be clear, informative, illustrated style.""",
    }.get(body.mode, "Create an engaging story.")

    prompt = f"""{mode_instructions}

Topic: {body.topic}
Number of scenes: {scenes_count}
Total duration: {body.duration} seconds (about {body.duration // scenes_count} seconds per scene)

Return ONLY valid JSON in this exact format, no markdown, no extra text:
{{
  "title": "Video title here",
  "intro": "Opening hook sentence (1-2 sentences)",
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "What the narrator says for this scene (2-4 sentences)",
      "image_prompt": "Detailed English image generation prompt for this scene",
      "duration": {body.duration // scenes_count}
    }}
  ],
  "outro": "Closing sentence"
}}"""

    result = call_openrouter(prompt, system="You are a video script writer. Always return valid JSON only.")

    # Try to parse JSON
    import json, re
    try:
        # Clean up response
        cleaned = result.strip()
        # Remove markdown code blocks if present
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        parsed = json.loads(cleaned)
        return {"success": True, "script": parsed, "mode": body.mode, "language": body.language}
    except Exception as e:
        # Return raw if JSON parse fails
        return {"success": False, "raw": result, "error": str(e)}

@app.post("/generate-report-content")
async def generate_report_content(body: ReportRequest):
    prompt = f"""Write a professional {body.report_type} in formal Filipino/English mixed language (like actual PNP report style).

Case Title: {body.case_title}
Prepared By: {body.prepared_by}
Station: {body.station}
Location of Incident: {body.location}
Date: {body.incident_date}
Time: {body.incident_time}
Details/Facts: {body.details}

Write a complete formal report with these sections:
1. EXECUTIVE SUMMARY
2. BACKGROUND / CIRCUMSTANCES
3. FINDINGS / FACTS
4. ANALYSIS
5. RECOMMENDATIONS / ACTION TAKEN

Use formal law enforcement language. Be thorough and professional."""

    result = call_openrouter(prompt)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=502, content={"error": result})
    return {"content": result}
