from fastapi import FastAPI, Depends, HTTPException, Request, Form, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Boolean, Float, DateTime
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
import re
import random


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
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "https://inextai.vercel.app"],  # Match frontend origin allowing multiple origin #### very useless
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


###########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#######
# OpenRouter API Key and Client Setup
OPENROUTER_API_KEY = ""#"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"
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",  # Ensure correct base URL
    api_key=OPENROUTER_API_KEY,
)





#python -m uvicorn bbb:app --reload --log-level debug


# Database Setup
DATABASE_URL = "sqlite:////tmp/web3ai.db" if os.getenv("VERCEL") else "sqlite:///./web3ai.db"

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
    progress = relationship("Progress", back_populates="user")  # Added relationship
    chat_sessions = relationship("ChatSession", back_populates="user")
    

class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=True)
    course_outline = Column(Text, nullable=False)  # JSON string of course outline
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    user = relationship("User", back_populates="learning_paths")
    topics = relationship("TopicProgress", back_populates="learning_path")
    exam_score = Column(Integer, default=0)
    exam_total = Column(Integer, default=0)
    exam_completed = Column(Boolean, default=False)
    learning_style = Column(String, default="articles")  # Store the style
    course_outline = Column(String)
    exam_badge_png_path = Column(String, nullable=True)
    exam_badge_pdf_path = Column(String, nullable=True)
    certificate_pdf_path = Column(String, nullable=True)

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
    completion_date = Column(DateTime)
    performance_score = Column(Float, nullable=True)
    temp_score = Column(Integer, default=0)  # Persistent field
    temp_total = Column(Integer, default=0)  # Persistent field
    badge_png_path = Column(String, nullable=True)
    badge_pdf_path = Column(String, nullable=True)
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

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=True)  # e.g., "NFT Chat 2025-03-22"
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    messages = relationship("ChatHistory", back_populates="session")
    user = relationship("User", back_populates="chat_sessions")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(String, default=lambda: datetime.utcnow().isoformat())
    user = relationship("User", back_populates="chat_history")
    session = relationship("ChatSession", back_populates="messages")

class Examt(Base):
    __tablename__ = "exam_ts"
    id = Column(Integer, primary_key=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float)
    completion_date = Column(String)

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


def extract_json(response_text):
    """
    Extracts JSON content from AI response, handling cases where JSON is inside code blocks or plain text.
    """
    try:
        # ✅ Use regex to find JSON inside triple backticks (handles ` ```json ... ``` `)
        match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)

        if match:
            json_content = match.group(1).strip()  # Extract JSON part
            return json_content  # ✅ Found JSON inside backticks

        # ✅ If no backticks, check if the whole response is already a valid JSON string
        response_text = response_text.strip()  # Remove extra whitespace
        if response_text.startswith("[") and response_text.endswith("]"):  # Likely a JSON array
            return response_text  # ✅ Treat entire response as JSON

        raise ValueError("No valid JSON block found in AI response.")  # If nothing works, raise an error
    
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        return None
    

