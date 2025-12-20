#!/usr/bin/env python3
"""
Enhanced Bowl Predictions with Rich Analytics
Generates detailed predictions using all available metrics for informed betting decisions
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def load_predictions():
    """Load latest postseason predictions"""
    pred_dir = Path("predictions/postseason_2025")
    latest = sorted(pred_dir.glob("postseason_predictions_2025_*.csv"))[-1]
    return pd.read_csv(latest)


def load_training_features():
    """Load rich feature data from training"""
    training_file = Path("data/training/weekly/training_data_2025_postseason.csv")
    if not training_file.exists():
        training_file = Path("data/processed/training/master_training_data_v2.csv")

    df = pd.read_csv(training_file)

    # Select key betting metrics
    feature_cols = [
        "id",
        "home_team",
        "away_team",
        "home_elo",
        "away_elo",
        "home_talent",
        "away_talent",
        "home_adjusted_epa",
        "away_adjusted_epa",
        "home_adjusted_epa_allowed",
        "away_adjusted_epa_allowed",
        "home_adjusted_explosiveness",
        "away_adjusted_explosiveness",
        "home_adjusted_success",
        "away_adjusted_success",
        "home_total_havoc_offense",
        "away_total_havoc_offense",
        "home_total_havoc_defense",
        "away_total_havoc_defense",
        "home_points_per_opportunity_offense",
        "away_points_per_opportunity_offense",
    ]

    available_cols = [c for c in feature_cols if c in df.columns]
    return df[available_cols]


def calculate_edges(row, features_df):
    """Calculate betting edges for a matchup"""
    game_id = row["id"]
    features = features_df[features_df["id"] == game_id]

    if features.empty:
        return {}

    ft = features.iloc[0]

    edges = {}

    # ELO Edge
    if pd.notna(ft.get("home_elo")) and pd.notna(ft.get("away_elo")):
        edges["elo_diff"] = ft["home_elo"] - ft["away_elo"]
        edges["elo_edge"] = (
            "Home"
            if edges["elo_diff"] > 50
            else ("Away" if edges["elo_diff"] < -50 else "Even")
        )

    # Talent Edge
    if pd.notna(ft.get("home_talent")) and pd.notna(ft.get("away_talent")):
        edges["talent_diff"] = ft["home_talent"] - ft["away_talent"]
        edges["talent_edge"] = (
            "Home"
            if edges["talent_diff"] > 0.02
            else ("Away" if edges["talent_diff"] < -0.02 else "Even")
        )

    # EPA Edge (Offensive Efficiency)
    if pd.notna(ft.get("home_adjusted_epa")) and pd.notna(ft.get("away_adjusted_epa")):
        edges["epa_off_diff"] = ft["home_adjusted_epa"] - ft["away_adjusted_epa"]
        edges["epa_edge"] = (
            "Home"
            if edges["epa_off_diff"] > 0.1
            else ("Away" if edges["epa_off_diff"] < -0.1 else "Even")
        )

    # Defensive EPA Edge
    if pd.notna(ft.get("home_adjusted_epa_allowed")) and pd.notna(
        ft.get("away_adjusted_epa_allowed")
    ):
        edges["epa_def_diff"] = (
            ft["away_adjusted_epa_allowed"] - ft["home_adjusted_epa_allowed"]
        )
        edges["def_edge"] = (
            "Home"
            if edges["epa_def_diff"] > 0.1
            else ("Away" if edges["epa_def_diff"] < -0.1 else "Even")
        )

    # Explosiveness Edge
    if pd.notna(ft.get("home_adjusted_explosiveness")) and pd.notna(
        ft.get("away_adjusted_explosiveness")
    ):
        edges["explosiveness_diff"] = (
            ft["home_adjusted_explosiveness"] - ft["away_adjusted_explosiveness"]
        )

    # Havoc Edge
    if pd.notna(ft.get("home_total_havoc_defense")) and pd.notna(
        ft.get("away_total_havoc_defense")
    ):
        edges["havoc_diff"] = (
            ft["home_total_havoc_defense"] - ft["away_total_havoc_defense"]
        )

    return edges


def generate_insight(row, edges):
    """Generate betting insight for a game"""
    insights = []

    # Check for statistical consensus
    advantages = []
    if edges.get("elo_edge") == "Home":
        advantages.append("ELO")
    if edges.get("talent_edge") == "Home":
        advantages.append("Talent")
    if edges.get("epa_edge") == "Home":
        advantages.append("EPA")
    if edges.get("def_edge") == "Home":
        advantages.append("Defense")

    away_advantages = []
    if edges.get("elo_edge") == "Away":
        away_advantages.append("ELO")
    if edges.get("talent_edge") == "Away":
        away_advantages.append("Talent")
    if edges.get("epa_edge") == "Away":
        away_advantages.append("EPA")
    if edges.get("def_edge") == "Away":
        away_advantages.append("Defense")

    # Confidence rating
    if len(advantages) >= 3:
        insights.append(f"🔥 STRONG: {row['home_team']} ({', '.join(advantages)})")
    elif len(away_advantages) >= 3:
        insights.append(f"🔥 STRONG: {row['away_team']} ({', '.join(away_advantages)})")
    elif len(advantages) >= 2:
        insights.append(f"✅ LEAN: {row['home_team']} ({', '.join(advantages)})")
    elif len(away_advantages) >= 2:
        insights.append(f"✅ LEAN: {row['away_team']} ({', '.join(away_advantages)})")
    else:
        insights.append("⚖️ EVEN: Statistical split")

    # Value indicators
    if edges.get("elo_diff", 0) > 100:
        insights.append("💎 VALUE: Large ELO gap")

    if abs(edges.get("explosiveness_diff", 0)) > 0.15:
        insights.append("⚡ EXPLOSIVE: Big playmaking edge")

    return " | ".join(insights)


def main():
    print("🏈 Generating Enhanced Bowl Predictions...")

    # Load data
    predictions = load_predictions()
    features = load_training_features()

    print(f"Loaded {len(predictions)} predictions")
    print(f"Loaded features for {len(features)} games")

    # Enhance predictions
    enhanced = []

    for idx, row in predictions.iterrows():
        edges = calculate_edges(row, features)
        insight = generate_insight(row, edges)

        # Build enhanced record
        game_date = pd.to_datetime(row["start_date"]).strftime("%b %d")

        enhanced_row = {
            "Date": game_date,
            "Matchup": f"{row['away_team']} @ {row['home_team']}",
            "Predicted_Winner": (
                row["home_team"] if row["home_win_prob"] > 0.5 else row["away_team"]
            ),
            "Win_Prob": f"{max(row['home_win_prob'], 1 - row['home_win_prob']):.1%}",
            "Predicted_Margin": f"{abs(row['predicted_margin']):.1f}",
            "ELO_Diff": (
                f"{edges.get('elo_diff', 0):.0f}" if edges.get("elo_diff") else "N/A"
            ),
            "Talent_Diff": (
                f"{edges.get('talent_diff', 0):.3f}"
                if edges.get("talent_diff")
                else "N/A"
            ),
            "EPA_Off_Diff": (
                f"{edges.get('epa_off_diff', 0):.2f}"
                if edges.get("epa_off_diff")
                else "N/A"
            ),
            "EPA_Def_Diff": (
                f"{edges.get('epa_def_diff', 0):.2f}"
                if edges.get("epa_def_diff")
                else "N/A"
            ),
            "Explosiveness": (
                f"{edges.get('explosiveness_diff', 0):.2f}"
                if edges.get("explosiveness_diff")
                else "N/A"
            ),
            "Havoc": (
                f"{edges.get('havoc_diff', 0):.2f}"
                if edges.get("havoc_diff")
                else "N/A"
            ),
            "Betting_Insight": insight,
        }

        enhanced.append(enhanced_row)

    # Save to CSV
    enhanced_df = pd.DataFrame(enhanced)
    output_file = f"predictions/enhanced_bowl_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    enhanced_df.to_csv(output_file, index=False)

    print(f"✅ Saved enhanced predictions to {output_file}")

    # Generate rich markdown guide
    md_output = "# 🏈 Enhanced Bowl Game Predictions - Full Analytics\n\n"
    md_output += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    md_output += "## Legend\n"
    md_output += "- **ELO Diff**: Team rating difference (>50 = significant edge)\n"
    md_output += (
        "- **Talent Diff**: 247Sports composite difference (>0.02 = talent gap)\n"
    )
    md_output += (
        "- **EPA Off/Def**: Expected Points Added per play (efficiency metrics)\n"
    )
    md_output += "- **Explosiveness**: Big play creation ability\n"
    md_output += "- **Havoc**: Defensive disruption rate\n\n"
    md_output += "## Games\n\n"

    for _, row in enhanced_df.iterrows():
        md_output += f"### {row['Matchup']}\n"
        md_output += f"**Date**: {row['Date']} | "
        md_output += (
            f"**Predicted Winner**: {row['Predicted_Winner']} ({row['Win_Prob']})\n\n"
        )
        md_output += f"**Analytics**:\n"
        md_output += f"- ELO Edge: {row['ELO_Diff']}\n"
        md_output += f"- Talent Edge: {row['Talent_Diff']}\n"
        md_output += f"- EPA Offensive: {row['EPA_Off_Diff']}\n"
        md_output += f"- EPA Defensive: {row['EPA_Def_Diff']}\n"
        md_output += f"- Explosiveness: {row['Explosiveness']}\n"
        md_output += f"- Havoc: {row['Havoc']}\n\n"
        md_output += f"**Betting Insight**: {row['Betting_Insight']}\n\n"
        md_output += "---\n\n"

    md_file = "predictions/enhanced_bowl_guide.md"
    with open(md_file, "w") as f:
        f.write(md_output)

    print(f"✅ Saved enhanced guide to {md_file}")
    print(f"\n🎯 Ready for betting with {len(enhanced_df)} games!")


if __name__ == "__main__":
    main()
