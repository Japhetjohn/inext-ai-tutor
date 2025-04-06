from fastapi import FastAPI, Depends, HTTPException, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
from pydantic import BaseModel
from passlib.context import CryptContext
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict
from dotenv import load_dotenv
import os
import openai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="iNextAI Web3 Learning Platform",
    description="AI-powered Web3 education platform with personalized learning paths",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# OpenAI Client Setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set. Please set it in the .env file.")

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENAI_API_KEY,
)

# Database Setup
DATABASE_URL = "sqlite:///./web3ai.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Jinja2 Templates & Static Files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Hashed password
    learning_paths = relationship("LearningPath", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")

class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=True)
    course_outline = Column(Text, nullable=False)  # JSON string of course outline
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    user = relationship("User", back_populates="learning_paths")
    topics = relationship("TopicProgress", back_populates="learning_path")

class TopicProgress(Base):
    __tablename__ = "topic_progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"))
    topic_name = Column(String, nullable=False)
    abstract = Column(Text, nullable=True)
    estimated_time = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    detailed_content = Column(Text, nullable=True)  # Persisted detailed content
    completed = Column(Boolean, default=False)
    completion_date = Column(String, nullable=True)
    performance_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    learning_path = relationship("LearningPath", back_populates="topics")

class CareerPath(Base):
    __tablename__ = "career_paths"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(String, default=lambda: datetime.utcnow().isoformat())
    user = relationship("User", back_populates="chat_history")

# Pydantic Models
class LearningPathInput(BaseModel):
    path_subject: str
    knowledge_level: str
    weekly_hours: str
    learning_style: str

class TopicProgressUpdate(BaseModel):
    topic_id: int
    completed: bool

class QuizAnswer(BaseModel):
    answer: str
    question_index: int

# Create Tables
Base.metadata.create_all(bind=engine)

def seed_career_paths():
    db = SessionLocal()
    try:
        if db.query(CareerPath).count() == 0:
            careers = [
                "Smart Contract Developer", "Web3 UX/UI Designer", "Blockchain Security Auditor",
                "DeFi Analyst", "NFT Strategist & Marketer", "DAO & Governance Specialist",
                "Blockchain Content Creator", "Metaverse & GameFi Developer", "Crypto Compliance & Legal Specialist"
            ]
            for career in careers:
                db.add(CareerPath(name=career, description=f"Overview of {career}"))
            db.commit()
    except Exception as e:
        logger.error(f"Error seeding career paths: {e}")
    finally:
        db.close()

seed_career_paths()

# Dependency for DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password Hashing Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Authenticate User
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

