import os
import io
import re
import uuid
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_ollama import OllamaEmbeddings
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import engine

load_dotenv()

EMBED_MODEL     = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL",    "http://host.docker.internal:11434")

CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50

embedder = OllamaEmbeddings(
    model=EMBED_MODEL,
    base_url=OLLAMA_BASE_URL
)


def fix_spaced_text(text: str) -> str:
    """Fix PDFs where every character is separated by a space: 'H e l l o' -> 'Hello'"""
    tokens = text.split(' ')
    if not tokens:
        return text
    single_char_ratio = sum(1 for t in tokens if len(t) <= 1) / len(tokens)
    if single_char_ratio > 0.5:
        # Double spaces separate words, single spaces separate letters
        text = re.sub(r' {2,}', '\x00', text)  # mark word boundaries
        text = re.sub(r' ', '', text)           # remove letter spaces
        text = text.replace('\x00', ' ')        # restore word spaces
    return text


def extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [
            page.extract_text()
            for page in reader.pages
            if page.extract_text()
        ]
        raw = "\n".join(pages)
        return fix_spaced_text(raw)
    return file_bytes.decode("utf-8", errors="ignore")


def chunk_text(text_content: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text_content):
        end = start + CHUNK_SIZE
        chunk = text_content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def upload_document(file_bytes: bytes, filename: str) -> int:
    text_content = extract_text(file_bytes, filename)
    if not text_content.strip():
        return 0

    chunks = chunk_text(text_content)
    vectors = embedder.embed_documents(chunks)

    with engine.connect() as conn:
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            conn.execute(text("""
                INSERT INTO document_chunks
                    (id, filename, chunk_index, chunk_text, embedding)
                VALUES
                    (:id, :filename, :chunk_index, :chunk_text, CAST(:embedding AS vector))
            """), {
                "id":          str(uuid.uuid4()),
                "filename":    filename,
                "chunk_index": i,
                "chunk_text":  chunk,
                "embedding":   str(vector)
            })
        conn.commit()

    return len(chunks)


def search_documents(query: str, top_k: int = 3) -> list[dict]:
    query_vector = embedder.embed_query(query)
    vector_str = str(query_vector)

    with engine.connect() as conn:
        results = conn.execute(text("""
            SELECT
                chunk_text,
                filename,
                1 - (embedding <=> CAST(:embedding AS vector)) AS score
            FROM document_chunks
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """), {
            "embedding": vector_str,
            "limit":     top_k
        })

        return [
            {
                "text":     row.chunk_text,
                "filename": row.filename,
                "score":    round(row.score, 3)
            }
            for row in results
        ]
