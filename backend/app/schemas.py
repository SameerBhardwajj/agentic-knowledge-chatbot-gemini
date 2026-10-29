
from datetime import datetime
from pydantic import BaseModel, Field

class ChatCreate(BaseModel):
    title: str = Field(default="New chat", max_length=200)

class ChatSummary(BaseModel):
    id: int
    title: str
    updated_at: datetime

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

class UserSummary(BaseModel):
    id: int
    name: str

class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