# Helper Functions
async def generate_course_outline(knowledge_level: str, path_subject: str, weekly_hours: str = "5", learning_style: str = "video"):
    try:
        # Parse weekly_hours
        if "-" in weekly_hours:
            low, high = map(int, weekly_hours.split("-"))
            avg_hours = (low + high) / 2
        else:
            avg_hours = int(weekly_hours)
    except Exception as e:
        logger.error(f"Error parsing weekly_hours: {e}")
        avg_hours = 5

    # Define topic count ranges based on knowledge level
    topic_ranges = {
        "beginner": (10, 15),
        "intermediate": (15, 18),
        "expert": (18, 25)
    }
    min_topics, max_topics = topic_ranges.get(knowledge_level, (10, 15))
    total_topics = random.randint(min_topics, max_topics)

    # Map knowledge level to description
    level_description = {
        "beginner": "a toddler with basic knowledge",
        "intermediate": "a junior professional with practical experience",
        "expert": "an advanced professional with high expertise"
    }
    level_context = level_description.get(knowledge_level, "a learner with unknown level")

    # Capitalize learning style for title consistency
    style_title = learning_style.capitalize()

    # Define content type and prompt based on learning style
    if learning_style == "video":
        content_type = "video-based lessons with visual explanations"
        prompt = f"""
        You are a career coach specializing in Web3, mentoring {level_context} interested in '{path_subject}' within the Web3 domain.
        - The learner can dedicate {avg_hours} hours per week, so adjust the pace and depth accordingly.
        - The learner prefers {content_type}, so structure the course as video content.
        - Create a tailored course outline with exactly {total_topics} main topics, each reflecting '{path_subject}' and suitable for {level_context}.
        - Adjust complexity and depth based on the learner's level:
          - 'beginner': Simple explanations, foundational concepts.
          - 'intermediate': Practical applications, some technical depth.
          - 'expert': In-depth technical details, advanced use cases.
        - For each main topic, provide:
          - 'topic' (main topic title)
          - 'description' (short overview of the topic)
          - 'subtopics' (array of 2-3 video lessons, each with):
            - 'title' (subtopic title)
            - 'description' (short description)
            - 'url' (placeholder YouTube URL like 'https://www.example-youtube.com/watch?v=...')
            - 'summary' (brief summary of the video content)
            - 'transcript' (short sample transcript starting with 'Welcome to...')
        - Ensure the response is a valid JSON array **without any additional text**.
        """
    elif learning_style == "interactive_labs":
        content_type = "hands-on interactive labs and exercises"
        prompt = f"""
        You are a career coach specializing in Web3, mentoring {level_context} interested in '{path_subject}' within the Web3 domain.
        - The learner can dedicate {avg_hours} hours per week, so adjust the pace and depth accordingly.
        - The learner prefers {content_type}, so structure the course as interactive, hands-on labs.
        - Create a tailored course outline with exactly {total_topics} topics, each reflecting '{path_subject}' and suitable for {level_context}.
        - Adjust complexity and depth based on the learner's level:
          - 'beginner': Simple tasks, foundational skills.
          - 'intermediate': Practical projects, moderate complexity.
          - 'expert': Advanced challenges, real-world applications.
        - For each topic, provide:
          - 'topic' (title)
          - 'abstract' (short description with career advice)
          - 'estimated_time' (duration like '2 hours')
          - 'content_type' (set to 'interactive_labs')
          - 'career_advice' (actionable steps)
          - 'tasks' (array of 1-3 hands-on examples, each with 'title', 'tool', 'outcome')
        - Ensure the response is a valid JSON array **without any additional text**.
        """
    else:  # Default to articles
        content_type = "text-based articles and readings"
        prompt = f"""
        You are a career coach specializing in Web3, mentoring {level_context} interested in '{path_subject}' within the Web3 domain.
        - The learner can dedicate {avg_hours} hours per week, so adjust the pace and depth accordingly.
        - The learner prefers {content_type}, so prioritize this format in the course structure.
        - Create a tailored course outline with exactly {total_topics} topics, each reflecting '{path_subject}' and suitable for {level_context}.
        - Adjust complexity and depth based on the learner's level:
          - 'beginner': Simple explanations, foundational concepts.
          - 'intermediate': Practical applications, some technical depth.
          - 'expert': In-depth technical details, advanced use cases.
        - For each topic, provide:
          - 'topic' (title)
          - 'abstract' (short description with career advice)
          - 'estimated_time' (duration like '2 hours')
          - 'content_type' (set to 'articles')
          - 'career_advice' (actionable steps)
        - Ensure the response is a valid JSON array **without any additional text**.
        """

    # Call the AI service with fallback
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            # timeout=30,
            # max_tokens=800  # Prevents truncation
        )

        raw_response = response.choices[0].message.content
        print("Raw AI Response:", raw_response)
        logger.debug(f"Raw response from AI: {raw_response}")

        # ✅ Extract JSON content from AI response
        json_data = extract_json(raw_response)
        if not json_data:
            raise ValueError("AI response did not contain valid JSON.")

        # ✅ Ensure JSON is valid before parsing
        course_outline = json.loads(json_data)
        for item in course_outline:
            if "title" in item and "topic" not in item:
                item["topic"] = item.pop("title")
            return course_outline

        # ✅ Validate topic structure
        if not isinstance(course_outline, list):
            raise ValueError("AI response is not a valid JSON list.")

        if len(course_outline) < min_topics or len(course_outline) > max_topics:
            raise ValueError(f"Expected {min_topics}-{max_topics} topics, but got {len(course_outline)}.")

        for topic in course_outline:
            if not all(k in topic for k in ["topic", "abstract", "estimated_time", "content_type"]):
                raise ValueError("Response is missing required fields in topics.")
            if "title" in item and "topic" not in item:
                item["topic"] = item.pop("title")

        return {
            "name": f"{path_subject} - {style_title}",  # e.g., "Web3 - Video"
            "topics": course_outline
        }

    except json.JSONDecodeError:
        logger.error("Error: The response is not valid JSON.")
        return {"error": "Invalid JSON format received from AI"}
    
    except Exception as e:
        logger.error(f"Error generating course outline with AI: {e}")
        
        # Fallback generation
        fallback_outline = []
        for i in range(total_topics):
            topic_name = f"{path_subject} Topic {i + 1}"
            abstract = f"Explore a key aspect of {path_subject}."
            
            if learning_style == "video":
                fallback_outline.append({
                    "topic": topic_name,
                    "description": f"Learn about {path_subject} through video content.",
                    "subtopics": [
                        {
                            "title": f"{topic_name} - Part 1",
                            "description": f"A basic introduction to {path_subject}.",
                            "url": "https://www.example-youtube.com/watch?v=fallback123",
                            "summary": f"A simple overview of {path_subject}.",
                            "transcript": f"Welcome to this fallback video on {path_subject}..."
                        },
                        {
                            "title": f"{topic_name} - Part 2",
                            "description": f"Key concepts in {path_subject}.",
                            "url": "https://www.example-youtube.com/watch?v=fallback456",
                            "summary": f"Explains a core idea in {path_subject}.",
                            "transcript": f"Welcome to part two of {path_subject}..."
                        }
                    ]
                })
            elif learning_style == "interactive_labs":
                fallback_outline.append({
                    "topic": topic_name,
                    "abstract": abstract,
                    "estimated_time": "2 hours",
                    "content_type": "interactive_labs",
                    "career_advice": f"Practice {path_subject} skills with a simple project.",
                    "tasks": [
                        {
                            "title": f"Try a {path_subject} Task",
                            "tool": "Basic Tool",
                            "outcome": f"Understand a {path_subject} concept."
                        },
                        {
                            "title": f"Build a {path_subject} Example",
                            "tool": "Fallback IDE",
                            "outcome": f"Create a simple {path_subject} output."
                        }
                    ]
                })
            else:  # Articles
                fallback_outline.append({
                    "topic": topic_name,
                    "abstract": abstract,
                    "estimated_time": "2 hours",
                    "content_type": "articles",
                    "career_advice": f"Read more about {path_subject} to deepen your understanding."
                })
        
        logger.debug(f"Generated fallback outline with {total_topics} topics for {learning_style}")
        return fallback_outline
    



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
    I am InextAI, your **dedicated Web3 career coach** and interactive guide. Whether you're just starting out or deep into the Web3 space, I’m here to **help you grow, refine your skills, and advance your career.** Let's explore together! 🚀

    🔹 **Your Profile**: You are a {level_context} interested in Web3.  
    🔹 **Your Message**: "{message}"  
    🔹 **Let's craft a personalized response that is informative, engaging, and actionable!**  

    ---  

    <h3>📌 Understanding Your Question</h3>  
    <p><strong>Here's what I gathered from your message:</strong> I'll break it down and provide a response that fits your expertise level.</p>  
    <p><strong>Before we proceed:</strong> Would you like a **concise** or **detailed** explanation? Also, are you looking for **theory, hands-on projects,** or **career advice**?</p>  

    ---  

    <h3>💡 Personalized Career Guidance</h3>  
    <p>Based on your level, I'll adjust my response:</p>  
    <ul>
        <li><strong>Beginner:</strong> I'll use **simple explanations & relatable analogies** to introduce Web3 concepts in a fun, engaging way.</li>
        <li><strong>Intermediate:</strong> Let's dive into **practical applications, hands-on projects, and technical insights.**</li>
        <li><strong>Expert:</strong> I'll share **cutting-edge trends, advanced strategies, and industry best practices** to elevate your expertise.</li>
    </ul>  

    ---  

    <h3>🚀 Actionable Next Steps</h3>  
    <p>To help you **apply** what you've learned, here are some next steps:</p>  
    <ul>
        <li>📚 **Read:** <a href="https://web3foundation.org/">Web3 Foundation</a> for core Web3 concepts.</li>
        <li>🛠 **Build:** Try a small project on **Ethereum, Solana, or Polkadot**.</li>
        <li>🎯 **Connect:** Join Web3 communities like **Bankless DAO** or **r/Web3**.</li>
        <li>📝 **Certify:** Consider a Web3 certification like <a href="https://academy.moralis.io/">Moralis Academy</a>.</li>
    </ul>  

    ---  

    <h3>🤔 What’s Next?</h3>  
    <p>Would you like to dive deeper into **a specific area** (e.g., Smart Contracts, NFTs, DAOs, DeFi)?</p>  
    <p><strong>Or perhaps you need help with a project or a job search?</strong> Let me know how I can assist you further! 😊</p>  
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
        # Check if username or email already exists
        if db.query(User).filter(User.username == username).first():
            return JSONResponse({"error": "Username already registered"}, status_code=400)
        if db.query(User).filter(User.email == email).first():
            return JSONResponse({"error": "Email already registered"}, status_code=400)

        # Hash password and create user
        hashed_password = get_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.add(new_user)
        db.commit()

        # ✅ Return JSON instead of redirecting (prevents 405 errors)
        return JSONResponse({"message": "Registration successful! Please login."}, status_code=201)

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
    try:
        career_paths = db.query(CareerPath).all()
        learning_paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
        learning_path_summaries = []
        t = {
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
            "learning_paths": t["learning_paths"],
            "learning_paths": learning_path_summaries
        })
    except Exception as e:
        logger.error(f"Error in dashboard_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)


@app.delete("/delete_learning_path/{learning_path_id}")
async def delete_learning_path(learning_path_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lp = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Learning path not found")
    db.delete(lp)
    db.commit()
    return {"message": "Learning path deleted"}


@app.post("/generate_learning_path")
async def generate_learning_path(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        data = await request.json()
        knowledge_level = data.get("knowledge_level", "beginner")
        path_subject = data["path_subject"]
        weekly_hours = data.get("weekly_hours", "5")
        learning_style = data.get("learning_style", "articles")

        # Generate course outline
        course_outline = await generate_course_outline(knowledge_level, path_subject, weekly_hours, learning_style)

        # Create learning path
        learning_path = LearningPath(
            user_id=user.id,
            learning_style=learning_style,
            name=path_subject +" - " + learning_style,
            course_outline=json.dumps(course_outline)
        )
        db.add(learning_path)
        db.commit()
        logger.debug(f"Created learning path with ID: {learning_path.id}")

        # Process topics with normalized key
        for topic in course_outline:
            topic_progress = TopicProgress(
                learning_path_id=learning_path.id,
                topic_name=topic["topic"],  # Now consistent across all styles
                completed=False
            )
            db.add(topic_progress)
        
        db.commit()
        return {"message": "Learning path generated", "learning_path_id": learning_path.id}
    except Exception as e:
        logger.error(f"Error in generate_learning_path: {str(e)}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate learning path: {str(e)}"}
        )
    

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
        # style_title = input.learning_style.capitalize()
        course_outline = await generate_course_outline("intermediate", career_name)

        learning_path = LearningPath(user_id=user_id, name=f"{career_name}", course_outline=json.dumps(course_outline))
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
    learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
    if not learning_path:
        return JSONResponse({"error": "Learning path not found"}, status_code=404)
    
    # Assuming course_outline is stored in learning_path.course_outline as JSON
    topics = json.loads(learning_path.course_outline) if learning_path.course_outline else []
    
    
    if not topics:
        logger.warning(f"Roadmap '{learning_path.name}' (ID: {learning_path_id}) is empty. Deleting.")
        db.delete(learning_path)
        db.commit()
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "Roadmap couldn't be generated due to empty content and has been deleted."
        }, status_code=400)
    

    # Add completion status
    topic_progress = db.query(TopicProgress).filter(TopicProgress.learning_path_id == learning_path_id).all()
    progress_dict = {tp.topic_name: tp.completed for tp in topic_progress}
    
    # Adjust for learning style
    learning_style = learning_path.learning_style  # Add this field to LearningPath model or derive it
    for topic in topics:
        if learning_style == "video":
            topic["completed"] = progress_dict.get(topic["topic"], False)
        elif learning_style == "interactive_labs":
            topic["completed"] = progress_dict.get(topic["topic"], False)
        else:  # articles
            topic["completed"] = progress_dict.get(topic["topic"], False)
    
    return templates.TemplateResponse("roadmap.html", {
        "request": request,
        "user": user,
        "learning_path": learning_path,
        "topics": topics,
        "learning_style": learning_style
    })


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
    learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
    if not learning_path:
        logger.error(f"Learning path not found: learning_path_id={learning_path_id}, user_id={user.id}")
        return JSONResponse({"error": "Learning path not found"}, status_code=404)
    
    topics = json.loads(learning_path.course_outline) if learning_path.course_outline else []
    if module_index >= len(topics):
        logger.error(f"Module index out of range: module_index={module_index}, total_topics={len(topics)}")
        return JSONResponse({"error": "Module not found"}, status_code=404)
    
    selected_topic = topics[module_index]
    topic_progress = db.query(TopicProgress).filter(
        TopicProgress.learning_path_id == learning_path_id,
        TopicProgress.topic_name == (selected_topic.get("topic") or selected_topic.get("title"))
    ).first()
    
    # Prepare selected_topic as a dictionary
    topic_data = selected_topic.copy()
    detailed_content = None
    
    if topic_progress:
        # Use existing detailed_content if available
        if topic_progress.detailed_content:
            detailed_content = topic_progress.detailed_content
        # Merge DB fields
        topic_data.update({
            "id": topic_progress.id,
            "topic_name": topic_progress.topic_name,
            "completed": topic_progress.completed,
            "completion_date": topic_progress.completion_date.isoformat() if topic_progress.completion_date else None,
            "performance_score": topic_progress.performance_score,
            "feedback": topic_progress.feedback
        })
    
    # Generate content only if not already stored
    if not detailed_content:
        detailed_content = await generate_detailed_content(selected_topic, learning_path.learning_style)
        if topic_progress:
            topic_progress.detailed_content = detailed_content
            db.commit()
        elif learning_path.learning_style != "video":  # Video doesn’t need persistent content
            new_progress = TopicProgress(
                learning_path_id=learning_path_id,
                topic_name=selected_topic.get("topic") or selected_topic.get("title"),
                detailed_content=detailed_content
            )
            db.add(new_progress)
            db.commit()
            topic_data["id"] = new_progress.id
    
    return templates.TemplateResponse("course.html", {
        "request": request,
        "learning_path": learning_path,
        "selected_topic": topic_data,
        "detailed_content": detailed_content,
        "learning_style": learning_path.learning_style,
        "module_index": module_index,
        "user": user  # Add user object to template context
    })


