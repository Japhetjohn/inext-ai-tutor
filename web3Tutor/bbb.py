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
import schemas, crud #blockchain


# In-memory storage for WebSocket connections (replace with DB for persistence if needed)
connections: Dict[str, WebSocket] = {}




load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],  # Match frontend origin allowing multiple origin #### very useless
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# OpenRouter API Key and Client Setup
OPENROUTER_API_KEY = "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"
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",  # Ensure correct base URL
    api_key=OPENROUTER_API_KEY,
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
    profile_photo = Column(String, nullable=True)
    wallet_address = Column(String, unique=True, nullable=True)
    is_wallet_connected = Column(Boolean, default=False)
    xp_points = Column(Integer, default=100)
    time_spent = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    badges = Column(String, default='["Web3 Novice", "Explorer"]')
    basic_progress = Column(Float, default=0.0)
    advanced_progress = Column(Float, default=0.0)
    expert_progress = Column(Float, default=0.0)
    current_level = Column(String, default="beginner")
    theme_preference = Column(String, default="light")
    learning_paths = relationship("LearningPath", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")
    progress = relationship("Progress", back_populates="user")

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

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module_id = Column(Integer, ForeignKey("modules.id"))
    completion_status = Column(Float, default=0.0)
    user = relationship("User", back_populates="progress")
    module = relationship("Module", back_populates="progress")  # Fixed relationship

class CareerPath(Base):
    __tablename__ = "career_paths"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    modules = relationship("Module", back_populates="career_path")  # Added relationship

class Module(Base):
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    career_path_id = Column(Integer, ForeignKey("career_paths.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    career_path = relationship("CareerPath", back_populates="modules")
    progress = relationship("Progress", back_populates="module")  # Fixed relationship
    course_content = relationship("CourseContent", back_populates="module")  # Added relationship

class CourseContent(Base):
    __tablename__ = "course_content"
    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey("modules.id"))
    content = Column(Text, nullable=False)
    module = relationship("Module", back_populates="course_content")

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

class TopicFeedback(BaseModel):
    topic_id: int
    performance_score: Optional[float] = None
    feedback: Optional[str] = None
    new_interest: Optional[str] = None

class QuizAnswer(BaseModel):
    answer: str
    question_index: int

# Create Tables
Base.metadata.create_all(bind=engine)

# Seed Career Paths
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
        # Seed some modules for each career path
        career_paths = db.query(CareerPath).all()
        for career in career_paths:
            if db.query(Module).filter(Module.career_path_id == career.id).count() == 0:
                modules = [
                    {"title": f"Introduction to {career.name}", "description": f"Learn the basics of {career.name}."},
                    {"title": f"Advanced {career.name} Concepts", "description": f"Deep dive into {career.name}."},
                    {"title": f"{career.name} Practical Applications", "description": f"Hands-on projects in {career.name}."}
                ]
                for module in modules:
                    db.add(Module(career_path_id=career.id, title=module["title"], description=module["description"]))
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

@app.post("/connect_wallet", response_model=schemas.User)
async def connect_wallet(user: schemas.UserBase, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_wallet(db, user.wallet_address)
    if not db_user:
        db_user = crud.create_user(db, user)
    return db_user


# Get Current User (Cookie-based Authentication)
def get_current_user(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    user_id = request.cookies.get("user_id")
    logger.debug(f"get_current_user for {request.url}: username_cookie={username}, user_id_cookie={user_id}")

    if not username or not user_id:
        logger.warning(f"get_current_user for {request.url}: Missing username or user_id cookies")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id_int = int(user_id)
        user = db.query(User).filter(User.username == username, User.id == user_id_int).first()
        if not user:
            logger.warning(f"get_current_user for {request.url}: No user found for username={username}, user_id={user_id_int}")
            raise HTTPException(status_code=401, detail="User not found or credentials mismatch")
        logger.debug(f"get_current_user for {request.url}: Authenticated user={user.username}, id={user.id}")
        return user
    except ValueError:
        logger.error(f"get_current_user for {request.url}: Invalid user_id format: {user_id}")
        raise HTTPException(status_code=401, detail="Invalid user_id format")

# Initialize base courses
initial_courses = [
    {
        "name": "Web3 Fundamentals",
        "topics": ["Introduction to Web3", "Blockchain Basics", "Cryptocurrency Fundamentals", "Smart Contracts 101"],
        "duration": "4 weeks",
        "level": "beginner"
    },
    {
        "name": "DeFi Mastery",
        "topics": ["DeFi Protocols", "Yield Farming", "Liquidity Pools", "Risk Management"],
        "duration": "6 weeks",
        "level": "intermediate"
    },
    {
        "name": "NFT Development",
        "topics": ["NFT Standards", "Marketplace Development", "NFT Smart Contracts", "NFT Security"],
        "duration": "5 weeks",
        "level": "advanced"
    },
    {
        "name": "Blockchain Security",
        "topics": ["Security Fundamentals", "Smart Contract Auditing", "Common Vulnerabilities", "Best Practices"],
        "duration": "8 weeks",
        "level": "expert"
    }
]

def init_courses(db: Session):
    try:
        existing_courses = db.query(LearningPath).count()
        if existing_courses == 0:
            for course in initial_courses:
                course_outline = [
                    {
                        "topic": topic,
                        "abstract": f"Learn about {topic}",
                        "estimated_time": "2 hours",
                        "content_type": "video"
                    } for topic in course["topics"]
                ]
                learning_path = LearningPath(
                    name=course["name"],
                    course_outline=json.dumps(course_outline),
                    level=course["level"]
                )
                db.add(learning_path)
            db.commit()
    except Exception as e:
        logger.error(f"Error initializing courses: {e}")

# Helper Functions
async def generate_course_outline(knowledge_level: str, path_subject: str, weekly_hours: str = "5", learning_style: str = "video"):
    try:
        if "-" in weekly_hours:
            low, high = map(int, weekly_hours.split("-"))
            avg_hours = (low + high) / 2
        else:
            avg_hours = int(weekly_hours)
    except Exception as e:
        logger.error(f"Error parsing weekly_hours: {e}")
        avg_hours = 5

    total_topics = max(10, int(avg_hours / 2))

    style_mapping = {
        "video": "video-based lessons with visual explanations",
        "articles": "text-based articles and readings",
        "interactive_labs": "hands-on interactive labs and exercises"
    }
    content_type = style_mapping.get(learning_style, "video-based lessons with visual explanations")

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

async def generate_detailed_content(topic: str, content_type: str = "video"):
    prompt = f"""
    You are an expert in Web3 education. For the topic '{topic}', create a detailed lesson plan in the context of Web3 tailored for {content_type}.
    Include the following sections:
    - Introduction: Provide an overview of the topic.
    - Key Concepts: List and explain the main ideas with depth.
    - Examples: Include real-world examples or case studies.
    - Practical Steps or Exercises: Suggest hands-on activities or steps for learning.
    - Further Reading/Resources: Recommend additional references (books, articles, videos).
    Output the content as HTML with sections clearly formatted:
    - Use <h3> for section headings (e.g., <h3>Introduction</h3>).
    - Use <p> for paragraphs.
    - Use <ul> and <li> for lists where applicable.
    - Use <strong> for emphasis instead of **.
    Example output:
    <h3>Introduction</h3>
    <p>An overview of {topic} in the Web3 context.</p>
    <h3>Key Concepts</h3>
    <ul>
        <li><strong>Concept 1:</strong> Explanation here.</li>
        <li><strong>Concept 2:</strong> Explanation here.</li>
    </ul>
    <h3>Examples</h3>
    <p>Example 1 description.</p>
    <h3>Practical Steps or Exercises</h3>
    <ol>
        <li>Step 1 description.</li>
        <li>Step 2 description.</li>
    </ol>
    <h3>Further Reading/Resources</h3>
    <ul>
        <li><a href='https://example.com'>Resource 1</a></li>
        <li>Book: Title by Author</li>
    </ul>
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
        return f"""
        <h3>Introduction</h3>
        <p>Failed to generate content for {topic} due to API error.</p>
        <h3>Key Concepts</h3>
        <p>N/A</p>
        <h3>Examples</h3>
        <p>N/A</p>
        <h3>Practical Steps or Exercises</h3>
        <p>Try again later.</p>
        <h3>Further Reading/Resources</h3>
        <p>Search online for {topic} resources.</p>
        """


async def generate_chat_response(message: str, user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    knowledge_level = "beginner"  # Default or fetch from user profile (e.g., user.knowledge_level)
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
      - 'beginner': Simple, encouraging language with foundational Web3 concepts.
      - 'intermediate': Practical advice with technical insights.
      - 'expert': Advanced strategies and industry trends.
    - Format the response in HTML with:
      - <h3> for section headers (e.g., "Career Advice", "Next Step").
      - <p> for paragraphs.
      - <ul> and <li> for lists of steps or tips.
      - <strong> for emphasis.
      - Links as <a href="URL">text</a>.
    - Provide a clear next step for the user to take in their Web3 career.
    """
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        html_response = response.choices[0].message.content
        # Basic sanitization to ensure valid HTML
        if not html_response.startswith("<"):
            html_response = f"<p>{html_response}</p>"
        return html_response
    except Exception as e:
        logger.error(f"Error generating chat response: {e}")
        return """
        <p>I'm here to guide you on your Web3 journey!</p>
        <p>Let’s start with the basics—Web3 is like a decentralized playground for the internet.</p>
        <h3>Next Step</h3>
        <p><strong>Explore</strong>: Check out an introductory Web3 course <a href='https://example.com'>here</a>.</p>
        """


# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, username, password)
        if not user:
            logger.warning(f"Login failed for username={username}: Incorrect username or password")
            return JSONResponse({"error": "Incorrect username or password"}, status_code=400)
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="username", value=user.username, httponly=True, secure=False, samesite="lax")
        response.set_cookie(key="user_id", value=str(user.id), httponly=True, secure=False, samesite="lax")
        logger.debug(f"User '{user.username}' (ID: {user.id}) logged in, cookies set")
        return response
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return JSONResponse({"error": "An internal error occurred during login"}, status_code=500)

@app.get("/check_login")
async def check_login(request: Request, db: Session = Depends(get_db)):
    try:
        username = request.cookies.get("username")
        user_id = request.cookies.get("user_id")
        logger.debug(f"Check login - Cookies: username={username}, user_id={user_id}")
        if not username or not user_id:
            return JSONResponse({"authenticated": False}, status_code=401)
        user_id_int = int(user_id)
        user = db.query(User).filter(User.username == username, User.id == user_id_int).first()
        if not user:
            return JSONResponse({"authenticated": False}, status_code=401)
        return JSONResponse({"authenticated": True, "user_id": user.id, "username": user.username})
    except ValueError:
        logger.error(f"Invalid user_id format in check_login: {user_id}")
        return JSONResponse({"authenticated": False}, status_code=401)
    except Exception as e:
        logger.error(f"Error in check_login: {str(e)}")
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        if db.query(User).filter(User.username == username).first():
            return JSONResponse({"error": "Username already registered"}, status_code=400)
        if db.query(User).filter(User.email == email).first():
            return JSONResponse({"error": "Email already registered"}, status_code=400)

        hashed_password = get_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.add(new_user)
        db.commit()
        return templates.TemplateResponse("success.html", {"request": request}, status_code=201)
    except Exception as e:
        logger.error(f"Error in register: {str(e)}")
        return JSONResponse({"error": "An internal error occurred during registration"}, status_code=500)


@app.get("/logout")
async def logout(request: Request):
    try:
        response = RedirectResponse(url="/", status_code=303)
        response.delete_cookie("username", samesite="lax")
        response.delete_cookie("user_id", samesite="lax")
        logger.debug("User logged out, cookies cleared")
        return response
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return JSONResponse({"error": "An internal error occurred during logout"}, status_code=500)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    init_courses(db)  # Initialize courses if not already done
    
    total_courses = db.query(LearningPath).count()
    completed_courses = db.query(LearningPath).join(TopicProgress).filter(
        TopicProgress.completed == True
    ).distinct().count()
    
    user_progress = {
        "completed_courses": completed_courses,
        "total_courses": total_courses,
        "time_spent": user.time_spent or 0,
        "xp_points": user.xp_points or 100,
        "badges": json.loads(user.badges) if user.badges else []
    }
    try:
        career_paths = db.query(CareerPath).all()
        learning_paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
        learning_path_summaries = []
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
        for lp in learning_paths:
            topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == lp.id).all()
            total_topics = len(topics)
            completed_topics = sum(1 for topic in topics if topic.completed)
            progress_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0
            learning_path_summaries.append({
                "id": lp.id,
                "name": lp.name or f"Learning Path #{lp.id}",
                "created_at": lp.created_at,
                "total_topics": total_topics,
                "completed_topics": completed_topics,
                "progress_percentage": progress_percentage
            })
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "wallet_connected": bool(user),
            "user": user,
            "career_paths": career_paths,
            "learning_paths": result["learning_paths"],
            "learning_paths": learning_path_summaries
        })
    except Exception as e:
        logger.error(f"Error in dashboard_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.post("/generate_learning_path")
async def generate_learning_path(input_data: LearningPathInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        logger.debug(f"Generating learning path for user: {user.username}, ID: {user.id}")
        logger.debug(f"Input data: {input_data.dict()}")

        course_outline = await generate_course_outline(
            input_data.knowledge_level,
            input_data.path_subject,
            input_data.weekly_hours,
            input_data.learning_style
        )
        logger.debug(f"Generated course outline: {course_outline}")

        learning_path = LearningPath(
            user_id=user.id,
            name=f"{input_data.path_subject} Path",
            course_outline=json.dumps(course_outline)
        )
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
    except HTTPException as e:
        logger.warning(f"HTTPException in generate_learning_path: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in generate_learning_path: {str(e)}")
        return JSONResponse({"error": f"Failed to generate learning path: {str(e)}"}, status_code=500)

# Generate Roadmap for Career Path
@app.get("/generate_roadmap/{career_id}/{user_id}")
async def generate_roadmap(career_id: int, user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if user_id != user.id:
            logger.warning(f"Unauthorized roadmap generation attempt: user_id={user_id}, authenticated user_id={user.id}")
            return JSONResponse({"error": "Unauthorized"}, status_code=403)

        career_path = db.query(CareerPath).filter(CareerPath.id == career_id).first()
        if not career_path:
            logger.warning(f"Career path not found: career_id={career_id}")
            return JSONResponse({"error": "Invalid career path"}, status_code=404)

        career_name = career_path.name
        course_outline = await generate_course_outline("intermediate", career_name)

        learning_path = LearningPath(user_id=user_id, name=f"{career_name} Path", course_outline=json.dumps(course_outline))
        db.add(learning_path)
        db.commit()
        db.refresh(learning_path)

        for topic in course_outline:
            topic_progress = TopicProgress(
                learning_path_id=learning_path.id,
                topic_name=topic["topic"],
                abstract=topic["abstract"],
                estimated_time=topic["estimated_time"],
                content_type=topic.get("content_type", "video")
            )
            db.add(topic_progress)
        db.commit()

        return RedirectResponse(url=f"/roadmap/{learning_path.id}", status_code=303)
    except HTTPException as e:
        logger.warning(f"HTTPException in generate_roadmap: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in generate_roadmap: {str(e)}")
        return JSONResponse({"error": f"Failed to generate roadmap: {str(e)}"}, status_code=500)

# Display Roadmap
@app.get("/roadmap/{learning_path_id}", response_class=HTMLResponse)
async def roadmap_page(request: Request, learning_path_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
        if not learning_path:
            logger.warning(f"Learning path not found: learning_path_id={learning_path_id}, user_id={user.id}")
            return JSONResponse({"error": "Learning path not found"}, status_code=404)

        course_outline = json.loads(learning_path.course_outline)
        topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == learning_path.id).all()
        return templates.TemplateResponse("roadmap.html", {
            "request": request,
            "user": user,
            "learning_path": learning_path,
            "course_outline": course_outline,
            "topics": topics
        })
    except HTTPException as e:
        logger.warning(f"HTTPException in roadmap_page: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in roadmap_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

#The corrected code replaces the outdated `openai.ChatCompletion.create` call with the correct `client.chat.completions.create` method for all OpenAI interactions, ensuring compatibility with the OpenRouter API.


@app.post("/api/update_time_spent")
async def update_time_spent(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        time = data.get('time', 0)
        user.time_spent = user.time_spent + time if user.time_spent else time
        db.commit()
        return {"status": "success", "time_spent": user.time_spent}
    except Exception as e:
        logger.error(f"Error updating time spent: {e}")
        raise HTTPException(status_code=500, detail="Failed to update time spent")

# Fallback for /roadmap without learning_path_id
@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap_fallback(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "career_paths": db.query(CareerPath).all(),
            "user": user,
            "learning_paths": [
                {
                    "id": lp.id,
                    "name": lp.name,
                    "progress_percentage": sum(1 for tp in db.query(TopicProgress).filter(TopicProgress.learning_path_id == lp.id, TopicProgress.completed).all()) / len(json.loads(lp.course_outline)) * 100 if json.loads(lp.course_outline) else 0
                } for lp in db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
            ],
            "error_message": "Please select a career path or generate a learning path to view a roadmap."
        })
    except Exception as e:
        logger.error(f"Error in roadmap_fallback: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.get("/course/{learning_path_id}/{module_index}}")
async def get_course_content(learning_path_id: int, topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id, TopicProgress.learning_path_id == learning_path_id).first()
        if not topic or topic.learning_path.user_id != user.id:
            logger.warning(f"Topic not found or unauthorized: topic_id={topic_id}, learning_path_id={learning_path_id}, user_id={user.id}")
            return JSONResponse({"error": "Topic not found or unauthorized"}, status_code=404)
        if not topic.detailed_content:
            topic.detailed_content = await generate_detailed_content(topic.topic_name, topic.content_type)
            db.commit()
        return {"topic": topic.topic_name, "content": topic.detailed_content}
    except HTTPException as e:
        logger.warning(f"HTTPException in get_course_content: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in get_course_content: {str(e)}")
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)

# Display Course Page for a Specific Topic
@app.get("/course/{learning_path_id}/{module_index}", response_class=HTMLResponse)
async def course_page(request: Request, learning_path_id: int, module_index: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
        if not learning_path:
            logger.warning(f"Learning path not found: learning_path_id={learning_path_id}, user_id={user.id}")
            return JSONResponse({"error": "Learning path not found"}, status_code=404)

        course_outline = json.loads(learning_path.course_outline)
        if module_index < 0 or module_index >= len(course_outline):
            logger.warning(f"Module index out of range: module_index={module_index}, course_outline_length={len(course_outline)}")
            return JSONResponse({"error": "Module not found"}, status_code=404)

        topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == learning_path.id).all()
        if not topics or module_index >= len(topics):
            logger.warning(f"Insufficient topics for module_index: module_index={module_index}, topics_count={len(topics)}")
            return JSONResponse({"error": "Module not found"}, status_code=404)

        selected_topic = topics[module_index]
        if not selected_topic.detailed_content:
            logger.debug(f"Generating detailed content for topic_id={selected_topic.id}, topic_name={selected_topic.topic_name}")
            detailed_content = await generate_detailed_content(selected_topic.topic_name, selected_topic.content_type)
            selected_topic.detailed_content = detailed_content
            db.commit()
            logger.debug(f"Detailed content saved for topic_id={selected_topic.id}")
        else:
            detailed_content = selected_topic.detailed_content

        return templates.TemplateResponse("course.html", {
            "request": request,
            "user": user,
            "learning_path": learning_path,
            "course_outline": course_outline,
            "topics": topics,
            "selected_topic": selected_topic,
            "module_index": module_index,
            "detailed_content": detailed_content
        })
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/", status_code=303)  # Redirect to login on 401
        logger.warning(f"HTTPException in course_page: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in course_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

# Update Topic Progress and Adjust Learning Path
@app.post("/update_topic_progress")
async def update_topic_progress(data: TopicFeedback, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        topic = db.query(TopicProgress).filter(TopicProgress.id == data.topic_id, TopicProgress.learning_path.has(user_id=user.id)).first()
        if not topic:
            logger.warning(f"Topic not found: topic_id={data.topic_id}, user_id={user.id}")
            return JSONResponse({"error": "Topic not found"}, status_code=404)

        # Update topic progress
        topic.completed = True
        topic.completion_date = datetime.utcnow().isoformat()
        if data.performance_score is not None:
            topic.performance_score = data.performance_score
        if data.feedback:
            topic.feedback = data.feedback
        db.commit()

        # If new interest specified, adjust the learning path
        if data.new_interest:
            learning_path = topic.learning_path
            course_outline = json.loads(learning_path.course_outline)
            prompt = f"""
            The user has expressed a new interest in '{data.new_interest}'.
            Adjust the existing course outline by adding 1-2 new topics related to this interest.
            Current course outline: {json.dumps(course_outline)}.
            Output the updated course outline as a JSON array of objects, each with 'topic' (string), 'abstract' (string), 'estimated_time' (string), and 'content_type' (string) fields.
            Example output:
            [
                {{"topic": "Intro to {data.new_interest}", "abstract": "Overview of {data.new_interest}.", "estimated_time": "2 hours", "content_type": "video"}},
                {{"topic": "Advanced {data.new_interest}", "abstract": "Deep dive into {data.new_interest} concepts.", "estimated_time": "3 hours", "content_type": "video"}}
            ]
            """
            try:
                response = client.chat.completions.create(
                    model="deepseek/deepseek-r1:free",
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30
                )
                logger.debug(f"Raw response from OpenRouter: {response.choices[0].message.content}")
                new_topics = json.loads(response.choices[0].message.content)
            except openai.OpenAIError as e:
                logger.error(f"OpenRouter API error while adjusting course outline: {e}")
                return JSONResponse({"error": f"Failed to adjust learning path: {str(e)}"}, status_code=500)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenRouter response as JSON: {e}")
                return JSONResponse({"error": "Failed to adjust learning path: Invalid response format from OpenRouter"}, status_code=500)

            # Update learning path with new topics
            course_outline.extend(new_topics)
            learning_path.course_outline = json.dumps(course_outline)
            db.commit()

            # Add new topics to topic progress
            for new_topic in new_topics:
                topic_progress = TopicProgress(
                    learning_path_id=learning_path.id,
                    topic_name=new_topic["topic"],
                    abstract=new_topic["abstract"],
                    estimated_time=new_topic["estimated_time"],
                    content_type=new_topic["content_type"]
                )
                db.add(topic_progress)
            db.commit()

        return {"message": "Topic progress updated"}
    except HTTPException as e:
        logger.warning(f"HTTPException in update_topic_progress: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in update_topic_progress: {str(e)}")
        return JSONResponse({"error": f"Failed to update topic progress: {str(e)}"}, status_code=500)

@app.get("/quiz/{topic_id}")
async def get_quiz(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id).first()
        if not topic or topic.learning_path.user_id != user.id:
            logger.warning(f"Topic not found or unauthorized: topic_id={topic_id}, user_id={user.id}")
            return JSONResponse({"error": "Topic not found or unauthorized"}, status_code=404)
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
    except HTTPException as e:
        logger.warning(f"HTTPException in get_quiz: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in get_quiz: {str(e)}")
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)


@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request, topic_id: int = None, learning_path_id: int = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        exam_mode = False
        topic = None
        questions = []
        if topic_id:
            topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id, TopicProgress.learning_path.has(user_id=user.id)).first()
            if not topic:
                logger.warning(f"Topic not found or unauthorized: topic_id={topic_id}, user_id={user.id}")
                return JSONResponse({"error": "Topic not found or unauthorized"}, status_code=404)
            questions = [
                {"text": f"What is a key concept in {topic.topic_name.lower()}?", "options": ["Option A", "Option B", "Option C", "Option D"], "correct_answer": "Option A"},
                {"text": f"How does {topic.topic_name.lower()} relate to Web3?", "options": ["Option X", "Option Y", "Option Z", "Option W"], "correct_answer": "Option Y"}
            ]
        elif learning_path_id:
            exam_mode = True
            learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
            if not learning_path:
                logger.warning(f"Learning path not found: learning_path_id={learning_path_id}, user_id={user.id}")
                return JSONResponse({"error": "Learning path not found"}, status_code=404)
            topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == learning_path_id).all()
            if not all(topic.completed for topic in topics):
                logger.warning(f"Exam mode denied: Not all topics completed for learning_path_id={learning_path_id}")
                return JSONResponse({"error": "Complete all modules before taking the exam"}, status_code=403)
            questions = [
                {"text": "Comprehensive question on Web3 concepts", "options": ["A", "B", "C", "D"], "correct_answer": "A"},
                {"text": "Advanced topic application", "options": ["X", "Y", "Z", "W"], "correct_answer": "Y"}
            ]

        return templates.TemplateResponse("quiz.html", {
            "request": request,
            "user": user,
            "topic": topic,
            "questions": questions,
            "learning_path_id": learning_path_id,
            "exam_mode": exam_mode
        })
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/", status_code=303)
        logger.warning(f"HTTPException in quiz_page: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in quiz_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.post("/submit_quiz/{topic_id}")
async def submit_quiz(topic_id: int, answer: QuizAnswer, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id).first()
        if not topic or topic.learning_path.user_id != user.id:
            logger.warning(f"Topic not found or unauthorized: topic_id={topic_id}, user_id={user.id}")
            return JSONResponse({"error": "Topic not found or unauthorized"}, status_code=404)
        quiz_data = await get_quiz(topic_id, user, db)
        if answer.question_index < 0 or answer.question_index >= len(quiz_data["questions"]):
            logger.warning(f"Invalid question index: question_index={answer.question_index}")
            return JSONResponse({"error": "Invalid question index"}, status_code=400)
        correct_answer = quiz_data["questions"][answer.question_index]["correct_answer"]
        if answer.answer == correct_answer:
            topic.completed = True
            topic.completion_date = datetime.utcnow().isoformat()
            db.commit()
            return {"message": "Correct! Moving to next question." if answer.question_index < len(quiz_data["questions"]) - 1 else "Quiz completed!"}
        return {"message": "Incorrect. Try again."}
    except HTTPException as e:
        logger.warning(f"HTTPException in submit_quiz: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in submit_quiz: {str(e)}")
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)

# Progress
@app.get("/progress", response_class=HTMLResponse)
async def get_progress(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        progress = db.query(Progress).filter(Progress.user_id == user.id).all()
        learning_paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
        progress_data = []
        for lp in learning_paths:
            topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == lp.id).all()
            completed_topics = sum(1 for topic in topics if topic.completed)
            total_topics = len(topics)
            progress_data.append({
                "learning_path_name": lp.name or f"Learning Path #{lp.id}",
                "total_topics": total_topics,
                "completed_topics": completed_topics,
                "progress_percentage": (completed_topics / total_topics * 100) if total_topics > 0 else 0
            })
        return templates.TemplateResponse("progress.html", {
            "request": request,
            "progress": progress,
            "progress_data": progress_data,
            "user": user
        })
    except Exception as e:
        logger.error(f"Error in get_progress: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.get("/wishlist")
async def get_wishlist(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if user_id != user.id:
            logger.warning(f"Unauthorized wishlist access attempt: user_id={user_id}, authenticated user_id={user.id}")
            return JSONResponse({"error": "Unauthorized"}, status_code=403)
        return [{"name": "Intro to Web3", "id": 1}, {"name": "Intro to AI", "id": 2}]
    except HTTPException as e:
        logger.warning(f"HTTPException in get_wishlist: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in get_wishlist: {str(e)}")
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    connections[user_id] = websocket
    await websocket.send_text(json.dumps({"message": "💬 Welcome! Ask any Web3-related question."}))

    history = db.query(ChatHistory).filter(ChatHistory.user_id == int(user_id)).order_by(ChatHistory.timestamp).all()
    for chat in history:
        await websocket.send_text(json.dumps({"chat_history": {"message": chat.message, "response": chat.response}}))

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"WebSocket connection rejected: User ID {user_id} not found")
            await websocket.close(code=1008)
            return
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
    finally:
        connections.pop(user_id, None)

@app.get("/chat_history")
async def get_chat_history(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        logger.debug(f"Fetching chat history for user_id={user_id}, authenticated user_id={user.id}")
        if user_id != user.id:
            logger.warning(f"Unauthorized access attempt: user_id={user_id} does not match authenticated user_id={user.id}")
            return JSONResponse({"error": "Unauthorized"}, status_code=403)

        history = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
        return [{"message": h.message, "response": h.response} for h in history]
    except HTTPException as e:
        logger.warning(f"HTTPException in get_chat_history: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)

# HTML Rendering Routes
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user: User = Depends(get_current_user)):
    try:
        return templates.TemplateResponse("chat.html", {"request": request, "user": user})
    except Exception as e:
        logger.error(f"Error in chat_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)


# Load environment variables
@app.get("/simulator", response_class=HTMLResponse)
async def simulator_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("simulator.html", {
        "request": request,
        "user": user
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user
    })

@app.post("/api/update_theme")
async def update_theme(theme: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user.theme_preference = theme.get("theme", "light")
        db.commit()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        raise HTTPException(status_code=500, detail="Failed to update theme")

@app.post("/api/save_notes")
async def save_notes(notes: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user.notes = notes.get("notes", "")
        db.commit()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error saving notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to save notes")

@app.post("/api/start_learning_path")
async def start_learning_path(level: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        path_name = f"{level['level'].capitalize()} Path"
        course_outline = await generate_course_outline(level['level'], "Web3", "5", "interactive_labs")
        learning_path = LearningPath(user_id=user.id, name=path_name, course_outline=json.dumps(course_outline))
        db.add(learning_path)
        db.commit()
        db.refresh(learning_path)
        return RedirectResponse(url=f"/roadmap/{learning_path.id}", status_code=303)
    except Exception as e:
        logger.error(f"Error starting learning path: {e}")
        return JSONResponse({"error": "Failed to start learning path"}, status_code=500)

#Run the FastAPI App
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)