# Get Current User (Cookie-based Authentication)
def get_current_user(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    user_id = request.cookies.get("user_id")

    logger.debug(f"get_current_user: username_cookie={username}, user_id_cookie={user_id}")

    if not username or not user_id:
        logger.warning("get_current_user: Missing username or user_id cookies")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id_int = int(user_id)
        user = db.query(User).filter(User.username == username, User.id == user_id_int).first()
        if not user:
            logger.warning(f"get_current_user: No user found for username={username}, user_id={user_id}")
            raise HTTPException(status_code=401, detail="User not found or credentials mismatch")
        logger.debug(f"get_current_user: Authenticated user={user.username}, id={user.id}")
        return user
    except ValueError:
        logger.error(f"get_current_user: Invalid user_id format: {user_id}")
        raise HTTPException(status_code=401, detail="Invalid user_id format")
    
# Helper Functions
async def generate_course_outline(knowledge_level: str, path_subject: str, weekly_hours: str, learning_style: str):
    try:
        if "-" in weekly_hours:
            low, high = map(int, weekly_hours.split("-"))
            avg_hours = (low + high) / 2
        else:
            avg_hours = int(weekly_hours)
    except Exception as e:
        logger.error(f"Error parsing weekly_hours: {e}")
        avg_hours = 5

    total_topics = max(3, int(avg_hours / 2))

    style_mapping = {
        "video": "video-based lessons with visual explanations",
        "articles": "text-based articles and readings",
        "interactive_labs": "hands-on interactive labs and exercises"
    }
    content_type = style_mapping.get(learning_style, "a mix of videos, articles, and labs")

    level_description = {
        "beginner": "a toddler with basic knowledge",
        "intermediate": "a junior professional with practical experience",
        "expert": "an advanced professional with high expertise"
    }
    level_context = level_description.get(knowledge_level, "a learner with unknown level")

    prompt = f"""
    You are a career coach specializing in Web3, mentoring {level_context} interested in '{path_subject}' within the Web3 domain.
    - The learner can dedicate {avg_hours} hours per week, so adjust the pace and depth accordingly.
    - The learner prefers {content_type}, so prioritize this format in the course structure.
    - Create a tailored course outline with {total_topics} distinct topics, each customized to reflect '{path_subject}' and suitable for {level_context}.
    - Adjust complexity and depth based on the learner's level:
      - 'beginner' (toddler): Simple explanations, foundational concepts, very elementary.
      - 'intermediate' (junior professional): Practical applications, some technical depth.
      - 'expert' (advanced professional): In-depth technical details, advanced use cases.
    - Provide career advice and actionable steps for each topic to help the learner progress in their Web3 career.
    - Format each topic as a JSON object with 'topic' (title), 'abstract' (description including career advice), 'estimated_time' (duration like '2 hours'), and 'content_type' (e.g., 'video').
    - Return the result as a JSON array.
    Example for 'beginner' and 'NFTs':
    [
        {{"topic": "Introduction to NFTs", "abstract": "Basics of NFTs with video lessons. Career tip: Start exploring NFT marketplaces to build familiarity.", "estimated_time": "2 hours", "content_type": "video"}},
        {{"topic": "NFT Standards (ERC-721)", "abstract": "Learn ERC-721 basics with interactive labs. Career tip: Experiment with creating a simple NFT.", "estimated_time": "1.5 hours", "content_type": "interactive_labs"}}
    ]
    """
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        raw_response = response.choices[0].message.content
        logger.debug(f"Raw response from OpenRouter: {raw_response}")
        course_outline = json.loads(raw_response)
        if not isinstance(course_outline, list) or len(course_outline) != total_topics:
            raise ValueError(f"Expected {total_topics} topics, got: {course_outline}")
        return course_outline
    except Exception as e:
        logger.error(f"Error generating course outline: {e}")
        return [
            {"topic": f"Introduction to {path_subject}", "abstract": f"Basics of {path_subject} using {content_type}. Career tip: Start exploring {path_subject} basics.", "estimated_time": "2 hours", "content_type": content_type}
            for _ in range(total_topics)
        ]

async def generate_detailed_content(topic: str, content_type: str):
    prompt = f"""
    You are a Web3 career coach. Provide detailed content for the topic '{topic}' tailored for {content_type}.
    - Include an engaging introduction, key concepts, and practical examples.
    - Add a career tip to help the learner advance in their Web3 career.
    - Format as plain text suitable for display.
    """
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating detailed content: {e}")
        return f"Content for {topic} is under development. Career tip: Keep exploring Web3 resources."

async def generate_chat_response(message: str, user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    knowledge_level = "beginner"  # Default or fetch from user profile
    level_description = {
        "beginner": "a toddler with basic knowledge",
        "intermediate": "a junior professional with practical experience",
        "expert": "an advanced professional with high expertise"
    }
    level_context = level_description.get(knowledge_level, "a learner with unknown level")

    prompt = f"""
    You are a Web3 career coach with high expertise, mentoring {level_context} in the Web3 domain.
    - Respond to the user's message: "{message}" with career advice, actionable steps, and encouragement tailored to their Web3 career journey.
    - Adjust your tone and depth based on their level:
      - 'beginner' (toddler): Simple, encouraging language with foundational Web3 concepts.
      - 'intermediate' (junior professional): Practical advice with technical insights.
      - 'expert' (advanced professional): Advanced strategies and industry trends.
    - Provide a clear next step for the user to take in their Web3 career.
    """
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating chat response: {e}")
        return "I'm here to guide you! Let’s start with the basics of Web3—explore an introductory course next."

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return JSONResponse({"error": "Incorrect username or password"}, status_code=400)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="username", value=user.username, httponly=True, secure=False)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True, secure=False)
    logger.debug(f"User '{user.username}' (ID: {user.id}) logged in, cookies set")
    return response

