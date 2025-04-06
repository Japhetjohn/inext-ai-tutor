
from sqlalchemy.orm import Session
from models import models
from schemas import schemas
import datetime

class DatabaseOperations:
    @staticmethod
    def get_user_by_wallet(db: Session, wallet_address: str):
        return db.query(models.User).filter(models.User.wallet_address == wallet_address).first()

    @staticmethod
    def create_user(db: Session, user: schemas.UserCreate):
        db_user = models.User(wallet_address=user.wallet_address)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def save_chat(db: Session, user_id: int, message: str, response: str):
        chat = models.ChatHistory(
            user_id=user_id,
            message=message,
            response=response,
            timestamp=datetime.datetime.utcnow().isoformat()
        )
        db.add(chat)
        db.commit()
        return chat

    @staticmethod
    def get_chat_history(db: Session, user_id: int):
        return db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user_id).all()

    @staticmethod
    def create_learning_path(db: Session, user_id: int, path: schemas.LearningPathCreate):
        name = f"{path.topic} ({path.difficulty})"
        db_path = models.LearningPath(user_id=user_id, name=name, **path.dict())
        db.add(db_path)
        db.commit()
        db.refresh(db_path)
        return db_path

    @staticmethod
    def get_learning_paths(db: Session, user_id: int):
        return db.query(models.LearningPath).filter(models.LearningPath.user_id == user_id).all()

    @staticmethod
    def award_tokens(db: Session, user_id: int, amount: float):
        user = db.query(models.User).filter(models.User.id == user_id).first()
        user.tokens += amount
        db.commit()
        return user
