import pandas as pd
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_data():
    file_path = Path("model_pack/updated_training_data.csv")
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return
    
    logger.info(f"Loading {file_path}...")
    df = pd.read_csv(file_path)
    initial_count = len(df)
    
    # Identify 2025 games with 0-0 scores
    # We assume 0-0 is invalid for 2025 (unplayed games)
    mask_zero_scores = (df['season'] == 2025) & (df['home_points'] == 0) & (df['away_points'] == 0)
    
    bad_games = df[mask_zero_scores]
    
    if len(bad_games) > 0:
        logger.warning(f"Found {len(bad_games)} games with 0-0 scores in 2025. These are likely unplayed games.")
        
        # Show breakdown by week
        logger.info("Breakdown of removed games by week:")
        print(bad_games['week'].value_counts().sort_index())
        
        # Remove them
        df_clean = df[~mask_zero_scores].copy()
        
        # Save
        df_clean.to_csv(file_path, index=False)
        logger.info(f"✅ Removed {len(bad_games)} bad games. Saved cleaned data to {file_path}")
        logger.info(f"New row count: {len(df_clean)} (was {initial_count})")
    else:
        logger.info("✅ No 0-0 games found in 2025. Data appears clean.")

if __name__ == "__main__":
    clean_data()