@app.get("/check_login")
async def check_login(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    user_id = request.cookies.get("user_id")
    if not username or not user_id:
        return JSONResponse({"authenticated": False}, status_code=401)
    try:
        user_id_int = int(user_id)
        user = db.query(User).filter(User.username == username, User.id == user_id_int).first()
        if not user:
            return JSONResponse({"authenticated": False}, status_code=401)
        return JSONResponse({"authenticated": True, "user_id": user.id, "username": user.username})
    except ValueError:
        return JSONResponse({"authenticated": False}, status_code=401)

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        return JSONResponse({"error": "Username already registered"}, status_code=400)
    if db.query(User).filter(User.email == email).first():
        return JSONResponse({"error": "Email already registered"}, status_code=400)
    
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    return JSONResponse({"message": "Registration successful, please login"}, status_code=201)

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("username")
    response.delete_cookie("user_id")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learning_paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
    result = {
        "user": {"username": user.username, "id": user.id},
        "learning_paths": [
            {
                "id": lp.id,
                "name": lp.name,
                "progress_percentage": sum(1 for tp in db.query(TopicProgress).filter(TopicProgress.learning_path_id == lp.id, TopicProgress.completed).all()) / len(json.loads(lp.course_outline)) * 100 if json.loads(lp.course_outline) else 0
            } for lp in learning_paths
        ]
    }
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "learning_paths": result["learning_paths"]})

