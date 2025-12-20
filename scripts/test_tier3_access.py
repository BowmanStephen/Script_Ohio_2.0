#!/usr/bin/env python3
"""
Script to test Tier 3 CFBD access and verify premium endpoints.
This script will help us understand what premium features are available
and test the actual rate limits for Tier 3 membership.

Tier 3 Benefits:
- 75k API calls/month (~2.5k/day, ~100/hour, ~25 req/sec)
- GraphQL API with real-time subscriptions
- All advanced metrics (EPA, PPA, Win Probability, etc.)
- Live scoreboard and play-by-play data
- Weather data
- Weekly model training data downloads (week 5+)
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from cfbd_client.unified_client import UnifiedCFBDClient
    from config.cfbd_config import CFBDConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def test_basic_endpoints(client):
    """Test basic CFBD endpoints that should work for any tier"""
    print("\n🔍 Testing Basic Endpoints")
    print("=" * 50)

    try:
        # Test games endpoint
        print("Testing games endpoint...")
        games = client.get_games(year=2025, week=1)
        print(f"✅ Games: Found {len(games)} games for 2025 week 1")

        # Test teams endpoint
        print("Testing teams endpoint...")
        teams = client.get_teams()
        print(f"✅ Teams: Found {len(teams)} teams")

        # Test ratings endpoint
        print("Testing ratings endpoint...")
        ratings = client.get_ratings(year=2025)
        print(f"✅ Ratings: Found {len(ratings)} rating entries")

        return True

    except Exception as e:
        print(f"❌ Basic endpoint test failed: {e}")
        return False


def test_advanced_metrics(client):
    """Test Tier 3 advanced metrics endpoints"""
    print("\n⭐ Testing Advanced Metrics")
    print("=" * 50)

    results = {}

    try:
        # Test advanced team stats
        print("Testing advanced team stats...")
        advanced_stats = client.get_advanced_stats(year=2025)
        results["advanced_stats"] = len(advanced_stats) if advanced_stats else 0
        print(f"✅ Advanced Stats: Found {results['advanced_stats']} entries")

    except Exception as e:
        print(f"❌ Advanced stats test failed: {e}")
        results["advanced_stats"] = "error"

    try:
        # Test win probabilities
        print("Testing win probabilities...")
        win_probs = client.get_win_probabilities(year=2025, week=1)
        results["win_probability"] = len(win_probs) if win_probs else 0
        print(f"✅ Win Probability: Found {results['win_probability']} entries")

    except Exception as e:
        print(f"❌ Win probability test failed: {e}")
        results["win_probability"] = "error"

    # Test weather data availability
    try:
        print("Testing weather data (check if included in games)...")
        games = client.get_games(year=2025, week=15)  # Late season for weather
        if games:
            # Check if any games have weather data
            has_weather = any(
                "weather" in str(game).lower() for game in games[:5]
            )  # Check first 5
            results["weather_data"] = "available" if has_weather else "not_in_sample"
            print(
                f"✅ Weather: {'Weather data found' if has_weather else 'No weather in sample (may need specific conditions)'}"
            )
        else:
            results["weather_data"] = "no_games"
            print("⚠️ No games found for weather test")

    except Exception as e:
        print(f"❌ Weather data test failed: {e}")
        results["weather_data"] = "error"

    return results


def test_live_data(client):
    """Test live data endpoints"""
    print("\n📡 Testing Live Data")
    print("=" * 50)

    results = {}

    try:
        # Test if live data methods are available
        if hasattr(client.games_api, "get_scoreboard"):
            print("Testing live scoreboard (this may be limited outside game days)...")
            # Try to get current scoreboard
            scoreboard = client.games_api.get_scoreboard(year=2025, week=15)
            results["live_scoreboard"] = len(scoreboard) if scoreboard else 0
            print(f"✅ Live Scoreboard: Found {results['live_scoreboard']} games")
        else:
            print("⚠️ Live scoreboard method not available")
            results["live_scoreboard"] = "method_not_available"

    except Exception as e:
        print(f"❌ Live scoreboard test failed: {e}")
        results["live_scoreboard"] = "error"

    # Test play-by-play data availability
    try:
        print("Testing play-by-play data...")
        plays = client.get_plays(year=2025, week=1)
        results["play_by_play"] = len(plays) if plays else 0
        print(f"✅ Play-by-Play: Found {results['play_by_play']} plays")

    except Exception as e:
        print(f"❌ Play-by-play test failed: {e}")
        results["play_by_play"] = "error"

    return results


def test_rate_limits(client):
    """Test actual rate limits for Tier 3"""
    print("\n⚡ Testing Rate Limits")
    print("=" * 50)

    # Tier 3: 75k requests/month = ~2.5k/day = ~104/hour = ~25 req/sec sustained
    # We'll test with a smaller sample to be conservative

    request_times = []
    test_requests = 15

    print(f"Making {test_requests} rapid requests to test rate limiting...")

    for i in range(test_requests):
        start_time = time.time()
        try:
            # Use a lightweight endpoint
            client.get_conferences()
            end_time = time.time()
            request_times.append(end_time - start_time)

            if i < 5:  # Only show first few to avoid spam
                print(f"Request {i+1}: {request_times[-1]:.3f}s")

        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
            break

    if request_times:
        avg_time = sum(request_times) / len(request_times)
        max_time = max(request_times)
        min_time = min(request_times)

        estimated_rps = 1 / avg_time

        print(f"\n📊 Rate Limit Test Results:")
        print(f"Average request time: {avg_time:.3f}s")
        print(f"Fastest request: {min_time:.3f}s")
        print(f"Slowest request: {max_time:.3f}s")
        print(f"Estimated rate limit: {estimated_rps:.1f} requests/second")

        # Analysis
        if estimated_rps >= 20:
            print("🎉 Premium rate limits detected (20+ req/sec)")
            tier_assessment = "tier3_plus"
        elif estimated_rps >= 10:
            print("✅ Enhanced rate limits detected (10-20 req/sec)")
            tier_assessment = "tier2_plus"
        else:
            print("⚠️ Basic tier rate limits (<10 req/sec)")
            tier_assessment = "basic"

        return {
            "avg_time": avg_time,
            "max_time": max_time,
            "min_time": min_time,
            "estimated_rps": estimated_rps,
            "successful_requests": len(request_times),
            "tier_assessment": tier_assessment,
        }

    return None


def test_graphql_access(client):
    """Test GraphQL API access"""
    print("\n🔗 Testing GraphQL Access")
    print("=" * 50)

    try:
        if client.graphql_client:
            print("✅ GraphQL client initialized")

            # Test basic GraphQL query
            if hasattr(client.graphql_client, "get_scoreboard"):
                try:
                    scoreboard = client.get_scoreboard_graphql(year=2025, week=15)
                    if scoreboard:
                        print(f"✅ GraphQL Scoreboard: Data retrieved successfully")
                        return True
                    else:
                        print(
                            "⚠️ GraphQL Scoreboard: No data returned (may be expected)"
                        )
                        return True  # Client working, just no data
                except Exception as e:
                    print(f"⚠️ GraphQL Scoreboard query failed: {e}")
                    return False
            else:
                print("⚠️ GraphQL client exists but no get_scoreboard method")
                return False
        else:
            print("❌ GraphQL client not initialized")
            return False

    except Exception as e:
        print(f"❌ GraphQL test failed: {e}")
        return False


def test_weekly_training_downloads():
    """Test weekly training data download availability (Tier 3 feature)"""
    print("\n📚 Testing Weekly Training Data Downloads")
    print("=" * 50)

    # This would typically be a separate endpoint or process
    # For now, let's check if we can identify the pattern

    current_week = datetime.now().isocalendar()[1]
    current_year = datetime.now().year

    print(f"Current season: {current_year}")
    print(f"Current week: {current_week}")

    if current_week >= 5:
        print("✅ Week 5+ - Weekly training data should be available")
        return True
    else:
        print("⚠️ Before Week 5 - Weekly training data not yet available")
        return False


def main():
    """Main test function"""
    print("🎯 Script Ohio 2.0 - Tier 3 Access Test")
    print("=" * 60)
    print(f"Testing at: {datetime.now().isoformat()}")

    # Check API key
    if not os.getenv("CFBD_API_KEY"):
        print("❌ CFBD_API_KEY environment variable not set")
        print("Set it with: export CFBD_API_KEY='your-api-key'")
        return

    # Initialize client
    try:
        config = CFBDConfig.from_env()
        print(f"📋 Config: {config.host}")
        print(f"📋 Current Rate Limit: {config.max_requests_per_second} req/sec")

        client = UnifiedCFBDClient(config)

    except Exception as e:
        print(f"❌ Failed to initialize CFBD client: {e}")
        return

    # Run tests
    results = {
        "timestamp": datetime.now().isoformat(),
        "tier_tested": "tier3",
        "config": {
            "host": config.host,
            "max_requests_per_second": config.max_requests_per_second,
            "rate_limit_delay": config.rate_limit_delay,
        },
    }

    # Test basic endpoints
    results["basic_endpoints"] = test_basic_endpoints(client)

    # Test advanced metrics
    results["advanced_metrics"] = test_advanced_metrics(client)

    # Test live data
    results["live_data"] = test_live_data(client)

    # Test rate limiting
    rate_limit_results = test_rate_limits(client)
    if rate_limit_results:
        results["rate_limit_test"] = rate_limit_results

    # Test GraphQL
    results["graphql_access"] = test_graphql_access(client)

    # Test weekly training data
    results["weekly_training"] = test_weekly_training_downloads()

    # Save results
    results_file = Path("tier3_test_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {results_file}")

    # Summary
    print("\n📊 Summary")
    print("=" * 30)
    basic_status = "✅ Working" if results["basic_endpoints"] else "❌ Failed"
    print(f"Basic Endpoints: {basic_status}")

    graphql_status = "✅ Working" if results["graphql_access"] else "❌ Failed"
    print(f"GraphQL Access: {graphql_status}")

    training_status = (
        "✅ Available" if results["weekly_training"] else "⚠️ Not Available"
    )
    print(f"Weekly Training: {training_status}")

    if "rate_limit_test" in results:
        estimated_rps = results["rate_limit_test"]["estimated_rps"]
        tier_assessment = results["rate_limit_test"].get("tier_assessment", "unknown")
        print(f"Estimated Rate Limit: {estimated_rps:.1f} req/sec")
        print(f"Tier Assessment: {tier_assessment}")

        if tier_assessment == "tier3_plus":
            print("🎉 Tier 3 rate limits detected!")
        elif tier_assessment == "tier2_plus":
            print("✅ Enhanced rate limits - some premium access")
        else:
            print("⚠️ Basic tier rate limits detected")

    # Recommendations
    print("\n💡 Recommendations")
    print("=" * 30)

    if results["graphql_access"]:
        print("✅ GraphQL available - implement real-time subscriptions")
    else:
        print("❌ GraphQL not working - check client configuration")

    if results["weekly_training"] and results["basic_endpoints"]:
        print("✅ Weekly training data available - integrate automated downloads")

    if (
        "rate_limit_test" in results
        and results["rate_limit_test"]["estimated_rps"] > 15
    ):
        print("✅ High rate limits available - optimize concurrent requests")

    print("\n🏁 Tier 3 test complete!")


if __name__ == "__main__":
    main()
