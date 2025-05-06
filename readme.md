# Web3 AI Tutor Platform

A comprehensive AI-powered learning platform for Web3 technology education.

## Features

- **Personalized Learning Paths**: AI-generated curriculum based on user preferences
- **Interactive Quizzes**: Test knowledge with dynamic assessments
- **Progress Tracking**: Monitor learning achievements
- **Web3 Integration**: Connect wallets for enhanced features
- **AI Chat Assistant**: Get real-time help with Web3 concepts

## Tech Stack

- Backend: FastAPI
- Database: SQLite
- AI Integration: OpenAI
- Web3: Web3.py
- Authentication: JWT + Wallet Authentication

## Getting Started

1. Install dependencies:
```bash
pip install -r web3Tutor/requirements.txt
```

2. Run the application:
```bash
cd web3Tutor
uvicorn back:app --host 0.0.0.0 --port 5000 --reload
```

3. Access the application at: https://[repl-id].repl.co

## Environment Variables ..

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Secret key for JWT tokens

## Features in Detail

### Learning Path Generation
- Choose your expertise level
- Select weekly time commitment
- Pick preferred learning style
- Get AI-customized curriculum

### Progress Tracking
- Quiz performance analytics
- Learning path completion status
- Achievement badges
- Interactive roadmaps

### Community Features
- Chat with AI tutor
- Progress leaderboard
- Achievement system

## Contributing

Feel free to submit issues and enhancement requests.