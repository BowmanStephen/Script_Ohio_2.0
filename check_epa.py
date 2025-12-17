import sys

import pandas as pd

try:
    df = pd.read_csv("model_pack/updated_training_data.csv", low_memory=False)
    # Check 2025 rows
    df_2025 = df[df["season"] == 2025]
    print(f"Total 2025 rows: {len(df_2025)}")

    if not df_2025.empty:
        # Check EPA columns
        epa_cols = ["home_adjusted_epa", "away_adjusted_epa"]
        print("\nEPA Columns in 2025 data:")
        print(df_2025[epa_cols].head(3))
        print("\nAre they all NaN?")
        print(df_2025[epa_cols].isna().all())

except Exception as e:
    print(f"Error: {e}")
