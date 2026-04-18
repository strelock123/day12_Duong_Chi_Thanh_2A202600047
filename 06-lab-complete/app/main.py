"""
Production AI Agent — Kết hợp tất cả Day 12 concepts
"""
import time
import signal
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

import redis

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_and_record_cost
from app.agent import graph
from langchain_core.messages import HumanMessage, AIMessage

# Logging — JSON structured
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0

r = None
if settings.redis_url:
    r = redis.from_url(settings.redis_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    time.sleep(0.1)  # simulate init
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))
    if r:
        r.close()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers.pop("server", None)
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception as e:
        logger.error(json.dumps({"event": "error", "error": str(e)}))
        raise

class AskRequest(BaseModel):
    user_id: str = Field(..., description="User ID for rate limit, cost guard and history")
    question: str = Field(..., min_length=1, max_length=2000, description="Your question for the agent")

class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    timestamp: str

@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
        },
    }

@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key)
):
    check_rate_limit(body.user_id)
    input_tokens = len(body.question.split()) * 2
    check_and_record_cost(body.user_id, input_tokens, 0)
    
    logger.info(json.dumps({
        "event": "agent_call",
        "user": body.user_id,
        "q_len": len(body.question)
    }))

    # 1. Get history from Redis
    raw_history = []
    if r:
        try:
            cached = r.get(f"history:{body.user_id}")
            if cached:
                raw_history = json.loads(cached)
        except Exception as e:
            logger.error(json.dumps({"event": "redis_error", "error": str(e)}))

    history_msgs = []
    for msg in raw_history:
        if msg.get("type") in ("user", "human"):
            history_msgs.append(HumanMessage(content=msg.get("content")))
        elif msg.get("type") in ("ai", "bot"):
            history_msgs.append(AIMessage(content=msg.get("content")))

    history_msgs.append(HumanMessage(content=body.question))

    # 2. Call LLM agent
    try:
        result = graph.invoke({"messages": history_msgs})
        final_msg = result["messages"][-1].content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    output_tokens = len(final_msg.split()) * 2
    check_and_record_cost(body.user_id, 0, output_tokens)

    # 3. Save back to Redis
    new_raw_history = []
    for msg in result["messages"]:
        if hasattr(msg, "type") and hasattr(msg, "content"):
            if msg.type in ("human", "ai") and msg.content:
                new_raw_history.append({"type": msg.type, "content": msg.content})

    if r:
        try:
            # save last 10 messages to limit size
            r.setex(f"history:{body.user_id}", 3600, json.dumps(new_raw_history[-10:]))
        except Exception as e:
            logger.error(json.dumps({"event": "redis_error", "error": str(e)}))

    return AskResponse(
        question=body.question,
        answer=final_msg,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

@app.get("/health", tags=["Operations"])
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "uptime_seconds": round(time.time() - START_TIME, 1)
    }

@app.get("/ready", tags=["Operations"])
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    if r:
        try:
            r.ping()
        except:
             raise HTTPException(503, "Redis connection failed")
    return {"status": "ready"}

def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)
