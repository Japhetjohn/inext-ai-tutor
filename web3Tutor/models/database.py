
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime

DATABASE_URL = "sqlite:///./web3ai.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    learning_paths = relationship("LearningPath", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")

# Add other model classes here...