from jinja2 import Environment, FileSystemLoader
import re

def youtube_id(value):
    """Extract YouTube video ID from a URL."""
    match = re.search(r'youtube\.com/watch\?v=([^&]+)', value)
    if match:
        return match.group(1)
    match = re.search(r'youtu\.be/([^?]+)', value)
    if match:
        return match.group(1)
    return value  # Return original value if no match

# Setup Jinja2 environment
templates = Jinja2Templates(directory="templates")
templates.env.filters['youtube_id'] = youtube_id

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
        topic.completion_date = datetime.utcnow()
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
                {{"topic": "Intro to {data.new_interest}", "abstract": "Overview of {data.new_interest}. "estimated_time": "2 hours", "content_type": "vide",o"}},
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



FALLBACK_QUESTIONS = [
    {
        "text": "What is a blockchain?",
        "type": "multiple_choice",
        "options": ["A. A distributed ledger", "B. A type of currency", "C. A centralized database", "D. A programming language"],
        "correct_answer": "A",
        "explanation": "A blockchain is a distributed ledger that records transactions across multiple nodes."
    },
    {
        "text": "Cryptocurrencies use centralized servers.",
        "type": "true_false",
        "options": ["True", "False"],
        "correct_answer": "False",
        "explanation": "Cryptocurrencies operate on decentralized networks like blockchains."
    },
    {
        "text": "What does 'DeFi' stand for?",
        "type": "multiple_choice",
        "options": ["A. Decentralized Finance", "B. Defined Funding", "C. Digital Fiat", "D. Direct Finance"],
        "correct_answer": "A",
        "explanation": "DeFi refers to financial systems built on decentralized blockchain technology."
    },
    {
        "text": "Smart contracts require manual execution.",
        "type": "true_false",
        "options": ["True", "False"],
        "correct_answer": "False",
        "explanation": "Smart contracts execute automatically when conditions are met on the blockchain."
    },
    {
        "text": "What is an NFT?",
        "type": "multiple_choice",
        "options": ["A. Network file transfer", "B. New financial tool", "C. Non-fungible token", "D. None of these"],
        "correct_answer": "C. Non-fungible token",
        "explanation": "NFTs are unique digital assets on a blockchain, distinguishing them from fungible tokens like Bitcoin."
    },
    {
        "text": "What is a blockchain?",
        "type": "multiple_choice",
        "options": ["A. A distributed ledger", "B. A type of currency", "C. A centralized database", "D. A programming language"],
        "correct_answer": "A. A distributed ledger",
        "explanation": "A blockchain is a distributed ledger that records transactions across multiple nodes."
    }
    # Add more as needed to cover up to 50 questions
]

