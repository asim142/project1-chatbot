import os
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.memory import get_history, add_turn, get_turn_count
from app.vectorstore import search_documents
from dotenv import load_dotenv

load_dotenv()

llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "llama3.2"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=0.7,
)

SYSTEM_PROMPT = """You are a helpful AI assistant with access to uploaded documents.

CRITICAL RULES:
1. If DOCUMENT CONTEXT is provided below, you ALREADY have the document content. Answer directly from it. NEVER ask the user to share or upload the file again.
2. Extract and present the requested information clearly from the provided context.
3. If the context does not contain the answer, say: 'This is not mentioned in the uploaded document.' then answer from general knowledge.
4. Never pretend you cannot see the document when context is provided to you."""


def build_messages(
    session_id: str,
    message: str,
    context_chunks: list[dict]
) -> list:
    # If we found relevant chunks, inject them into the system prompt
    if context_chunks:
        context_text = "\n\n".join(
            f"[Source: {c['filename']}  relevance: {c['score']}]\n{c['text']}"
            for c in context_chunks
        )
        system_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- DOCUMENT CONTEXT ---\n{context_text}\n--- END CONTEXT ---"
        )
    else:
        system_content = SYSTEM_PROMPT

    messages = [SystemMessage(content=system_content)]

    # Inject Redis chat history so the AI remembers the conversation
    for turn in get_history(session_id):
        if turn["role"] == "human":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))

    # Add the new user message last
    messages.append(HumanMessage(content=message))
    return messages


def get_response(session_id: str, message: str) -> dict:
    context_chunks = search_documents(message, top_k=2)
    messages = build_messages(session_id, message, context_chunks)
    response = llm.invoke(messages)
    reply = response.content
    add_turn(session_id, message, reply)
    sources = list({c["filename"] for c in context_chunks})
    return {
        "response":   reply,
        "sources":    sources,
        "turn_count": get_turn_count(session_id)
    }


def stream_response(session_id: str, message: str):
    context_chunks = search_documents(message, top_k=2)
    messages = build_messages(session_id, message, context_chunks)
    full_reply = ""
    for chunk in llm.stream(messages):
        token = chunk.content
        if token:
            full_reply += token
            yield token, None
    add_turn(session_id, message, full_reply)
    sources = list({c["filename"] for c in context_chunks})
    yield None, sources