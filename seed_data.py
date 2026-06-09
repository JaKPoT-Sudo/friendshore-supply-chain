"""
seed_data.py — Demo supply chain data for FriendShore.

Represents a fictional AESA radar prime contractor's Tier 1-3 supply chain,
seeded with known-risky Chinese suppliers to demonstrate the tool's value.

All company names and relationships are FICTIONAL / SYNTHETIC.
"""

from __future__ import annotations

DEMO_ANALYSES = [
    {
        "name": "AESA Radar System — DefenseTech Solutions BOM Analysis",
        "source_text": "See demo — synthetic data",
        "overall_risk_score": 72,
        "bottom_line": (
            "Critical dependency on two Chinese semiconductor suppliers (Longhua Microelectronics "
            "and Yangtze Memory Technologies) creates significant supply chain vulnerability. "
            "Longhua is a single point of failure for GaAs wafer supply. Immediate reshoring "
            "action recommended before next NDAA section 889 compliance review."
        ),
        "risk_summary": (
            "Three high-risk suppliers identified in Tier 2 and Tier 3. Chinese-sourced GaAs "
            "wafers and NAND flash represent the most critical exposures. Samsung Electro-Mechanics "
            "concentration across two Tier-1 suppliers creates a secondary resilience risk."
        ),
        "single_points_of_failure": ["Longhua Microelectronics"],
        "alternative_suggestions": [
            {
                "original_supplier": "Longhua Microelectronics",
                "component": "GaAs wafers",
                "alternatives": [
                    {
                        "company": "II-VI Incorporated",
                        "country": "USA",
                        "rationale": "Leading domestic GaAs/InP wafer manufacturer with DoD qualification; established supply agreements with major defense primes."
                    },
                    {
                        "company": "Qorvo",
                        "country": "USA",
                        "rationale": "Vertically integrated compound semiconductor manufacturer; ITAR-compliant, CMMC certified, active in AESA programs."
                    },
                    {
                        "company": "IQE PLC",
                        "country": "UK",
                        "rationale": "Five Eyes partner nation; world's largest independent epiwafer supplier with US manufacturing presence."
                    }
                ]
            },
            {
                "original_supplier": "Yangtze Memory Technologies",
                "component": "NAND flash",
                "alternatives": [
                    {
                        "company": "Micron Technology",
                        "country": "USA",
                        "rationale": "US-headquartered NAND manufacturer; domestic fabs in Boise ID; qualified for defense-grade flash storage."
                    },
                    {
                        "company": "Samsung Semiconductor (US div.)",
                        "country": "USA",
                        "rationale": "New Austin TX fab; US-origin NAND available with proper contractual sourcing requirements."
                    },
                    {
                        "company": "Kioxia (formerly Toshiba Memory)",
                        "country": "Japan",
                        "rationale": "Allied nation; Japan NAND manufacturing; preferred alternative for DoD programs avoiding YMTC."
                    }
                ]
            }
        ],
        "nodes": [
            {"name": "DefenseTech Solutions",      "country": "USA",         "tier": 0, "component": None,                   "is_focal": True},
            {"name": "Raytheon Components Group",  "country": "USA",         "tier": 1, "component": "RF/microwave modules", "is_focal": False},
            {"name": "BAE Systems Electronics",    "country": "UK",          "tier": 1, "component": "Antenna arrays",       "is_focal": False},
            {"name": "Shimadzu Defense",           "country": "Japan",       "tier": 1, "component": "Signal processors",    "is_focal": False},
            {"name": "Longhua Microelectronics",   "country": "China",       "tier": 2, "component": "GaAs wafers",          "is_focal": False},
            {"name": "Texas Instruments Defense",  "country": "USA",         "tier": 2, "component": "FPGAs",                "is_focal": False},
            {"name": "Infineon Technologies",      "country": "Germany",     "tier": 2, "component": "Power modules",        "is_focal": False},
            {"name": "Samsung Electro-Mechanics",  "country": "South Korea", "tier": 2, "component": "MLCC capacitors",      "is_focal": False},
            {"name": "Yangtze Memory Technologies","country": "China",       "tier": 2, "component": "NAND flash",           "is_focal": False},
            {"name": "MP Materials",               "country": "USA",         "tier": 3, "component": "Rare earth metals",    "is_focal": False},
            {"name": "CMOC International",         "country": "China",       "tier": 3, "component": "Cobalt",               "is_focal": False},
        ],
        "edges": [
            {"supplier": "Raytheon Components Group",  "customer": "DefenseTech Solutions",     "component": "RF/microwave modules"},
            {"supplier": "BAE Systems Electronics",    "customer": "DefenseTech Solutions",     "component": "Antenna arrays"},
            {"supplier": "Shimadzu Defense",           "customer": "DefenseTech Solutions",     "component": "Signal processors"},
            {"supplier": "Longhua Microelectronics",   "customer": "Raytheon Components Group", "component": "GaAs wafers"},
            {"supplier": "Texas Instruments Defense",  "customer": "Raytheon Components Group", "component": "FPGAs"},
            {"supplier": "Infineon Technologies",      "customer": "BAE Systems Electronics",   "component": "Power modules"},
            {"supplier": "Samsung Electro-Mechanics",  "customer": "BAE Systems Electronics",   "component": "MLCC capacitors"},
            {"supplier": "Samsung Electro-Mechanics",  "customer": "Shimadzu Defense",          "component": "MLCC capacitors"},
            {"supplier": "Yangtze Memory Technologies","customer": "Shimadzu Defense",          "component": "NAND flash"},
            {"supplier": "MP Materials",               "customer": "Longhua Microelectronics",  "component": "Rare earth metals"},
            {"supplier": "CMOC International",         "customer": "Longhua Microelectronics",  "component": "Cobalt"},
        ],
    }
]
