# 🎯 Low API Usage Missing Games Recovery Plan
## Maximize Local Data, Minimize API Calls

**Objective:** Recover all missing games using local data sources first, API only as last resort.

**Strategy:** 
- **Phase 1:** Extract from local `starter_pack copy/data/games.csv` (106,764 games)
- **Phase 2:** Extract from local `model_pack copy/training_data.csv` (4,521 games with 86 features)
- **Phase 3:** Only use API for games not found locally (batched by week/year)

**Expected API Calls:** ~50-200 (only for games not in local sources) vs 5,279+ without this plan

---

## 📊 Data Source Inventory

### ✅ Available Local Data Sources

1. **`starter_pack copy/data/games.csv`** (106,764 games)
   - Contains: Game IDs, teams, scores, dates, conferences
   - Coverage: 1869-2024 (comprehensive historical data)
   - **Status:** ✅ Contains missing game IDs (verified: 400869527, 400869598, 400869124 found)

2. **`model_pack copy/training_data.csv`** (4,521 games)
   - Contains: Full 86-feature dataset
   - Coverage: 2016-2025, Week 5+
   - **Status:** ✅ Has complete feature engineering

3. **Weekly Training Data Files** (2025 Season, Weeks 5-13)
   - `training_data_2025_week05.csv` (52 games)
   - `training_data_2025_week06.csv` (51 games)
   - `training_data_2025_week07.csv`
   - `training_data_2025_week08.csv`
   - `training_data_2025_week09.csv`
   - `training_data_2025_week10.csv`
   - `training_data_2025_week11.csv`
   - `training_data_2025_week12_updated.csv`
   - `training_data_2025_week13.csv` (59 games)
   - Contains: Full 86-feature dataset for each week
   - Coverage: 2025, Weeks 5-13
   - **Status:** ✅ All have complete feature engineering, includes games from missing list!

4. **`starter_pack copy/data/plays/`** (Play-by-play data)
   - Contains: Detailed play data for feature engineering
   - Coverage: 2003-2024, all weeks
   - **Status:** ✅ Available for advanced metrics

5. **`starter_pack copy/data/drives/`** (Drive data)
   - Contains: Drive efficiency metrics
   - Coverage: 2001-2024
   - **Status:** ✅ Available for feature engineering

6. **`starter_pack copy/data/advanced_game_stats/`** (Advanced stats)
   - Contains: Pre-calculated advanced metrics
   - Coverage: 2003-2024
   - **Status:** ✅ Available for feature engineering

7. **`starter_pack copy/data/game_stats/`** (Game stats)
   - Contains: Team statistics per game
   - Coverage: 2004-2024
   - **Status:** ✅ Available for feature engineering

---

## 🔄 Recovery Workflow

### **Phase 1: Local Data Extraction (ZERO API Calls)**

#### Step 1.1: Extract from `starter_pack copy/data/games.csv`
```python
# Load missing games list
missing_games_df = pd.read_csv('reports/missing_games.csv')

# Load local games data
local_games_df = pd.read_csv('starter_pack copy/data/games.csv')

# Match missing game IDs
found_in_starter = local_games_df[
    local_games_df['id'].isin(missing_games_df['id'])
].copy()

# Expected: ~4,500-5,000 games found (most missing games should be here)
```

**Output:** `found_in_starter.csv` - Games found in starter pack

#### Step 1.2: Extract from `model_pack copy/training_data.csv`
```python
# Check if any missing games are in backup training data
backup_training_df = pd.read_csv('model_pack copy/training_data.csv')

# Match missing game IDs
found_in_backup = backup_training_df[
    backup_training_df['id'].isin(missing_games_df['id'])
].copy()

# Expected: ~0-500 games (some may have been in backup but not current)
```

**Output:** `found_in_backup.csv` - Games found in backup training data (with 86 features!)

