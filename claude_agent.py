"""
claude_agent.py — Claude-powered BOM parsing and alternative supplier suggestions.

Two jobs:
  1. parse_bom()        — turn raw text (CSV, paste, etc.) into structured nodes + edges
  2. suggest_alternatives() — given high-risk suppliers, return friendshore alternatives
"""

from __future__ import annotations

import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MAX_TOKENS, CLAUDE_MODEL


class AgentError(Exception):
    pass


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_bom(raw_text: str) -> dict:
    """
    Send BOM text to Claude. Returns:
      {
        "company_name": str,
        "nodes": [{"name": str, "country": str|null, "tier": int, "component": str|null}],
        "edges": [{"supplier": str, "customer": str, "component": str|null}]
      }
    Raises AgentError on any failure.
    """
    prompt = f"""You are a defense supply chain analyst. Parse the following Bill of Materials (BOM) or supplier list and extract structured supply chain data.

Return ONLY valid JSON matching this exact schema (no markdown, no explanation):
{{
  "company_name": "The focal/prime company name — the one whose supply chain this is",
  "nodes": [
    {{"name": "Supplier Corp", "country": "USA", "tier": 1, "component": "RF modules"}},
    ...
  ],
  "edges": [
    {{"supplier": "Supplier Corp", "customer": "Prime Company", "component": "RF modules"}},
    ...
  ]
}}

Rules:
- "tier" 0 = the focal/prime company, tier 1 = direct suppliers, tier 2 = sub-suppliers, etc.
- If country is not mentioned, use null
- Include the focal company as a tier-0 node
- Every node must appear in at least one edge (except the focal company which is a customer)
- Use the actual company names from the text, not generic names

BOM TEXT:
{raw_text[:4000]}"""

    try:
        response = _get_client().messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text
        cleaned = _strip_fences(raw)
        result = json.loads(cleaned)
    except anthropic.APIError as exc:
        raise AgentError(f"Claude API error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AgentError(f"Claude returned invalid JSON: {exc}") from exc

    # Basic validation
    if "nodes" not in result or "edges" not in result:
        raise AgentError("Claude response missing 'nodes' or 'edges' keys")

    return result


def suggest_alternatives(
    high_risk_suppliers: list[dict],
    focal_company: str,
    industry_context: str = "defense electronics",
) -> list[dict]:
    """
    Given a list of high-risk supplier dicts (name, country, component),
    ask Claude for friendshore alternatives.

    Returns:
      [
        {
          "original_supplier": str,
          "component": str,
          "alternatives": [
            {"company": str, "country": str, "rationale": str}
          ]
        }
      ]
    """
    if not high_risk_suppliers:
        return []

    supplier_list = "\n".join(
        f"- {s.get('name','?')} ({s.get('country','unknown')}) — {s.get('component','?')}"
        for s in high_risk_suppliers
    )

    prompt = f"""You are a defense supply chain risk analyst specializing in reshoring and friendshoring.

The prime contractor "{focal_company}" operates in the {industry_context} sector.

The following suppliers are HIGH RISK (based in adversarial nations or single points of failure):
{supplier_list}

For each high-risk supplier, suggest 2-3 credible alternative suppliers from FRIENDLY nations (USA, Canada, Mexico, UK, Germany, France, Japan, South Korea, Australia, Taiwan, India).

Return ONLY valid JSON — an array matching this schema (no markdown):
[
  {{
    "original_supplier": "Longhua Microelectronics",
    "component": "GaAs wafers",
    "alternatives": [
      {{
        "company": "II-VI Incorporated",
        "country": "USA",
        "rationale": "Leading domestic GaAs wafer manufacturer, qualified for defense programs"
      }}
    ]
  }}
]

Use real companies where possible. If uncertain, use plausible company names and note it in the rationale."""

    try:
        response = _get_client().messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text
        cleaned = _strip_fences(raw)
        result = json.loads(cleaned)
    except anthropic.APIError as exc:
        raise AgentError(f"Claude API error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AgentError(f"Claude returned invalid JSON for alternatives: {exc}") from exc

    if not isinstance(result, list):
        raise AgentError("Claude alternatives response must be a JSON array")

    return result
