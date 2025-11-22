#!/usr/bin/env python3
"""
Week 13 Setup Verification Script
Verifies all Week 13 components are ready for analysis
"""

import os
import sys
from pathlib import Path
import pandas as pd
import json

def check_file_exists(filepath: str, description: str) -> tuple[bool, str]:
    """Check if a file exists"""
    if os.path.exists(filepath):
        return True, f"✅ {description} found"
    return False, f"❌ {description} NOT found: {filepath}"

def check_directory_exists(dirpath: str, description: str) -> tuple[bool, str]:
    """Check if a directory exists"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        return True, f"✅ {description} exists"
    return False, f"❌ {description} NOT found: {dirpath}"

def verify_week13_games() -> tuple[bool, list[str]]:
    """Verify Week 13 games are in the system"""
    messages = []
    games_path = "starter_pack/data/2025_games.csv"
    
    if not os.path.exists(games_path):
        return False, [f"❌ Games file not found: {games_path}"]
    
    try:
        games_df = pd.read_csv(games_path)
        week13_games = games_df[(games_df['week'] == 13) & (games_df['season'] == 2025)]
        
        if len(week13_games) > 0:
            messages.append(f"✅ Week 13 games found: {len(week13_games)} games")
            teams = set(week13_games['home_team'].tolist() + week13_games['away_team'].tolist())
            messages.append(f"✅ Teams in Week 13: {len(teams)} teams")
        else:
            messages.append("❌ No Week 13 games found in 2025_games.csv")
            return False, messages
    except Exception as e:
        messages.append(f"❌ Error reading games file: {e}")
        return False, messages
    
    return True, messages

def verify_week12_results() -> tuple[bool, list[str]]:
    """Verify Week 12 results are complete"""
    messages = []
    games_path = "starter_pack/data/2025_games.csv"
    
    if not os.path.exists(games_path):
        return False, [f"❌ Games file not found: {games_path}"]
    
    try:
        games_df = pd.read_csv(games_path)
        week12_games = games_df[(games_df['week'] == 12) & (games_df['season'] == 2025)]
        
        if len(week12_games) == 0:
            messages.append("⚠️ No Week 12 games found")
            return False, messages
        
        completed = week12_games[
            (week12_games['home_points'].notna()) & 
            (week12_games['away_points'].notna())
        ]
        
        messages.append(f"Week 12 games: {len(week12_games)} total")
        messages.append(f"Week 12 completed: {len(completed)} games")
        
        if len(completed) == len(week12_games):
            messages.append("✅ All Week 12 games completed")
            return True, messages
        else:
            messages.append(f"⚠️ {len(week12_games) - len(completed)} Week 12 games still pending")
            return False, messages
    except Exception as e:
        messages.append(f"❌ Error checking Week 12 results: {e}")
        return False, messages

def verify_training_data() -> tuple[bool, list[str]]:
    """Verify training data includes Week 12"""
    messages = []
    training_path = "model_pack/updated_training_data.csv"
    
    if not os.path.exists(training_path):
        return False, [f"❌ Training data not found: {training_path}"]
    
    try:
        train_df = pd.read_csv(training_path)
        week12_2025 = train_df[(train_df['season'] == 2025) & (train_df['week'] == 12)]
        
        messages.append(f"Total training games: {len(train_df)}")
        messages.append(f"Week 12 2025 games in training: {len(week12_2025)}")
        
        if len(week12_2025) > 0:
            messages.append("✅ Week 12 data included in training data")
            return True, messages
        else:
            messages.append("⚠️ Week 12 data not yet in training data")
            return False, messages
    except Exception as e:
        messages.append(f"❌ Error reading training data: {e}")
        return False, messages

def verify_models() -> tuple[bool, list[str]]:
    """Verify model files exist and are loadable"""
    messages = []
    model_files = [
        ("model_pack/ridge_model_2025.joblib", "Ridge model"),
        ("model_pack/xgb_home_win_model_2025.pkl", "XGBoost model"),
        ("model_pack/fastai_home_win_model_2025.pkl", "FastAI model")
    ]
    
    all_exist = True
    for filepath, description in model_files:
        exists, msg = check_file_exists(filepath, description)
        messages.append(msg)
        if not exists:
            all_exist = False
    
    # Try to load models
    if all_exist:
        try:
            import joblib
            import pickle
            
            # Test Ridge
            ridge = joblib.load("model_pack/ridge_model_2025.joblib")
            messages.append("✅ Ridge model loads successfully")
            
            # Test XGBoost
            with open("model_pack/xgb_home_win_model_2025.pkl", 'rb') as f:
                xgb = pickle.load(f)
            messages.append("✅ XGBoost model loads successfully")
            
        except Exception as e:
            messages.append(f"⚠️ Model loading error: {e}")
            all_exist = False
    
    return all_exist, messages

def verify_agents() -> tuple[bool, list[str]]:
    """Verify Week 13 uses weekly agents (generic, week-agnostic)"""
    messages = []
    # Week 13 uses generic weekly agents, not week-specific agents
    agent_files = [
        ("agents/weekly_matchup_analysis_agent.py", "Weekly Matchup Analysis Agent"),
        ("agents/weekly_model_validation_agent.py", "Weekly Model Validation Agent"),
        ("agents/weekly_prediction_generation_agent.py", "Weekly Prediction Generation Agent"),
        ("agents/weekly_analysis_orchestrator.py", "Weekly Analysis Orchestrator")
    ]
    
    all_exist = True
    for filepath, description in agent_files:
        exists, msg = check_file_exists(filepath, description)
        messages.append(msg)
        if not exists:
            all_exist = False
    
    return all_exist, messages

def verify_directories() -> tuple[bool, list[str]]:
    """Verify Week 13 directory structure"""
    messages = []
    directories = [
        ("data/week13/enhanced", "Week 13 enhanced data directory"),
        ("analysis/week13", "Week 13 analysis directory"),
        ("predictions/week13", "Week 13 predictions directory")
    ]
    
    all_exist = True
    for dirpath, description in directories:
        exists, msg = check_directory_exists(dirpath, description)
        messages.append(msg)
        if not exists:
            all_exist = False
    
    return all_exist, messages

def main():
    """Run all verification checks"""
    print("=" * 70)
    print("Week 13 Setup Verification")
    print("=" * 70)
    print()
    
    all_checks_passed = True
    results = {}
    
    # Check 1: Week 13 games
    print("1. Checking Week 13 games...")
    passed, messages = verify_week13_games()
    results['week13_games'] = passed
    for msg in messages:
        print(f"   {msg}")
    print()
    
    # Check 2: Week 12 results
    print("2. Checking Week 12 results...")
    passed, messages = verify_week12_results()
    results['week12_results'] = passed
    for msg in messages:
        print(f"   {msg}")
    print()
    
    # Check 3: Training data
    print("3. Checking training data...")
    passed, messages = verify_training_data()
    results['training_data'] = passed
    for msg in messages:
        print(f"   {msg}")
    print()
    
    # Check 4: Model files
    print("4. Checking model files...")
    passed, messages = verify_models()
    results['models'] = passed
    for msg in messages:
        print(f"   {msg}")
    print()
    
    # Check 5: Agent files
    print("5. Checking Week 13 agent files...")
    passed, messages = verify_agents()
    results['agents'] = passed
    for msg in messages:
        print(f"   {msg}")
    print()
    
    # Check 6: Directory structure
    print("6. Checking directory structure...")
    passed, messages = verify_directories()
    results['directories'] = passed
    for msg in messages:
        print(f"   {msg}")
    print()
    
    # Summary
    print("=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name.replace('_', ' ').title()}")
    
    all_passed = all(results.values())
    print()
    
    if all_passed:
        print("✅ All checks passed! Week 13 setup is complete.")
        return 0
    else:
        print("❌ Some checks failed. Please address the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

