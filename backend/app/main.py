
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .agent import run_agent
from .config import FRONTEND_ORIGIN
from .db import Base, engine, get_db
from .models import Chat, Message, User
from .schemas import ChatCreate, ChatMessageRequest, ChatSummary, MessageOut, UserSummary

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Knowledge Chatbot", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def current_user_id(x_user_id: str | None = Header(default=None)) -> int:
    # DEMO ONLY. Replace with JWT/session authentication in production.
    if not x_user_id:
        raise HTTPException(401, "X-User-ID header is required.")
    try:
        return int(x_user_id)
    except ValueError as exc:
        raise HTTPException(400, "X-User-ID must be an integer.") from exc

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/users", response_model=list[UserSummary])
def users(db: Session = Depends(get_db)):
    return [UserSummary(id=u.id, name=u.name)
            for u in db.scalars(select(User).order_by(User.id)).all()]

@app.get("/api/chats", response_model=list[ChatSummary])
def list_chats(user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    chats = db.scalars(
        select(Chat).where(Chat.user_id == user_id).order_by(Chat.updated_at.desc())
    ).all()
    return chats

@app.post("/api/chats", response_model=ChatSummary)
def create_chat(payload: ChatCreate, user_id: int = Depends(current_user_id),
                db: Session = Depends(get_db)):
    chat = Chat(user_id=user_id, title=payload.title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

@app.get("/api/chats/{chat_id}/messages", response_model=list[MessageOut])
def get_messages(chat_id: int, user_id: int = Depends(current_user_id),
                 db: Session = Depends(get_db)):
    chat = db.scalar(select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id))
    if not chat:
        raise HTTPException(404, "Chat not found.")
    return chat.messages

@app.post("/api/chats/{chat_id}/messages")
def send_message(chat_id: int, payload: ChatMessageRequest,
                 user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    chat = db.scalar(select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id))
    if not chat:
        raise HTTPException(404, "Chat not found.")

    history = [(m.role, m.content) for m in chat.messages]
    db.add(Message(chat_id=chat.id, role="user", content=payload.message))
    db.flush()

    answer, sources, tools_used = run_agent(
        db, user_id, payload.message, history
    )

    db.add(Message(chat_id=chat.id, role="assistant", content=answer))
    if chat.title == "New chat":
        chat.title = payload.message[:60]
    db.commit()

    return {
        "answer": answer,
        "sources": [
            {"id": s["id"], "title": s["title"], "source": s["source"],
             "similarity": s["similarity"]}
            for s in sources
        ],
        "tools_used": tools_used,
    }