@app.get("/dashboard/personalize", response_class=HTMLResponse)
async def personalize_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.post("/generate_learning_path")
async def generate_learning_path(input_data: LearningPathInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        logger.debug(f"Generating learning path for user: {user.username}, ID: {user.id}")
        logger.debug(f"Input data: {input_data.dict()}")  # Log input data for debugging
        course_outline = await generate_course_outline(input_data.knowledge_level, input_data.path_subject, input_data.weekly_hours, input_data.learning_style)
        logger.debug(f"Generated course outline: {course_outline}")  # Log the generated outline

        learning_path = LearningPath(user_id=user.id, name=f"{input_data.path_subject} Path", course_outline=json.dumps(course_outline))
        db.add(learning_path)
        db.commit()
        db.refresh(learning_path)
        logger.debug(f"Created learning path with ID: {learning_path.id}")

        for topic in course_outline:
            topic_progress = TopicProgress(
                learning_path_id=learning_path.id,
                topic_name=topic["topic"],
                abstract=topic["abstract"],
                estimated_time=topic["estimated_time"],
                content_type=topic["content_type"]
            )
            db.add(topic_progress)
        db.commit()
        logger.debug("Created topic progress entries")

        return {"learning_path_id": learning_path.id}
    except Exception as e:
        logger.error(f"Error in generate_learning_path: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate learning path: {str(e)}")
    

    
@app.get("/roadmap")
async def roadmap(learning_path_id: int = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not learning_path_id:
        raise HTTPException(status_code=400, detail="learning_path_id is required")
    learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    course_outline = json.loads(learning_path.course_outline)
    topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == learning_path_id).all()
    return {
        "id": learning_path.id,
        "name": learning_path.name,
        "course_outline": [
            {
                "id": t.id,
                "topic": t.topic_name,
                "estimated_time": t.estimated_time,
                "content_type": t.content_type,
                "progress_percentage": t.progress_percentage or 0,
                "completed": t.completed
            } for t in topics
        ]
    }

@app.get("/course/{learning_path_id}/{topic_id}")
async def get_course_content(learning_path_id: int, topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id, TopicProgress.learning_path_id == learning_path_id).first()
    if not topic or topic.learning_path.user_id != user.id:
        raise HTTPException(status_code=404, detail="Topic not found or unauthorized")
    if not topic.detailed_content:
        topic.detailed_content = await generate_detailed_content(topic.topic_name, topic.content_type)
        db.commit()
    return {"topic": topic.topic_name, "content": topic.detailed_content}

@app.get("/quiz/{topic_id}")
async def get_quiz(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id).first()
    if not topic or topic.learning_path.user_id != user.id:
        raise HTTPException(status_code=404, detail="Topic not found or unauthorized")
    questions = [
        {
            "text": f"What is a key concept in {topic.topic_name.lower()}?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A"
        },
        {
            "text": f"How does {topic.topic_name.lower()} relate to Web3?",
            "options": ["Option X", "Option Y", "Option Z", "Option W"],
            "correct_answer": "Option Y"
        }
    ]
    return {"topic": topic.topic_name, "questions": questions}

@app.post("/submit_quiz/{topic_id}")
async def submit_quiz(topic_id: int, answer: QuizAnswer, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id).first()
    if not topic or topic.learning_path.user_id != user.id:
        raise HTTPException(status_code=404, detail="Topic not found or unauthorized")
    quiz_data = await get_quiz(topic_id, user, db)
    correct_answer = quiz_data["questions"][answer.question_index]["correct_answer"]
    if answer.answer == correct_answer:
        topic.completed = True
        topic.completion_date = datetime.utcnow().isoformat()
        db.commit()
        return {"message": "Correct! Moving to next question." if answer.question_index < len(quiz_data["questions"]) - 1 else "Quiz completed!"}
    return {"message": "Incorrect. Try again."}

@app.post("/update_topic_progress")
async def update_topic_progress(topic_data: TopicProgressUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topic = db.query(TopicProgress).filter(TopicProgress.id == topic_data.topic_id).first()
    if not topic or topic.learning_path.user_id != user.id:
        raise HTTPException(status_code=404, detail="Topic not found or unauthorized")
    topic.completed = topic_data.completed
    if topic.completed:
        topic.completion_date = datetime.utcnow().isoformat()
    db.commit()
    return {"status": "success"}

@app.get("/wishlist")
async def get_wishlist(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return [{"name": "Intro to Web3", "id": 1}, {"name": "Intro to AI", "id": 2}]

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=1008)
        return
    try:
        while True:
            data = await websocket.receive_text()
            chat_history = ChatHistory(user_id=user_id, message=data, response="Processing...")
            db.add(chat_history)
            db.commit()

            response = await generate_chat_response(data, user_id, db)
            chat_history.response = response
            db.commit()

            await websocket.send_text(json.dumps({"message": response, "chat_history": {"message": data, "response": response}}))
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user_id: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({"message": "An error occurred."}))

@app.get("/chat_history")
async def get_chat_history(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.debug(f"Requesting chat history for user_id={user_id}, authenticated user_id={user.id}")
    if user_id != user.id:
        logger.warning(f"Unauthorized access attempt: user_id={user_id} does not match authenticated user_id={user.id}")
        raise HTTPException(status_code=403, detail="Unauthorized")
    history = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
    return [{"message": h.message, "response": h.response} for h in history]

# HTML Rendering Routes
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})

@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap_page(request: Request, id: int, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("roadmap.html", {"request": request, "user": user, "learning_path_id": id})

@app.get("/course_content", response_class=HTMLResponse)
async def course_content_page(request: Request, learning_path_id: int, topic_id: int, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("course_content.html", {"request": request, "user": user, "learning_path_id": learning_path_id, "topic_id": topic_id})

@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request, topic_id: int, learning_path_id: int, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("quiz.html", {"request": request, "user": user, "topic_id": topic_id, "learning_path_id": learning_path_id})

# Run the FastAPI App
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)