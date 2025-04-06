from sqlalchemy.orm import Session
import bbb, schemas
import datetime

def get_user_by_wallet(db: Session, wallet_address: str):
    return db.query(bbb.User).filter(bbb.User.wallet_address == wallet_address).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = bbb.User(wallet_address=user.wallet_address)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def save_chat(db: Session, user_id: int, message: str, response: str):
    chat = bbb.ChatHistory(
        user_id=user_id,
        message=message,
        response=response,
        timestamp=datetime.datetime.utcnow().isoformat()
    )
    db.add(chat)
    db.commit()
    return chat

def get_chat_history(db: Session, user_id: int):
    return db.query(bbb.ChatHistory).filter(bbb.ChatHistory.user_id == user_id).all()

def create_learning_path(db: Session, user_id: int, path: schemas.LearningPathCreate):
    name = f"{path.topic} ({path.difficulty})"
    db_path = bbb.LearningPath(user_id=user_id, name=name, **path.dict())
    db.add(db_path)
    db.commit()
    db.refresh(db_path)
    return db_path

def get_learning_paths(db: Session, user_id: int):
    return db.query(bbb.LearningPath).filter(bbb.LearningPath.user_id == user_id).all()

def award_tokens(db: Session, user_id: int, amount: float):
    user = db.query(bbb.User).filter(bbb.User.id == user_id).first()
    user.tokens += amount
    db.commit()
    return user