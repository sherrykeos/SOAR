<div align="center">

# <img src="./frontend/public/assets/zekrosLogov1.png" alt="ZEKROS Logo" height="42" align="absmiddle" /> ZEKROS
### *Where Every Move Decays.*

A Next-Gen Monochromatic Real-Time Strategy Arena built on adaptive boards, vanishing piece queues, and tactical token mechanics.

[![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4.0-38BDF8?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Node.js](https://img.shields.io/badge/Node.js-v20+-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org/)
[![Express](https://img.shields.io/badge/Express-v5.0-000000?style=for-the-badge&logo=express&logoColor=white)](https://expressjs.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-v4.8-010101?style=for-the-badge&logo=socket.io&logoColor=white)](https://socket.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-v16+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Prisma](https://img.shields.io/badge/Prisma-v6.19-2D3748?style=for-the-badge&logo=prisma&logoColor=white)](https://www.prisma.io/)

<br />

![ZEKROS Hero Preview](/frontend/public/assets/hero-pvp-element.gif)

</div>

---

## 📖 Overview

**ZEKROS** turns the classic tic-tac-toe concept into a deep, high-stakes tactical strategy game. Traditional games suffer from early ties and predictable patterns; ZEKROS introduces a **living arena** where:
- Boards shift between **3×3, 4×4, 5×5, and 6×6** dimensions.
- Pieces have a **finite lifespan** — placing a new piece beyond the piece limit causes your oldest piece to dissolve into the void.
- **Reclaim Tokens** allow players to override decay, lock critical cells, or resurrect vanishing positions.
- **AI Neural Bots** & **Deterministic Heuristic Engine** adapt to your playstyle in singleplayer.
- Real-Time **WebSockets** sync 1v1 duels, custom private rooms, and global matchmaking with zero-latency state replication.

---

## 🎮 Core Game Mechanics

```
┌─────────────────────────────────────────────────────────┐
│                      GAMEPLAY LOOP                      │
├─────────────────────────────────────────────────────────┤
│ 1. PLACEMENT  ➜ Place symbol (X/O) on any open cell.     │
│ 2. DECAY      ➜ Exceeding piece limit vanishes oldest.  │
│ 3. RECLAIM    ➜ Spend Token to lock or preserve cell.   │
│ 4. VICTORY    ➜ Align N symbols horizontally/vertically. │
└─────────────────────────────────────────────────────────┘
```

### 1. Arena Dimensions & Constraints
| Grid Size | Win Requirement | Max Active Pieces / Player | Token Allowance |
| :---: | :---: | :---: | :---: |
| **3 × 3** | 3 in a row | 3 Pieces | 3 Tokens |
| **4 × 4** | 4 in a row | 4 Pieces | 3 Tokens |
| **5 × 5** | 5 in a row | 5 Pieces | 3 Tokens |
| **6 × 6** | 6 in a row | 6 Pieces | 4 Tokens |

### 2. Auto-Decay Queue (Spatial Memory)
When a player reaches their maximum allowed active pieces on the board, placing another piece puts their oldest piece into a **Fading State**. On the next turn, that fading piece completely vanishes from the board, opening up strategic counter-attack opportunities.

### 3. Reclaim Tokens
Each player starts with a limited supply of Reclaim Tokens. Spending a token allows you to:
- **Lock a cell** permanently to prevent opponent overrides.
- **Preserve a fading piece** from vanishing on the next turn.

---

## 🕹️ Play Modes

<br />

<div align="center">
  
![Multiplayer Mesh](/frontend/public/assets/ai-multiplayer-mesh.gif)

</div>

<br />

- ⚔️ **Local PvP (Pass & Play):** Play offline with a friend on the exact same device. No network connection required.
- 🤖 **Bot Engine (Smart Bot & Neural AI):**
  - **Smart Bot (v1):** Deterministic Minimax engine with immediate win/threat evaluation.
  - **Neural AI (v2):** Multi-ply depth planner that predicts move chains and evaluates positional board value.
- 🛡️ **Custom Rooms:** Create private rooms with custom grid sizes, turn timers, and passcode protection (`#ZK-XXXX`).
- 🌐 **Multiplayer & Matchmaking:** Real-time online duels with regional socket clusters, live spectator feeds, and ELO rating tracking.

---

## 🏗️ System Architecture

```mermaid
graph TD
    Client["React 19 Frontend (Vite + TanStack Router)"]
    
    subgraph Backend Engine ["Node.js / Express 5 Application"]
        API["Express REST API (/api)"]
        SocketServer["Socket.IO Server"]
        Auth["Passport.js (JWT & Google OAuth 2.0)"]
        GameEngine["ZEKROS Rules & Decay Engine"]
        BotEngine["Minimax / Neural Bot Solver"]
    end
    
    Database[("PostgreSQL Database")]
    Prisma["Prisma ORM"]

    Client <-->|"HTTPS / REST"| API
    Client <-->|"WSS / Socket.IO"| SocketServer
    API --> Auth
    API --> Prisma
    SocketServer --> GameEngine
    GameEngine --> BotEngine
    Prisma --> Database
```

---

## 🛠️ Technology Stack

### Frontend
- **Framework:** React 19 (Hooks, Suspense, Concurrent Rendering)
- **Bundler:** Vite 8 + TSConfig Paths
- **Routing:** TanStack Router (`@tanstack/react-router`)
- **State & Query:** TanStack Query (`@tanstack/react-query`) & Zustand
- **Styling:** Vanilla CSS + TailwindCSS v4 (`@tailwindcss/vite`) + Monochromatic Design Tokens
- **Animations:** Motion (`motion/react`) & WebCodecs Canvas (`ImageDecoder` API)
- **Icons & Audio:** Lucide React & Howler.js

### Backend
- **Runtime:** Node.js v20+ (ES Modules)
- **Framework:** Express v5
- **Real-Time Engine:** Socket.IO v4.8
- **Database ORM:** Prisma ORM v6.19
- **Database:** PostgreSQL v16+
- **Authentication:** Passport.js (Google OAuth 2.0, Local JWT with Refresh Tokens)
- **Validation:** Zod v4

---

## 📂 Project Structure

```
Zekros/
├── frontend/                     # React 19 SPA Frontend
│   ├── public/
│   │   └── assets/               # WebP/GIF/JPG visual media assets
│   ├── src/
│   │   ├── components/           # UI & Site Components
│   │   │   ├── app/              # Application layout & navigation
│   │   │   ├── game/             # Interactive Game Arena & Board
│   │   │   └── site/             # Landing page sections (Hero, How, Features, Modes, Stats, CTA)
│   │   ├── constants/            # App configuration & metadata constants
│   │   ├── contexts/             # React Context providers (Play Entry, Auth)
│   │   ├── hooks/                # Custom hooks (useCurrentUser, socket hooks)
│   │   ├── lib/                  # Utility libraries & Socket client instance
│   │   ├── pages/                # Page views (About, Settings, History, Arena)
│   │   ├── routes/               # TanStack Router route definitions
│   │   └── styles.css            # Global CSS design tokens & glass utilities
│   └── package.json
│
├── backend/                      # Express 5 REST & Socket Server
│   ├── prisma/
│   │   └── schema.prisma         # Prisma Schema (User, Match, Move, Session, UserStats, UserRating)
│   ├── src/
│   │   ├── app/                  # Server entry & Express app config
│   │   ├── auth/                 # Passport.js authentication strategies
│   │   ├── botEngine/            # Smart Bot (Minimax) & Neural AI Solver
│   │   ├── controllers/          # Express route controllers (Auth, User, Match, Room)
│   │   ├── Engine/               # Core ZEKROS Board & Rules Engine
│   │   ├── middleware/           # Auth validation, CORS, error handler
│   │   ├── routes/               # Express API routes (/api/auth, /api/matches, /api/rooms)
│   │   ├── services/             # Business logic & email services (Brevo)
│   │   └── socket/               # Socket.IO connection, room, & game event handlers
│   └── package.json
└── README.md
```

---

## 🚀 Quick Start & Local Setup

### Prerequisites
- **Node.js** v20.0.0 or higher
- **npm** v10.0.0 or higher
- **PostgreSQL** database instance (Local or hosted on Supabase/Neon/Render)

### 1. Clone the Repository
```bash
git clone https://github.com/sherrykeos/Zekros.git
cd Zekros
```

### 2. Configure Environment Variables

Create `.env` in `backend/`:
```env
PORT=5000
NODE_ENV=development
FRONTEND_URL=http://localhost:8080

# Database Connection
DATABASE_URL="postgresql://postgres:password@localhost:5432/zekros?schema=public"

# Auth Secrets
JWT_SECRET="your_super_secret_jwt_key_here"
REFRESH_TOKEN_SECRET="your_super_secret_refresh_key_here"

# Google OAuth (Optional)
GOOGLE_CLIENT_ID="your_google_client_id"
GOOGLE_CLIENT_SECRET="your_google_client_secret"
GOOGLE_CALLBACK_URL="http://localhost:5000/api/auth/google/callback"

# Email Service (Brevo - Optional)
BREVO_API_KEY="your_brevo_api_key"
```

Create `.env` in `frontend/`:
```env
VITE_API_URL=http://localhost:5000/api
VITE_SOCKET_URL=http://localhost:5000
```

### 3. Setup & Start Backend
```bash
cd backend
npm install
npx prisma db push
npm start
```

### 4. Setup & Start Frontend
```bash
cd ../frontend
npm install
npm run dev
```

Open your browser at `http://localhost:8080` to experience ZEKROS!

---

## 🌐 API & Socket Protocol

### REST Endpoints
| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/auth/register` | `POST` | Register local account |
| `/api/auth/login` | `POST` | Authenticate & issue JWT cookie |
| `/api/auth/me` | `GET` | Retrieve current authenticated user profile |
| `/api/matches` | `GET` | Fetch match history & stats |
| `/api/rooms/create` | `POST` | Create a private custom lobby |
| `/api/rooms/join` | `POST` | Join custom room via passcode |

### Socket.IO Real-Time Events
| Event Name | Direction | Payload / Action |
| :--- | :---: | :--- |
| `join-room` | Client ➔ Server | Join room ID or match queue |
| `make-move` | Client ➔ Server | `{ matchId, row, col }` |
| `game-state` | Server ➔ Client | Broadcasts updated board, decay queue, and turn clock |
| `timer-tick` | Server ➔ Client | Synchronizes active player turn countdown |
| `reclaim-cell` | Client ➔ Server | Spend token to lock/preserve cell |

---

## 🚢 Production Deployment

### Deploying Frontend
- Build the production bundle: `npm run build` inside `frontend/`
- Deploy output `dist/` directory to **Vercel**, **Netlify**, or **Render Static Site**.

### Deploying Backend & WebSockets
- Deploy `backend/` to **Render Web Service**, **Railway**, **Fly.io**, or **AWS EC2**.
- Ensure WebSockets are enabled and configure `FRONTEND_URL` in environment variables for CORS.

---

## 📄 License & Credits

Designed & Developed with high precision by **KEOS Labs / Sherry Keos**.

- **Author / Lead Engineer:** Sharad Kumar ([GitHub](https://github.com/sherrykeos) · [LinkedIn](https://www.linkedin.com/in/sharad--kumar/))
- **Support Contact:** `shaj7492@gmail.com`
- **Studio:** [KEOS Studio](https://keos.studio)

*Copyright © 2026 KEOS Labs. All rights reserved.*
