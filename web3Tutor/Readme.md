# iNextAI Web3 Learning Platform

## Overview
AI-powered Web3 education platform featuring personalized learning paths, wallet integration, and interactive content.

## Features
- User authentication & profiles
- Web3 wallet integration (EVM compatible)
- AI-generated learning paths
- Progress tracking & analytics
- Interactive quizzes
- Real-time chat support

## Tech Stack
- Backend: FastAPI, SQLAlchemy
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- Web3: web3.py, WalletConnect v2
- AI: OpenAI/OpenRouter API

## Setup Instructions

1. Configure Environment Variables
Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_key
WALLETCONNECT_PROJECT_ID=your_wc_project_id
JWT_SECRET=your_jwt_secret
```

2. Install Dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Application:
```bash
python back.py
```

## Pending Tasks

1. Environment Setup:
- [ ] Add OpenAI/OpenRouter API key
- [ ] Configure WalletConnect Project ID
- [ ] Set JWT secret for authentication

2. Wallet Integration:
- [ ] Complete WalletConnect setup
- [ ] Add support for multiple EVM chains
- [ ] Implement transaction signing

3. Content Development:
- [ ] Create initial learning paths
- [ ] Develop quiz content
- [ ] Add interactive exercises

4. Testing:
- [ ] Unit tests
- [ ] Integration tests
- [ ] User acceptance testing

## API Documentation
Access the API docs at `/docs` when running the application.

## License
MIT License