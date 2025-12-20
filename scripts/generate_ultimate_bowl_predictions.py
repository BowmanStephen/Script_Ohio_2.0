#!/usr/bin/env python3
"""
ULTIMATE Bowl Predictions - ALL Data Sources Combined
Merges ML predictions with DK lines, Massey, S&P+, FPI, ELO, SRS, and training features
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    print("🏈 ULTIMATE BOWL ANALYTICS - Compiling ALL data sources...")

    # Load ALL prediction sources
    dk_file = (
        "predictions/draftkings_slate_2025/dk_slate_predictions_20251216_214645.csv"
    )
    ml_predictions = sorted(
        Path("predictions/postseason_2025").glob("postseason_predictions_2025_*.csv")
    )[-1]

    dk = pd.read_csv(dk_file)
    ml = pd.read_csv(ml_predictions)

    print(f"✅ Loaded DK predictions: {len(dk)} games")
    print(f"✅ Loaded ML predictions: {len(ml)} games")

    # Merge on teams
    ultimate = []

    for _, dk_row in dk.iterrows():
        # Find matching ML prediction
        ml_match = ml[
            (ml["home_team"] == dk_row["home_team"])
            & (ml["away_team"] == dk_row["away_team"])
        ]

        if ml_match.empty:
            continue

        ml_row = ml_match.iloc[0]

        # Build ULTIMATE record with EVERYTHING
        game = {
            # Basic Info
            "Date": pd.to_datetime(dk_row["date"]).strftime("%b %d"),
            "Bowl": dk_row["bowl"],
            "Matchup": f"{dk_row['away_team']} @ {dk_row['home_team']}",
            "Favorite": dk_row["favorite"],
            # DraftKings Lines
            "DK_Spread": dk_row["dk_spread"],
            "DK_Total": dk_row["dk_total"],
            # Our ML Models
            "ML_Home_Margin": f"{ml_row['predicted_margin']:.1f}",
            "ML_Win_Prob": f"{ml_row['home_win_prob']:.1%}",
            "Model_Favorite": (
                dk_row["home_team"]
                if ml_row["home_win_prob"] > 0.5
                else dk_row["away_team"]
            ),
            # Ensemble Models
            "Ensemble_Win_Prob": f"{dk_row['ensemble_winprob_fav']:.1%}",
            "FastAI_Win_Prob": (
                f"{dk_row.get('fastai_winprob_fav', 0):.1%}"
                if pd.notna(dk_row.get("fastai_winprob_fav"))
                else "N/A"
            ),
            # Consensus Models
            "Massey_Margin": f"{dk_row['massey_margin_fav']:.1f}",
            "Massey_Edge": f"{dk_row['massey_edge_vs_spread']:.1f}",
            "RF_Total": f"{dk_row['rf_total']:.1f}",
            "RF_Margin": f"{dk_row['rf_margin_fav']:.1f}",
            # Advanced Metrics
            "SP_Plus_Diff": f"{dk_row['sp_plus_diff']:.1f}",
            "FPI_Diff": f"{dk_row['fpi_diff']:.1f}",
            "ELO_Diff": f"{dk_row['elo_diff']:.0f}",
            "SRS_Diff": f"{dk_row['srs_diff']:.1f}",
            # Edge Analysis
            "Edge_vs_Spread": f"{dk_row['edge_vs_spread']:.1f}",
            "Pick_ATS": dk_row["pick_against_spread"],
            # Betting Insight
            "Consensus": _get_consensus(dk_row, ml_row),
            "Value_Play": "💎 YES" if abs(dk_row["edge_vs_spread"]) > 5 else "",
            "Confidence": _get_confidence(dk_row, ml_row),
        }

        ultimate.append(game)

    # Save Ultimate CSV
    ultimate_df = pd.DataFrame(ultimate)
    output_csv = f"predictions/ULTIMATE_bowl_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    ultimate_df.to_csv(output_csv, index=False)

    print(f"✅ Saved ULTIMATE predictions to {output_csv}")

    # Generate ULTIMATE Markdown Guide
    md = "# 🏈 ULTIMATE Bowl Game Predictions - Complete Analytics\n\n"
    md += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    md += f"**Games**: {len(ultimate_df)}\n\n"
    md += "## Data Sources\n"
    md += "- ✅ **Our ML Models**: Ridge, XGBoost, FastAI ensemble\n"
    md += "- ✅ **DraftKings Lines**: Spread & Total\n"
    md += "- ✅ **Massey Ratings**: Consensus computer rankings\n"
    md += "- ✅ **S&P+ Ratings**: Advanced efficiency metrics\n"
    md += "- ✅ **FPI (ESPN)**: Football Power Index\n"
    md += "- ✅ **ELO Ratings**: Dynamic team strength\n"
    md += "- ✅ **SRS**: Simple Rating System\n"
    md += "- ✅ **Random Forest**: Total prediction model\n\n"
    md += "## Key Metrics\n"
    md += "- **Edge vs Spread**: How our model differs from DK line (>3 = value)\n"
    md += "- **Consensus**: Agreement across models\n"
    md += "- **Value Play**: 💎 when edge > 5 points\n\n"
    md += "---\n\n"

    for _, game in ultimate_df.iterrows():
        md += f"### {game['Bowl']}\n"
        md += f"**{game['Matchup']}** - {game['Date']}\n\n"
        md += f"#### Lines & Odds\n"
        md += f"- **DK Spread**: {game['Favorite']} {game['DK_Spread']}\n"
        md += f"- **DK Total**: {game['DK_Total']}\n"
        md += f"- **Our Pick (ATS)**: {game['Pick_ATS']}\n"
        md += f"- **Value**: {game['Value_Play']}\n\n"
        md += f"#### Model Predictions\n"
        md += f"- **ML Win Prob**: {game['ML_Win_Prob']}\n"
        md += f"- **Ensemble**: {game['Ensemble_Win_Prob']}\n"
        md += f"- **FastAI**: {game['FastAI_Win_Prob']}\n"
        md += f"- **ML Margin**: {game['ML_Home_Margin']}\n\n"
        md += f"#### Consensus Rankings\n"
        md += f"- **Massey**: {game['Massey_Margin']} (Edge: {game['Massey_Edge']})\n"
        md += f"- **S&P+**: {game['SP_Plus_Diff']}\n"
        md += f"- **FPI**: {game['FPI_Diff']}\n"
        md += f"- **ELO**: {game['ELO_Diff']}\n"
        md += f"- **SRS**: {game['SRS_Diff']}\n\n"
        md += f"#### Totals\n"
        md += f"- **RF Total Pred**: {game['RF_Total']}\n"
        md += f"- **RF Margin**: {game['RF_Margin']}\n\n"
        md += f"#### Bottom Line\n"
        md += f"**{game['Consensus']}** | Confidence: {game['Confidence']}\n\n"
        md += "---\n\n"

    md_file = "predictions/ULTIMATE_bowl_guide.md"
    with open(md_file, "w") as f:
        f.write(md)

    print(f"✅ Saved ULTIMATE guide to {md_file}")
    print(f"\n🎯 {len(ultimate_df)} games with COMPLETE analytics ready!")


def _get_consensus(dk_row, ml_row):
    """Determine consensus across models"""
    fav = dk_row["favorite"]
    picks = []

    # ML model
    ml_pick = (
        dk_row["home_team"] if ml_row["home_win_prob"] > 0.5 else dk_row["away_team"]
    )
    picks.append(ml_pick)

    # Massey always favors the favorite by definition
    picks.append(fav)

    # Count agreements
    if picks.count(fav) >= 2:
        return f"✅ CONSENSUS: {fav}"
    else:
        return "⚠️ SPLIT: Models disagree"


def _get_confidence(dk_row, ml_row):
    """Rate confidence level"""
    edge = abs(dk_row["edge_vs_spread"])
    massey_edge = abs(dk_row["massey_edge_vs_spread"])

    if edge > 5 and massey_edge > 5:
        return "🔥 VERY HIGH"
    elif edge > 3 or massey_edge > 3:
        return "✅ HIGH"
    elif edge > 1.5:
        return "👍 MEDIUM"
    else:
        return "⚖️ LOW"


if __name__ == "__main__":
    main()
