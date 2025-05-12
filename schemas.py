from pydantic import BaseModel
from typing import Optional, List

class UserBase(BaseModel):
    wallet_address: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    tokens: float
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    message: str
    save_history: bool

class ChatResponse(BaseModel):
    response: str

class LearningPathBase(BaseModel):
    topic: str
    difficulty: str
    duration: int
    content_type: str

class LearningPathCreate(LearningPathBase):
    pass

class LearningPath(LearningPathBase):
    id: int
    name: str
    progress_percentage: float
    class Config:
        from_attributes = True

class QuizResult(BaseModel):
    score: float
    completed: bool