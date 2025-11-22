#!/usr/bin/env python3
"""
Quick Week 12 Analysis Runner
Runs the main analysis that worked and generates key artifacts
"""
import sys
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """Quick analysis runner that focuses on the working parts"""
    print("🏈 Running Quick Week 12 Analysis...")

    # Load the generated predictions
    predictions_path = Path("predictions/week12_all_games_predictions.csv")
    if predictions_path.exists():
        predictions_df = pd.read_csv(predictions_path)
        print(f"✅ Loaded {len(predictions_df)} predictions with advanced statistics")

        # Convert confidence_pct to numeric for sorting
        predictions_df['confidence_numeric'] = predictions_df['confidence_pct'].str.rstrip('%').astype(float)

        # Show summary statistics
        avg_confidence = predictions_df['confidence_numeric'].mean()
        high_upset_games = predictions_df[predictions_df['upset_potential'] == 'High']
        value_bets = predictions_df[predictions_df['betting_value'].str.contains('Value', case=False, na=False)]

        print(f"\n📊 Key Insights:")
        print(f"• Average confidence: {avg_confidence:.1f}%")
        print(f"• High upset potential games: {len(high_upset_games)}")
        print(f"• Betting value opportunities: {len(value_bets)}")

        # Show top 5 most confident predictions
        top_confident = predictions_df.nlargest(5, 'confidence_numeric')
        print(f"\n🎯 Top 5 Most Confident Predictions:")
        for _, game in top_confident.iterrows():
            print(f"• {game['matchup']}: {game['prediction']} ({game['confidence_pct']})")

        # Generate quick insights JSON
        insights = {
            "generated_at": datetime.now().isoformat(),
            "total_games": len(predictions_df),
            "average_confidence": avg_confidence,
            "high_upset_games": len(high_upset_games),
            "value_opportunities": len(value_bets),
            "top_confident_games": top_confident[['matchup', 'prediction', 'confidence_pct']].to_dict('records')
        }

        insights_path = Path("predictions/quick_insights.json")
        with open(insights_path, 'w') as f:
            json.dump(insights, f, indent=2)

        print(f"\n💾 Quick insights saved to {insights_path}")
        print("🚀 Analysis complete! Your Week 12 predictions are ready!")

    else:
        print(f"❌ Predictions file not found at {predictions_path}")
        print("Please run the main analysis first.")

if __name__ == "__main__":
    main()