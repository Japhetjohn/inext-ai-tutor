# iNextAI Web3 Learning Platform

## Project Overview
An AI-powered Web3 learning platform with adaptive learning paths, wallet integration, and interactive content.

## Project Structure

```
web3Tutor/
├── controllers/           # Route controllers
│   └── landing_controller.py
├── database/             # Database operations
│   └── database_operations.py
├── models/              # Database models
│   └── database.py
├── pages/               # Page-specific logic
│   └── landing/
├── services/           # Business logic services
│   └── wallet_service.py
├── static/             # Static assets
│   ├── css/
│   └── js/
└── templates/          # HTML templates
    ├── landing/
    └── roadmaps/
```

## Core Components

### Backend Files
- `app.py` - Main application entry point
- `server.py` - Server configuration
- `models.py` - Database models
- `schemas.py` - Pydantic schemas
- `database_operations.py` - Database operations
- `blockchain.py` - Web3/blockchain integration
- `walletconnect.py` - Wallet connection handling

### Frontend Templates
- `templates/dashboard.html` - Main user dashboard
- `templates/landing.html` - Landing page
- `templates/roadmaps/*.html` - Learning roadmaps
- `templates/quiz.html` - Quiz interface
- `templates/progress.html` - Progress tracking


## Key Features

This section combines elements from the original README's feature descriptions with the structured approach of the edited snippet.

1. **User Dashboard:**  Wallet connection, learning progress tracking, personalized roadmaps (Username displayed at the top, Web3 wallet connection required, Social integration (X/Twitter & Discord), IP tracking to prevent Sybil attacks).
2. **Learning System:** AI-generated content, interactive quizzes, progress analytics (Notes section for key insights, Time spent tracking for engagement analysis, Progress chart for learning phases, Quiz performance tracking, Points & rewards system).
3. **Web3 Integration:** Wallet authentication, token rewards, blockchain interaction.
4. **Additional Features:** Leaderboard (Displays top learners based on quiz performance), Achievements & Badges (Earn rewards for reaching milestones), Discord Community Discussion Board (Forum for discussions).


## Learning Flow & Phases (from original README)

The iNextAI Tutor is an AI-driven, structured Web3 education model designed for different expertise levels:

**Learning Flow:**

1. Users select their learning phase (Beginner, Advanced, or Expert).
2. Courses unlock sequentially after completing previous modules.
3. AI provides step-by-step guidance and AI-generated visuals.
4. User progress is tracked, and quizzes are generated dynamically.
5. Users earn badges, points, and certificates for completing courses.

**Learning Phases:**

Phase 1: Basic (Newbies Pack) → Web3 fundamentals (Blockchain, Wallets, DeFi, DAOs, NFTs)
Phase 2: Advanced (Web3 Practitioner) → Smart contracts, DeFi strategies, Layer 2 scaling
Phase 3: Expert (Web3 Builder & Innovator) → DApp development, smart contract auditing, tokenomics


## Personalized Learning Path (from original README)

**How It Works:**

Users select their current knowledge level & interests (e.g., NFTs, DeFi, DAOs).
AI customizes the learning path and adapts based on progress.
If a user struggles, AI provides extra explanations & practice quizzes.
Learning paths update dynamically as users improve.

**Example:**

A user selects “I want to learn about NFTs”, and the AI generates:
✅ Intro to NFTs → Basics, marketplaces, creation
✅ Smart Contracts for NFTs → How NFTs work on-chain
✅ Advanced Topics → NFTs in gaming, metaverse


## Tech Stack & AI Models Used

This section integrates information from the original README.

**Tech Stack:**

Frontend: React, Next.js, Tailwind CSS
Backend: FastAPI, Django, Node.js
Blockchain: Solidity, Web3.js, ethers.js, Hedera Hashgraph
Database: PostgreSQL, MongoDB

**AI Models Used in iNextAI:**

1. GPT-4, Llama 3, Falcon → AI tutor for explanations
2. BERT, T5, LangChain → AI-powered quiz generation
3. DALL·E, Stable Diffusion, Midjourney → AI-generated images & flashcards
4. Reinforcement Learning (PPO) → Adaptive learning progress tracking
5. RoBERTa, OpenAI Sentiment Model → Engagement & sentiment analysis
6. OpenAI Whisper, ElevenLabs → Voice-based AI learning assistant


## Setup & Installation

1. Install dependencies:
```bash
pip install -r web3Tutor/requirements.txt
```

2. Configure environment variables in `.env`:
```
OPENAI_API_KEY=your_key
WALLETCONNECT_PROJECT_ID=your_id
```

3. Run the application:
```bash
cd web3Tutor
python app.py
```

## Development Guidelines

1. **File Organization:** Keep route handlers in `controllers/`, database operations in `database/`, business logic in `services/`.
2. **Adding Features:** Create corresponding templates in `templates/`, add static assets to `static/`, update routes in appropriate controllers.
3. **Database Changes:** Update models in `models.py`, add schemas in `schemas.py`, create operations in `database_operations.py`.


## Contributing

1. Follow the existing file structure
2. Maintain consistent naming conventions
3. Update documentation for new features
4. Test thoroughly before committing


## License
MIT License