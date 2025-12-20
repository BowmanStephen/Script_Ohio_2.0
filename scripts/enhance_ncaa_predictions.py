#!/usr/bin/env python3
"""
Enhance ncaapredictions.csv with all V4 analytics
"""

from pathlib import Path

import pandas as pd

print("📊 Enhancing ncaapredictions.csv with V4 Analytics")
print("=" * 80)

# Load current NCAA predictions
ncaa_current = pd.read_csv("predictions/ncaapredictions.csv")
print(
    f"Current NCAA predictions: {len(ncaa_current)} games, {len(ncaa_current.columns)} columns"
)

# Load V4 with all analytics
v4 = pd.read_csv(
    sorted(Path("predictions").glob("ULTIMATE_v4_bowl_predictions_*.csv"))[-1]
)
print(f"V4 predictions: {len(v4)} games, {len(v4.columns)} columns")

# Merge V4 data into NCAA predictions by matching teams
enhanced = []

for _, ncaa_row in ncaa_current.iterrows():
    # Try to find matching game in V4
    ncaa_matchup = ncaa_row.get("matchup", "") or ncaa_row.get("Matchup", "")

    # Find matching V4 row
    v4_match = v4[v4["Matchup"] == ncaa_matchup]

    if not v4_match.empty:
        # Merge all V4 columns
        merged_row = ncaa_row.to_dict()
        v4_row = v4_match.iloc[0].to_dict()

        # Add key V4 metrics
        merged_row["V4_Home_ELO"] = v4_row.get("Home_ELO", "N/A")
        merged_row["V4_Away_ELO"] = v4_row.get("Away_ELO", "N/A")
        merged_row["V4_ELO_Diff"] = v4_row.get("ELO_Diff", "N/A")
        merged_row["V4_Home_Talent"] = v4_row.get("Home_Talent", "N/A")
        merged_row["V4_Away_Talent"] = v4_row.get("Away_Talent", "N/A")
        merged_row["V4_Talent_Diff"] = v4_row.get("Talent_Diff", "N/A")
        merged_row["V4_Home_EPA"] = v4_row.get("Home_EPA", "N/A")
        merged_row["V4_Away_EPA"] = v4_row.get("Away_EPA", "N/A")
        merged_row["V4_Home_Success_Rate"] = v4_row.get("Home_Success", "N/A")
        merged_row["V4_Away_Success_Rate"] = v4_row.get("Away_Success", "N/A")
        merged_row["V4_Home_Explosive_Rate"] = v4_row.get("Home_Explosive_Rate", "N/A")
        merged_row["V4_Away_Explosive_Rate"] = v4_row.get("Away_Explosive_Rate", "N/A")
        merged_row["V4_Home_Recent_Form"] = v4_row.get("Home_Recent_Form", "N/A")
        merged_row["V4_Away_Recent_Form"] = v4_row.get("Away_Recent_Form", "N/A")
        merged_row["V4_Momentum"] = v4_row.get("Momentum", "N/A")
        merged_row["V4_Home_Rest_Days"] = v4_row.get("Home_Rest_Days", "N/A")
        merged_row["V4_Away_Rest_Days"] = v4_row.get("Away_Rest_Days", "N/A")
        merged_row["V4_Rest_Advantage"] = v4_row.get("Rest_Advantage", "N/A")
        merged_row["V4_Confidence"] = v4_row.get("Confidence", "N/A")
        merged_row["V4_Pick_ATS"] = v4_row.get("Pick_ATS", "N/A")
        merged_row["V4_Edge_vs_Spread"] = v4_row.get("Edge_vs_Spread", "N/A")
        merged_row["V4_Value_Play"] = v4_row.get("Value_Play", "N/A")
        merged_row["V4_Massey_Margin"] = v4_row.get("Massey_Margin", "N/A")
        merged_row["V4_SP_Plus_Diff"] = v4_row.get("SP_Plus_Diff", "N/A")
        merged_row["V4_FPI_Diff"] = v4_row.get("FPI_Diff", "N/A")
        merged_row["V4_Data_Quality"] = v4_row.get("Data_Quality", "N/A")

        enhanced.append(merged_row)
    else:
        # No V4 match, keep original
        enhanced.append(ncaa_row.to_dict())

# Create enhanced DataFrame
enhanced_df = pd.DataFrame(enhanced)

# Save
output = "predictions/ncaapredictions_ENHANCED.csv"
enhanced_df.to_csv(output, index=False)

print(f"\n✅ Enhanced predictions saved to {output}")
print(f"✅ Original columns: {len(ncaa_current.columns)}")
print(f"✅ Enhanced columns: {len(enhanced_df.columns)}")
print(f"✅ Added: {len(enhanced_df.columns) - len(ncaa_current.columns)} new columns")

print(f"\n📊 New Columns Added:")
new_cols = [col for col in enhanced_df.columns if col.startswith("V4_")]
for col in new_cols[:10]:  # Show first 10
    print(f"  • {col}")
if len(new_cols) > 10:
    print(f"  ... and {len(new_cols) - 10} more")

print("\n" + "=" * 80)
print("🎯 NCAA predictions now include full V4 analytics!")
print("=" * 80)
