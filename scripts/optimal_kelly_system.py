#!/usr/bin/env python3
"""
OPTIMAL BETTING SYSTEM
Using Kelly Criterion + Sharp Betting Principles + Optimal Model Weighting
"""

from pathlib import Path

import numpy as np
import pandas as pd

print("🎯 CREATING OPTIMAL BETTING SYSTEM (KELLY CRITERION)")
print("=" * 80)

# Load V8 weighted
v8 = pd.read_csv(
    sorted(Path("predictions").glob("ULTIMATE_v8_WEIGHTED_bowl_predictions_*.csv"))[-1]
)

# ============================================================================
# OPTIMAL MODEL WEIGHTING (Based on Gambling Research)
# ============================================================================

OPTIMAL_WEIGHTS = {
    # Market-based models (40%) - Markets are ~52% efficient
    "live_consensus": 0.25,  # 25% - Wisdom of crowds + sharp action
    "sharp_money": 0.15,  # 15% - Line movement indicates sharp money
    # Established public models (35%) - Proven track records
    "massey": 0.12,  # 12% - Long-term accuracy
    "sagarin": 0.10,  # 10% - Historically strong
    "fpi": 0.08,  # 8% - ESPN backing, large dataset
    "sp_plus": 0.05,  # 5% - Good but newer
    # Rating systems (15%)
    "elo": 0.10,  # 10% - Simple, proven
    "talent": 0.05,  # 5% - Recruiting matters
    # Your models (10%) - Unproven in bowls
    "our_ml": 0.10,  # 10% - Conservative until validated
}

print("\n📊 OPTIMAL WEIGHTING (Gambling-Focused):")
print("-" * 80)
category_totals = {"Market": 0, "Public Models": 0, "Ratings": 0, "Your Models": 0}

for model, weight in OPTIMAL_WEIGHTS.items():
    if model in ["live_consensus", "sharp_money"]:
        cat = "Market"
    elif model in ["massey", "sagarin", "fpi", "sp_plus"]:
        cat = "Public Models"
    elif model in ["elo", "talent"]:
        cat = "Ratings"
    else:
        cat = "Your Models"
    category_totals[cat] += weight
    print(f"  {model:20s}: {weight:5.1%}")

print("\n📈 Category Totals:")
for cat, total in category_totals.items():
    print(f"  {cat:20s}: {total:5.1%}")

# ============================================================================
# KELLY CRITERION IMPLEMENTATION
# ============================================================================


def kelly_criterion(win_prob, decimal_odds, fractional=0.25):
    """
    Calculate Kelly Criterion bet size

    Args:
        win_prob: Probability of winning (0-1)
        decimal_odds: Decimal odds (e.g., 1.91 for -110)
        fractional: Fraction of full Kelly (0.25 = quarter Kelly)

    Returns:
        Recommended bet size as % of bankroll
    """
    if win_prob <= 0 or win_prob >= 1:
        return 0

    # Kelly formula: f* = (bp - q) / b
    # where b = decimal_odds - 1, p = win_prob, q = 1 - win_prob
    b = decimal_odds - 1
    p = win_prob
    q = 1 - p

    kelly_fraction = (b * p - q) / b

    # Apply fractional Kelly (conservative)
    bet_size = max(0, kelly_fraction * fractional)

    return bet_size


def american_to_decimal(american_odds):
    """Convert American odds to decimal"""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


# ============================================================================
# CALCULATE OPTIMAL BETS
# ============================================================================

optimal_bets = []

