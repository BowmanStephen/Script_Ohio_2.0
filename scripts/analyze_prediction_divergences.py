#!/usr/bin/env python3
"""
Analyze prediction divergences between Ohio Model and System Average.

This script:
1. Compares Ohio Model vs System Average predictions
2. Identifies high-divergence games (|ohio - system_avg| > 10 points)
3. Categorizes games:
   - ohio_wrong_consensus_right: Learning opportunities
   - ohio_right_consensus_wrong: Unique value cases
   - consensus_aligned: High confidence games
4. Generates weekly divergence report
5. Exports divergence data to CSV
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings

import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import Prediction_Tracker loader
from scripts.load_prediction_tracker import load_prediction_tracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


def load_ohio_predictions(week: int, season: int = 2025) -> pd.DataFrame:
    """Load Ohio Model predictions for specified week."""
    logger.info(f"📊 Loading Ohio Model predictions for Week {week}...")
    
    prediction_paths = [
        project_root / 'predictions' / f'week{week}' / f'week{week}_predictions_all_*.csv',
        project_root / 'predictions' / f'week{week}' / f'week{week}_predictions_enhanced.csv',
        project_root / 'predictions' / f'week{week}' / f'week{week}_predictions.csv',
        project_root / 'predictions' / f'week{week}_predictions.csv',
        project_root / f'week{week}_predictions.csv',
    ]
    
    for pattern in prediction_paths:
        if '*' in str(pattern):
            matches = list(pattern.parent.glob(pattern.name))
            if matches:
                pattern = matches[0]
            else:
                continue
        
        if pattern.exists():
            try:
                df = pd.read_csv(pattern, low_memory=False)
                logger.info(f"  ✅ Loaded {len(df)} predictions from {pattern}")
                return df
            except Exception as e:
                logger.warning(f"  ⚠️  Error loading {pattern}: {e}")
    
    logger.error(f"❌ No Ohio Model predictions found for Week {week}")
    return pd.DataFrame()


def match_games(ohio_df: pd.DataFrame, tracker_df: pd.DataFrame) -> pd.DataFrame:
    """Match Ohio predictions with Prediction_Tracker data."""
    logger.info("🔗 Matching games...")
    
    def create_key(row):
        home = str(row.get('home_team', '')).strip().lower()
        away = str(row.get('away_team', '')).strip().lower()
        week = row.get('week', '')
        season = row.get('season', 2025)
        return f"{season}_{week}_{away}_{home}"
    
    if 'game_key' not in ohio_df.columns:
        ohio_df['game_key'] = ohio_df.apply(create_key, axis=1)
    if 'game_key' not in tracker_df.columns:
        tracker_df['game_key'] = tracker_df.apply(create_key, axis=1)
    
    merged = ohio_df.merge(
        tracker_df[['game_key', 'system_average', 'opening_line', 'sagarin', 'phcover', 'phwin']],
        on='game_key',
        how='inner',
        suffixes=('', '_tracker')
    )
    
    logger.info(f"✅ Matched {len(merged)} games")
    return merged


def categorize_divergences(df: pd.DataFrame, divergence_threshold: float = 10.0) -> pd.DataFrame:
    """
    Categorize games based on divergence between Ohio Model and System Average.
    
    Args:
        df: DataFrame with Ohio and System Average predictions
        divergence_threshold: Threshold for high divergence (default 10.0 points)
    
    Returns:
        DataFrame with divergence categories
    """
    logger.info("📊 Categorizing divergences...")
    
    result_df = df.copy()
    
    # Get Ohio Model margin
    ohio_col = 'ensemble_margin' if 'ensemble_margin' in df.columns else 'predicted_margin'
    if ohio_col not in df.columns:
        logger.error("❌ No Ohio Model predictions found")
        return pd.DataFrame()
    
    ohio_margin = df[ohio_col]
    system_avg = df['system_average']
    
    # Calculate divergence
    result_df['divergence'] = ohio_margin - system_avg
    result_df['abs_divergence'] = result_df['divergence'].abs()
    
    # High divergence flag
    result_df['high_divergence'] = result_df['abs_divergence'] > divergence_threshold
    
    # Categorize games (if actual results available)
    if 'phwin' in df.columns and 'phcover' in df.columns:
        # Determine actual winner (positive margin = home win)
        # phwin: 1 = home win, 0 = away win
        # phcover: 1 = home cover, 0 = away cover
        
        # Ohio Model predicted winner
        ohio_predicted_winner = (ohio_margin > 0).astype(int)
        
        # System Average predicted winner
        system_avg_predicted_winner = (system_avg > 0).astype(int)
        
        # Actual winner
        actual_winner = df['phwin'].fillna(0.5).astype(int)
        
        # Categorize
        result_df['ohio_correct'] = (ohio_predicted_winner == actual_winner)
        result_df['system_avg_correct'] = (system_avg_predicted_winner == actual_winner)
        
        # Category flags
        result_df['ohio_wrong_consensus_right'] = (
            ~result_df['ohio_correct'] & result_df['system_avg_correct']
        )
        result_df['ohio_right_consensus_wrong'] = (
            result_df['ohio_correct'] & ~result_df['system_avg_correct']
        )
        result_df['consensus_aligned'] = (
            result_df['ohio_correct'] & result_df['system_avg_correct']
        )
        result_df['both_wrong'] = (
            ~result_df['ohio_correct'] & ~result_df['system_avg_correct']
        )
    else:
        # No actual results - just categorize by divergence
        result_df['ohio_wrong_consensus_right'] = False
        result_df['ohio_right_consensus_wrong'] = False
        result_df['consensus_aligned'] = result_df['abs_divergence'] <= 5.0  # Low divergence = aligned
        result_df['both_wrong'] = False
    
    return result_df


def generate_divergence_report(df: pd.DataFrame, week: int, season: int = 2025) -> str:
    """Generate markdown divergence analysis report."""
    logger.info("📝 Generating divergence report...")
    
    report_lines = [
        f"# Week {week} Prediction Divergence Analysis",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Season:** {season}",
        "",
        "## Overview",
        "",
        f"This report analyzes divergences between the Ohio Model and System Average predictions for Week {week}.",
        "",
        "## Summary Statistics",
        "",
    ]
    
    # Divergence statistics
    if 'divergence' in df.columns:
        divergence = df['divergence'].dropna()
        abs_divergence = df['abs_divergence'].dropna()
        
        report_lines.extend([
            f"- **Total Games Analyzed:** {len(df)}",
            f"- **Games with System Average:** {df['system_average'].notna().sum()}",
            f"- **Mean Divergence:** {divergence.mean():.2f} points (Ohio - System Avg)",
            f"- **Std Dev:** {divergence.std():.2f} points",
            f"- **Mean Absolute Divergence:** {abs_divergence.mean():.2f} points",
            f"- **Max Divergence:** {abs_divergence.max():.2f} points",
            "",
        ])
    
    # High divergence games
    if 'high_divergence' in df.columns:
        high_div_count = df['high_divergence'].sum()
        report_lines.extend([
            f"## High Divergence Games (>10 points)",
            "",
            f"- **Count:** {high_div_count} games ({high_div_count/len(df)*100:.1f}%)",
            "",
        ])
        
        if high_div_count > 0:
            high_div_games = df[df['high_divergence']].copy()
            report_lines.append("### Top 10 Highest Divergences")
            report_lines.append("")
            report_lines.append("| Home Team | Away Team | Ohio Model | System Avg | Divergence |")
            report_lines.append("|-----------|----------|------------|------------|------------|")
            
            top_div = high_div_games.nlargest(10, 'abs_divergence')
            for _, row in top_div.iterrows():
                home = row.get('home_team', 'Unknown')
                away = row.get('away_team', 'Unknown')
                ohio = row.get('ensemble_margin', row.get('predicted_margin', 0))
                sys_avg = row.get('system_average', 0)
                div = row.get('divergence', 0)
                report_lines.append(f"| {home} | {away} | {ohio:.1f} | {sys_avg:.1f} | {div:.1f} |")
            report_lines.append("")
    
    # Categorization (if actual results available)
    if 'ohio_correct' in df.columns:
        report_lines.extend([
            "## Prediction Accuracy",
            "",
            f"- **Ohio Model Accuracy:** {df['ohio_correct'].mean():.1%}",
            f"- **System Average Accuracy:** {df['system_avg_correct'].mean():.1%}",
            "",
            "## Game Categories",
            "",
        ])
        
        if 'ohio_wrong_consensus_right' in df.columns:
            learning_opps = df['ohio_wrong_consensus_right'].sum()
            report_lines.append(f"- **Learning Opportunities** (Ohio wrong, System Avg right): {learning_opps} games")
        
        if 'ohio_right_consensus_wrong' in df.columns:
            unique_value = df['ohio_right_consensus_wrong'].sum()
            report_lines.append(f"- **Unique Value Cases** (Ohio right, System Avg wrong): {unique_value} games")
        
        if 'consensus_aligned' in df.columns:
            aligned = df['consensus_aligned'].sum()
            report_lines.append(f"- **Consensus Aligned** (Both correct): {aligned} games")
        
        if 'both_wrong' in df.columns:
            both_wrong = df['both_wrong'].sum()
            report_lines.append(f"- **Both Wrong:** {both_wrong} games")
        report_lines.append("")
    
    # Key Insights
    report_lines.extend([
        "## Key Insights",
        "",
        "1. **High Divergence Games**: Games with large differences between Ohio Model and System Average may indicate:",
        "   - High uncertainty matchups",
        "   - Potential data quality issues",
        "   - Edge cases worth manual review",
        "",
        "2. **Learning Opportunities**: Games where System Average was correct but Ohio Model was wrong can reveal:",
        "   - Missing features or signals",
        "   - Model calibration issues",
        "   - Areas for improvement",
        "",
        "3. **Unique Value**: Games where Ohio Model was correct but System Average was wrong show:",
        "   - Where the model adds unique value",
        "   - Competitive advantages",
        "",
    ])
    
    return "\n".join(report_lines)


def analyze_divergences(week: int, season: int = 2025, divergence_threshold: float = 10.0) -> pd.DataFrame:
    """
    Analyze prediction divergences for specified week.
    
    Args:
        week: Week number
        season: Season year
        divergence_threshold: Threshold for high divergence
    
    Returns:
        DataFrame with divergence analysis
    """
    logger.info("=" * 80)
    logger.info(f"ANALYZING PREDICTION DIVERGENCES FOR WEEK {week}")
    logger.info("=" * 80)
    
    # Step 1: Load Ohio Model predictions
    ohio_df = load_ohio_predictions(week, season)
    if ohio_df.empty:
        logger.error("❌ Cannot analyze divergences without Ohio Model predictions")
        return pd.DataFrame()
    
    # Step 2: Load Prediction_Tracker data
    tracker_df = load_prediction_tracker(week=week, season=season)
    if tracker_df.empty:
        logger.error("❌ Cannot analyze divergences without Prediction_Tracker data")
        return pd.DataFrame()
    
    # Step 3: Match games
    matched_df = match_games(ohio_df, tracker_df)
    if matched_df.empty:
        logger.error("❌ No matched games found")
        return pd.DataFrame()
    
    # Step 4: Categorize divergences
    result_df = categorize_divergences(matched_df, divergence_threshold)
    
    # Step 5: Generate report
    report_content = generate_divergence_report(result_df, week, season)
    
    # Save report
    reports_dir = project_root / 'reports'
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f'week{week}_divergence_analysis.md'
    with open(report_path, 'w') as f:
        f.write(report_content)
    logger.info(f"✅ Saved divergence report to {report_path}")
    
    # Save divergence data
    analysis_dir = project_root / 'data' / 'analysis'
    analysis_dir.mkdir(parents=True, exist_ok=True)
    data_path = analysis_dir / f'week{week}_divergences.csv'
    result_df.to_csv(data_path, index=False)
    logger.info(f"✅ Saved divergence data to {data_path}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ DIVERGENCE ANALYSIS COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total games: {len(result_df)}")
    if 'high_divergence' in result_df.columns:
        logger.info(f"High divergence games: {result_df['high_divergence'].sum()}")
    if 'ohio_wrong_consensus_right' in result_df.columns:
        logger.info(f"Learning opportunities: {result_df['ohio_wrong_consensus_right'].sum()}")
    if 'ohio_right_consensus_wrong' in result_df.columns:
        logger.info(f"Unique value cases: {result_df['ohio_right_consensus_wrong'].sum()}")
    
    return result_df


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze prediction divergences')
    parser.add_argument('--week', type=int, default=13, help='Week number (default: 13)')
    parser.add_argument('--season', type=int, default=2025, help='Season year (default: 2025)')
    parser.add_argument('--threshold', type=float, default=10.0, help='Divergence threshold (default: 10.0)')
    
    args = parser.parse_args()
    
    try:
        result_df = analyze_divergences(args.week, args.season, args.threshold)
        
        if result_df.empty:
            logger.error("❌ No divergence analysis generated")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Divergence analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