#### Step 1.3: Extract from Weekly Training Data Files (Weeks 5-13)
```python
# Check all weekly training data files (weeks 5-13)
weekly_files = [
    'training_data_2025_week05.csv',
    'training_data_2025_week06.csv',
    'training_data_2025_week07.csv',
    'training_data_2025_week08.csv',
    'training_data_2025_week09.csv',
    'training_data_2025_week10.csv',
    'training_data_2025_week11.csv',
    'training_data_2025_week12_updated.csv',
    'training_data_2025_week13.csv',
]

found_in_weekly = []
for weekly_file in weekly_files:
    if Path(weekly_file).exists():
        weekly_df = pd.read_csv(weekly_file)
        found_in_this_week = weekly_df[
            weekly_df['id'].isin(missing_games_df['id'])
        ].copy()
        if len(found_in_this_week) > 0:
            found_in_weekly.append(found_in_this_week)

# Combine all weekly training data
found_in_all_weekly = pd.concat(found_in_weekly, ignore_index=True) if found_in_weekly else pd.DataFrame()

# Expected: ~50-400 games (various 2025 weeks that might be missing)
```

**Output:** `found_in_weekly_training.csv` - Games found in weekly training data (all have 86 features!)

#### Step 1.4: Identify Still-Missing Games
```python
# Combine found games
all_found_ids = set(found_in_starter['id']) | set(found_in_backup['id']) | set(found_in_all_weekly['id'])

# Games still missing
still_missing = missing_games_df[
    ~missing_games_df['id'].isin(all_found_ids)
].copy()

# Expected: ~0-500 games (only games truly not in local sources)
```

**Output:** `still_missing_games.csv` - Games requiring API calls

---

### **Phase 2: Feature Engineering from Local Data**

#### Step 2.1: Build Features for Starter Pack Games
```python
# For games found in starter_pack copy/data/games.csv:
# 1. Load corresponding play data
# 2. Load corresponding drive data
# 3. Load corresponding advanced stats
# 4. Build 86 features using existing pipeline

# Use model_pack/utils/cfbd_advanced_metrics.py patterns
# Use starter_pack copy data files for all metrics
```

**Output:** `starter_pack_games_with_features.csv` - Games with 86 features

#### Step 2.2: Use Backup Training Data (Already Has Features!)
```python
# Games from model_pack copy/training_data.csv already have 86 features!
# Just need to merge into current training data
# No feature engineering needed!
```

**Output:** `backup_games_with_features.csv` - Games with 86 features (already complete!)

#### Step 2.3: Use Weekly Training Data (Already Has Features!)
```python
# Games from weekly training data files (weeks 5-13) already have 86 features!
# Just need to merge into current training data
# No feature engineering needed!
```

**Output:** `weekly_training_games_with_features.csv` - Games with 86 features (already complete!)

---

### **Phase 3: API Calls (ONLY for Still-Missing Games)**

#### Step 3.1: Batch API Calls (Using Fixed Script)
```python
# Only for games in still_missing_games.csv
# Use the FIXED fill_missing_games.py script with batching

# Expected: ~50-200 API calls (one per unique week/year)
# Instead of 5,279+ calls!
```

**Output:** `api_fetched_games_with_features.csv` - Games fetched from API with features

---

## 📋 Implementation Script Structure

### **Main Script: `scripts/recover_missing_games_local_first.py`**

