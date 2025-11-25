#!/usr/bin/env python3
"""
Shared Utilities for Data Acquisition

Common functions used across data acquisition scripts to reduce duplication:
- GraphQL/REST client initialization
- Rate limiting
- Data validation
- Column normalization

Author: Model Pack Improvement Plan
Created: 2025-11-19
"""

import logging
import os
from typing import Optional, Dict, Any
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class DataAcquisitionUtils:
    """Shared utilities for data acquisition operations"""
    
    @staticmethod
    def get_api_key() -> str:
        """
        Get CFBD API key from environment variables.
        
        Returns:
            API key string
            
        Raises:
            ValueError: If API key is not found
        """
        api_key = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
        if not api_key:
            raise ValueError(
                "CFBD_API_KEY or CFBD_API_TOKEN environment variable required. "
                "Get your API key from https://collegefootballdata.com/"
            )
        return api_key
    
    @staticmethod
    def initialize_graphql_client(api_key: str, force_rest: bool = False) -> Optional[Any]:
        """
        Initialize GraphQL client if available.
        
        Args:
            api_key: CFBD API key
            force_rest: If True, skip GraphQL initialization
            
        Returns:
            GraphQL client instance or None
        """
        if force_rest:
            return None
            
        try:
            from src.data_sources.cfbd_graphql import CFBDGraphQLClient
            client = CFBDGraphQLClient(api_key=api_key, host="production")
            # Test connectivity
            test_result = client.query("query { __typename }", {})
            if test_result:
                logger.info("✅ GraphQL client initialized successfully")
                return client
            else:
                logger.warning("⚠️ GraphQL connectivity test failed")
                return None
        except ImportError:
            logger.warning("⚠️ GraphQL client not available - will use REST API only")
            return None
        except Exception as e:
            logger.warning(f"⚠️ GraphQL client initialization failed: {e}")
            return None
    
    @staticmethod
    def initialize_rest_clients(api_key: str):
        """
        Initialize REST API clients.
        
        Args:
            api_key: CFBD API key
            
        Returns:
            Dictionary of API client instances
        """
        try:
            import cfbd
            from cfbd import ApiClient, BettingApi, Configuration, GamesApi, PlaysApi, RatingsApi, TeamsApi
            
            configuration = Configuration()
            configuration.access_token = api_key
            configuration.host = "https://api.collegefootballdata.com"
            api_client = ApiClient(configuration)
            
            return {
                'api_client': api_client,
                'games_api': GamesApi(api_client),
                'plays_api': PlaysApi(api_client),
                'teams_api': TeamsApi(api_client),
                'ratings_api': RatingsApi(api_client),
                'betting_api': BettingApi(api_client),
            }
        except ImportError as e:
            logger.error(f"Failed to import CFBD REST clients: {e}")
            raise
    
    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names from camelCase to snake_case.
        
        Args:
            df: DataFrame with potentially mixed column naming
            
        Returns:
            DataFrame with normalized column names
        """
        if df.empty:
            return df
        
        # Column renaming dictionary (camelCase -> snake_case)
        column_mapping = {
            "homeTeam": "home_team",
            "awayTeam": "away_team",
            "homePoints": "home_points",
            "awayPoints": "away_points",
            "seasonType": "season_type",
            "startDate": "start_date",
            "homeConference": "home_conference",
            "awayConference": "away_conference",
            "neutralSite": "neutral_site",
            "conferenceGame": "conference_game"
        }
        
        # Rename columns that exist
        rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
        if rename_dict:
            df = df.rename(columns=rename_dict)
        
        # Convert start_date to datetime if present
        if "start_date" in df.columns:
            df["start_date"] = pd.to_datetime(df["start_date"], errors='coerce')
        
        return df
    
    @staticmethod
    def convert_graphql_to_dataframe(records: list) -> pd.DataFrame:
        """
        Convert GraphQL records to DataFrame with proper normalization.
        
        Args:
            records: List of game records from GraphQL
            
        Returns:
            Normalized DataFrame with snake_case columns
        """
        if not records:
            return pd.DataFrame()
        
        # Use json_normalize to flatten nested structures
        df = pd.json_normalize(records)
        
        # Normalize column names
        df = DataAcquisitionUtils.normalize_column_names(df)
        
        return df
    
    @staticmethod
    def is_fbs_game(row: pd.Series, config) -> bool:
        """
        Check if a game row is between FBS teams.
        
        Args:
            row: DataFrame row containing game information
            config: Configuration object with is_fbs_conference method
            
        Returns:
            True if both teams are FBS, False otherwise
        """
        home_conf = row.get("home_conference") or row.get("homeConference")
        away_conf = row.get("away_conference") or row.get("awayConference")
        
        # Handle string or None values
        if home_conf is None or pd.isna(home_conf):
            home_conf = ""
        if away_conf is None or pd.isna(away_conf):
            away_conf = ""
        
        # Convert to string if needed
        if hasattr(home_conf, 'name'):
            home_conf = home_conf.name
        if hasattr(away_conf, 'name'):
            away_conf = away_conf.name
        
        home_conf = str(home_conf) if home_conf else ""
        away_conf = str(away_conf) if away_conf else ""
        
        return (config.is_fbs_conference(home_conf) or config.is_fbs_conference(away_conf))
    
    @staticmethod
    def validate_game_data(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate game data quality.
        
        Args:
            df: DataFrame containing game data
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'total_games': len(df),
            'missing_required_fields': 0,
            'invalid_dates': 0,
            'duplicate_games': 0,
            'is_valid': True
        }
        
        if df.empty:
            validation_results['is_valid'] = False
            return validation_results
        
        # Check required fields
        required_fields = ['season', 'week', 'home_team', 'away_team']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            validation_results['missing_required_fields'] = len(missing_fields)
            validation_results['is_valid'] = False
        
        # Check for duplicate games
        if all(field in df.columns for field in ['season', 'week', 'home_team', 'away_team']):
            duplicates = df.duplicated(subset=['season', 'week', 'home_team', 'away_team']).sum()
            validation_results['duplicate_games'] = int(duplicates)
            if duplicates > 0:
                validation_results['is_valid'] = False
        
        # Check date validity
        if 'start_date' in df.columns:
            invalid_dates = df['start_date'].isna().sum()
            validation_results['invalid_dates'] = int(invalid_dates)
        
        return validation_results
    
    @staticmethod
    def create_rate_limiter():
        """
        Create rate limiter instance.
        
        Returns:
            RateLimiter instance
        """
        try:
            from starter_pack.utils.cfbd_loader import RateLimiter
            return RateLimiter()
        except ImportError:
            logger.warning("RateLimiter not available - rate limiting disabled")
            # Return a mock rate limiter
            class MockRateLimiter:
                def wait(self):
                    pass
            return MockRateLimiter()

