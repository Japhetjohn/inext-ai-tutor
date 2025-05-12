
# from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Boolean, Float
# from sqlalchemy.orm import declarative_base, sessionmaker, relationship
# from datetime import datetime

# # Database Connection
# DATABASE_URL = "sqlite:///./web3ai.db"  # Change for PostgreSQL if needed
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()


# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     username = Column(String, unique=True, nullable=False)
#     email = Column(String, unique=True, nullable=False)
#     password = Column(String, nullable=False)  # Hashed password
#     learning_paths = relationship("LearningPath", back_populates="user")
#     chat_history = relationship("ChatHistory", back_populates="user")
#     progress = relationship("Progress", back_populates="user")  # Added relationship
#     chat_sessions = relationship("ChatSession", back_populates="user")

# class LearningPath(Base):
#     __tablename__ = "learning_paths"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     name = Column(String, nullable=True)
#     course_outline = Column(Text, nullable=False)  # JSON string of course outline
#     created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
#     user = relationship("User", back_populates="learning_paths")
#     topics = relationship("TopicProgress", back_populates="learning_path")

# class TopicProgress(Base):
#     __tablename__ = "topic_progress"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     learning_path_id = Column(Integer, ForeignKey("learning_paths.id"))
#     topic_name = Column(String, nullable=False)
#     abstract = Column(Text, nullable=True)
#     estimated_time = Column(String, nullable=True)
#     content_type = Column(String, nullable=True)
#     detailed_content = Column(Text, nullable=True)  # Persisted detailed content
#     completed = Column(Boolean, default=False)
#     completion_date = Column(String, nullable=True)
#     performance_score = Column(Float, nullable=True)
#     feedback = Column(Text, nullable=True)
#     learning_path = relationship("LearningPath", back_populates="topics")

# class Progress(Base):
#     __tablename__ = "progress"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     module_id = Column(Integer, ForeignKey("modules.id"))
#     completion_status = Column(Float, default=0.0)
#     user = relationship("User", back_populates="progress")
#     module = relationship("Module", back_populates="progress")  # Fixed relationship

# class CareerPath(Base):
#     __tablename__ = "career_paths"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String, unique=True, nullable=False)
#     description = Column(Text)
#     modules = relationship("Module", back_populates="career_path")  # Added relationship

# class Module(Base):
#     __tablename__ = "modules"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     career_path_id = Column(Integer, ForeignKey("career_paths.id"))
#     title = Column(String, nullable=False)
#     description = Column(Text)
#     career_path = relationship("CareerPath", back_populates="modules")
#     progress = relationship("Progress", back_populates="module")  # Fixed relationship
#     course_content = relationship("CourseContent", back_populates="module")  # Added relationship

# class CourseContent(Base):
#     __tablename__ = "course_content"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     module_id = Column(Integer, ForeignKey("modules.id"))
#     content = Column(Text, nullable=False)
#     module = relationship("Module", back_populates="course_content")

# class ChatSession(Base):
#     __tablename__ = "chat_sessions"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     title = Column(String, nullable=True)  # e.g., "NFT Chat 2025-03-22"
#     created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
#     messages = relationship("ChatHistory", back_populates="session")
#     user = relationship("User", back_populates="chat_sessions")
    
# class ChatHistory(Base):
#     __tablename__ = "chat_history"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
#     message = Column(Text, nullable=False)
#     response = Column(Text, nullable=False)
#     timestamp = Column(String, default=lambda: datetime.utcnow().isoformat())
#     user = relationship("User", back_populates="chat_history")
#     session = relationship("ChatSession", back_populates="messages")


# # Create Tables
# Base.metadata.create_all(bind=engine)



# # from sqlalchemy import create_engine, inspect

# # # Connect to your database (Modify for PostgreSQL)
# # DATABASE_URL = "sqlite:///./web3ai.db"
# # engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# # # Create an inspector to check database structure
# # inspector = inspect(engine)

# # # Get all table names
# # tables = inspector.get_table_names()
# # print("📌 Tables in Database:", tables)


# # def list_database_schema():
# #     inspector = inspect(engine)
# #     tables = inspector.get_table_names()

# #     print("\n📌 Database Schema Overview")
# #     for table_name in tables:
# #         print(f"\n🔹 Table: {table_name}")
# #         columns = inspector.get_columns(table_name)
# #         for column in columns:
# #             print(f"   - {column['name']} ({column['type']})")

# # # Call the function
# # list_database_schema()


# from fastapi import FastAPI, WebSocket
# app = FastAPI()

# @app.websocket("/ws")
# async def ws_test(websocket: WebSocket):
#     await websocket.accept()
#     await websocket.send_text("Hello WebSocket")
#     await websocket.close()

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8001)

"""
 headers = {"Authorization": f"Bearer {api_key.strip()}"}
    prompt = f"Generate detailed content for {topic.get('topic') or topic.get('title')} in {learning_style} format."
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/completions",  # Update to your API endpoint
                json={"prompt": prompt, "max_tokens": 500},
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["text"]"""


# import sqlite3
# import logging
# from datetime import datetime
# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# # Database file (adjust path as needed)
# DB_FILE = "web3ai.db"  # Replace with your actual SQLite file path