for idx, row in v8.iterrows():
    try:
        away, home = row["Matchup"].split(" @ ")
    except:
        continue

    # Recalculate with OPTIMAL weights
    predictions = []

    if pd.notna(row.get("Live_Consensus_Line")):
        predictions.append(
            float(row["Live_Consensus_Line"]) * OPTIMAL_WEIGHTS["live_consensus"]
        )

    if (
        pd.notna(row.get("Line_Movement_Points"))
        and abs(float(row["Line_Movement_Points"])) >= 2
    ):
        predictions.append(
            float(row["Line_Movement_Points"]) * OPTIMAL_WEIGHTS["sharp_money"]
        )

    if pd.notna(row.get("Massey_Margin")):
        predictions.append(float(row["Massey_Margin"]) * OPTIMAL_WEIGHTS["massey"])

    if pd.notna(row.get("FPI_Diff")):
        predictions.append(float(row["FPI_Diff"]) * OPTIMAL_WEIGHTS["fpi"])

    if pd.notna(row.get("SP_Plus_Diff")):
        predictions.append(float(row["SP_Plus_Diff"]) * OPTIMAL_WEIGHTS["sp_plus"])

    if pd.notna(row.get("ELO_Diff")):
        predictions.append(float(row["ELO_Diff"]) * OPTIMAL_WEIGHTS["elo"])

    if pd.notna(row.get("ML_Home_Margin")):
        predictions.append(float(row["ML_Home_Margin"]) * OPTIMAL_WEIGHTS["our_ml"])

    if not predictions:
        continue

    optimal_margin = sum(predictions)

    # Calculate edge vs DK spread
    if pd.notna(row.get("DK_Spread")):
        dk_spread = float(row["DK_Spread"])
        edge = abs(optimal_margin) - abs(dk_spread)

        # Only bet if edge > 2.5% (covers vig + some cushion)
        if edge >= 1.0:  # 1 point = ~2.5% edge roughly
            # Convert margin to win probability (rough approximation)
            # 3 points = ~60% favorite, 7 points = ~70%, 14 points = ~85%
            win_prob = 0.5 + (optimal_margin / 28.0)  # Simplified conversion
            win_prob = max(0.52, min(0.95, win_prob))  # Clamp between 52-95%

            # Standard -110 odds = 1.909 decimal
            decimal_odds = 1.909

            # Calculate Kelly (using 25% fractional for safety)
            kelly_pct = kelly_criterion(win_prob, decimal_odds, fractional=0.25)

            # Unit sizing (1 unit = 1% of bankroll typically)
            units = kelly_pct * 100

            # Classification
            if units >= 3.0:
                tier = "🔥 MAX PLAY"
            elif units >= 2.0:
                tier = "✅ STRONG"
            elif units >= 1.0:
                tier = "👍 SOLID"
            elif units >= 0.5:
                tier = "⚖️ SMALL"
            else:
                continue  # Don't bet if < 0.5 units

            optimal_bets.append(
                {
                    "Matchup": row["Matchup"],
                    "Pick": home if optimal_margin < 0 else away,
                    "Edge": edge,
                    "Win_Prob": win_prob,
                    "Kelly_%": kelly_pct * 100,
                    "Units": units,
                    "Tier": tier,
                    "Optimal_Margin": optimal_margin,
                    "DK_Spread": dk_spread,
                }
            )

# Create dataframe
bets_df = pd.DataFrame(optimal_bets)
bets_df = bets_df.sort_values("Units", ascending=False)

# Save
output = "predictions/OPTIMAL_KELLY_BETS.csv"
bets_df.to_csv(output, index=False)

print(f"\n✅ Created {len(bets_df)} optimal bets")
print(f"✅ Saved to: {output}")

print(f"\n🎯 BET DISTRIBUTION:")
print("-" * 80)
for tier in ["🔥 MAX PLAY", "✅ STRONG", "👍 SOLID", "⚖️ SMALL"]:
    tier_bets = bets_df[bets_df["Tier"] == tier]
    if len(tier_bets) > 0:
        total_units = tier_bets["Units"].sum()
        print(f"\n{tier} ({len(tier_bets)} bets, {total_units:.1f} total units):")
        for _, bet in tier_bets.head(5).iterrows():
            print(f"  • {bet['Pick']:25s} ({bet['Matchup'][:40]:40s})")
            print(
                f"    Edge: {bet['Edge']:+5.1f} | Win%: {bet['Win_Prob']:.1%} | Kelly: {bet['Kelly_%']:.2f}% | Units: {bet['Units']:.2f}"
            )

print("\n" + "=" * 80)
print("💡 RECOMMENDATIONS:")
print("=" * 80)
print("1. Use 25% fractional Kelly (already implemented) - reduces variance")
print("2. Only bet when edge ≥ 1 point (~2.5%)")
print(
    "3. Total bankroll allocation: " + f"{bets_df['Kelly_%'].sum():.1f}% (diversified)"
)
print("4. Max single bet: " + f"{bets_df['Kelly_%'].max():.2f}% of bankroll")
print("5. Track results to validate model weights")
print("=" * 80)
