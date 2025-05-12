To refactor your bbb.py backend code into a Model-View-Controller (MVC) architecture within the provided directory structure (Main/), we’ll break it down into modular files. MVC separates concerns: Models (data and database logic), Controllers (business logic and request handling), and Views (response rendering, though in a FastAPI app, this often means templates or JSON responses). Given your directory structure, I’ll map the components accordingly, starting from the backend code you’ve shared (e.g., /submit_quiz, /submit_exam, /dashboard, etc.).
I’ll assume bbb.py contains a mix of routes, database logic, and template rendering, and I’ll distribute it across the files you listed: app.py, router.py, Model.py, Config.py, Auth.py, Chat.py, Quiz.py, etc. Here’s how to structure it:
Directory Structure Breakdown
Main/
├── app.py         # Main FastAPI app setup and entry point
├── router.py      # Centralized router imports (optional, for modularity)
├── Model.py       # Database models (LearningPath, TopicProgress, User, etc.)
├── Config.py      # Configuration (database setup, environment variables)
├── Auth.py        # Authentication logic (get_current_user, login/logout)
├── Chat.py        # Chat-related routes and logic
├── Quiz.py        # Quiz and exam-related routes and logic
├── Dashboard.py   # Dashboard-related routes and logic (new file)
└── Templates/     # HTML templates (e.g., quiz.html, dashboard.html)
    ├── quiz.html
    ├── dashboard.html
    └── exam.html
Step-by-Step MVC Refactor
1. app.py (Main Entry Point)
Purpose: Initializes the FastAPI app, mounts routers, and sets up middleware.
Role in MVC: Ties everything together, but primarily delegates to controllers.
python
# Main/app.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from Config import init_db  # Database setup
from Auth import auth_router
from Chat import chat_router
from Quiz import quiz_router
from Dashboard import dashboard_router

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="Templates")

# Initialize database
@app.on_event("startup")
async def startup_event():
    await init_db()  # From Config.py

# Include routers (controllers)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(quiz_router, prefix="/quiz", tags=["quiz"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

# Root endpoint (optional)
@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>Welcome to Infinity Academy</h1>"
2. router.py (Optional Centralized Router)
Purpose: If you prefer a single file to manage all routers, use this instead of including them directly in app.py.
Role in MVC: Aggregates controller routes (optional).
python
# Main/router.py
from fastapi import APIRouter
from Auth import auth_router
from Chat import chat_router
from Quiz import quiz_router
from Dashboard import dashboard_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(quiz_router, prefix="/quiz", tags=["quiz"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

# In app.py, replace individual includes with:
# app.include_router(router)
3. Model.py (Models)
Purpose: Defines database models (e.g., User, LearningPath, TopicProgress).
Role in MVC: Represents the Model layer—data structure and storage.
python
# Main/Model.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    course_outline = Column(String)
    created_at = Column(String)
    exam_score = Column(Integer, default=0)
    exam_total = Column(Integer, default=0)
    exam_completed = Column(Boolean, default=False)

class TopicProgress(Base):
    __tablename__ = "topic_progress"
    id = Column(Integer, primary_key=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"))
    topic_name = Column(String)
    detailed_content = Column(String, nullable=True)
    abstract = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    performance_score = Column(Float, nullable=True)
    completion_date = Column(String, nullable=True)
    temp_score = Column(Integer, default=0)
    temp_total = Column(Integer, default=0)
4. Config.py (Configuration)
Purpose: Handles database setup and configuration.
Role in MVC: Supports the Model layer with database connectivity.
python
# Main/Config.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Model import Base
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///instance/database.db"  # Adjust path as needed
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
5. Auth.py (Authentication Controller)
Purpose: Handles login, logout, and user authentication logic.
Role in MVC: Controller for authentication, interacts with User model.
python
# Main/Auth.py
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from Model import User
from Config import get_db
import logging

logger = logging.getLogger(__name__)
auth_router = APIRouter()

async def get_current_user(response: Response, db: Session = Depends(get_db)):
    # Simplified; add real auth logic (e.g., JWT, cookies)
    user_id = 2  # Example from logs
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    logger.debug(f"Authenticated user={user.username}, id={user.id}")
    return user

@app.post("/login")
async def login(response: Response, username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password_hash != password:  # Add hashing in production
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response.set_cookie(key="username", value=username)
    response.set_cookie(key="user_id", value=str(user.id))
    logger.debug(f"User '{username}' (ID: {user.id}) logged in, cookies set")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/logout")
async def logout(response: Response):
    response.delete_cookie("username")
    response.delete_cookie("user_id")
    return RedirectResponse(url="/", status_code=303)
6. Chat.py (Chat Controller)
Purpose: Handles chat-related endpoints (e.g., /chat).
Role in MVC: Controller for chat functionality.
python
# Main/Chat.py
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from Config import get_db
from Auth import get_current_user
from fastapi.templating import Jinja2Templates

chat_router = APIRouter()
templates = Jinja2Templates(directory="Templates")

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})
7. Quiz.py (Quiz and Exam Controller)
Purpose: Manages quiz and exam routes (e.g., /quiz, /submit_quiz, /submit_exam).
Role in MVC: Controller for quiz/exam logic, interacts with Model.py.
python
# Main/Quiz.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from Model import LearningPath, TopicProgress
from Config import get_db
from Auth import get_current_user
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)
quiz_router = APIRouter()
templates = Jinja2Templates(directory="Templates")

@quiz_router.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request, topic_id: int = None, learning_path_id: int = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if topic_id:
        topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id).first()
        questions = await generate_quiz_questions(topic, num_questions=6)  # Example function
        exam_mode = False
    elif learning_path_id:
        learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id).first()
        questions = await generate_exam_questions(learning_path)  # Example function
        exam_mode = True
    total_questions = len(questions)
    logger.debug(f"Total questions sent to frontend: {total_questions}")
    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "user": user,
        "selected_topic": topic if topic_id else None,
        "questions": questions,
        "learning_path_id": learning_path_id,
        "exam_mode": exam_mode,
        "module_index": 0,
        "total_questions": total_questions
    })

