import os
import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.agent_loop import run_autonomous_kokai_loop
from memory.store import save_memory

# =========================
# AUTOMATION TASK
# =========================

async def trigger_daily_marathon_pipeline():
    print("[AUTOMATION CRON]: KOKAI_AI Scheduled Runner Triggered.")
    pass

# =========================
# FASTAPI LIFESPAN
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        trigger_daily_marathon_pipeline,
        trigger=CronTrigger(
            hour=21,
            minute=0,
            second=0,
            timezone="Asia/Manila"
        )
    )

    scheduler.start()

    yield

    scheduler.shutdown()

# =========================
# FASTAPI INIT
# =========================

app = FastAPI(
    title="KOKAI_AI",
    lifespan=lifespan
)

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================
# RATE LIMIT
# =========================

RATE_LIMIT_STORE = {}
MAX_REQUESTS_PER_MINUTE = 15

@app.middleware("http")
async def secure_gateway_middleware(request: Request, call_next):

    # Skip static/ui routes
    if request.url.path.startswith("/ui") or request.url.path.startswith("/static"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown_ip"

    current_time = time.time()

    if client_ip not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[client_ip] = []

    # Clean old timestamps
    RATE_LIMIT_STORE[client_ip] = [
        t for t in RATE_LIMIT_STORE[client_ip]
        if current_time - t < 60
    ]

    # Check rate limit
    if len(RATE_LIMIT_STORE[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="[SECURITY ALERT]: Rate limit active."
        )

    RATE_LIMIT_STORE[client_ip].append(current_time)

    return await call_next(request)

# =========================
# REQUEST MODEL
# =========================

class RequestBody(BaseModel):
    prompt: str

# =========================
# ROOT ENDPOINT
# =========================

@app.get("/")
async def root():
    return {
        "status": "KOKAI_AI ONLINE",
        "message": "Render deployment successful"
    }

# =========================
# CHAT ENDPOINT
# =========================

@app.post("/chat")
async def chat(body: RequestBody):

    autonomous_response = await run_autonomous_kokai_loop(body.prompt)

    save_memory(
        body.prompt + " | Response: " + autonomous_response[:100]
    )

    return {
        "response": autonomous_response
    }

# =========================
# STATIC UI
# =========================

app.mount(
    "/ui",
    StaticFiles(directory="static", html=True),
    name="static"
)
