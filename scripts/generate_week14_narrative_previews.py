#!/usr/bin/env python3
"""
Generate Week 14 Narrative Previews
Creates markdown narrative previews for all Week 14 games
"""

import pandas as pd
import json
from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

def generate_narrative_preview(row):
    """Generate narrative preview for a single game"""
    home_team = row.get('home_team', 'Home Team')
    away_team = row.get('away_team', 'Away Team')
    spread = row.get('spread', 0)
    predicted_margin = row.get('predicted_margin', 0)
    home_win_prob = row.get('home_win_probability', 0.5)
    confidence = row.get('ensemble_confidence', 0.5)
    ats_pick = row.get('ats_pick', 'No Edge')
    model_summary = row.get('model_summary', '')
    
    # Determine game type
    if abs(predicted_margin) <= 3:
        game_type = "Close Game"
    elif abs(predicted_margin) > 21:
        game_type = "Potential Blowout"
    else:
        game_type = "Competitive Matchup"
    
    # Build narrative
    narrative = f"""## {away_team} @ {home_team}

**Game Type**: {game_type}
**Spread**: {home_team} {spread:+.1f}
**Predicted Margin**: {predicted_margin:+.1f} points
**Home Win Probability**: {home_win_prob:.1%}
**Model Confidence**: {confidence:.1%}

### Prediction Summary

{model_summary if model_summary else f"Models predict {home_team if predicted_margin > 0 else away_team} to win by {abs(predicted_margin):.1f} points."}

### ATS Recommendation

**Pick**: {ats_pick}

### Key Factors

"""
    
    # Add key factors based on available data
    if 'model_agreement' in row:
        agreement = row['model_agreement']
        narrative += f"- **Model Agreement**: {agreement.capitalize()}\n"
    
    if 'model_edge_pts' in row:
        edge = row['model_edge_pts']
        if edge > 7:
            narrative += f"- **Strong Edge**: {edge:.1f} points of value\n"
        elif edge > 3:
            narrative += f"- **Moderate Edge**: {edge:.1f} points of value\n"
    
    if confidence > 0.7:
        narrative += f"- **High Confidence**: Models are very confident in this prediction\n"
    elif confidence < 0.5:
        narrative += f"- **Low Confidence**: Models show uncertainty in this matchup\n"
    
    narrative += "\n---\n\n"
    
    return narrative

def main():
    """Main execution"""
    print("📝 Generating Week 14 Narrative Previews...")
    print("=" * 60)
    
    predictions_dir = PROJECT_ROOT / "predictions" / "week14"
    analysis_dir = PROJECT_ROOT / "analysis" / "week14"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Load unified predictions
    unified_path = predictions_dir / "week14_predictions_unified.csv"
    if not unified_path.exists():
        print(f"❌ Unified predictions not found: {unified_path}")
        return 1
    
    df = pd.read_csv(unified_path)
    print(f"✅ Loaded predictions: {len(df)} games")
    
    # Generate narratives
    narratives = []
    for _, row in df.iterrows():
        narrative = generate_narrative_preview(row)
        narratives.append(narrative)
    
    # Combine into markdown document
    md_content = f"""# Week 14 Game Previews

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This document contains narrative previews for all {len(df)} Week 14 games, including model predictions, ATS recommendations, and key factors for each matchup.

---

"""
    
    md_content += "\n".join(narratives)
    
    # Save markdown
    md_path = analysis_dir / "week14_narrative_previews.md"
    with open(md_path, 'w') as f:
        f.write(md_content)
    
    print(f"✅ Saved narrative previews: {md_path}")
    print(f"   Total games: {len(df)}")
    
    print("\n" + "=" * 60)
    print("✅ Week 14 Narrative Previews Generated Successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

