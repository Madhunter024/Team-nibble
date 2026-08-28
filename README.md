# 🛡️ Nibdefender

**Nibdefender** is an AI-powered, real-time threat detection and rate-limiting system built for high-concurrency API protection. Nibdefender combines FastAPI backend security middleware, Redis sliding-window rate limiting, Scikit-learn anomaly detection, LangChain automated incident reporting, and a Tremor dashboard for real-time observability.


---

## 🏗️ Monorepo Architecture

```
Nibdefender/
├── backend/               # FastAPI Security Gateway & Middleware
│   ├── config.py          # Pydantic Settings configuration & env parser
│   ├── main.py            # Gateway entry point, lifespan & route registration
│   ├── middleware/        # Redis rate-limiting, IP blacklisting & PyJWT
│   │   ├── __init__.py
│   │   ├── rate_limiter.py # Sliding-window rate limiter & dynamic IP blocker
│   │   ├── redis_rate_limit.py # ThreatTracker singleton & metric metrics
│   │   └── jwt_auth.py
│   ├── routes/            # Honeypot & dummy endpoints for attacker simulation
│   └── requirements.txt   # Backend Python dependencies
├── frontend/              # Next.js & Tremor Security Operations Dashboard
│   ├── app/               # Next.js App Router (page.tsx, layout.tsx)
│   ├── components/        # Dashboard shell & Scrolling ThreatFeed log
│   ├── lib/               # API fetching utilities
│   └── package.json
├── ml_engine/             # Anomaly Detection & AI Incident Generator
│   ├── train_model.py     # Synthetic data generation & IsolationForest trainer
│   ├── inference.py       # Real-time anomaly detection pipeline
│   ├── ai_reporter.py     # LangChain / OpenAI security report generator
│   └── requirements.txt
├── scripts/               # Attacker Simulation Suite
│   └── attacker.py        # Automated attack script (DDoS, SQLi, Auth Brute-force)
├── .env.example           # Shared environment variables
├── .gitignore
└── README.md
```

---

## 📦 Backend Dependencies & Requirements

The Nibdefender backend gateway relies on the following core Python libraries:

| Dependency | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **`fastapi`** | `0.110.0` | High-performance ASGI web framework |
| **`uvicorn[standard]`** | `0.28.0` | Production ASGI web server with `httptools` & `uvloop` |
| **`redis`** | `5.0.0` | Async Redis client (`redis.asyncio`) for ZSET sliding-window rate limiting & IP blacklisting |
| **`pydantic`** | `2.6.0` | Strict data validation & type enforcement |
| **`pydantic-settings`** | `2.2.0` | Environment settings management parsing `.env` file |
| **`pyjwt`** | `2.8.0` | JSON Web Token encoding and verification |
| **`python-dotenv`** | `1.0.0` | Loading environment variables from `.env` |
| **`httpx`** | `0.27.0` | Async HTTP client for endpoint testing and health verification |
| **`requests`** | `2.31.0` | Synchronous HTTP request utility |

---

## 🚀 Quick Start Guide

### 1. Backend Setup (FastAPI & Redis)

#### **Step 1: Navigate to the `backend/` directory**
```bash
cd backend
```

#### **Step 2: Create & activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### **Step 3: Install all backend dependencies**
```bash
pip install -r requirements.txt
```

#### **Step 4: Configure environment variables (optional)**
```bash
cp ../.env.example .env
```

#### **Step 5: Start the FastAPI Gateway server**
```bash
uvicorn main:app --reload --port 8000
```
*The API gateway will start on `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.*

---

### 2. Frontend Setup (Next.js & Tremor)
```bash
cd frontend
npm install
npm run dev
```

### 3. ML Engine Setup (Scikit-learn & LangChain)
```bash
cd ml_engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python train_model.py  # Train IsolationForest model
python inference.py    # Test anomaly prediction
```

### 4. Run Attacker Simulation
```bash
cd scripts
python attacker.py
```

---

## 🛠️ Prerequisites & System Dependencies Installation

Before running Nibdefender, ensure you have **Python (3.9+)**, **Node.js (18+)**, **npm**, and **Redis Server** installed on your system.

### Required Software & Tools
| Dependency | Recommended Version | Purpose |
| :--- | :--- | :--- |
| **Python** | 3.9+ | Backend (FastAPI), ML Engine, Attacker Simulation |
| **Node.js & npm** | Node v18+ / npm v9+ | Frontend Dashboard (Next.js & Tremor) |
| **Redis Server** | 6.x / 7.x | IP Rate Limiting & High-Speed Blocking Storage |
| **Git** | Latest | Version control |

---

### 💻 OS-Specific System Installation Commands

#### 🍎 macOS (via Homebrew)
```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python, Node.js, and Redis
brew install python node redis git

# 3. Start Redis Server service
brew services start redis
```

#### 🐧 Linux (Ubuntu / Debian)
```bash
# 1. Update package lists
sudo apt update && sudo apt upgrade -y

# 2. Install Python, venv, Node.js, npm, Redis, and Git
sudo apt install -y python3 python3-pip python3-venv nodejs npm redis-server git

# 3. Start and enable Redis service
sudo systemctl enable --now redis-server
```

#### 🐧 Linux (Fedora / RHEL)
```bash
sudo dnf install -y python3 python3-pip nodejs redis git
sudo systemctl enable --now redis
```

#### 🐧 Linux (Arch Linux)
```bash
sudo pacman -S python python-pip nodejs npm redis git
sudo systemctl enable --now redis
```

#### 🪟 Windows

**Option A: Using Windows Package Manager (`winget` in PowerShell)**
```powershell
# 1. Install Python, Node.js, and Git
winget install Python.Python.3.11
winget install OpenJS.NodeJS.LTS
winget install Git.Git

# 2. Install Redis for Windows (or via Memurai / WSL2)
winget install Redis.Redis
```

**Option B: Using WSL2 (Windows Subsystem for Linux - Recommended for Redis)**
```bash
# Inside WSL Ubuntu Terminal:
sudo apt update
sudo apt install -y python3 python3-venv nodejs npm redis-server
sudo service redis-server start
```

---

## 📡 Backend API Contract & Health Check

### Health Verification Endpoint (`GET /health`)
Verifies application operational state and async Redis ping status:
```json
{
  "status": "healthy",
  "redis": "connected"
}
```

### Threat Metrics Endpoint (`GET /api/threat-metrics`)
Returns operational security metrics, Redis-blocked IP sets, and security alerts for the dashboard:
```json
{
  "total_requests": 150,
  "blocked_ips_count": 2,
  "blocked_ips_list": ["192.168.1.105", "10.0.0.5"],
  "recent_alerts": [
    {
      "id": "alert_c91f42a0",
      "timestamp": "2026-08-28T21:10:00Z",
      "severity": "CRITICAL",
      "message": "IP 192.168.1.105 automatically blacklisted for 1hr after 3 consecutive rate limit breaches."
    }
  ]
}
```

---

## 🔒 Key Features
- **Redis IP Rate Limiting & Blocking:** Dynamic IP throttling via ZSET sliding window and automatic 1-hour blacklisting after repeated limit breaches.
- **Pydantic Settings Management:** Centralized environment variable parsing from `.env`.
- **JWT Authentication Guard:** Token validation and access control middleware.
- **ML Anomaly Detection:** IsolationForest model trained on request velocity, entropy, and payload anomalies.
- **AI-Powered Incident Reports:** LLM-generated analysis summarizing detected security incidents in human-readable reports.
- **Real-Time Tremor Dashboard:** Live threat feed visualizer and operational security metrics.
