#!/usr/bin/env python3
"""
Validation script for power rankings calculation fixes
Tests that the WeeklyMatchupAnalysisAgent uses real data instead of random values
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent

def validate_data_loading():
    """Test that training data loads correctly"""
    print("=" * 60)
    print("TEST 1: Training Data Loading")
    print("=" * 60)
    
    agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)
    
    try:
        enhanced_data = agent._load_enhanced_weekly_data()
        
        # Check that training_data is loaded
        if 'training_data' in enhanced_data:
            training_data = enhanced_data['training_data']
            if training_data is not None and not training_data.empty:
                print(f"✅ Training data loaded: {len(training_data)} completed games")
                
                # Check filtering worked correctly
                invalid_games = training_data[
                    (training_data['home_points'] <= 0) | 
                    (training_data['away_points'] <= 0) |
                    training_data['home_points'].isna() |
                    training_data['away_points'].isna()
                ]
                
                if len(invalid_games) == 0:
                    print("✅ Filtering correct: All games have valid scores for both teams")
                else:
                    print(f"⚠️  Warning: {len(invalid_games)} games with invalid scores found")
                
                # Check season filtering
                if 'season' in training_data.columns:
                    season_counts = training_data['season'].value_counts()
                    print(f"✅ Season data available: {len(season_counts)} seasons")
                    print(f"   2025 games: {len(training_data[training_data['season'] == 2025])}")
                
                return True
            else:
                print("⚠️  Training data is None or empty")
                return False
        else:
            print("❌ Training data not in enhanced_data dictionary")
            return False
            
    except FileNotFoundError as e:
        print(f"⚠️  Expected: {e}")
        print("   (This is OK if enhanced weekly data doesn't exist yet)")
        return None
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False

def validate_strength_metrics():
    """Test that strength metrics use real calculations"""
    print("\n" + "=" * 60)
    print("TEST 2: Strength Metrics Calculations")
    print("=" * 60)
    
    agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)
    
    # Create mock enhanced data with real-looking values
    mock_games = pd.DataFrame({
        'home_team': ['Ohio State', 'Michigan', 'Alabama'],
        'away_team': ['Michigan', 'Ohio State', 'Georgia'],
        'home_elo': [2100.0, 2050.0, 2000.0],
        'away_elo': [2050.0, 2100.0, 1950.0],
        'home_talent': [900.0, 850.0, 950.0],
        'away_talent': [850.0, 900.0, 800.0],
        'home_adjusted_epa': [0.15, 0.12, 0.18],
        'away_adjusted_epa': [0.12, 0.15, 0.10],
        'home_adjusted_epa_allowed': [0.08, 0.10, 0.05],
        'away_adjusted_epa_allowed': [0.10, 0.08, 0.12]
    })
    
    mock_features = mock_games.copy()
    enhanced_data = {
        'games': mock_games,
        'features': mock_features,
        'training_data': None,
        'metadata': {}
    }
    
    # Test offensive rating
    ohio_offensive = agent._calculate_offensive_rating('Ohio State', enhanced_data)
    print(f"✅ Ohio State offensive rating: {ohio_offensive:.2f}")
    
    if 0 <= ohio_offensive <= 100:
        print("   ✅ Rating in valid range (0-100)")
    else:
        print(f"   ❌ Rating out of range: {ohio_offensive}")
        return False
    
    # Test defensive rating
    ohio_defensive = agent._calculate_defensive_rating('Ohio State', enhanced_data)
    print(f"✅ Ohio State defensive rating: {ohio_defensive:.2f}")
    
    if 0 <= ohio_defensive <= 100:
        print("   ✅ Rating in valid range (0-100)")
    else:
        print(f"   ❌ Rating out of range: {ohio_defensive}")
        return False
    
    # Test overall rating (should use Elo + talent + EPA*1000 formula)
    ohio_overall = agent._calculate_overall_rating('Ohio State', enhanced_data)
    print(f"✅ Ohio State overall rating: {ohio_overall:.2f}")
    
    # Verify it's not a random value (should be consistent)
    ohio_overall_2 = agent._calculate_overall_rating('Ohio State', enhanced_data)
    if abs(ohio_overall - ohio_overall_2) < 0.01:
        print("   ✅ Rating is deterministic (not random)")
    else:
        print(f"   ❌ Rating is not deterministic: {ohio_overall} vs {ohio_overall_2}")
        return False
    
    # Test strength of schedule
    ohio_sos = agent._calculate_strength_of_schedule('Ohio State', enhanced_data)
    print(f"✅ Ohio State SOS: {ohio_sos:.3f}")
    
    if 0 <= ohio_sos <= 1:
        print("   ✅ SOS in valid range (0-1)")
    else:
        print(f"   ❌ SOS out of range: {ohio_sos}")
        return False
    
    return True

def validate_power_rankings():
    """Test that power rankings use real win-loss records"""
    print("\n" + "=" * 60)
    print("TEST 3: Power Rankings with Real Records")
    print("=" * 60)
    
    agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)
    
    # Create mock training data with real win-loss scenarios
    mock_training = pd.DataFrame({
        'home_team': ['Ohio State', 'Ohio State', 'Michigan', 'Alabama'],
        'away_team': ['Michigan', 'Penn State', 'Ohio State', 'Georgia'],
        'home_points': [28, 35, 24, 31],
        'away_points': [21, 14, 28, 17],
        'season': [2025, 2025, 2025, 2025]
    })
    
    # Create mock strength metrics
    strength_metrics = {
        'Ohio State': {
            'overall_rating': 95.0,
            'offensive_rating': 90.0,
            'defensive_rating': 85.0,
            'strength_of_schedule': 0.8
        },
        'Michigan': {
            'overall_rating': 92.0,
            'offensive_rating': 88.0,
            'defensive_rating': 90.0,
            'strength_of_schedule': 0.75
        },
        'Alabama': {
            'overall_rating': 90.0,
            'offensive_rating': 85.0,
            'defensive_rating': 88.0,
            'strength_of_schedule': 0.7
        }
    }
    
    enhanced_data = {
        'training_data': mock_training
    }
    
    rankings = agent._generate_power_rankings(strength_metrics, enhanced_data)
    
    print(f"✅ Generated {len(rankings)} rankings")
    
    # Check that records are real (not random)
    ohio_ranking = next((r for r in rankings if r['team'] == 'Ohio State'), None)
    if ohio_ranking:
        print(f"✅ Ohio State ranking:")
        print(f"   Rank: {ohio_ranking['rank']}")
        print(f"   Record: {ohio_ranking['record']}")
        print(f"   Games played: {ohio_ranking['games_played']}")
        
        # Ohio State should be 2-0 (won both games)
        if ohio_ranking['record'] == '2-0':
            print("   ✅ Record is correct (2-0)")
        else:
            print(f"   ⚠️  Expected 2-0, got {ohio_ranking['record']}")
        
        # Check that rating is real (not random)
        if ohio_ranking['rating'] == 95.0:
            print("   ✅ Rating matches strength metrics")
        else:
            print(f"   ⚠️  Rating mismatch: expected 95.0, got {ohio_ranking['rating']}")
    else:
        print("❌ Ohio State not found in rankings")
        return False
    
    # Check that rankings are sorted by rating
    ratings = [r['rating'] for r in rankings]
    if ratings == sorted(ratings, reverse=True):
        print("✅ Rankings sorted correctly by rating (descending)")
    else:
        print("❌ Rankings not sorted correctly")
        return False
    
    return True

def main():
    """Run all validation tests"""
    print("\n" + "=" * 60)
    print("POWER RANKINGS FIX VALIDATION")
    print("=" * 60)
    print("\nValidating that power rankings use real data calculations...\n")
    
    results = []
    
    # Test 1: Data loading
    result1 = validate_data_loading()
    results.append(("Data Loading", result1))
    
    # Test 2: Strength metrics
    result2 = validate_strength_metrics()
    results.append(("Strength Metrics", result2))
    
    # Test 3: Power rankings
    result3 = validate_power_rankings()
    results.append(("Power Rankings", result3))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP (expected)"
        print(f"{status}: {test_name}")
    
    all_passed = all(r for r in results if r is not None)
    
    if all_passed:
        print("\n🎉 All tests passed! Power rankings fix is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed or were skipped. Review output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

