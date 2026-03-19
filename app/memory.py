import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

MEMORY_KEY = "chat:history:{session_id}"
MAX_TURNS = 10


def get_history(session_id: str) -> list[dict]:
    key = MEMORY_KEY.format(session_id=session_id)
    try:
        data = r.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return []


def save_history(session_id: str, history: list[dict]):
    key = MEMORY_KEY.format(session_id=session_id)
    # Keep only last MAX_TURNS exchanges to avoid huge prompts
    if len(history) > MAX_TURNS * 2:
        history = history[-(MAX_TURNS * 2):]
    try:
        # Expires after 24 hours automatically
        r.setex(key, 86400, json.dumps(history))
    except Exception:
        pass


def add_turn(session_id: str, human: str, ai: str):
    history = get_history(session_id)
    history.append({"role": "human", "content": human})
    history.append({"role": "ai",    "content": ai})
    save_history(session_id, history)


def clear_session(session_id: str) -> bool:
    key = MEMORY_KEY.format(session_id=session_id)
    try:
        r.delete(key)
        return True
    except Exception:
        return False


def get_turn_count(session_id: str) -> int:
    return len(get_history(session_id)) // 2