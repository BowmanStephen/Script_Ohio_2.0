import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_talent_data(games_df: pd.DataFrame, talent_df: pd.DataFrame) -> pd.DataFrame:
    """Merge talent data into games DataFrame (Simplified version from agent)"""
    print("Inside merge_talent_data function")
    logger.info("Merging talent data...")
    if talent_df.empty or games_df.empty:
        return games_df

    school_col = "school" if "school" in talent_df.columns else "team"
    print(f"School column identified: {school_col}")

    if school_col in talent_df.columns and "talent" in talent_df.columns:
        # Strip whitespace
        talent_df[school_col] = talent_df[school_col].astype(str).str.strip()
        if "home_team" in games_df.columns:
            games_df["home_team"] = games_df["home_team"].astype(str).str.strip()
        if "away_team" in games_df.columns:
            games_df["away_team"] = games_df["away_team"].astype(str).str.strip()

        print("Creating talent map...")
        talent_map = talent_df.set_index(school_col)["talent"].to_dict()
        print(f"Talent map size: {len(talent_map)}")

        print("Mapping home talent...")
        if "home_team" in games_df.columns:
            games_df["home_talent"] = games_df["home_team"].map(talent_map)

        print("Mapping away talent...")
        if "away_team" in games_df.columns:
            games_df["away_talent"] = games_df["away_team"].map(talent_map)

    return games_df


def main():
    print("Starting reproduction script...")

    # Paths
    base_dir = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
    games_path = base_dir / "model_pack/updated_training_data.csv"
    talent_path = base_dir / "model_pack/data/talent/talent_2025.csv"

    # Load Data
    print(f"Loading games from {games_path}")
    if not games_path.exists():
        print("Games file not found!")
        return

    games_df = pd.read_csv(games_path, low_memory=False)
    print(f"Games loaded: {len(games_df)} rows")

    print(f"Loading talent from {talent_path}")
    if not talent_path.exists():
        print("Talent file not found!")
        return

    talent_df = pd.read_csv(talent_path)
    print(f"Talent loaded: {len(talent_df)} rows")

    # Run Merge
    print("Calling merge_talent_data...")
    try:
        merged_df = merge_talent_data(games_df, talent_df)
        print("Merge successful!")
        print(merged_df[["home_team", "home_talent"]].head())
    except Exception as e:
        print(f"Merge FAILED with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
