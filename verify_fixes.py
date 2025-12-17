import importlib.util
import logging
import os
import sys
from pathlib import Path

import pandas as pd

# Set up project path
PROJECT_ROOT = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_logging_config():
    print("\n--- Testing Logging Configuration ---")

    # 1. Test model_training_agent logging
    print("Importing model_training_agent...")
    try:
        from model_pack import model_training_agent

        print("Successfully imported model_training_agent.")

        # Check if root logger has handlers (it shouldn't if we fixed it)
        root_logger = logging.getLogger()
        if len(root_logger.handlers) == 0:
            print("PASS: Root logger has no handlers after import (Correct behavior).")
        else:
            print(
                f"WARNING: Root logger has {len(root_logger.handlers)} handlers (Expected 0)."
            )
            for h in root_logger.handlers:
                print(f"  - {h}")

    except Exception as e:
        print(f"FAIL: Error importing model_training_agent: {e}")


def test_merge_robustness():
    print("\n--- Testing merge_talent_data Robustness ---")

    try:
        from model_pack.data_acquisition_agent import DataAcquisitionAgent

        agent = DataAcquisitionAgent()

        # Test 1: Empty DataFrames
        print("Test 1: Empty DataFrames...")
        res = agent.merge_talent_data(pd.DataFrame(), pd.DataFrame())
        if res.empty:
            print("PASS: Handled empty DataFrames correctly.")
        else:
            print("FAIL: Did not return empty DataFrame for empty input.")

        # Test 2: Valid Data
        print("Test 2: Valid Data...")
        games = pd.DataFrame(
            {
                "home_team": ["Ohio State", "Michigan"],
                "away_team": ["Penn State", "Wisconsin"],
                "home_points": [10, 20],
            }
        )
        talent = pd.DataFrame(
            {
                "school": ["Ohio State", "Michigan", "Penn State", "Wisconsin"],
                "talent": [900, 850, 800, 750],
            }
        )

        res = agent.merge_talent_data(games, talent)
        if "home_talent" in res.columns:
            print("PASS: Merged talent data successfully.")
            print(res[["home_team", "home_talent"]])
        else:
            print("FAIL: Failed to merge talent columns.")

        # Test 3: Invalid Data (Missing columns)
        print("Test 3: Invalid Data (Missing columns)...")
        bad_talent = pd.DataFrame({"wrong_col": [1, 2, 3]})
        res = agent.merge_talent_data(games, bad_talent)
        if "home_talent" not in res.columns:  # Should return original df
            print(
                "PASS: Handled invalid talent DataFrame correctly (returned original)."
            )
        else:
            print("FAIL: Unexpectedly modified DataFrame with invalid input.")

    except Exception as e:
        print(f"FAIL: Error during robustness test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_logging_config()
    test_merge_robustness()
