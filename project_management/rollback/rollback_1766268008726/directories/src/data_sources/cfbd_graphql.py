"""GraphQL client for CollegeFootballData.com API.

This module provides a GraphQL client for accessing CFBD's GraphQL API,
which requires Patreon Tier 3+ access.
"""

import logging
import os
from typing import Any, Dict, Optional

try:
    from gql import Client, gql
    from gql.transport.requests import RequestsHTTPTransport

    GQL_AVAILABLE = True
except ImportError:
    GQL_AVAILABLE = False
    Client = None  # type: ignore
    gql = None  # type: ignore
    RequestsHTTPTransport = None  # type: ignore

logger = logging.getLogger(__name__)

# GraphQL endpoint configuration
DEFAULT_GRAPHQL_ENDPOINT = "https://graphql.collegefootballdata.com/v1/graphql"
NEXT_GRAPHQL_ENDPOINT = "https://apinext.collegefootballdata.com/v1/graphql"


def _build_headers(api_key: str) -> Dict[str, str]:
    """Build HTTP headers for GraphQL requests."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "ScriptOhio2.0/CFBD-GraphQL",
    }


class CFBDGraphQLClient:
    """
    GraphQL client for CollegeFootballData.com API.

    This client provides access to CFBD's GraphQL API, which requires
    Patreon Tier 3+ subscription. Supports both production and Next API hosts.

    Example:
        >>> client = CFBDGraphQLClient(api_key="your_key")
        >>> result = client.get_scoreboard(season=2025, week=12)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: str = "production",
        timeout: int = 30,
    ):
        """
        Initialize GraphQL client.

        Args:
            api_key: CFBD API key (defaults to CFBD_API_KEY env var)
            host: API host - "production" or "next" (default: "production")
            timeout: Request timeout in seconds (default: 30)

        Raises:
            ImportError: If gql library is not installed
            ValueError: If API key is not provided
        """
        if not GQL_AVAILABLE:
            raise ImportError(
                "gql library is required for GraphQL support. "
                "Install with: pip install gql[all] requests"
            )

        # Check if GraphQL is explicitly disabled
        if os.getenv("CFBD_GRAPHQL_DISABLED", "false").lower() == "true":
            raise ValueError(
                "GraphQL is explicitly disabled via CFBD_GRAPHQL_DISABLED environment variable"
            )

        # Get API key (support both CFBD_API_KEY and CFBD_API_TOKEN)
        self.api_key = (
            api_key or os.getenv("CFBD_API_KEY") or os.getenv("CFBD_API_TOKEN")
        )
        if not self.api_key:
            raise ValueError(
                "CFBD_API_KEY or CFBD_API_TOKEN is required for GraphQL access. "
                "Set environment variable or pass api_key parameter."
            )

        # Determine endpoint based on host
        if host.lower() == "next":
            endpoint = NEXT_GRAPHQL_ENDPOINT
        else:
            endpoint = DEFAULT_GRAPHQL_ENDPOINT

        self.endpoint = endpoint
        self.host = host.lower()

        # Initialize transport and client
        self._transport = RequestsHTTPTransport(
            url=self.endpoint,
            headers=_build_headers(self.api_key),
            timeout=timeout,
        )
        self._client = Client(
            transport=self._transport,
            fetch_schema_from_transport=False,
        )

        logger.info(f"GraphQL client initialized for {self.host} host")

    def query(
        self, query_string: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query_string: GraphQL query string
            variables: Optional query variables

        Returns:
            Query result dictionary

        Raises:
            Exception: If query execution fails
        """
        try:
            document = gql(query_string)
            result = self._client.execute(document, variable_values=variables)
            return result
        except Exception as e:
            logger.error(f"GraphQL query failed: {e}")
            raise

    def get_scoreboard(
        self,
        season: int,
        week: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get live scoreboard data.

        Args:
            season: Season year (e.g., 2025)
            week: Optional week number

        Returns:
            Scoreboard data dictionary
        """
        query = """
        query Scoreboard($season: Int!, $week: smallint) {
          game(
            where: {
              season: { _eq: $season }
              week: { _eq: $week }
            }
            order_by: { startDate: asc }
          ) {
            id
            season
            week
            seasonType
            startDate
            homeTeam
            awayTeam
            homePoints
            awayPoints
            completed
            venue
          }
        }
        """
        variables: Dict[str, Any] = {"season": season}
        if week is not None:
            variables["week"] = week

        return self.query(query, variables)

    def get_ratings(
        self,
        season: int,
        team: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get team ratings data.

        Args:
            season: Season year (e.g., 2025)
            team: Optional team name filter

        Returns:
            Ratings data dictionary
        """
        # Build query conditionally - GraphQL requires different structure if team filter is used
        if team:
            query = """
            query Ratings($year: smallint!, $team: String) {
              ratings(
                where: {
                  year: { _eq: $year }
                  team: { _eq: $team }
                }
              ) {
                team
                year
                conference
                conferenceId
                elo
                fpi
                spOverall
                spOffense
                spDefense
                spSpecialTeams
                srs
                fpiOverallEfficiency
                fpiOffensiveEfficiency
                fpiDefensiveEfficiency
                fpiSpecialTeamsEfficiency
                fpiResumeRank
                fpiSosRank
                fpiStrengthOfRecordRank
                fpiGameControlRank
                fpiAvgWinProbabilityRank
              }
            }
            """
            variables: Dict[str, Any] = {"year": season, "team": team}
        else:
            query = """
            query Ratings($year: smallint!) {
              ratings(
                where: {
                  year: { _eq: $year }
                }
              ) {
                team
                year
                conference
                conferenceId
                elo
                fpi
                spOverall
                spOffense
                spDefense
                spSpecialTeams
                srs
                fpiOverallEfficiency
                fpiOffensiveEfficiency
                fpiDefensiveEfficiency
                fpiSpecialTeamsEfficiency
                fpiResumeRank
                fpiSosRank
                fpiStrengthOfRecordRank
                fpiGameControlRank
                fpiAvgWinProbabilityRank
              }
            }
            """
            variables: Dict[str, Any] = {"year": season}

        return self.query(query, variables)

    def get_recruits(
        self,
        season: int,
        team: Optional[str] = None,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """
        Get recruiting data.

        Args:
            season: Recruiting class year (e.g., 2025)
            team: Optional team name filter
            limit: Maximum number of recruits to return (default: 25)

        Returns:
            Recruiting data dictionary
        """
        query = """
        query Recruits($season: smallint!, $team: String, $limit: Int!) {
          recruit(
            where: {
              year: { _eq: $season }
              college: { school: { _eq: $team } }
            }
            limit: $limit
            order_by: [{ rating: desc }, { stars: desc }]
          ) {
            id
            name
            stars
            rating
            position {
              position
              positionGroup
            }
            recruitType
            overallRank
            college {
              school
              conference
            }
            year
          }
        }
        """
        variables: Dict[str, Any] = {
            "season": season,
            "limit": limit,
        }
        if team:
            variables["team"] = team

        return self.query(query, variables)

    def get_plays(
        self,
        season: int,
        week: Optional[int] = None,
        game_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get play-by-play data via GraphQL.

        Args:
            season: Season year (e.g., 2025)
            week: Optional week number
            game_id: Optional specific game ID

        Returns:
            Play-by-play data dictionary
        """
        query = """
        query Plays($season: Int!, $week: smallint, $gameId: Int) {
          play(
            where: {
              game: {
                season: { _eq: $season }
                week: { _eq: $week }
                id: { _eq: $gameId }
              }
            }
            order_by: { playNumber: asc }
          ) {
            id
            gameId
            driveId
            playNumber
            offense
            defense
            offenseConference
            defenseConference
            home
            period
            clock
            yardLine
            distance
            yardsGained
            down
            playType
            playText
            ppa
            wallclock
          }
        }
        """
        variables: Dict[str, Any] = {"season": season}
        if week is not None:
            variables["week"] = week
        if game_id is not None:
            variables["gameId"] = game_id

        return self.query(query, variables)

    def _normalize_betting_line(self, line_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize GraphQL betting line data to match REST API shape.

        Args:
            line_data: Raw GraphQL betting line data

        Returns:
            Normalized betting line dictionary matching REST API format
        """
        # Extract nested game data if present
        game = line_data.get("game", {})
        if isinstance(game, dict):
            game_id = game.get("id")
            home_team = game.get("homeTeam")
            away_team = game.get("awayTeam")
            start_date = game.get("startDate")
        else:
            game_id = line_data.get("gameId")
            home_team = None
            away_team = None
            start_date = None

        # Normalize to REST API shape
        normalized = {
            "id": line_data.get("id"),
            "gameId": game_id or line_data.get("gameId"),
            "season": None,  # Will be filled from context
            "week": None,  # Will be filled from context
            "seasonType": "regular",
            "startDate": start_date,
            "homeTeam": home_team,
            "awayTeam": away_team,
            "provider": line_data.get("provider"),
            "spread": line_data.get("spread"),
            "formattedSpread": line_data.get("formattedSpread"),
            "overUnder": line_data.get("overUnder"),
            "formattedOverUnder": line_data.get("formattedOverUnder"),
            "homeMoneyline": line_data.get("homeMoneyline"),
            "awayMoneyline": line_data.get("awayMoneyline"),
        }

        # Remove None values to match REST API behavior
        return {k: v for k, v in normalized.items() if v is not None}

    def get_betting_lines(
        self,
        season: int,
        week: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get betting lines via GraphQL.

        Args:
            season: Season year (e.g., 2025)
            week: Optional week number

        Returns:
            Betting lines data dictionary
        """
        query = """
        query BettingLines($season: Int!, $week: smallint) {
          bettingLine(
            where: {
              game: {
                season: { _eq: $season }
                week: { _eq: $week }
              }
            }
            order_by: { game: { startDate: asc } }
          ) {
            id
            gameId
            game {
              id
              homeTeam
              awayTeam
              startDate
            }
            provider
            spread
            overUnder
            homeMoneyline
            awayMoneyline
            formattedSpread
            formattedOverUnder
          }
        }
        """
        variables: Dict[str, Any] = {"season": season}
        if week is not None:
            variables["week"] = week

        return self.query(query, variables)
