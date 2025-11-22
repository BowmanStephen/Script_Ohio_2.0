#!/usr/bin/env python3
"""
Create Interactive HTML Dashboard with Real Week 12 Data
"""
import pandas as pd
import json
from pathlib import Path

def create_dashboard():
    """Create HTML dashboard with real data from the predictions CSV"""

    # Load the real predictions data
    predictions_path = Path("predictions/week12_all_games_predictions.csv")
    if not predictions_path.exists():
        print("❌ Predictions CSV not found!")
        return

    df = pd.read_csv(predictions_path)
    print(f"✅ Loaded {len(df)} predictions from CSV")

    # Convert data to JSON format for JavaScript
    games_data = []
    for _, row in df.iterrows():
        game = {
            "matchup": row['matchup'],
            "prediction": row['prediction'],
            "confidence": row['confidence_pct'],
            "home_score": int(row['predicted_home_score']),
            "away_score": int(row['predicted_away_score']),
            "margin": float(row['predicted_margin']),
            "elo_diff": row['elo_diff_formatted'],
            "upset_potential": row['upset_potential'],
            "betting_value": row['betting_value'],
            "explanation": row['explanation']
        }
        games_data.append(game)

    # Calculate statistics
    avg_confidence = df['confidence_pct'].str.rstrip('%').astype(float).mean()
    high_upset_count = len(df[df['upset_potential'] == 'High'])
    value_bets_count = len(df[df['betting_value'].str.contains('Value', na=False)])

    # Confidence distribution
    confidence_dist = {
        'high': len(df[df['confidence_pct'].str.rstrip('%').astype(float) > 90]),
        'medium': len(df[(df['confidence_pct'].str.rstrip('%').astype(float) > 70) &
                        (df['confidence_pct'].str.rstrip('%').astype(float) <= 90)]),
        'low': len(df[df['confidence_pct'].str.rstrip('%').astype(float) <= 70])
    }

    # Upset vs Value breakdown
    upset_value_matrix = {
        'high_upset_value': len(df[(df['upset_potential'] == 'High') &
                                  (df['betting_value'].str.contains('Value', na=False))]),
        'high_upset_standard': len(df[(df['upset_potential'] == 'High') &
                                      (~df['betting_value'].str.contains('Value', na=False))]),
        'medium_upset_value': len(df[(df['upset_potential'] == 'Medium') &
                                    (df['betting_value'].str.contains('Value', na=False))]),
        'medium_upset_standard': len(df[(df['upset_potential'] == 'Medium') &
                                        (~df['betting_value'].str.contains('Value', na=False))]),
        'low_upset_value': len(df[(df['upset_potential'] == 'Low') &
                                  (df['betting_value'].str.contains('Value', na=False))]),
        'low_upset_standard': len(df[(df['upset_potential'] == 'Low') &
                                     (~df['betting_value'].str.contains('Value', na=False))])
    }

    # Read the HTML template
    template_path = Path("visualizations/week12_dashboard.html")
    if not template_path.exists():
        print("❌ Dashboard template not found!")
        return

    with open(template_path, 'r') as f:
        html_content = f.read()

    # Replace placeholder data with real data
    html_content = html_content.replace(
        '// Sample data - in production, this would be loaded from your CSV',
        f'// Real data loaded from {len(df)} Week 12 predictions'
    )

    html_content = html_content.replace(
        'const predictionsData = [',
        f'const predictionsData = {json.dumps(games_data, indent=6)};'
    )

    # Remove the closing bracket and semicolon from the sample data
    lines = html_content.split('\n')
    new_lines = []
    skip_end = False

    for line in lines:
        if 'const predictionsData = [' in line:
            new_lines.append(line)
            skip_end = True
        elif '];' in line and skip_end:
            # Skip the closing bracket of sample data
            continue
        else:
            new_lines.append(line)

    # Update statistics in the HTML
    html_content = '\n'.join(new_lines)
    html_content = html_content.replace('<p class="number">48</p>', f'<p class="number">{len(df)}</p>')
    html_content = html_content.replace('<p class="number">94.7%</p>', f'<p class="number">{avg_confidence:.1f}%</p>')
    html_content = html_content.replace('<p class="number">33</p>', f'<p class="number">{high_upset_count}</p>')
    html_content = html_content.replace('<p class="number">19</p>', f'<p class="number">{value_bets_count}</p>')

    # Update chart data
    html_content = html_content.replace(
        "data: [45, 3, 0]",
        f"data: [{confidence_dist['high']}, {confidence_dist['medium']}, {confidence_dist['low']}]"
    )

    html_content = html_content.replace(
        """data: [
                        {
                            label: 'Value Bets',
                            data: [15, 4, 0],
                            backgroundColor: '#28a745'
                        },
                        {
                            label: 'Standard Bets',
                            data: [18, 9, 2],
                            backgroundColor: '#6c757d'
                        }
                    ]""",
        f"""data: [
                        {{
                            label: 'Value Bets',
                            data: [{upset_value_matrix['high_upset_value']}, {upset_value_matrix['medium_upset_value']}, {upset_value_matrix['low_upset_value']}],
                            backgroundColor: '#28a745'
                        }},
                        {{
                            label: 'Standard Bets',
                            data: [{upset_value_matrix['high_upset_standard']}, {upset_value_matrix['medium_upset_standard']}, {upset_value_matrix['low_upset_standard']}],
                            backgroundColor: '#6c757d'
                        }}
                    ]"""
    )

    # Save the updated dashboard
    dashboard_path = Path("visualizations/week12_interactive_dashboard.html")
    with open(dashboard_path, 'w') as f:
        f.write(html_content)

    print(f"✅ Interactive dashboard created: {dashboard_path}")
    print(f"📊 Dashboard features:")
    print(f"   • {len(df)} real Week 12 games")
    print(f"   • Average confidence: {avg_confidence:.1f}%")
    print(f"   • High upset potential games: {high_upset_count}")
    print(f"   • Value betting opportunities: {value_bets_count}")
    print(f"🚀 Open {dashboard_path} in your browser to view!")

if __name__ == "__main__":
    create_dashboard()