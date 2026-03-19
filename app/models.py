from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "user_001",
                "message": "What does the document say about pricing?"
            }
        }


class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str
    sources: list[str]
    turn_count: int


class UploadResponse(BaseModel):
    filename: str
    chunks_stored: int
    message: str


class SessionInfo(BaseModel):
    session_id: str
    turn_count: int
    history: list[dict]


class ClearResponse(BaseModel):
    session_id: str
    cleared: bool
    message: str