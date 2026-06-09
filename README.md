# FriendShore Supply Chain De-Risking Engine

AI-powered supply chain risk analyzer for defense contractors — identifies Chinese/Russian/Iranian supplier dependencies, single points of failure, and recommends allied-nation alternatives.

Built for the defense acquisition and national security market (Leidos, SAIC, Booz Allen Hamilton, primes and sub-contractors).

---

## What It Does

1. **Upload a BOM** — paste or upload any Bill of Materials (CSV, text, free-form)
2. **AI Parsing** — Claude extracts suppliers, countries, tiers, and components automatically
3. **Graph Analysis** — NetworkX builds a directed dependency graph and computes risk scores
4. **Risk Scoring** — each supplier scored 0–100 based on country risk, single-point-of-failure status, and concentration
5. **SPF Detection** — articulation point analysis identifies suppliers whose loss would break the supply chain
6. **Friendshore Alternatives** — Claude recommends allied-nation replacements for every high-risk supplier

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.12 |
| Graph engine | NetworkX (articulation points, directed graphs) |
| Visualization | matplotlib (PNG graph rendering) |
| AI | Claude Haiku (BOM parsing + alternative suggestions) |
| Database | SQLite + SQLAlchemy 2.0 |
| Frontend | Jinja2 templates + vanilla CSS |
| Deploy | Render (free tier) |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/JaKPoT-Sudo/friendshore-supply-chain.git
cd friendshore-supply-chain

# 2. Add your Anthropic API key
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY=sk-ant-...

# 3. Run (Windows)
START_HERE.bat

# Or manually:
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\uvicorn main:app --reload
```

Open http://localhost:8000

---

## Demo

Load the pre-built AESA radar supply chain demo at `/seed`. Shows:

- 11 suppliers across 3 tiers
- 3 high-risk Chinese suppliers (Longhua Microelectronics, Yangtze Memory Technologies, CMOC International)
- 1 single point of failure (GaAs wafers — Longhua is the only source)
- Friendshore alternatives from II-VI, Qorvo, Micron, Kioxia, and others

---

## API Keys Required

| Key | Where to get it | Cost |
|-----|----------------|------|
| `ANTHROPIC_API_KEY` | console.anthropic.com | ~$0.01/analysis (Haiku model) |

---

## Risk Scoring Model

| Factor | Weight |
|--------|--------|
| High-risk country (China, Russia, Iran, NK…) | +40 |
| Single point of failure (articulation point) | +30 |
| High tier concentration (supplies 3+ customers) | +20 |
| Missing country data | +10 |
| **Max score** | **100** |

Risk levels: High (≥60) · Medium (≥30) · Low (<30)

---

## Deployment (Render)

1. Push to GitHub
2. Connect repo at render.com → New Web Service
3. Set `ANTHROPIC_API_KEY` as an Environment Secret in the Render dashboard
4. Deploy — Render auto-detects `render.yaml`

---

## Tests

```bash
venv\Scripts\python.exe -m pytest tests/ -v
# 15 passed in 0.74s
```

Tests cover: country risk classification, node scoring, SPF detection, graph builder integration.

---

*DEMONSTRATION ONLY — synthetic data — not for operational use*
