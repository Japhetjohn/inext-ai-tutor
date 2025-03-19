# Infinity Academy

## 📌 Abstract
Infinity Academy is a **Web3 learning platform** that offers **AI-powered personalized courses** on **blockchain technologies**.  
It allows users to:
✅ **Create custom learning paths**  
✅ **Track progress** through quizzes & exams  
✅ **Explore Web3 career paths**  
✅ **Integrate wallet authentication** for exclusive content  

---

## 🚀 **Core Features**
🔹 **Personalized Learning Paths** – Generate AI-based courses on Web3 topics.  
🔹 **Wallet Authentication** – Users connect wallets (MetaMask) to access premium content.  
🔹 **AI-Powered Content** – Uses OpenAI to generate learning modules & quizzes.  
🔹 **Quizzes & Exams** – Test knowledge with AI-generated assessments.  
🔹 **Career Paths** – Predefined Web3 learning tracks (e.g., Smart Contract Developer).  
🔹 **User Dashboard** – Save, track, and manage learning progress.  

---

## 🔧 **Prerequisites**
- **Python 3.8+**
- **A web browser (e.g., Chrome) with MetaMask installed** (for wallet integration)
- **Database**: SQLite (default) or PostgreSQL

---

## ⚙️ **Setup and Installation**
### 1️⃣ **Clone the Repository**
```bash
git clone <repository-url>
cd infinity-academy
2️⃣ Create a Virtual Environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3️⃣ Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
4️⃣ Set Up Environment Variables
Create a .env file in the project root and add:

ini
Copy
Edit
DATABASE_URL=sqlite:///infinity_academy.db
OPENAI_API_KEY=your_openai_api_key
FIGMA_API_KEY=your_figma_api_key
SECRET_KEY=your_secret_key
▶️ Running the Application
Start the FastAPI Server
bash
Copy
Edit
uvicorn main:app --reload
✅ The API will run on http://localhost:8000

Access the API Documentation
Go to http://localhost:8000/docs to test API endpoints.

🎓 Walkthrough: How to Use Infinity Academy
1️⃣ Login or Register
Visit http://localhost:8000/
Login or create an account.
2️⃣ Explore the Dashboard
Navigate to /dashboard
Select a career path or create a custom learning path.
3️⃣ Generate a Learning Path
Enter a topic (e.g., "Blockchain Security")
Select a difficulty level (Beginner / Intermediate / Advanced)
Choose content type (Videos, Articles, Code Examples)
Click "Generate My Learning Path"
If wallet isn’t connected, a MetaMask prompt will appear.
4️⃣ Complete Modules
Click a module from the roadmap (/roadmap/{learning_path_id})
Read the AI-generated content
Mark the module as complete
Take the quiz (/quiz?topic_id={topic_id}&learning_path_id={learning_path_id})
5️⃣ Take the Final Exam
Once all modules are complete, a "Take Exam" button appears.
Take the comprehensive final exam before completing the course.
6️⃣ Manage Learning Paths
Return to dashboard to view all learning paths.
Delete paths if needed.
Explore Web3 career paths or wishlist saved topics.