@quiz_router.post("/submit_quiz/{topic_id}")
async def submit_quiz(topic_id: int, submission: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id).first()
    if not topic:
        return JSONResponse({"error": "Topic not found"}, status_code=404)
    question_index = submission["question_index"]
    is_correct = submission["is_correct"]
    total_questions = submission["total_questions"]
    
    topic.temp_total = (topic.temp_total or 0) + 1
    if is_correct:
        topic.temp_score = (topic.temp_score or 0) + 1
    logger.debug(f"Quiz progress: {topic.temp_score}/{topic.temp_total}")
    
    if question_index == total_questions - 1:
        performance_score = (topic.temp_score / topic.temp_total) * 100
        topic.performance_score = performance_score
        topic.completed = True
        topic.temp_score = 0
        topic.temp_total = 0
        db.commit()
        logger.debug(f"Quiz final score calculated: {performance_score:.1f}%")
        return {"message": f"Quiz completed! Score: {performance_score:.1f}%", "final_score": float(performance_score)}
    
    db.commit()
    return {"message": "Next question recorded"}

@quiz_router.post("/submit_exam/{learning_path_id}")
async def submit_exam(learning_path_id: int, submission: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id).first()
    if not learning_path:
        return JSONResponse({"error": "Learning path not found"}, status_code=404)
    question_index = submission["question_index"]
    is_correct = submission["is_correct"]
    total_questions = submission["total_questions"]
    
    learning_path.exam_total = (learning_path.exam_total or 0) + 1
    if is_correct:
        learning_path.exam_score = (learning_path.exam_score or 0) + 1
    logger.debug(f"Exam progress: {learning_path.exam_score}/{learning_path.exam_total}")
    
    if question_index == total_questions - 1:
        final_score = (learning_path.exam_score / learning_path.exam_total) * 100
        learning_path.exam_completed = True
        learning_path.exam_score = 0
        learning_path.exam_total = 0
        db.commit()
        logger.debug(f"Exam final score calculated: {final_score:.1f}%")
        return {"message": f"Exam completed! Score: {final_score:.1f}%", "final_score": float(final_score)}
    
    db.commit()
    return {"message": "Next question recorded"}
8. Dashboard.py (Dashboard Controller)
Purpose: Manages dashboard-related routes (e.g., /dashboard).
Role in MVC: Controller for dashboard, renders the view.
python
# Main/Dashboard.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from Model import LearningPath, TopicProgress
from Config import get_db
from Auth import get_current_user
from fastapi.templating import Jinja2Templates

dashboard_router = APIRouter()
templates = Jinja2Templates(directory="Templates")

@dashboard_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learning_paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
    for lp in learning_paths:
        total_topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == lp.id).count()
        completed_topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == lp.id, TopicProgress.completed).count()
        lp.progress_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        lp.completed_topics = completed_topics
        lp.total_topics = total_topics
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "learning_paths": learning_paths
    })
Running the App
Update Imports: Ensure all files import necessary dependencies (e.g., fastapi, sqlalchemy).
Run: Start with uvicorn Main.app:app --reload.
Test: Access endpoints like /dashboard, /quiz?topic_id=41, /submit_quiz/41.
MVC Mapping
Model: Model.py (data structures and database schema).
View: Templates in Templates/ (e.g., quiz.html, rendered by controllers).
Controller: Auth.py, Chat.py, Quiz.py, Dashboard.py (handle requests, business logic, and render responses).
This structure modularizes bbb.py into reusable components, aligning with MVC principles while leveraging FastAPI’s strengths. Let me know if you need help with specific functions (e.g., generate_quiz_questions) or further refinements!