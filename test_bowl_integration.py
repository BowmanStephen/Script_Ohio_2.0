#!/usr/bin/env python3
"""
Integration test for bowl analytics system
Tests web app and API integration
"""

import json
import time

import requests


def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:5002"

    print("🧪 Testing Bowl Analytics API Integration...")

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Health check: {data['bowl_games_count']} games loaded")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

    # Test bowl games endpoint
    try:
        response = requests.get(f"{base_url}/api/bowl-games")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        games = data["games"]
        print(f"✅ Bowl games: {len(games)} games retrieved")

        # Check first game has expected fields
        if games:
            game = games[0]
            required_fields = ["home_team", "away_team", "predicted_margin"]
            missing_fields = [f for f in required_fields if f not in game]
            if missing_fields:
                print(f"⚠️  Missing fields in first game: {missing_fields}")
            else:
                print(f"✅ Game data structure valid")
    except Exception as e:
        print(f"❌ Bowl games test failed: {e}")
        return False

    # Test team stats endpoint
    try:
        response = requests.get(f"{base_url}/api/team-stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        stats = data["stats"]
        print(f"✅ Team stats: {len(stats)} teams retrieved")

        # Check a sample team has expected stats
        if stats:
            team_name = list(stats.keys())[0]
            team_stats = stats[team_name]
            if "offense_rating" in team_stats:
                print(f"✅ Team stats structure valid for {team_name}")
    except Exception as e:
        print(f"❌ Team stats test failed: {e}")
        return False

    # Test predictions comparison endpoint
    try:
        response = requests.get(f"{base_url}/api/predictions-comparison")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        predictions = data["predictions"]
        print(f"✅ Predictions comparison: {len(predictions)} predictions retrieved")
    except Exception as e:
        print(f"❌ Predictions comparison test failed: {e}")
        return False

    return True


def test_cors_headers():
    """Test CORS headers are present"""
    try:
        response = requests.options("http://localhost:5002/api/bowl-games")
        cors_headers = {
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
        }
        response_headers = set(response.headers.keys())
        if cors_headers.issubset(response_headers):
            print("✅ CORS headers present")
            return True
        else:
            print(f"⚠️  Missing CORS headers: {cors_headers - response_headers}")
            return False
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("🚀 Starting Bowl Analytics System Integration Test")
    print("=" * 60)

    # Wait a moment for servers to fully start
    time.sleep(1)

    # Test API endpoints
    api_success = test_api_endpoints()

    # Test CORS
    cors_success = test_cors_headers()

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print(f"   API Integration: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   CORS Configuration: {'✅ PASS' if cors_success else '❌ FAIL'}")

    overall_success = api_success and cors_success
    print(
        f"\n🎯 OVERALL: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}"
    )

    if overall_success:
        print("\n🎉 Bowl Analytics System is ready!")
        print("   📱 Web App: http://localhost:5173")
        print("   🔗 API Server: http://localhost:5002")
        print("\n💡 Usage:")
        print("   1. Open http://localhost:5173 in your browser")
        print("   2. Click 'Bowl Analytics' to view the dashboard")
        print("   3. Navigate between different analytics views")

    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
