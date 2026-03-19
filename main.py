import os
import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.chat import get_response, stream_response
from app.memory import get_history, clear_session
from app.vectorstore import upload_document
from app.database import init_db
from app.models import (
    ChatRequest, ChatResponse,
    UploadResponse, SessionInfo, ClearResponse
)
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on startup — creates tables if not exist
    init_db()
    yield


app = FastAPI(
    title="Project 1 — RAG Chatbot",
    description=(
        "Local RAG chatbot · Ollama + PostgreSQL/pgvector + Redis\n\n"
        "1. Upload a PDF via /upload\n"
        "2. Chat via /chat\n"
        "3. View history via /session/{id}\n"
        "4. Clear memory via DELETE /session/{id}"
    ),
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "RAG Chatbot",
        "status":  "running",
        "docs":    "http://localhost:8000/docs"
    }


@app.delete("/documents")
def clear_documents():
    from app.database import engine
    from sqlalchemy import text as sql_text
    with engine.connect() as conn:
        conn.execute(sql_text("DELETE FROM document_chunks"))
        conn.commit()
    return {"message": "All documents cleared"}


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    allowed = {".pdf", ".txt"}
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Only {allowed} files supported")

    content = await file.read()
    if not content:
        raise HTTPException(400, "File is empty")

    chunks_stored = upload_document(content, file.filename)
    if chunks_stored == 0:
        raise HTTPException(422, "Could not extract text from file")

    return UploadResponse(
        filename=file.filename,
        chunks_stored=chunks_stored,
        message=f"Indexed {chunks_stored} chunks into PostgreSQL. Now use /chat"
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    if not req.session_id.strip():
        raise HTTPException(400, "session_id cannot be empty")

    result = get_response(req.session_id, req.message)

    return ChatResponse(
        session_id=req.session_id,
        message=req.message,
        response=result["response"],
        sources=result["sources"],
        turn_count=result["turn_count"]
    )


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    if not req.session_id.strip():
        raise HTTPException(400, "session_id cannot be empty")

    def generate():
        for token, sources in stream_response(req.session_id, req.message):
            if token is not None:
                yield f"data: {json.dumps({'token': token})}\n\n"
            else:
                yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/session/{session_id}", response_model=SessionInfo)
def get_session(session_id: str):
    history = get_history(session_id)
    return SessionInfo(
        session_id=session_id,
        turn_count=len(history) // 2,
        history=history
    )


@app.delete("/session/{session_id}", response_model=ClearResponse)
def clear(session_id: str):
    success = clear_session(session_id)
    return ClearResponse(
        session_id=session_id,
        cleared=success,
        message="Session cleared" if success else "Failed"
    )


@app.get("/health")
def health():
    return {
        "status":      "ok",
        "chat_model":  os.getenv("OLLAMA_MODEL"),
        "embed_model": os.getenv("OLLAMA_EMBED_MODEL"),
        "database":    "postgresql + pgvector",
        "cache":       "redis"
    }