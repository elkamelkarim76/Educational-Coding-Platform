from pydantic import BaseModel


class ChatMessageCreate(BaseModel):
    user_id: int
    content: str


class ChatMessageOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    username: str
    content: str
    created_at: str

    class Config:
        from_attributes = True
