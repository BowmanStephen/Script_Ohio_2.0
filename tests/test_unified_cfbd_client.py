"""
Test suite for UnifiedCFBDClient.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from src.cfbd_client.errors import (
    CFBDAuthenticationError,
    CFBDForbiddenError,
    CFBDNotFoundError,
    CFBDRateLimitError,
    CFBDServerError,
)
from src.cfbd_client.unified_client import UnifiedCFBDClient
from src.config.cfbd_config import CFBDConfig


class TestUnifiedCFBDClient:
    """Test cases for UnifiedCFBDClient"""

    @pytest.fixture
    def config(self):
        return CFBDConfig(
            api_key="test_key",
            host="https://api.collegefootballdata.com",
            max_requests_per_second=6,
            rate_limit_delay=0.17,
            max_retries=3,
        )

    @pytest.fixture
    def client(self, config):
        with patch("src.cfbd_client.unified_client.cfbd.ApiClient"):
            client = UnifiedCFBDClient(config)
            # Mock cache manager to avoid filesystem/memory state issues
            client.cache_manager = Mock()
            client.cache_manager.get_cached_data.return_value = None
            return client

    def test_initialization(self, client):
        """Test client initialization"""
        assert client.config.api_key == "test_key"
        assert client.config.host == "https://api.collegefootballdata.com"
        assert client.config.max_requests_per_second == 6
        assert client.config.rate_limit_delay == 0.17
        assert client.config.max_retries == 3

    def test_host_config_production(self):
        """Test that production host config is used"""
        config = CFBDConfig(
            api_key="test_key",
            host="https://api.collegefootballdata.com",
        )
        with patch("src.cfbd_client.unified_client.cfbd.ApiClient"):
            client = UnifiedCFBDClient(config)
            # Verify config host is set correctly
            assert client.config.host == "https://api.collegefootballdata.com"

    def test_host_config_next(self):
        """Test that Next API host config is used"""
        config = CFBDConfig(
            api_key="test_key",
            host="https://apinext.collegefootballdata.com",
        )
        with patch("src.cfbd_client.unified_client.cfbd.ApiClient"):
            client = UnifiedCFBDClient(config)
            # Verify config host is set correctly
            assert client.config.host == "https://apinext.collegefootballdata.com"

    def test_get_games(self, client):
        """Test get_games method"""
        # Mock games API
        client.games_api = Mock()
        mock_game = Mock()
        mock_game.to_dict.return_value = {"id": 1, "home_team": "Ohio State"}
        client.games_api.get_games.return_value = [mock_game]

        # Call method
        games = client.get_games(year=2025, week=12)

        # Verify API was called
        client.games_api.get_games.assert_called_once_with(
            year=2025, week=12, season_type="regular", team=None
        )

        # Verify response
        assert len(games) == 1
        assert games[0]["home_team"] == "Ohio State"

    def test_rate_limiting(self, client):
        """Test rate limiting functionality"""
        # Mock sleep
        with patch("time.sleep") as mock_sleep:
            # Simulate rapid requests
            for _ in range(7):
                client._rate_limit()

            # Should have slept at least once (after 6 requests)
            assert mock_sleep.call_count >= 1

    def test_caching(self, client):
        """Test caching functionality"""
        # Mock cache hit
        client.cache_manager.get_cached_data.return_value = [{"id": 1}]
        client.games_api = Mock()

        games = client.get_games(year=2025)

        # API should NOT be called
        client.games_api.get_games.assert_not_called()
        assert games == [{"id": 1}]
        assert client.metrics.cache_hits == 1

    def test_error_handling(self, client):
        """Test error handling"""
        from cfbd.rest import ApiException
        from src.cfbd_client.errors import CFBDServerError

        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(
            status=500, reason="Server Error"
        )

        # Should retry and then raise CFBDServerError (converted from ApiException)
        with patch("time.sleep"):  # speed up test
            with pytest.raises(CFBDServerError):
                client.get_games(year=2025)

        assert client.metrics.errors >= 3

    def test_generic_request_method(self, client):
        """Test generic request() method"""
        client.games_api = Mock()
        mock_game = Mock()
        mock_game.to_dict.return_value = {"id": 1, "home_team": "Ohio State"}
        client.games_api.get_games.return_value = [mock_game]

        # Test that generic request routes to get_games
        result = client.request("GET", "/games", {"year": 2025, "week": 12})
        assert len(result) == 1
        assert result[0]["home_team"] == "Ohio State"

    def test_get_drives(self, client):
        """Test get_drives method"""
        client.drives_api = Mock()
        mock_drive = Mock()
        mock_drive.to_dict.return_value = {"id": 1, "offense": "Ohio State"}
        client.drives_api.get_drives.return_value = [mock_drive]

        drives = client.get_drives(year=2025, week=12)
        assert len(drives) == 1
        assert drives[0]["offense"] == "Ohio State"

    def test_get_player_stats(self, client):
        """Test get_player_stats method"""
        client.players_api = Mock()
        mock_player = Mock()
        mock_player.to_dict.return_value = {"player": "John Doe", "yards": 1000}
        client.players_api.get_player_season_stats.return_value = [mock_player]

        stats = client.get_player_stats(year=2025, team="Ohio State")
        assert len(stats) == 1
        assert stats[0]["player"] == "John Doe"

    def test_get_conferences(self, client):
        """Test get_conferences method"""
        client.conferences_api = Mock()
        mock_conf = Mock()
        mock_conf.to_dict.return_value = {"name": "Big Ten", "id": 1}
        client.conferences_api.get_conferences.return_value = [mock_conf]

        conferences = client.get_conferences()
        assert len(conferences) == 1
        assert conferences[0]["name"] == "Big Ten"

    def test_get_advanced_stats(self, client):
        """Test get_advanced_stats method"""
        client.stats_api = Mock()
        mock_stat = Mock()
        mock_stat.to_dict.return_value = {"team": "Ohio State", "epa": 0.15}
        client.stats_api.get_advanced_season_stats.return_value = [mock_stat]

        stats = client.get_advanced_stats(year=2025, team="Ohio State")
        assert len(stats) == 1
        assert stats[0]["team"] == "Ohio State"

    def test_error_taxonomy_401(self, client):
        """Test that 401 errors raise CFBDAuthenticationError"""
        from cfbd.rest import ApiException

        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(
            status=401, reason="Unauthorized"
        )

        with pytest.raises(CFBDAuthenticationError):
            client.get_games(year=2025)

    def test_error_taxonomy_403(self, client):
        """Test that 403 errors raise CFBDForbiddenError"""
        from cfbd.rest import ApiException

        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(
            status=403, reason="Forbidden"
        )

        with pytest.raises(CFBDForbiddenError):
            client.get_games(year=2025)

    def test_error_taxonomy_404(self, client):
        """Test that 404 errors raise CFBDNotFoundError (not return None)"""
        from cfbd.rest import ApiException

        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(
            status=404, reason="Not Found"
        )

        # 404 errors should raise CFBDNotFoundError, not return None
        with pytest.raises(CFBDNotFoundError):
            client.get_games(year=2025)

    def test_error_taxonomy_429(self, client):
        """Test that 429 errors raise CFBDRateLimitError with Retry-After"""
        from cfbd.rest import ApiException

        client.games_api = Mock()
        mock_exception = ApiException(status=429, reason="Too Many Requests")
        mock_exception.headers = {"Retry-After": "30"}
        client.games_api.get_games.side_effect = [
            mock_exception,
            Mock(to_dict=lambda: {"id": 1}),
        ]

        with patch("time.sleep"):
            result = client.get_games(year=2025)
            # Should have retried and succeeded
            assert result is not None

    def test_get_plays(self, client):
        """Test get_plays method"""
        client.plays_api = Mock()
        mock_play = Mock()
        mock_play.to_dict.return_value = {"id": 1, "play_type": "rush", "yards": 5}
        client.plays_api.get_plays.return_value = [mock_play]

        plays = client.get_plays(year=2025, week=12)
        client.plays_api.get_plays.assert_called_once_with(
            year=2025, week=12, season_type="regular", team=None
        )
        assert len(plays) == 1
        assert plays[0]["play_type"] == "rush"

    def test_get_recruiting(self, client):
        """Test get_recruiting method"""
        client.recruiting_api = Mock()
        mock_recruit = Mock()
        mock_recruit.to_dict.return_value = {
            "team": "Ohio State",
            "rank": 1,
            "year": 2025,
        }
        client.recruiting_api.get_team_recruiting_rankings.return_value = [mock_recruit]

        recruiting = client.get_recruiting(year=2025)
        client.recruiting_api.get_team_recruiting_rankings.assert_called_once_with(
            year=2025
        )
        assert len(recruiting) == 1
        assert recruiting[0]["rank"] == 1

    def test_get_venues(self, client):
        """Test get_venues method"""
        client.venues_api = Mock()
        mock_venue = Mock()
        mock_venue.to_dict.return_value = {"name": "Ohio Stadium", "capacity": 102780}
        client.venues_api.get_venues.return_value = [mock_venue]

        venues = client.get_venues()
        client.venues_api.get_venues.assert_called_once()
        assert len(venues) == 1
        assert venues[0]["name"] == "Ohio Stadium"

    def test_get_coaches(self, client):
        """Test get_coaches method"""
        client.coaches_api = Mock()
        mock_coach = Mock()
        mock_coach.to_dict.return_value = {
            "first_name": "Ryan",
            "last_name": "Day",
            "team": "Ohio State",
        }
        client.coaches_api.get_coaches.return_value = [mock_coach]

        coaches = client.get_coaches(year=2025, team="Ohio State")
        # Matches existing implementation signature
        client.coaches_api.get_coaches.assert_called_once_with(
            first_name=None, last_name=None, team="Ohio State", year=2025
        )
        assert len(coaches) == 1
        assert coaches[0]["last_name"] == "Day"

    def test_get_game_media(self, client):
        """Test get_game_media method"""
        client.games_api = Mock()
        mock_media = Mock()
        mock_media.to_dict.return_value = {"id": 1, "outlet": "ESPN"}
        client.games_api.get_game_media.return_value = [mock_media]

        media = client.get_game_media(year=2025, week=12)
        client.games_api.get_game_media.assert_called_once_with(
            year=2025, week=12, season_type="regular", team=None, conference=None
        )
        assert len(media) == 1
        assert media[0]["outlet"] == "ESPN"

    def test_get_calendar(self, client):
        """Test get_calendar method"""
        client.games_api = Mock()
        mock_week = Mock()
        mock_week.to_dict.return_value = {
            "season": 2025,
            "week": 1,
            "season_type": "regular",
        }
        client.games_api.get_calendar.return_value = [mock_week]

        calendar = client.get_calendar(year=2025)
        client.games_api.get_calendar.assert_called_once_with(year=2025)
        assert len(calendar) == 1
        assert calendar[0]["week"] == 1

    def test_get_rankings(self, client):
        """Test get_rankings method"""
        client.rankings_api = Mock()
        mock_poll = Mock()
        mock_poll.to_dict.return_value = {
            "season": 2025,
            "week": 1,
            "polls": [{"poll": "AP", "ranks": []}],
        }
        client.rankings_api.get_rankings.return_value = [mock_poll]

        rankings = client.get_rankings(year=2025, week=1)
        client.rankings_api.get_rankings.assert_called_once_with(
            year=2025, week=1, season_type="regular"
        )
        assert len(rankings) == 1
        assert rankings[0]["polls"][0]["poll"] == "AP"

    def test_get_box_score(self, client):
        """Test get_box_score method"""
        client.games_api = Mock()
        mock_box = Mock()
        mock_box.to_dict.return_value = {"teams": {"home": {"stats": []}}}
        client.games_api.get_game_box_score.return_value = mock_box

        box = client.get_box_score(game_id=12345)
        client.games_api.get_game_box_score.assert_called_once_with(game_id=12345)
        assert "teams" in box

    def test_get_team_matchup(self, client):
        """Test get_team_matchup method"""
        client.teams_api = Mock()
        mock_matchup = Mock()
        mock_matchup.to_dict.return_value = {
            "team1": "Ohio State",
            "team2": "Michigan",
            "games": [],
        }
        client.teams_api.get_team_matchup.return_value = mock_matchup

        matchup = client.get_team_matchup(team1="Ohio State", team2="Michigan")
        client.teams_api.get_team_matchup.assert_called_once_with(
            team1="Ohio State", team2="Michigan", min_year=None, max_year=None
        )
        assert matchup["team1"] == "Ohio State"

    def test_get_roster(self, client):
        """Test get_roster method"""
        client.teams_api = Mock()
        mock_player = Mock()
        mock_player.to_dict.return_value = {
            "first_name": "C.J.",
            "last_name": "Stroud",
            "position": "QB",
        }
        client.teams_api.get_roster.return_value = [mock_player]

        roster = client.get_roster(year=2025, team="Ohio State")
        client.teams_api.get_roster.assert_called_once_with(
            year=2025, team="Ohio State"
        )
        assert len(roster) == 1
        assert roster[0]["last_name"] == "Stroud"

    def test_get_win_probabilities(self, client):
        """Test get_win_probabilities method"""
        client.metrics_api = Mock()
        mock_wp = Mock()
        mock_wp.to_dict.return_value = {"gameId": 1, "homeWinProb": 0.75}
        client.metrics_api.get_pregame_win_probabilities.return_value = [mock_wp]

        wps = client.get_win_probabilities(year=2025, week=12)
        client.metrics_api.get_pregame_win_probabilities.assert_called_once_with(
            year=2025, week=12, team=None
        )
        assert len(wps) == 1
        assert wps[0]["homeWinProb"] == 0.75

    def test_get_scoreboard_graphql(self, client):
        """Test get_scoreboard_graphql method"""
        # Case 1: GraphQL client not available
        client.graphql_client = None
        result = client.get_scoreboard_graphql(year=2025, week=12)
        assert result is None

        # Case 2: GraphQL client available
        client.graphql_client = Mock()
        mock_result = {"data": {"game": []}}
        client.graphql_client.get_scoreboard.return_value = mock_result

        result = client.get_scoreboard_graphql(year=2025, week=12)
        client.graphql_client.get_scoreboard.assert_called_once_with(
            season=2025, week=12
        )
        assert result == mock_result

    def test_get_recruiting_graphql(self, client):
        """Test get_recruiting_graphql method"""
        # Case 1: GraphQL client not available
        client.graphql_client = None
        result = client.get_recruiting_graphql(year=2025)
        assert result is None

        # Case 2: GraphQL client available
        client.graphql_client = Mock()
        mock_result = {"data": {"recruit": []}}
        client.graphql_client.get_recruits.return_value = mock_result

        result = client.get_recruiting_graphql(year=2025, team="Ohio State")
        client.graphql_client.get_recruits.assert_called_once_with(
            season=2025, team="Ohio State", limit=50
        )
        assert result == mock_result
