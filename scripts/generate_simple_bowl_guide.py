#!/usr/bin/env python3
"""Generate a simplified bowl guide from JSON predictions with enhanced analysis."""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def to_markdown_table(df):
    """Simple internal markdown table formatter to avoid dependencies."""
    if df.empty:
        return ""

    headers = df.columns.tolist()
    rows = df.values.tolist()

    # Calculate widths
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    # Create rows
    header_row = (
        "| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)) + " |"
    )
    separator_row = "| " + " | ".join("-" * w for w in widths) + " |"

    data_rows = []
    for row in rows:
        data_rows.append(
            "| " + " | ".join(str(val).ljust(w) for val, w in zip(row, widths)) + " |"
        )

    return "\n".join([header_row, separator_row] + data_rows)


def main():
    json_path = PROJECT_ROOT / "predictions" / "bowls_2025_predictions.json"
    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)

    games = data.get("games", [])
    if not games:
        print("No games found in predictions.")
        sys.exit(0)

    df = pd.DataFrame(games)

    # Sort by date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

    # Format for display
    def format_row(row):
        date_val = row.get("date")
        date_str = (
            date_val.strftime("%Y-%m-%d %H:%M") if pd.notnull(date_val) else "TBD"
        )

        home = row.get("home_team", "Unknown")
        away = row.get("away_team", "Unknown")
        win_prob = row.get("home_win_prob", 0.5)
        margin = row.get("predicted_margin", 0.0)  # Negative = Home Favored (e.g. -7.5)

        # Enhanced Metrics
        home_talent = row.get("home_talent")
        away_talent = row.get("away_talent")
        home_elo = row.get("home_elo")
        away_elo = row.get("away_elo")
        market_spread = row.get("spread")  # Standard: Neg if Home Favored

        # Calculations
        talent_diff = (
            (home_talent - away_talent) if (home_talent and away_talent) else 0.0
        )
        # Talent Edge: Positive if Home has more talent

        elo_diff_val = (home_elo - away_elo) if (home_elo and away_elo) else 0.0

        # Determine Winner & Spread for Display
        if margin < 0:
            winner = home
            proj_spread_display = abs(margin)
            prob = win_prob
        else:
            winner = away
            proj_spread_display = margin
            prob = 1 - win_prob

        # Confidence
        if prob > 0.65:
            confidence = "High"
            conf_emoji = "🟢"
        elif prob > 0.55:
            confidence = "Med"
            conf_emoji = "🟡"
        else:
            confidence = "Low"
            conf_emoji = "🔴"

        # Edge Analysis (Talent)
        if talent_diff > 100:
            talent_edge = f"{home} (+{int(talent_diff)})"
        elif talent_diff < -100:
            talent_edge = f"{away} (+{int(abs(talent_diff))})"
        elif home_talent and away_talent:
            talent_edge = "Even"
        else:
            talent_edge = "-"

        # Market Value Play
        # Compare our margin to market spread
        # Our margin: -7.0 (Home by 7)
        # Market margin: -3.0 (Home by 3)
        # Diff: -4.0 (We like Home MORE than market)
        value_play = ""
        if market_spread is not None and margin is not None:
            diff = margin - market_spread
            # If diff is negative, we simulate Home doing BETTER (more negative score) than market
            if diff < -3.0:
                value_play = f"Value: {home}"
            elif diff > 3.0:
                value_play = f"Value: {away}"

        # Upset Alert
        # Underdog (prob < 0.5) with Win Prob > 35% AND value play?
        # Or simply, if market heavily favors one team but we have it close
        upset_alert = ""
        if market_spread is not None:
            # Market thinks Home is big favorite (-7), we have it close (-1 or +)
            if market_spread < -7 and margin > -3:
                upset_alert = "⚠️ Upset Watch"
            # Market thinks Away is big favorite (+7 -> market spread is +7? No, usually spread is Home relative)
            # If Away is favored, spread is POSITIVE (e.g. +7 Home Dog)
            elif market_spread > 7 and margin < 3:
                upset_alert = "⚠️ Upset Watch"

        # formatting final row
        return {
            "Date": date_str,
            "Matchup": f"{away} at {home}",
            "Winner": f"{winner}",
            "Prob": f"{prob:.1%}",
            "Line": f"{winner} -{proj_spread_display:.1f}",
            "Talent Edge": talent_edge,
            "Value": value_play,
            "Notes": upset_alert,
        }

    formatted_rows = df.apply(format_row, axis=1).tolist()
    formatted_df = pd.DataFrame(formatted_rows)

    # Convert to Markdown
    md_lines = []
    md_lines.append("# 🏈 2025 Bowl Game Predictions (Enhanced)")
    md_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    md_lines.append("### Legend")
    md_lines.append(
        "- **Talent Edge**: Team with significantly higher 247Sports composite ratings."
    )
    md_lines.append(
        "- **Value**: Where our model differs from the market line by > 3 points."
    )
    md_lines.append("- **Upset Watch**: Games where a heavy favorite is on alert.")
    md_lines.append("\n")

    md_lines.append(to_markdown_table(formatted_df))

    output_path = PROJECT_ROOT / "predictions" / "user_bowl_guide.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write("\n".join(md_lines))

    print(f"✅ Wrote enhanced guide to {output_path}")


if __name__ == "__main__":
    main()
