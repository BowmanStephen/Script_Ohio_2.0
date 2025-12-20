#!/usr/bin/env python3
"""
Add public betting consensus for contrarian analysis
"""

from pathlib import Path

import pandas as pd

print("💰 ADDING PUBLIC BETTING CONSENSUS")
print("=" * 80)

# Load V6
v6 = pd.read_csv(
    sorted(Path("predictions").glob("ULTIMATE_v6_bowl_predictions_*.csv"))[-1]
)

# Public consensus data from Covers.com (as of Dec 17)
public_consensus = {
    "UNLV @ Ohio": {"public_pct": 72, "side": "UNLV", "total_picks": 286},
    "Western Kentucky @ Southern Miss": {
        "public_pct": 70,
        "side": "Western Kentucky",
        "total_picks": 257,
    },
    "Old Dominion @ South Florida": {
        "public_pct": 69,
        "side": "South Florida",
        "total_picks": 705,
    },
    "Washington State @ Utah State": {
        "public_pct": 67,
        "side": "Utah State",
        "total_picks": 405,
    },
    "Central Michigan @ Northwestern": {
        "public_pct": 67,
        "side": "Northwestern",
        "total_picks": 240,
    },
    "New Mexico @ Minnesota": {
        "public_pct": 64,
        "side": "Minnesota",
        "total_picks": 250,
    },
    "Georgia Southern @ Appalachian State": {
        "public_pct": 64,
        "side": "Appalachian State",
        "total_picks": 108,
    },
    "Georgia Tech @ BYU": {"public_pct": 63, "side": "BYU", "total_picks": 155},
    "North Texas @ San Diego State": {
        "public_pct": 62,
        "side": "North Texas",
        "total_picks": 143,
    },
    "Missouri State @ Arkansas State": {
        "public_pct": 62,
        "side": "Arkansas State",
        "total_picks": 502,
    },
    "James Madison @ Oregon": {"public_pct": 62, "side": "Oregon", "total_picks": 449},
    "Pittsburgh @ East Carolina": {
        "public_pct": 61,
        "side": "Pittsburgh",
        "total_picks": 163,
    },
    "FIU @ UTSA": {"public_pct": 61, "side": "FIU", "total_picks": 228},
    "Connecticut @ Army": {"public_pct": 61, "side": "Connecticut", "total_picks": 156},
    "Miami @ Texas A&M": {"public_pct": 60, "side": "Texas A&M", "total_picks": 492},
    "LSU @ Houston": {"public_pct": 59, "side": "Houston", "total_picks": 148},
    "California @ Hawaii": {"public_pct": 58, "side": "Hawaii", "total_picks": 271},
    "Louisiana @ Delaware": {"public_pct": 57, "side": "Louisiana", "total_picks": 592},
    "Virginia @ Missouri": {"public_pct": 55, "side": "Missouri", "total_picks": 147},
    "Penn State @ Clemson": {
        "public_pct": 54,
        "side": "Penn State",
        "total_picks": 162,
    },
    "Western Michigan @ Kennesaw State": {
        "public_pct": 52,
        "side": "Western Michigan",
        "total_picks": 471,
    },
}

# Add to V6
added = 0
for idx, row in v6.iterrows():
    matchup = row["Matchup"]

    # Check if we have consensus for this game
    if matchup in public_consensus:
        consensus = public_consensus[matchup]
        v6.at[idx, "Public_Pct"] = consensus["public_pct"]
        v6.at[idx, "Public_Side"] = consensus["side"]
        v6.at[idx, "Total_Public_Picks"] = consensus["total_picks"]

        # Contrarian indicator (70%+ on one side = fade opportunity)
        if consensus["public_pct"] >= 70:
            v6.at[idx, "Contrarian_Play"] = "🎯 STRONG FADE"
        elif consensus["public_pct"] >= 65:
            v6.at[idx, "Contrarian_Play"] = "⚠️ FADE ALERT"
        elif consensus["public_pct"] <= 55:
            v6.at[idx, "Contrarian_Play"] = "⚖️ BALANCED"
        else:
            v6.at[idx, "Contrarian_Play"] = "✅ MODERATE"

        added += 1

# Save V7 (final final)
output = f"predictions/ULTIMATE_v7_bowl_predictions_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
v6.to_csv(output, index=False)

print(f"✅ Added public consensus to {added} games")
print(f"✅ Saved V7: {output}")
print(f"✅ Total columns: {len(v6.columns)}")
print("\n📊 Contrarian Opportunities:")
print(
    f"  🎯 STRONG FADE (70%+): {len(v6[v6['Contrarian_Play'] == '🎯 STRONG FADE'])} games"
)
print(
    f"  ⚠️ FADE ALERT (65-69%): {len(v6[v6['Contrarian_Play'] == '⚠️ FADE ALERT'])} games"
)
print("=" * 80)
