"""
config.py — FriendShore Supply Chain De-Risking Engine configuration.
All risk thresholds, country classifications, and model settings live here.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# --- API ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_MAX_TOKENS = 3000

# --- App ---
APP_TITLE = "FriendShore Supply Chain De-Risking Engine"
DEMO_MODE = True
DEMO_BANNER = "DEMONSTRATION ONLY — SYNTHETIC DATA — NOT FOR OPERATIONAL USE"
DATABASE_URL = "sqlite:///./friendshore.db"

# --- Graph rendering ---
GRAPH_OUTPUT_DIR = "static/graphs"

# --- Risk scoring ---
# Countries considered high-risk per US policy (USMCA, Xinjiang concerns, etc.)
HIGH_RISK_COUNTRIES = {
    "China", "PRC", "People's Republic of China", "Russia", "Iran",
    "North Korea", "DPRK", "Belarus", "Venezuela",
}

# Countries considered friendly / low-risk for supply chain purposes
FRIENDLY_NATIONS = {
    "United States", "USA", "US",
    "Mexico", "Canada",
    "United Kingdom", "UK",
    "Germany", "France", "Italy", "Netherlands", "Poland", "Czech Republic",
    "Japan", "South Korea", "Australia", "Taiwan",
    "Vietnam", "India", "Thailand", "Malaysia",
    "Israel",
}

# Risk score weights
RISK_WEIGHTS = {
    "high_risk_country": 40,      # supplier is in a high-risk nation
    "single_point_of_failure": 30, # only one supplier for a component
    "high_tier_concentration": 20, # one node supplies 3+ customers
    "missing_country_data": 10,    # country unknown
}

# Maximum risk score (sum of all weights = 100)
MAX_RISK_SCORE = 100
