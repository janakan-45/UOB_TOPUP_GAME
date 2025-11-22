# 🍌 Banana Brain Blitz

An engaging puzzle game where players solve banana math puzzles, earn points, level up, and compete on leaderboards. Built with Django REST Framework backend and React TypeScript frontend.

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Documentation](#-documentation)
- [Technologies](#-technologies)
- [API Endpoints](#-api-endpoints)
- [Game Mechanics](#-game-mechanics)

## ✨ Features

### Core Gameplay
- 🧩 **Puzzle Solving**: Solve banana math puzzles from external API
- ⏱️ **Time-Based**: Race against the clock to solve puzzles
- 🎯 **Multiple Difficulties**: Easy, Medium, and Hard modes

### Power-Ups
- 💡 **Hints**: 5 different hint types (wrong answer, range, parity, comparison, multiple choice)
- 🧊 **Time Freeze**: Add extra time to the timer
- 🍌 **Super Banana**: Double points for next correct answer

### Progression Systems
- 📈 **XP & Levels**: Earn XP and level up (100 XP per level)
- 🔥 **Combo System**: Build combos for bonus points
- ⭐ **Perfect Solve**: Bonus rewards for solving without hints
- 🍀 **Lucky Streak**: 5% chance for 2x point multiplier

### Social & Challenges
- 🏆 **Leaderboard**: Compete with other players
- 📅 **Daily Challenges**: Complete daily challenges for bonus coins
- 📊 **Statistics**: Track your progress and achievements

### User Features
- 🔐 **Authentication**: JWT-based auth with email OTP support
- 💰 **Economy**: Earn and spend coins on power-ups
- 🎨 **Beautiful UI**: Modern, animated interface with particle effects

## 📁 Project Structure

```
GAME/
├── UOB_TOPUP_GAME-1_current git/     # Backend (Django)
│   └── BananaGame/
│       ├── Banana/                   # Main app
│       └── manage.py
│
├── banana-brain-blitz-86917-main/    # Frontend (React)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── ...
│   └── package.json
│
├── GAME_CHANGES_DOCUMENTATION.md     # Detailed changes doc
├── QUICK_REFERENCE.md                 # Quick reference guide
└── README.md                          # This file
```

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.8+, Django 5.1+
- **Frontend**: Node.js 18+, npm/yarn/pnpm
- **Database**: PostgreSQL (or SQLite for development)

### Backend Setup

```bash
# Navigate to backend directory
cd "UOB_TOPUP_GAME-1_current git/BananaGame"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

Backend runs on `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd banana-brain-blitz-86917-main

# Install dependencies
npm install

# Create .env file
echo "VITE_BASE_API=http://localhost:8000" > .env

# Start development server
npm run dev
```

Frontend runs on `http://localhost:5173`

## 📚 Documentation

- **[Backend README](UOB_TOPUP_GAME-1_current%20git/README.md)** - Backend API documentation
- **[Frontend README](banana-brain-blitz-86917-main/README.md)** - Frontend documentation
- **[Game Changes Documentation](GAME_CHANGES_DOCUMENTATION.md)** - Detailed feature documentation
- **[Quick Reference](QUICK_REFERENCE.md)** - Quick reference guide

## 🛠️ Technologies

### Backend
- Django 5.1+
- Django REST Framework
- JWT Authentication (djangorestframework-simplejwt)
- PostgreSQL/SQLite

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- React Router

## 🔌 API Endpoints

### Authentication
- `POST /banana/register/` - Register
- `POST /banana/login/` - Login
- `POST /banana/login/request-otp/` - Request OTP
- `POST /banana/login/verify-otp/` - Verify OTP

### Game
- `GET /banana/puzzle/` - Get puzzle
- `POST /banana/check-puzzle/` - Check answer
- `POST /banana/submit-score/` - Submit score
- `GET /banana/leaderboard/` - Get leaderboard

### Power-Ups & Mechanics
- `POST /banana/use-hint/` - Use hint
- `POST /banana/set-difficulty/` - Set difficulty
- `GET /banana/daily-challenge/` - Get daily challenge
- `POST /banana/claim-daily-challenge/` - Claim reward
- `GET /banana/game-stats/` - Get stats

See [Backend README](UOB_TOPUP_GAME-1_current%20git/README.md) for full API documentation.

## 🎮 Game Mechanics

### Scoring Formula

```
Total Points = (Base + Time Bonus + Combo Bonus + Perfect Bonus) × Multipliers

Where:
- Base = 10 × difficulty_multiplier
- Time Bonus = max(0, (40 - time_taken) / 2), capped at 15
- Combo Bonus = combo_count × 2
- Perfect Bonus = 10 (if no hints used)
- Multipliers = Lucky (2x, 5% chance) × Super Banana (2x, if active)
```

### Difficulty Levels

| Level | Time | Points Multiplier |
|-------|------|-------------------|
| Easy | 50s | 0.7x |
| Medium | 40s | 1.0x |
| Hard | 30s | 1.5x |

### Hint Types

1. **Wrong Answer** - "X is NOT the answer"
2. **Range** - "Answer is between X and Y"
3. **Parity** - "Answer is ODD/EVEN"
4. **Comparison** - "Answer is LESS/GREATER than X"
5. **Multiple Choice** - "Answer is one of: X, Y, Z"

### Progression

- **XP**: 1 XP per point (+5 for perfect solve)
- **Level Up**: Every 100 XP
- **Combo**: Build by solving correctly
- **Daily Challenge**: 5 puzzles = 50+ coins

## 🎯 Power-Ups

| Power-Up | Cost | Effect |
|----------|------|--------|
| Hint | 10 coins | Get random hint (5 types) |
| Time Freeze | 15 coins | +10 seconds to timer |
| Super Banana | 25 coins | 2x points for next solve |

## 📦 Installation

### Full Stack Setup

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd GAME
   ```

2. **Setup Backend** (see [Backend README](UOB_TOPUP_GAME-1_current%20git/README.md))
   ```bash
   cd "UOB_TOPUP_GAME-1_current git/BananaGame"
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

3. **Setup Frontend** (see [Frontend README](banana-brain-blitz-86917-main/README.md))
   ```bash
   cd banana-brain-blitz-86917-main
   npm install
   echo "VITE_BASE_API=http://localhost:8000" > .env
   npm run dev
   ```

4. **Open browser**
   - Navigate to `http://localhost:5173`
   - Register/Login and start playing!

## 🚀 Deployment

### Backend Deployment
- See [Backend README](UOB_TOPUP_GAME-1_current%20git/README.md#-deployment)

### Frontend Deployment
- See [Frontend README](banana-brain-blitz-86917-main/README.md#-building-for-production)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of the Banana Brain Blitz game.

## 🐛 Troubleshooting

### Backend Issues
- Check Django version compatibility
- Verify database migrations: `python manage.py migrate`
- Check CORS settings for frontend connection

### Frontend Issues
- Verify `VITE_BASE_API` in `.env`
- Check if backend is running
- Clear cache: `rm -rf node_modules && npm install`

### API Connection
- Ensure backend is running on port 8000
- Check CORS configuration
- Verify API base URL in frontend `.env`

## 📞 Support

- Check documentation files for detailed information
- Review [Game Changes Documentation](GAME_CHANGES_DOCUMENTATION.md) for feature details
- Open an issue on the repository

---

**Made with 🍌 and ❤️**

Happy Puzzling! 🎮✨