# Extend to at least 50 questions for exams by duplicating with slight variations
def get_fallback_questions(num_questions: int, topic_name: str = "Web3"):
    return [
        {
            "text": f"What is a key concept in {topic_name.lower()} (Q{i+1})?",
            "type": "multiple_choice",
            "options": ["A. Blockchain", "B. Centralized system", "C. Manual ledger", "D. None"],
            "correct_answer": "A",
            "explanation": f"A fallback question for {topic_name} focusing on blockchain basics."
        } if i % 2 == 0 else
        {
            "text": f"Is {topic_name.lower()} centralized? (Q{i+1})",
            "type": "true_false",
            "options": ["True", "False"],
            "correct_answer": "False",
            "explanation": f"{topic_name} operates on decentralized principles."
        } for i in range(num_questions)
    ]



# Add helper function to generate quiz questions dynamically
async def generate_quiz_questions(topic: TopicProgress, num_questions: int = 10):
    """
    Generate 8-13 quiz questions using OpenAI based on topic_name and detailed_content.
    Falls back to dynamically generated questions if API fails.
    """
    prompt = f"""
    You are a Web3 education expert. Generate {num_questions} quiz questions for the topic '{topic.topic_name}' in the Web3 domain.
    Use the following detailed content as context: {topic.detailed_content or topic.abstract}.
    - Include a mix of question types: 80% multiple-choice (4 options), 20% true/false.
    - For each question, provide:
      - 'text': The question text.
      - 'type': 'multiple_choice' or 'true_false'.
      - 'options': List of 4 options for multiple-choice, ['True', 'False'] for true/false.
      - 'correct_answer': The correct option (e.g., 'A' or 'True').
      - 'explanation': A brief explanation for the correct answer (1-2 sentences).
    - Ensure questions are relevant to Web3 and the topic’s content.
    Return the t as a JSON array.
    Example:
    [
        {{
        "text": "What is an NFT?",
        "type": "multiple_choice",
        "options": ["A. Network file transfer", "B. New financial tool", "C. Non-fungible token", "D. None of these"],
        "correct_answer": "A. Non-fungible token",
        "explanation": "NFTs are unique digital assets on a blockchain, distinguishing them from fungible tokens like Bitcoin."
        }},
        {{
            "text": "What is a blockchain?",
            "type": "multiple_choice",
            "options": ["A. A distributed ledger", "B. A type of currency", "C. A centralized database", "D. A programming language"],
            "correct_answer": "A. A distributed ledger",
            "explanation": "A blockchain is a distributed ledger that records transactions across multiple nodes."
        }},
        {{
            "text": "Cryptocurrencies use centralized servers.",
            "type": "true_false",
            "options": ["True", "False"],
            "correct_answer": "False",
            "explanation": "Cryptocurrencies operate on decentralized networks like blockchains."
        }},
        {{
            "text": "What does 'DeFi' stand for?",
            "type": "multiple_choice",
            "options": ["A. Defined Funding", "B. Decentralized Finance", "C. Digital Fiat", "D. Direct Finance"],
            "correct_answer": "B. Decentralized Finance",
            "explanation": "DeFi refers to financial systems built on decentralized blockchain technology."
        }},
        {{
            "text": "Smart contracts require manual execution.",
            "type": "true_false",
            "options": ["True", "False"],
            "correct_answer": "True",
            "explanation": "Smart contracts execute automatically when conditions are met on the blockchain."
        }}
    ]
    
    """
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        raw_response = response.choices[0].message.content
        logger.debug(f"Raw response from AI: {raw_response}")
        print("Raw AI Response:", raw_response)

        json_data = extract_json(raw_response)
        if not json_data:
            raise ValueError("AI response did not contain valid JSON.")

        questions = json.loads(json_data)
        print("Parsed AI Response:", questions)

        if not isinstance(questions, list) or len(questions) < 8:
            raise ValueError("Invalid question set generated")
        
        questions = questions[:13]  # Cap at 13
        logger.debug(f"Generated {len(questions)} questions for topic: {topic.topic_name}")
        return questions
    except Exception as e:
        logger.error(f"Error generating quiz questions: {e}")
        # fallback_questions = []
        # for i in range(num_questions):
        #     fallback_text = f"What is a basic concept related to {topic.topic_name.lower()}?"
        #     if topic.abstract:
        #         fallback_text = f"Based on the idea of '{topic.abstract[:50]}...', what is a fundamental aspect of {topic.topic_name.lower()}?"
        #     fallback_questions.append({
        #         "text": fallback_text,
        #         "type": "multiple_choice",
        #         "options": ["A. Basic Idea", "B. Another Idea", "C. Different Concept", "D. Unrelated"],
        #         "correct_answer": "A. Basic Idea",
        #         "explanation": "This is a fallback question due to an error in generating the quiz."
        #     })
        # logger.debug(f"Using fallback: {len(fallback_questions)} questions")
        # return fallback_questions
        # print(fallback_questions)
        
        # return fallback_questions
        # fallback = get_fallback_questions(num_questions, topic.topic_name)
        # logger.debug(f"Using fallback: {len(fallback)} questions")
        # return fallback
       
        return [
            {
                "text": "What is a blockchain?",
                "type": "multiple_choice",
                "options": ["A. A distributed ledger", "B. A type of currency", "C. A centralized database", "D. A programming language"],
                "correct_answer": "A. A distributed ledger",
                "explanation": "A blockchain is a distributed ledger that records transactions across multiple nodes."
            },
            {
                "text": "Cryptocurrencies use centralized servers.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation": "Cryptocurrencies operate on decentralized networks like blockchains."
            },
            {
                "text": "What does 'DeFi' stand for?",
                "type": "multiple_choice",
                "options": ["A. Decentralized Finance", "B. Defined Funding", "C. Digital Fiat", "D. Direct Finance"],
                "correct_answer": "A. Decentralized Finance",
                "explanation": "DeFi refers to financial systems built on decentralized blockchain technology."
            },
            {
                "text": "Smart contracts require manual execution.",
                "type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation": "Smart contracts execute automatically when conditions are met on the blockchain."
            },
            {
                "text": "What is an NFT?",
                "type": "multiple_choice",
                "options": ["A. Network file transfer", "B. New financial tool", "C. Non-fungible token", "D. None of these"],
                "correct_answer": "C. Non-fungible token",
                "explanation": "NFTs are unique digital assets on a blockchain, distinguishing them from fungible tokens like Bitcoin."
            },
            {
                "text": "What is a blockchain?",
                "type": "multiple_choice",
                "options": ["A. A distributed ledger", "B. A type of currency", "C. A centralized database", "D. A programming language"],
                "correct_answer": "A. A distributed ledger",
                "explanation": "A blockchain is a distributed ledger that records transactions across multiple nodes."
            }
            # Add more as needed 
        ]


