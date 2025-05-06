
from pydantic import BaseModel
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    profile_photo: Optional[str] = None
    wallet_address: Optional[str] = None
    theme_preference: Optional[str] = None
    notes: Optional[str] = None

class User(UserBase):
    id: int
    xp_points: int = 100
    time_spent: int = 0
    badges: str = "[]"
    is_wallet_connected: bool = False
    basic_progress: float = 0.0
    advanced_progress: float = 0.0
    expert_progress: float = 0.0
    current_level: str = "beginner"
    
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    message: str
    save_history: bool = True

class ChatResponse(BaseModel):
    response: str

class LearningPathBase(BaseModel):
    topic: str
    difficulty: str
    duration: int
    content_type: str

class LearningPathCreate(LearningPathBase):
    user_id: int

class LearningPath(LearningPathBase):
    id: int
    name: str
    progress_percentage: float = 0.0
    
    class Config:
        from_attributes = True

class TopicProgressUpdate(BaseModel):
    topic_id: int
    completed: bool
    performance_score: Optional[float] = None
    feedback: Optional[str] = None

class QuizResult(BaseModel):
    score: float
    completed: bool
