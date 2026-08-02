from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.chains import chat_stream
from app.config import get_settings
from app.database import create_database, seed_database
from app.schema import load_schema

app = FastAPI(title="AI SQL Assistant", version="1.0.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict] = Field(default_factory=list)


@app.on_event("startup")
def _startup() -> None:
    create_database()


@app.get("/")
def root() -> dict:
    return {"name": "AI SQL Assistant", "status": "ok"}


@app.get("/api/config")
def config() -> dict:
    tables = [{"name": t.name, "columns": [{"name": c.name, "type": c.type} for c in t.columns]} for t in load_schema()]
    return {
        "provider": settings.llm_provider,
        "ollama": {
            "model": settings.ollama_model,
            "base_url": settings.ollama_base_url,
        },
        "nvidia": {
            "model": settings.nvidia_model,
            "configured": bool(settings.nvidia_api_key),
        },
        "gemini": {
            "model": settings.gemini_model,
            "configured": bool(settings.gemini_api_key),
        },
        "tables": tables,
    }


@app.post("/api/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        chat_stream(req.message, req.history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/reset")
def reset() -> JSONResponse:
    seed_database(settings.db_path)
    return JSONResponse({"status": "ok", "message": "Base de données réinitialisée."})
