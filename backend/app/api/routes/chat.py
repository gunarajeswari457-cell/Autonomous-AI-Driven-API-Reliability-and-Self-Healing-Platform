from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.services.ai_engine import chat_reply

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context: dict | None = None


@router.post("/chat")
async def chat(payload: ChatRequest, _: User = Depends(get_current_user)):
    return await chat_reply(payload.message, payload.context)
