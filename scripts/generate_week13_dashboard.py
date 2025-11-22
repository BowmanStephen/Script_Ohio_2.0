import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import sys

def generate_dashboard():
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "analysis" / "week13"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find latest predictions JSON
    pred_dir = project_root / "predictions" / "week13"
    pred_files = sorted(pred_dir.glob("week13_model_predictions_*.json"))
    if not pred_files:
        print("❌ No prediction files found")
        return False
    
    pred_file = pred_files[-1]
    print(f"Loading predictions from: {pred_file}")
    
    with open(pred_file, 'r') as f:
        data = json.load(f)
        
    predictions = data['predictions']
    
    # Convert to DataFrame for plotting
    df_preds = pd.DataFrame([{
        'game': f"{p['away_team']} @ {p['home_team']}",
        'winner': p['ensemble_prediction']['predicted_winner'],
        'confidence': p['ensemble_prediction']['confidence'],
        'home_team': p['home_team'],
        'away_team': p['away_team'],
        'home_win_prob': p['model_predictions'].get('xgb', {}).get('home_win_probability', 0.5)
    } for p in predictions])
    
    # 1. Confidence Distribution Plot
    fig_conf = px.histogram(df_preds, x='confidence', nbins=20, 
                           title='Prediction Confidence Distribution',
                           labels={'confidence': 'Confidence Score (0.5-1.0)'},
                           color_discrete_sequence=['#1f77b4'])
    fig_conf.update_layout(bargap=0.1)
    
    # 2. Win Probability Plot (Top Games by Confidence)
    top_conf = df_preds.sort_values('confidence', ascending=False).head(15)
    fig_top = px.bar(top_conf, x='confidence', y='game', orientation='h',
                    title='Top 15 High Confidence Predictions',
                    color='confidence',
                    hover_data=['winner'],
                    labels={'game': 'Game', 'confidence': 'Confidence'})
    fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
    
    # 3. Predictions Table (HTML)
    table_html = df_preds.sort_values('confidence', ascending=False).to_html(
        classes='table table-striped table-hover', index=False, float_format='%.3f'
    )
    
    # Generate Full HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Week 13 Prediction Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .card {{ margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .high-conf {{ background-color: #d4edda; }}
            .low-conf {{ background-color: #f8d7da; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="mb-4">Week 13 Prediction Dashboard</h1>
            <p class="text-muted">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            {fig_conf.to_html(full_html=False, include_plotlyjs='cdn')}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            {fig_top.to_html(full_html=False, include_plotlyjs=False)}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Detailed Predictions Table</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        {table_html}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    output_file = output_dir / "week13_dashboard.html"
    with open(output_file, 'w') as f:
        f.write(html_content)
        
    print(f"✅ Dashboard generated: {output_file}")
    return True

if __name__ == "__main__":
    generate_dashboard()