# def add_columns_if_not_exist():
#     try:
#         # Connect to the database
#         conn = sqlite3.connect(DB_FILE)
#         cursor = conn.cursor()

#         # Check and add columns to learning_paths
#         cursor.execute("PRAGMA table_info(users)")
#         columns = [col[1] for col in cursor.fetchall()]
#         logger.debug(f"Existing columns in users: {columns}")

#         # if "learning_style" not in columns:
#         #     cursor.execute("ALTER TABLE learning_paths ADD COLUMN learning_style STRING DEFAULT Ariticle")
#         #     logger.debug("Added exam_score column to learning_paths")
#         # if "course_outline" not in columns:
#         #     cursor.execute("ALTER TABLE learning_paths ADD COLUMN course_outline STRING DEFAULT False")
#         #     logger.debug("Added exam_completed column to learning_paths")
#         conn = sqlite3.connect("web3ai.db")
#         conn.execute("ALTER TABLE users ADD COLUMN notes TEXT")
#         conn.execute("ALTER TABLE users ADD COLUMN basic_progress Float")
#         conn.execute("ALTER TABLE users ADD COLUMN advanced_progress Float")
#         conn.execute("ALTER TABLE users ADD COLUMN expert_progress Float")
#         conn.execute("ALTER TABLE users ADD COLUMN current_level String")
#         conn.execute("ALTER TABLE users ADD COLUMN theme_preference String")
#         conn.execute("ALTER TABLE users ADD COLUMN profile_photo String")
#         conn.execute("ALTER TABLE users ADD COLUMN wallet_address String")
#         conn.execute("ALTER TABLE users ADD COLUMN is_wallet_connected Boolean,")
#         conn.execute("ALTER TABLE users ADD COLUMN xp_points Integer")
#         conn.execute("ALTER TABLE users ADD COLUMN time_spent Integer")
#         conn.execute("ALTER TABLE users ADD COLUMN theme_preference String")
#         # Check and add columns to topic_progress
#         cursor.execute("PRAGMA table_info(users)")
#         columns = [col[1] for col in cursor.fetchall()]
#         logger.debug(f"Existing columns in users: {columns}")

#         # Check current data
#         # cursor.execute("SELECT id, completion_date FROM topic_progress WHERE completion_date IS NOT NULL")
#         rows = cursor.fetchall()

#         # for row in rows:
#         #     id, completion_date = row
#         #     if isinstance(completion_date, str):
#         #         try:
#         #             # Test if it’s a valid ISO string
#         #             datetime.fromisoformat(completion_date)
#         #         except ValueError:
#         #             # If not, assume a common format (e.g., "2025-03-27 12:00:00") and convert
#         #             try:
#         #                 dt = datetime.strptime(completion_date, "%Y-%m-%d %H:%M:%S")
#         #                 new_date = dt.isoformat()
#         #                 cursor.execute("UPDATE topic_progress SET completion_date = ? WHERE id = ?", (new_date, id))
#         #             except ValueError:
#         #                 logger.warning(f"Invalid date format for id={id}: {completion_date}")

                
#         #         cursor.execute("PRAGMA table_info(learning_paths)")
#         #         columns = [col[1] for col in cursor.fetchall()]

#         # if "temp_score" not in columns:
#         #     cursor.execute("ALTER TABLE topic_progress ADD COLUMN temp_score INTEGER DEFAULT 0")
#         #     logger.debug("Added temp_score column to topic_progress")
#         # if "temp_total" not in columns:
#         #     cursor.execute("ALTER TABLE topic_progress ADD COLUMN temp_total INTEGER DEFAULT 0")
#         #     logger.debug("Added temp_total column to topic_progress")

#         # Commit changes
#         conn.commit()
#         logger.info("Database schema updated successfully")

#     except sqlite3.Error as e:
#         logger.error(f"Error updating database schema: {e}")
#     finally:
#         conn.close()

# if __name__ == "__main__":
#     add_columns_if_not_exist()


import sqlite3
conn = sqlite3.connect("web3ai.db")

# conn.execute("ALTER TABLE users ADD COLUMN notes TEXT")
# conn.execute("ALTER TABLE users ADD COLUMN basic_progress Float")
# conn.execute("ALTER TABLE users ADD COLUMN advanced_progress Float")
# conn.execute("ALTER TABLE users ADD COLUMN expert_progress Float")
# conn.execute("ALTER TABLE users ADD COLUMN current_level String")
# conn.execute("ALTER TABLE users ADD COLUMN theme_preference String")
# conn.execute("ALTER TABLE users ADD COLUMN profile_photo String")
# conn.execute("ALTER TABLE users ADD COLUMN wallet_address String")
conn.execute("ALTER TABLE users ADD COLUMN badges String")
# conn.execute("ALTER TABLE users ADD COLUMN xp_points Integer")
# conn.execute("ALTER TABLE users ADD COLUMN time_spent Integer")
# conn.execute("ALTER TABLE users ADD COLUMN theme_preference String")
# conn.commit()

# Print all columns in the topic_progress table
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("Columns in users table:")
for column in columns:
    print(f" - {column[1]} ({column[2]})")  # column[1] is name, column[2] is type

conn.close()