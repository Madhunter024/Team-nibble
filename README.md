# 🛡️ Nibdefender

**Nibdefender** is an AI-powered, real-time threat detection and rate-limiting system built for high-concurrency API protection. Developed during a 48-hour hackathon, Nibdefender combines FastAPI backend security middleware, Scikit-learn anomaly detection, LangChain automated incident reporting, and a Tremor dashboard for real-time observability.

---

## 🏗️ Monorepo Architecture

```
Nibdefender/
├── backend/               # FastAPI Security Gateway & Middleware
│   ├── main.py            # Entry point & CORS/route registration
│   ├── middleware/        # Redis rate-limiting & PyJWT verification
│   ├── routes/            # Honeypot & dummy endpoints for attacker simulation
│   └── requirements.txt
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

## 🚀 Quick Start Guide

### 1. Backend Setup (FastAPI & Redis)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup (Next.js & Tremor)
```bash
cd frontend
npm install
npm run dev
```

### 3. ML Engine Setup (Scikit-learn & LangChain)
```bash
cd ml_engine
python -m venv venv
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

### 💻 OS-Specific Installation Commands

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

## 🔒 Key Features
- **Redis IP Rate Limiting & Blocking:** Dynamic IP throttling and immediate blocking of flagged malicious addresses.
- **JWT Authentication Guard:** Token validation and access control middleware.
- **ML Anomaly Detection:** IsolationForest model trained on request velocity, entropy, and payload anomalies.
- **AI-Powered Incident Reports:** LLM-generated analysis summarizing detected security incidents in human-readable reports.
- **Real-Time Tremor Dashboard:** Live threat feed visualizer and operational security metrics.

