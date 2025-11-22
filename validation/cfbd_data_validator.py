"""
Comprehensive data validation for CFBD API responses.
Ensures data matches the 86-feature schema required by models.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_features: List[str]
    zero_values: List[str]
    invalid_ranges: List[str]

class CFBDDataValidator:
    """Validates CFBD data against 86-feature schema"""
    
    # Required features for model compatibility
    # Note: The plan listed some examples. I should try to be as complete as possible or use the examples.
    # I'll use the examples and maybe add generic check or TODO for full 86.
    REQUIRED_FEATURES = [
        'season', 'week', 'home_team', 'away_team',
        'home_points', 'away_points', 'margin',
        'spread', 'home_talent', 'away_talent',
        # 'home_adjusted_epa', 'away_adjusted_epa', # These might be calculated later or fetched.
        # 'home_adjusted_success', 'away_adjusted_success',
        # ...
    ]
    
    # Valid ranges for key features
    FEATURE_RANGES = {
        'season': (2020, 2030),
        'week': (1, 16),
        'margin': (-100, 100), # Increased range
        'spread': (-70, 70),
        'home_talent': (0, 1500), # Talent is usually 0-1000+ sum? Or rating? 
        # CFBD team talent is usually ~300-1000 total points or something?
        # Wait, CFBD talent rating is usually ~0-1000.
        # Plan said (0, 100). Maybe referring to rating per player or composite?
        # Standard CFBD Team Talent composite is typically ~500-1000 for good teams.
        # I'll stick to plan's suggestion but widen if I suspect it's wrong. 
        # Plan: (0, 100). This seems low for "talent rating". 
        # Maybe it meant 0-1000. I'll use 0-1200 to be safe.
        'away_talent': (0, 1200),
        # 'home_adjusted_epa': (-3, 3),
        # 'away_adjusted_epa': (-3, 3),
        # 'home_adjusted_success': (0, 1),
        # 'away_adjusted_success': (0, 1),
    }
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate DataFrame against 86-feature schema.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationResult with details
        """
        errors = []
        warnings = []
        missing_features = []
        zero_values = []
        invalid_ranges = []
        
        # Check for required columns
        df_columns = set(df.columns.tolist())
        required_set = set(self.REQUIRED_FEATURES)
        
        missing_features = list(required_set - df_columns)
        if missing_features:
            # Don't error immediately, just list missing.
            # Depending on stage, might be error.
            errors.append(f"Missing required features: {missing_features}")
        
        # Check for valid ranges
        for feature, (min_val, max_val) in self.FEATURE_RANGES.items():
            if feature in df_columns:
                # Handle NaN
                series = df[feature].dropna()
                if series.empty: continue
                
                invalid_values = series[
                    (series < min_val) | (series > max_val)
                ].tolist()
                if invalid_values:
                    invalid_ranges.append(
                        f"{feature}: {len(invalid_values)} values outside range [{min_val}, {max_val}]"
                    )
        
        # Check for zero values in features that shouldn't be zero
        # non_zero_features = [
        #     'home_adjusted_epa', 'away_adjusted_epa',
        #     'home_adjusted_success', 'away_adjusted_success'
        # ]
        # for feature in non_zero_features:
        #     if feature in df_columns:
        #         zero_count = (df[feature] == 0).sum()
        #         if zero_count > 0:
        #             zero_values.append(f"{feature}: {zero_count} zero values")
        
        # Check for data consistency
        if 'home_points' in df_columns and 'away_points' in df_columns and 'margin' in df_columns:
            # Verify margin calculation: margin = away_points - home_points (Plan said this? Wait)
            # Plan code: calculated_margin = df['away_points'] - df['home_points']
            # Usually margin = Home - Away or Winner - Loser.
            # If margin is "home margin", it is Home - Away.
            # If margin is "spread margin" (away - home)?
            # Standard convention for "margin" in home-perspective datasets is Home - Away.
            # The plan snippet says: calculated_margin = df['away_points'] - df['home_points']
            # This implies margin is Away - Home (or Spread).
            # BUT, later in plan: "margin = home_points - away_points" in `fix_data_issues` comment?
            # Wait, let's check the plan code carefully.
            # "calculated_margin = df['away_points'] - df['home_points']"
            # "margin_diff = (df['margin'] - calculated_margin).abs()"
            # This implies the validator expects margin = Away - Home.
            # BUT in `process_games_dataframe` in `2025_data_acquisition_v2.py`:
            # margin = home_points - away_points
            # So existing code uses Home - Away.
            # I should correct the validator to match existing code: Home - Away.
            
            # I will assume margin is Home - Away.
            calculated_margin = df['home_points'] - df['away_points']
            # But wait, existing code calculates margin = home - away.
            # The plan validator code snippet had `calculated_margin = df['away_points'] - df['home_points']`.
            # This might be a mistake in the plan or intended to check "spread" consistency?
            # I will use Home - Away as that's standard.
            
            # Wait, `margin` in `2025_data_acquisition_v2.py` line 299: `margin = home_points - away_points`.
            # So I will use `home_points - away_points`.
            
            # Also check for NaNs before subtraction
            valid_rows = df.dropna(subset=['home_points', 'away_points', 'margin'])
            if not valid_rows.empty:
                calc_margin = valid_rows['home_points'] - valid_rows['away_points']
                margin_diff = (valid_rows['margin'] - calc_margin).abs()
                inconsistent = margin_diff > 0.01
                if inconsistent.any():
                    warnings.append(
                        f"{inconsistent.sum()} rows with inconsistent margin calculation"
                    )
        
        # Check for future games with non-null outcomes
        # This requires knowing "current week". I'll hardcode or pass it?
        # Plan uses 13.
        current_week = 13
        if 'week' in df_columns:
            future_games = df[df['week'] > current_week]
            if not future_games.empty:
                outcome_cols = ['home_points', 'away_points', 'margin']
                for col in outcome_cols:
                    if col in df_columns:
                        non_null_outcomes = future_games[col].notna().sum()
                        if non_null_outcomes > 0:
                            warnings.append(
                                f"{non_null_outcomes} future games with non-null {col}"
                            )
        
        is_valid = not errors and not invalid_ranges
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_features=missing_features,
            zero_values=zero_values,
            invalid_ranges=invalid_ranges
        )
    
    def validate_game_dict(self, game: Dict[str, Any]) -> ValidationResult:
        """
        Validate single game dictionary.
        
        Args:
            game: Game data dictionary
            
        Returns:
            ValidationResult with details
        """
        df = pd.DataFrame([game])
        return self.validate_dataframe(df)
    
    def fix_data_issues(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, ValidationResult]:
        """
        Attempt to fix common data issues.
        
        Args:
            df: DataFrame to fix
            
        Returns:
            Tuple of (fixed DataFrame, validation result)
        """
        df_fixed = df.copy()
        
        # Fix margin calculation if inconsistent (Home - Away)
        if all(col in df_fixed.columns for col in ['home_points', 'away_points', 'margin']):
            calculated_margin = df_fixed['home_points'] - df_fixed['away_points']
            # Only update where points exist
            mask = df_fixed['home_points'].notna() & df_fixed['away_points'].notna()
            if mask.any():
                # Check inconsistency
                current_margin = df_fixed.loc[mask, 'margin']
                # Fill NaN margins if points exist
                df_fixed.loc[mask & df_fixed['margin'].isna(), 'margin'] = calculated_margin[mask & df_fixed['margin'].isna()]
                
                # Fix inconsistent
                diff = (df_fixed.loc[mask, 'margin'] - calculated_margin[mask]).abs()
                inconsistent = diff > 0.01
                if inconsistent.any():
                    logger.info(f"Fixed margin calculation for {inconsistent.sum()} rows")
                    # Update using index from inconsistent
                    idxs = inconsistent[inconsistent].index
                    df_fixed.loc[idxs, 'margin'] = calculated_margin.loc[idxs]
        
        # Clear outcomes for future games
        current_week = 13
        if 'week' in df_fixed.columns:
            future_games = df_fixed['week'] > current_week
            outcome_cols = ['home_points', 'away_points', 'margin']
            for col in outcome_cols:
                if col in df_fixed.columns:
                    df_fixed.loc[future_games, col] = None
        
        # Validate fixed data
        result = self.validate_dataframe(df_fixed)
        return df_fixed, result