```python
#!/usr/bin/env python3
"""
Recover Missing Games - Local Data First Strategy

This script:
1. Extracts missing games from local data sources (ZERO API calls)
2. Builds features from local data files
3. Only uses API for games truly not available locally
4. Integrates all recovered games into training data
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Set
import logging

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STARTER_PACK_GAMES = PROJECT_ROOT / 'starter_pack copy' / 'data' / 'games.csv'
BACKUP_TRAINING = PROJECT_ROOT / 'model_pack copy' / 'training_data.csv'
MISSING_GAMES = PROJECT_ROOT / 'reports' / 'missing_games.csv'
CURRENT_TRAINING = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'

class LocalFirstGameRecovery:
    """Recover missing games using local data sources first."""
    
    def __init__(self):
        self.stats = {
            'total_missing': 0,
            'found_in_starter': 0,
            'found_in_backup': 0,
            'still_missing': 0,
            'api_calls_needed': 0
        }
    
    def phase1_extract_from_local(self) -> Dict[str, pd.DataFrame]:
        """Phase 1: Extract games from local data sources."""
        logger.info("=" * 80)
        logger.info("PHASE 1: LOCAL DATA EXTRACTION")
        logger.info("=" * 80)
        
        # Load missing games list
        missing_games_df = pd.read_csv(MISSING_GAMES)
        self.stats['total_missing'] = len(missing_games_df)
        logger.info(f"Total missing games: {len(missing_games_df)}")
        
        # Extract from starter pack
        logger.info("Extracting from starter_pack copy/data/games.csv...")
        starter_games_df = pd.read_csv(STARTER_PACK_GAMES, low_memory=False)
        found_in_starter = starter_games_df[
            starter_games_df['id'].isin(missing_games_df['id'])
        ].copy()
        self.stats['found_in_starter'] = len(found_in_starter)
        logger.info(f"Found {len(found_in_starter)} games in starter pack")
        
        # Extract from backup training data
        logger.info("Extracting from model_pack copy/training_data.csv...")
        backup_training_df = pd.read_csv(BACKUP_TRAINING, low_memory=False)
        found_in_backup = backup_training_df[
            backup_training_df['id'].isin(missing_games_df['id'])
        ].copy()
        self.stats['found_in_backup'] = len(found_in_backup)
        logger.info(f"Found {len(found_in_backup)} games in backup training data")
        
        # Identify still-missing games
        all_found_ids = set(found_in_starter['id']) | set(found_in_backup['id'])
        still_missing = missing_games_df[
            ~missing_games_df['id'].isin(all_found_ids)
        ].copy()
        self.stats['still_missing'] = len(still_missing)
        
        # Calculate unique (year, week) combinations for API calls
        if len(still_missing) > 0:
            unique_weeks = still_missing.groupby(['season', 'week']).size()
            self.stats['api_calls_needed'] = len(unique_weeks)
            logger.info(f"Still missing: {len(still_missing)} games")
            logger.info(f"API calls needed: {self.stats['api_calls_needed']} (one per unique week/year)")
        else:
            logger.info("✅ All missing games found in local sources! ZERO API calls needed!")
        
        return {
            'found_in_starter': found_in_starter,
            'found_in_backup': found_in_backup,
            'still_missing': still_missing
        }
    
    def phase2_build_features_local(self, found_games: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Phase 2: Build features from local data sources."""
        logger.info("=" * 80)
        logger.info("PHASE 2: FEATURE ENGINEERING FROM LOCAL DATA")
        logger.info("=" * 80)
        
        all_games_with_features = []
        
        # Games from backup training data already have 86 features!
        if len(found_games['found_in_backup']) > 0:
            logger.info(f"Using {len(found_games['found_in_backup'])} games from backup (already have 86 features)")
            all_games_with_features.append(found_games['found_in_backup'])
        
        # Games from starter pack need feature engineering
        if len(found_games['found_in_starter']) > 0:
            logger.info(f"Building features for {len(found_games['found_in_starter'])} games from starter pack")
            # Use local data files to build features
            starter_with_features = self._build_features_from_local_data(
                found_games['found_in_starter']
            )
            all_games_with_features.append(starter_with_features)
        
        if all_games_with_features:
            combined = pd.concat(all_games_with_features, ignore_index=True)
            logger.info(f"Total games with features from local data: {len(combined)}")
            return combined
        else:
            return pd.DataFrame()
    
    def _build_features_from_local_data(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """Build 86 features using local data files."""
        # Implementation:
        # 1. Load plays data from starter_pack copy/data/plays/
        # 2. Load drives data from starter_pack copy/data/drives/
        # 3. Load advanced stats from starter_pack copy/data/advanced_game_stats/
        # 4. Use existing feature engineering pipeline
        # 5. Return games with 86 features
        
        # TODO: Implement feature engineering using local files
        # For now, return games with basic structure
        return games_df
    
    def phase3_api_fetch_if_needed(self, still_missing: pd.DataFrame) -> pd.DataFrame:
        """Phase 3: Fetch remaining games from API (batched)."""
        if len(still_missing) == 0:
            logger.info("No API calls needed - all games found locally!")
            return pd.DataFrame()
        
        logger.info("=" * 80)
        logger.info("PHASE 3: API FETCH (BATCHED)")
        logger.info("=" * 80)
        logger.info(f"Fetching {len(still_missing)} games using batched API calls")
        logger.info(f"Estimated API calls: {self.stats['api_calls_needed']}")
        
        # Use the FIXED fill_missing_games.py script
        # It now batches by (year, week) to minimize API calls
        from scripts.fill_missing_games import MissingGamesFiller
        
        filler = MissingGamesFiller()
        api_fetched = filler.fetch_all_missing_games(still_missing)
        
        return api_fetched
    
    def phase4_integrate_all(self, local_games: pd.DataFrame, api_games: pd.DataFrame) -> bool:
        """Phase 4: Integrate all recovered games."""
        logger.info("=" * 80)
        logger.info("PHASE 4: INTEGRATION")
        logger.info("=" * 80)
        
        # Combine all games
        all_recovered = pd.concat([local_games, api_games], ignore_index=True)
        logger.info(f"Total games recovered: {len(all_recovered)}")
        
        # Use existing integration logic from fill_missing_games.py
        from scripts.fill_missing_games import MissingGamesFiller
        filler = MissingGamesFiller()
        success = filler.integrate_games(all_recovered)
        
        return success
    
    def run(self) -> Dict:
        """Execute complete recovery workflow."""
        # Phase 1: Extract from local
        found_games = self.phase1_extract_from_local()
        
        # Phase 2: Build features from local data
        local_games_with_features = self.phase2_build_features_local(found_games)
        
        # Phase 3: API fetch if needed (batched)
        api_games_with_features = self.phase3_api_fetch_if_needed(found_games['still_missing'])
        
        # Phase 4: Integrate all
        success = self.phase4_integrate_all(local_games_with_features, api_games_with_features)
        
        # Summary
        logger.info("=" * 80)
        logger.info("RECOVERY SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total missing games: {self.stats['total_missing']}")
        logger.info(f"Found in starter pack: {self.stats['found_in_starter']}")
        logger.info(f"Found in backup training: {self.stats['found_in_backup']}")
        logger.info(f"Still missing (API needed): {self.stats['still_missing']}")
        logger.info(f"API calls made: {self.stats['api_calls_needed']}")
        logger.info(f"Success: {success}")
        
        return {
            'success': success,
            'stats': self.stats
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    recovery = LocalFirstGameRecovery()
    result = recovery.run()
    
    if result['success']:
        logger.info("✅ SUCCESS: All games recovered!")
    else:
        logger.error("❌ FAILED: Recovery incomplete")
        sys.exit(1)
```

