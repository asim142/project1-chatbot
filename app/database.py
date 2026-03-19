import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create pgvector extension and chunks table if not exists."""
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create chunks table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id          TEXT PRIMARY KEY,
                filename    TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text  TEXT NOT NULL,
                embedding   vector(768),
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # Create index for fast similarity search
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON document_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """))

        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()