# Enhanced GET /quiz/{topic_id} for topic-specific quizzes
@app.get("/quiz/{topic_id}")
async def get_quiz(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id).first()
        if not topic or topic.learning_path.user_id != user.id:
            logger.warning(f"Topic not found or unauthorized: topic_id={topic_id}, user_id={user.id}")
            return JSONResponse({"error": "Topic not found or unauthorized"}, status_code=404)
        
        # Generate 8-13 questions dynamically
        questions = await generate_quiz_questions(topic, num_questions=10)  # Default to 10 questions
        return {"topic": topic.topic_name, "questions": questions}
    except Exception as e:
        logger.error(f"Error in get_quiz: {str(e)}")
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)

# Enhanced GET /quiz for both topic quizzes and exams
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
            questions = await generate_quiz_questions(topic, num_questions=10)
        
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
            
            prompt = f"""
            Generate 18-23 quiz questions for an exam covering these Web3 topics: {', '.join(t.topic_name for t in topics)}.
            Use the combined content: {[t.detailed_content or t.abstract for t in topics]}.
            - Include a mix: 80% multiple-choice (4 options), 20% true/false.
            - For each question, provide: 'text', 'type', 'options', 'correct_answer', 'explanation'.
            Return as a JSON array.
            """
            try:
                response = client.chat.completions.create(
                    model="deepseek/deepseek-r1:free",
                    messages=[{"role": "user", "content": prompt}],
                    timeout=60
                )
                raw_response = response.choices[0].message.content
                logger.debug(f"Raw response from AI: {raw_response}")
                json_data = extract_json(raw_response)
                if not json_data:
                    raise ValueError("AI response did not contain valid JSON.")
                questions = json.loads(json_data)
                questions = questions[:21]  # Cap at 21
                logger.debug(f"Generated {len(questions)} exam questions")
            except Exception as e:
                logger.error(f"Error generating exam questions: {e}")
                fallback_questions = []
                # Use a generic topic name for exams since multiple topics are involved
                exam_topic_name = "Web3 Exam"
                for i in range(22):  # Default to 22 for exams
                    fallback_text = f"What is a basic concept related to {exam_topic_name.lower()}?"
                    if topics and topics[0].abstract:  # Use first topic’s abstract as a sample
                        fallback_text = f"Based on the idea of '{topics[0].abstract[:50]} in relation to web3 revolution...', what is a fundamental aspect of {exam_topic_name.lower()}?"
                    fallback_questions.append({
                        "text": fallback_text,
                        "type": "multiple_choice",
                        "options": ["A. Basic Idea", "B. Another Idea", "C. Different Concept", "D. Unrelated"],
                        "correct_answer": "A",
                        "explanation": "This is a fallback question due to an error in generating the exam."
                    })
                questions = fallback_questions[:21]  # Cap at 50
                logger.debug(f"Using fallback: {len(questions)} exam questions")
                # return [
                #     {
                #         "text": "What is a blockchain?",
                #         "type": "multiple_choice",
                #         "options": ["A. A distributed ledger", "B. A type of currency", "C. A centralized database", "D. A programming language"],
                #         "correct_answer": "A. A distributed ledger",
                #         "explanation": "A blockchain is a distributed ledger that records transactions across multiple nodes."
                #     },
                #     {
                #         "text": "Cryptocurrencies use centralized servers.",
                #         "type": "true_false",
                #         "options": ["True", "False"],
                #         "correct_answer": "False",
                #         "explanation": "Cryptocurrencies operate on decentralized networks like blockchains."
                #     },
                #     {
                #         "text": "What does 'DeFi' stand for?",
                #         "type": "multiple_choice",
                #         "options": ["A. Decentralized Finance", "B. Defined Funding", "C. Digital Fiat", "D. Direct Finance"],
                #         "correct_answer": "A. Decentralized Finance",
                #         "explanation": "DeFi refers to financial systems built on decentralized blockchain technology."
                #     },
                #     {
                #         "text": "Smart contracts require manual execution.",
                #         "type": "true_false",
                #         "options": ["True", "False"],
                #         "correct_answer": "False",
                #         "explanation": "Smart contracts execute automatically when conditions are met on the blockchain."
                #     },
                #     {
                #         "text": "What is an NFT?",
                #         "type": "multiple_choice",
                #         "options": ["A. Network file transfer", "B. New financial tool", "C. Non-fungible token", "D. None of these"],
                #         "correct_answer": "C. Non-fungible token",
                #         "explanation": "NFTs are unique digital assets on a blockchain, distinguishing them from fungible tokens like Bitcoin."
                #     },
                #     {
                #         "text": "What is a blockchain?",
                #         "type": "multiple_choice",
                #         "options": ["A. A distributed ledger", "B. A type of currency", "C. A centralized database", "D. A programming language"],
                #         "correct_answer": "A. A distributed ledger",
                #         "explanation": "A blockchain is a distributed ledger that records transactions across multiple nodes."
                #     }
                #     # Add more as needed 
                # ]
        
        total_questions = len(questions)
        logger.debug(f"Total questions: {total_questions}, Questions: {questions}")
        return templates.TemplateResponse("quiz.html", {
            "request": request,
            "user": user,
            "selected_topic": topic,
            "questions": questions,
            "learning_path_id": learning_path_id,
            "exam_mode": exam_mode,
            "module_index": 0,
            "total_questions": total_questions
        })
    except Exception as e:
        logger.error(f"Error in quiz_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
    




# Enhanced POST /submit_quiz/{topic_id} with scoring and feedback
@app.post("/submit_quiz/{topic_id}")
async def submit_quiz(topic_id: int, submission: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        topic = db.query(TopicProgress).filter(TopicProgress.id == topic_id, TopicProgress.learning_path.has(user_id=user.id)).first()
        if not topic:
            logger.warning(f"Topic not found or unauthorized: topic_id={topic_id}, user_id={user.id}")
            return JSONResponse({"error": "Topic not found or unauthorized"}, status_code=404)
        
        answer = submission["answer"]
        question_index = submission["question_index"]
        is_correct = submission["is_correct"]
        total_questions = submission["total_questions"]
        
        # Increment persistent fields
        topic.temp_total = (topic.temp_total or 0) + 1
        if is_correct:
            topic.temp_score = (topic.temp_score or 0) + 1
        logger.debug(f"Quiz progress: {topic.temp_score}/{topic.temp_total}")
        
        if question_index == total_questions - 1:
            performance_score = (topic.temp_score / topic.temp_total) * 100
            topic.performance_score = performance_score
            topic.completed = True
            topic.completion_date = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            # Reset progress after completion
            topic.temp_score = 0
            topic.temp_total = 0
            db.commit()
            logger.debug(f"Quiz final score calculated: {performance_score:.1f}%")
            return {
                "message": f"Quiz completed! Score: {performance_score:.1f}%",
                "final_score": float(performance_score)
            }
        
        db.commit()
        return {"message": "Next question recorded"}
    except Exception as e:
        logger.error(f"Error in submit_quiz: {str(e)}")
        return JSONResponse({"error": f"Internal error: {str(e)}"}, status_code=500)    


@app.post("/submit_exam/{learning_path_id}")
async def submit_exam(learning_path_id: int, submission: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
        if not learning_path:
            logger.warning(f"Learning path not found: learning_path_id={learning_path_id}, user_id={user.id}")
            return JSONResponse({"error": "Learning path not found"}, status_code=404)
        
        answer = submission["answer"]
        question_index = submission["question_index"]
        is_correct = submission["is_correct"]
        total_questions = submission["total_questions"]
        
        # Increment persistent fields
        learning_path.exam_total = (learning_path.exam_total or 0) + 1
        if is_correct:
            learning_path.exam_score = (learning_path.exam_score or 0) + 1
        logger.debug(f"Exam progress: {learning_path.exam_score}/{learning_path.exam_total}")
        
        if question_index == total_questions - 1:
            final_score = (learning_path.exam_score / learning_path.exam_total) * 100
            # Reset progress after completion
            learning_path.exam_score = 0
            learning_path.exam_total = 0
            learning_path.exam_completed = True  # Mark as completed
            db.commit()
            logger.debug(f"Exam final score calculated: {final_score:.1f}%")
            return {
                "message": f"Exam completed! Score: {final_score:.1f}%",
                "final_score": float(final_score)
            }
        
        db.commit()
        return {"message": "Next question recorded"}
    except Exception as e:
        logger.error(f"Error in submit_exam: {str(e)}")
        return JSONResponse({"error": f"Internal error: {str(e)}"}, status_code=500)    



@app.get("/exam", response_class=HTMLResponse)
async def exam_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        learning_paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
        learning_path_summaries = []
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
        return templates.TemplateResponse("exam.html", {
            "request": request,
            "user": user,
            "learning_paths": learning_path_summaries
        })
    except Exception as e:
        logger.error(f"Error in exam_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)


@app.get("/debug/topics")
async def debug_topics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    topics = db.query(TopicProgress).filter(TopicProgress.learning_path.has(user_id=user.id)).all()
    return [{"id": t.id, "topic_name": t.topic_name, "learning_path_id": t.learning_path_id} for t in topics]





# New endpoint to get the next uncompleted course or first module
@app.get("/course/next/{learning_path_id}")
async def get_next_course(learning_path_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
        if not learning_path:
            logger.warning(f"Learning path not found: learning_path_id={learning_path_id}, user_id={user.id}")
            return JSONResponse({"error": "Learning path not found"}, status_code=404)

        topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == learning_path_id).order_by(TopicProgress.id).all()
        if not topics:
            logger.warning(f"No topics found for learning_path_id={learning_path_id}")
            return JSONResponse({"error": "No topics available"}, status_code=404)

        # Find the first uncompleted topic
        for index, topic in enumerate(topics):
            if not topic.completed:
                return {"module_index": index}
        
        # If all topics are completed, return the first module (index 0)
        return {"module_index": 0}
    except Exception as e:
        logger.error(f"Error in get_next_course: {str(e)}")
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)


# Updated GET /progress
@app.get("/progress", response_class=HTMLResponse)
async def get_progress(request: Request, learning_path_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        progress = db.query(Progress).filter(Progress.user_id == user.id).all()
        learning_paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
        progress_data = []
        selected_learning_path = None

        if learning_path_id:
            selected_learning_path = db.query(LearningPath).filter(LearningPath.id == learning_path_id, LearningPath.user_id == user.id).first()
            if not selected_learning_path:
                logger.warning(f"Learning path not found: learning_path_id={learning_path_id}, user_id={user.id}")
                return HTMLResponse(content="Learning path not found", status_code=404)

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
            "user": user,
            "learning_path": selected_learning_path  # Pass the full LearningPath object
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





from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse

@app.get("/me")
async def get_current_user_details(user: User = Depends(get_current_user)):
    logger.debug(f"Fetching details for user_id={user.id}")
    return {"user_id": user.id, "username": user.username}


async def get_current_user_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    cookies = websocket.cookies
    username = cookies.get("username")
    user_id = cookies.get("user_id")
    if not username or not user_id:
        raise HTTPException(status_code=403, detail="Not authenticated")
    user = db.query(User).filter(User.username == username, User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=403, detail="User not found")
    return user

from fastapi import WebSocket
from typing import Optional

@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    print("Test WebSocket request received")
    await websocket.accept()
    print("Test WebSocket connected")
    await websocket.send_text("Test connection successful")
    print("Test WebSocket connected")
    await websocket.send_text("Test connection successful")
    await websocket.send_text("Test WebSocket request received")
    await websocket.close()

from fastapi.websockets import WebSocketState

from starlette.websockets import WebSocketDisconnect


# Helper to create a new chat session
async def create_new_chat_session(user_id: int, db: Session) -> int:
    new_session = ChatSession(
        user_id=user_id,
        title=f"New Chat {datetime.utcnow().isoformat()[:10]}"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    logger.debug(f"Created new chat session with ID: {new_session.id}")
    return new_session.id

@app.websocket("/ws/chat/{user_id}/{session_id}")
async def websocket_chat(websocket: WebSocket, user_id: int, session_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    logger.debug(f"WebSocket connection attempt: user_id={user_id}, session_id={session_id}")

    # Authentication via cookies
    cookies = websocket.cookies
    username = cookies.get("username")
    stored_user_id = cookies.get("user_id")
    if not username or not stored_user_id:
        logger.warning("Missing authentication cookies")
        await websocket.send_text(json.dumps({"error": "Unauthorized: Missing authentication cookies"}))
        await websocket.close(code=1008)
        return

    try:
        stored_user_id = int(stored_user_id)
        if stored_user_id != user_id:
            logger.warning(f"User ID mismatch: URL={user_id}, cookie={stored_user_id}")
            await websocket.send_text(json.dumps({"error": "Unauthorized: User ID mismatch"}))
            await websocket.close(code=1008)
            return
        
        user = db.query(User).filter(User.id == stored_user_id, User.username == username).first()
        if not user:
            logger.warning("User not found")
            await websocket.send_text(json.dumps({"error": "Unauthorized: User not found"}))
            await websocket.close(code=1008)
            return
    except ValueError:
        logger.warning("Invalid user_id format")
        await websocket.send_text(json.dumps({"error": "Unauthorized: Invalid user_id format"}))
        await websocket.close(code=1008)
        return

    # Validate or create session
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        effective_session_id = await create_new_chat_session(user_id, db)
        await websocket.send_text(json.dumps({
            "session_id": effective_session_id,
            "message": f"Session {session_id} not found, new session {effective_session_id} created"
        }))
    else:
        effective_session_id = session_id

    # Send chat history
    history = db.query(ChatHistory).filter(ChatHistory.session_id == effective_session_id).order_by(ChatHistory.timestamp).all()
    for chat in history:
        await websocket.send_text(json.dumps({
            "chat_history": {"message": chat.message, "response": chat.response},
            "session_id": effective_session_id
        }))

    # Main message loop
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message: {data}")

            # If this is the first message in a new session, summarize it for the title
            session = db.query(ChatSession).filter(ChatSession.id == effective_session_id).first()
            if not history and session.title.startswith("New Chat"):
                summary = await summarize_user_input(data)
                session.title = summary
                db.commit()

            chat_history = ChatHistory(
                user_id=user.id,
                session_id=effective_session_id,
                message=data,
                response="Processing..."
            )
            db.add(chat_history)
            db.commit()

            response = await generate_chat_response(data, user.id, db)
            chat_history.response = response
            db.commit()

            await websocket.send_text(json.dumps({
                "message": response,
                "session_id": effective_session_id,
                "title": session.title if not history else None  # Send title only for first message
            }))

            history = db.query(ChatHistory).filter(ChatHistory.session_id == effective_session_id).all()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user_id={user_id}, session_id={effective_session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({"error": f"Server error: {str(e)}"}))
    finally:
        await websocket.close()        




@app.get("/chat/new_session")
async def new_chat_session(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session_id = await create_new_chat_session(user.id, db)
    return {"session_id": session_id}



async def summarize_user_input(message: str) -> str:
    
    # Summarize the user's input into a short, recognizable title.
    
    # Simple heuristic: Take first few words or key phrase
    words = message.split()
    if len(words) <= 3:
        return message  # Short messages can be used as-is
    else:
        # Use OpenAI to summarize if message is long
        prompt = f"""
        Summarize the following user input into a concise title (max 50 characters):
        "{message}"
        Example: "What are NFTs?" -> "NFT Basics".
        """
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=[{"role": "user", "content": prompt}],
                timeout=10
            )
            summary = response.choices[0].message.content.strip()
            return summary[:50]  # Enforce length limit
        except Exception as e:
            logger.error(f"Error summarizing input: {e}")
            # Fallback: Truncate first few words
            return " ".join(words[:3])[:50]


@app.get("/chat_history")
async def get_chat_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        logger.debug(f"Fetching chat history for authenticated user_id={user.id}")

        # ✅ Check if ChatSession table exists
        try:
            sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).all()
            chat_sessions = [
                {
                    "session_id": session.id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "messages": [
                        {"message": h.message, "response": h.response, "timestamp": h.timestamp}
                        for h in session.messages
                    ]
                }
                for session in sessions
            ]
        except Exception as e:
            logger.warning(f"ChatSession query failed: {str(e)}")
            chat_sessions = []

        # ✅ Fetch chat history if ChatSession is missing
        history = db.query(ChatHistory).filter(ChatHistory.user_id == user.id).all()
        chat_messages = [{"message": h.message, "response": h.response} for h in history]

        return {
            "chat_sessions": chat_sessions,  
            "chat_messages": chat_messages
        }

    except HTTPException as e:
        logger.warning(f"HTTPException in get_chat_history: {str(e)}")
        return JSONResponse({"error": e.detail}, status_code=e.status_code)

    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}", exc_info=True)
        return JSONResponse({"error": "An internal error occurred"}, status_code=500)




# @app.get("/chat_history")
# async def get_chat_history(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     try:
#         logger.debug(f"Fetching chat history for user_id={user_id}, authenticated user_id={user.id}")
#         if user_id != user.id:
#             logger.warning(f"Unauthorized access attempt: user_id={user_id} does not match authenticated user_id={user.id}")
#             return JSONResponse({"error": "Unauthorized"}, status_code=403)

#         history = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
#         return [{"message": h.message, "response": h.response} for h in history]
#     except HTTPException as e:
#         logger.warning(f"HTTPException in get_chat_history: {str(e)}")
#         return JSONResponse({"error": e.detail}, status_code=e.status_code)
#     except Exception as e:
#         logger.error(f"Error in get_chat_history: {str(e)}")
#         return JSONResponse({"error": "An internal error occurred"}, status_code=500)
    
    

# @app.get("/chat_history")
# async def get_chat_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     sessions = db.query(ChatSession).filter(ChatSession.user_id == user.id).all()
#     return [
#         {
#             "session_id": session.id,
#             "title": session.title,
#             "created_at": session.created_at,
#             "messages": [{"message": h.message, "response": h.response, "timestamp": h.timestamp} for h in session.messages]
#         }
#         for session in sessions
#     ]


# HTML Rendering Routes
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user: User = Depends(get_current_user)):
    
    try:
        return templates.TemplateResponse("chat.html", {"request": request, "user": user})
    except Exception as e:
        logger.error(f"Error in chat_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)


# Load environment variables@app.get("/chat")
async def chat_page(request: Request, db: Session = Depends(get_db)):
    wallet = request.cookies.get("wallet")
    user = crud.get_user_by_wallet(db, wallet) if wallet else None
    chat_history = crud.get_chat_history(db, user.id) if user else []
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "wallet_connected": bool(user), "user": user or {}, "chat_history": chat_history}
    )

@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(chat: schemas.ChatMessage, db: Session = Depends(get_db), request: Request = None):
    wallet = request.cookies.get("wallet")
    response = generate_chat_response(chat.message)
    if wallet and chat.save_history:
        user = crud.get_user_by_wallet(db, wallet)
        crud.save_chat(db, user.id, chat.message, response)
    return {"response": response}

@app.post("/chat/message")
async def post_message(data: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session_id = data.get("session_id")
    message = data["message"]
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first() if session_id else None
    if not session:
        session = ChatSession(user_id=user.id, title=f"Chat {datetime.utcnow().isoformat()[:10]}")
        db.add(session)
        db.commit()
    chat_history = ChatHistory(user_id=user.id, session_id=session.id, message=message, response="Processing...")
    db.add(chat_history)
    db.commit()
    response = await generate_chat_response(message, user.id, db)
    chat_history.response = response
    db.commit()
    return {"session_id": session.id, "message": response}


@app.get("/course_content", response_class=HTMLResponse)
async def course_content_page(request: Request, learning_path_id: int, topic_id: int, user: User = Depends(get_current_user)):
    try:
        return templates.TemplateResponse("course.html", {
            "request": request,
            "user": user,
            "learning_path_id": learning_path_id,
            "topic_id": topic_id
        })
    except Exception as e:
        logger.error(f"Error in course_content_page: {str(e)}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.get("/badges", response_class=HTMLResponse)
async def badges_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quiz_badges = []
    exam_rewards = []
    learning_paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
    for lp in learning_paths:
        topics = db.query(TopicProgress).filter(TopicProgress.learning_path_id == lp.id, TopicProgress.badge_png_path.isnot(None)).all()
        for topic in topics:
            quiz_badges.append({
                "topic_id": topic.id,
                "learning_path_name": lp.name,
                "module_name": topic.topic_name,
                "badge_png_path": topic.badge_png_path,
                "badge_pdf_path": topic.badge_pdf_path
            })
        if lp.exam_completed and lp.exam_badge_png_path:
            exam_rewards.append({
                "learning_path_id": lp.id,
                "learning_path_name": lp.name,
                "exam_badge_png_path": lp.exam_badge_png_path,
                "exam_badge_pdf_path": lp.exam_badge_pdf_path,
                "certificate_pdf_path": lp.certificate_pdf_path
            })
    return templates.TemplateResponse("badges.html", {
        "request": request,
        "quiz_badges": quiz_badges,
        "exam_rewards": exam_rewards
    })


# Run the FastAPI App
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")