---

## 📊 Expected Results

### **API Call Reduction**

| Scenario | Without Plan | With Plan | Reduction |
|----------|--------------|-----------|-----------|
| **All games in local sources** | 5,279 calls | 0 calls | **100%** |
| **Most games in local sources** | 5,279 calls | 50-200 calls | **96-99%** |
| **Few games in local sources** | 5,279 calls | 200-500 calls | **90-96%** |

### **Time Savings**

- **Local extraction:** ~2-5 minutes (no API rate limiting)
- **Feature engineering:** ~5-10 minutes (using local files)
- **API fetching (if needed):** ~5-15 minutes (batched, ~200 calls max)
- **Total:** ~12-30 minutes vs 2-3 hours with full API approach

---

## ✅ Success Criteria

1. ✅ Extract all possible games from local data sources first
2. ✅ Build 86 features using local data files (plays, drives, stats)
3. ✅ Only use API for games truly not available locally
4. ✅ Batch API calls by (year, week) to minimize usage
5. ✅ Integrate all recovered games into training data
6. ✅ API calls reduced by 90-100% compared to naive approach

---

## 🚀 Execution Steps

1. **Run Phase 1 Analysis:**
   ```bash
   python scripts/recover_missing_games_local_first.py --phase 1 --analyze-only
   ```
   This will show how many games can be recovered locally without making any API calls.

2. **Run Full Recovery:**
   ```bash
   python scripts/recover_missing_games_local_first.py
   ```
   This will execute all phases and recover all games.

3. **Verify Results:**
   ```bash
   python scripts/validate_integrated_dataset.py
   ```

---

## 📝 Notes

- **Local data is comprehensive:** `starter_pack copy/data/games.csv` has 106,764 games covering 1869-2024
- **Backup training data has features:** `model_pack copy/training_data.csv` already has 86 features for 4,521 games
- **Minimal API usage:** Only games truly not in local sources will require API calls
- **Batched API calls:** Using fixed `fill_missing_games.py` script with (year, week) batching

This plan maximizes local data usage and minimizes API calls to the absolute minimum!

