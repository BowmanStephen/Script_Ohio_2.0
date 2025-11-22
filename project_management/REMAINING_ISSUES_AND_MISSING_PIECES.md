# Comprehensive Outstanding Issues - Script Ohio 2.0

**Generated:** 2025-11-17  
**Status:** Active Issues Requiring Resolution  
**Last Updated:** 2025-11-17

## Executive Summary

**Total Issues Identified:** 42+ across 8 categories  
**Critical Issues:** 9 (blocking functionality)  
**High Priority:** 7 (affects core features)  
**Medium Priority:** 16 (enhancements needed)  
**Low Priority:** 10+ (nice-to-have improvements)

This document provides a comprehensive catalog of all outstanding issues in the Script Ohio 2.0 project, with detailed fix implementations, code examples, and step-by-step resolution instructions.

---

## Table of Contents

1. [Category 1: GraphQL Removal Issues (Critical)](#category-1-graphql-removal-issues-critical)
2. [Category 2: 2025 Season Data Issues (High Priority)](#category-2-2025-season-data-issues-high-priority)
3. [Category 3: Model Training Issues (High Priority)](#category-3-model-training-issues-high-priority)
4. [Category 4: Code Quality Issues (Medium Priority)](#category-4-code-quality-issues-medium-priority)
5. [Category 5: Data Validation Issues (Medium Priority)](#category-5-data-validation-issues-medium-priority)
6. [Category 6: Integration Issues (Medium Priority)](#category-6-integration-issues-medium-priority)
7. [Category 7: Documentation Issues (Low Priority)](#category-7-documentation-issues-low-priority)
8. [Category 8: Known Limitations (Low Priority)](#category-8-known-limitations-low-priority)
9. [Priority Action Plan](#priority-action-plan)
10. [Summary Statistics](#summary-statistics)

---

## Category 1: GraphQL Removal Issues (Critical)

**Priority:** Critical  
**Impact:** Agents will fail when GraphQL capabilities are called  
**Estimated Fix Time:** 8-10 hours

### 1.1 Agent Files with GraphQL Dependencies

#### A. `agents/insight_generator_agent.py`

**Issues:**
- **Line 145-151:** Capability `graphql_trend_scan` defined
- **Line 202-203:** Action handler for `graphql_trend_scan`
- **Lines 489-549:** `_execute_graphql_trend_scan()` method
- **Lines 665-675:** `_get_graphql_client()` method
- **Line 34:** Import of `CFBDGraphQLClient` (may fail)

**Current Broken Code:**

```python
# Line 144-151: Capability definition
AgentCapability(
    name="graphql_trend_scan",
    description="Surface recruiting/talent trends via the CFBD GraphQL endpoint.",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["cfbd_graphql_client"],
    data_access=["graphql.collegefootballdata.com"],
    execution_time_estimate=3.0,
)

# Line 202-203: Action handler
elif action == "graphql_trend_scan":
    return self._execute_graphql_trend_scan(parameters, user_context)

# Lines 489-549: GraphQL execution method
def _execute_graphql_trend_scan(
    self,
    parameters: Dict[str, Any],
    user_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Call the CFBD GraphQL endpoint to surface recruiting/talent trends."""
    client = self._get_graphql_client()
    if client is None:
        return {
            "success": False,
            "error": "GraphQL client unavailable. Confirm gql dependency and Patreon access.",
        }
    # ... rest of GraphQL implementation
```

**Fixed Code:**

```python
# REMOVE the graphql_trend_scan capability entirely (lines 144-151)
# Keep only REST-based capabilities

# Line 202-203: Update action handler to return unavailable
elif action == "graphql_trend_scan":
    return {
        "success": False,
        "error": "GraphQL access not available. This feature requires Patreon Tier 3+ access.",
        "error_type": "feature_unavailable",
        "alternative": "Use 'cfbd_real_time_analysis' for REST-based data access"
    }

# Lines 489-549: Replace _execute_graphql_trend_scan with unavailable response
def _execute_graphql_trend_scan(
    self,
    parameters: Dict[str, Any],
    user_context: Dict[str, Any],
) -> Dict[str, Any]:
    """GraphQL access not available - returns unavailable status."""
    logger.warning("GraphQL trend scan requested but GraphQL access is not available")
    return {
        "success": False,
        "error": "GraphQL access not available. This feature requires Patreon Tier 3+ access.",
        "error_type": "feature_unavailable",
        "alternative": "Use 'cfbd_real_time_analysis' for REST-based data access",
        "available_alternatives": [
            "cfbd_real_time_analysis - REST-based CFBD data access",
            "Use REST API endpoints for team talent and recruiting data"
        ]
    }

# Lines 665-675: Update _get_graphql_client to always return None with warning
def _get_graphql_client(self) -> Optional[Any]:
    """GraphQL client not available - returns None with warning."""
    logger.warning("GraphQL client requested but GraphQL access is not available")
    return None
```

**Step-by-Step Fix Instructions:**

1. Open `agents/insight_generator_agent.py`
2. **Remove lines 144-151:** Delete the `graphql_trend_scan` capability definition
3. **Update lines 202-203:** Replace the action handler to return unavailable status
4. **Replace lines 489-549:** Replace `_execute_graphql_trend_scan` method with unavailable response
5. **Update lines 665-675:** Modify `_get_graphql_client` to return None with warning
6. **Update line 34:** Keep the import but it will be None (already handled with try/except)
7. Test: Verify agent doesn't crash when GraphQL capability is requested

**Verification:**
```python
# Test that GraphQL capability is gracefully handled
from agents.insight_generator_agent import InsightGeneratorAgent

agent = InsightGeneratorAgent("test_001")
result = agent._execute_action(
    "graphql_trend_scan",
    {"season": 2025},
    {"detected_role": "analyst"}
)
assert result["success"] == False
assert "unavailable" in result["error"].lower()
```

---

#### B. `agents/workflow_automator_agent.py`

**Issues:**
- **Lines 36-40:** Import of `CFBDGraphQLClient` with fallback
- **Line 136:** `self._graphql_client = None` initialization
- **Line 201:** Capability mentions `cfbd_graphql_client` in tools_required
- **Line 571:** Calls `_fetch_graphql_summary()` in `cfbd_pipeline`
- **Lines 702-716:** `_fetch_graphql_summary()` method
- **Lines 754-764:** `_get_graphql_client()` method
- **Line 636:** Parameter `graphql_limit` in orchestrator

**Current Broken Code:**

```python
# Lines 36-40: Import
try:
    from data_sources import (
        CFBDClientConfig as DSClientConfig,
        CFBDGraphQLClient as DSGraphQLClient,
        CFBDRESTDataSource as DSRESTDataSource,
    )
except ImportError:
    DSClientConfig = None  # type: ignore
    DSGraphQLClient = None  # type: ignore
    DSRESTDataSource = None  # type: ignore

# Line 136: Initialization
self._graphql_client = None

# Line 571: Usage in cfbd_pipeline
graphql_summary = self._fetch_graphql_summary(season, parameters.get("graphql_limit", 10))

# Lines 702-716: GraphQL summary method
def _fetch_graphql_summary(self, season: int, limit: int) -> Dict[str, Any]:
    client = self._get_graphql_client()
    if client is None:
        return {"available": False, "reason": "graphql_client_unavailable"}
    try:
        recruits = client.fetch_recruits(year=season, limit=limit).get("recruit", [])
        talent = client.fetch_team_talent(year=season).get("teamTalent", [])
        return {
            "available": True,
            "recruit_sample": recruits[:5],
            "talent_sample": talent[:5],
        }
    except Exception as exc:
        logger.warning("GraphQL summary failed: %s", exc)
        return {"available": False, "reason": str(exc)}
```

**Fixed Code:**

```python
# Lines 36-40: Keep import but document it's unused
try:
    from data_sources import (
        CFBDClientConfig as DSClientConfig,
        # CFBDGraphQLClient removed - GraphQL not available
        CFBDRESTDataSource as DSRESTDataSource,
    )
except ImportError:
    DSClientConfig = None  # type: ignore
    DSRESTDataSource = None  # type: ignore

# Line 136: Remove or keep as None (will never be used)
# self._graphql_client = None  # GraphQL not available

# Line 571: Remove GraphQL call from cfbd_pipeline
# REMOVE: graphql_summary = self._fetch_graphql_summary(season, parameters.get("graphql_limit", 10))
# Replace with:
graphql_summary = {"available": False, "reason": "graphql_not_available"}

# Update pipeline result to remove graphql_summary or mark as unavailable
# In the return statement, either remove graphql_summary or set it to unavailable

# Lines 702-716: Update _fetch_graphql_summary to always return unavailable
def _fetch_graphql_summary(self, season: int, limit: int) -> Dict[str, Any]:
    """GraphQL summary not available - returns unavailable status."""
    logger.warning("GraphQL summary requested but GraphQL access is not available")
    return {
        "available": False,
        "reason": "graphql_not_available",
        "message": "GraphQL access requires Patreon Tier 3+ access",
        "alternative": "Use REST API endpoints for team data"
    }

# Lines 754-764: Update _get_graphql_client to always return None
def _get_graphql_client(self) -> Optional[Any]:
    """GraphQL client not available - returns None."""
    logger.warning("GraphQL client requested but GraphQL access is not available")
    return None

# Line 636: Remove graphql_limit parameter or make it optional with default None
# In analytics_orchestrator.py, remove graphql_limit from parameters
```

**Step-by-Step Fix Instructions:**

1. Open `agents/workflow_automator_agent.py`
2. **Update lines 36-40:** Remove `CFBDGraphQLClient` from imports (or keep but document unused)
3. **Line 136:** Keep `self._graphql_client = None` or remove (optional)
4. **Line 571:** Replace GraphQL call with unavailable status
5. **Lines 702-716:** Update `_fetch_graphql_summary` to return unavailable
6. **Lines 754-764:** Update `_get_graphql_client` to return None
7. **Update capability definition (line 201):** Remove `cfbd_graphql_client` from tools_required
8. **Update analytics_orchestrator.py line 636:** Remove `graphql_limit` parameter

**Verification:**
```python
# Test that workflow doesn't fail without GraphQL
from agents.workflow_automator_agent import WorkflowAutomatorAgent

agent = WorkflowAutomatorAgent("test_001")
result = agent._fetch_graphql_summary(2025, 10)
assert result["available"] == False
assert "not_available" in result["reason"]
```

---

#### C. `agents/cfbd_integration_agent.py`

**Issues:**
- **Line 41:** Capability mentions "CFBD GraphQL" in data_access
- **Line 48:** Capability requires "graphql_subscription" tool
- **Line 49:** Capability mentions "CFBD GraphQL" in data_access

**Current Broken Code:**

```python
# Lines 40-51: Capability definitions
AgentCapability(
    name="team_snapshot",
    description="Return normalized CFBD snapshot for a single team",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["cfbd_client"],
    data_access=["CFBD REST", "CFBD GraphQL"],  # Line 41
    execution_time_estimate=1.0,
),
AgentCapability(
    name="live_scoreboard",
    description="Return the latest live scoreboard events",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["graphql_subscription"],  # Line 48
    data_access=["CFBD GraphQL"],  # Line 49
    execution_time_estimate=0.2,
),
```

**Fixed Code:**

```python
# Lines 40-51: Updated capability definitions
AgentCapability(
    name="team_snapshot",
    description="Return normalized CFBD snapshot for a single team",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["cfbd_client"],
    data_access=["CFBD REST"],  # Removed GraphQL reference
    execution_time_estimate=1.0,
),
AgentCapability(
    name="live_scoreboard",
    description="Return the latest live scoreboard events (REST-based)",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["cfbd_rest_client"],  # Changed from graphql_subscription
    data_access=["CFBD REST"],  # Changed from GraphQL
    execution_time_estimate=0.2,
),
```

**Step-by-Step Fix Instructions:**

1. Open `agents/cfbd_integration_agent.py`
2. **Line 41:** Change `data_access=["CFBD REST", "CFBD GraphQL"]` to `data_access=["CFBD REST"]`
3. **Line 48:** Change `tools_required=["graphql_subscription"]` to `tools_required=["cfbd_rest_client"]`
4. **Line 49:** Change `data_access=["CFBD GraphQL"]` to `data_access=["CFBD REST"]`
5. **Update description:** Note that live_scoreboard is REST-based

---

#### D. `agents/analytics_orchestrator.py`

**Issues:**
- **Line 111:** GraphQL subscription manager startup attempt
- **Line 612:** Keyword detection includes 'graphql'
- **Line 636:** `graphql_limit` parameter passed to workflow

**Current Broken Code:**

```python
# Lines 105-112: GraphQL subscription manager
self.subscription_manager = None
if self.cfbd_provider and CFBDSubscriptionManager:
    try:
        self.subscription_manager = CFBDSubscriptionManager(telemetry_hook=self._record_cfbd_event)
        self.subscription_manager.start_scoreboard_feed()
    except RuntimeError as exc:
        logger.warning("Could not start GraphQL subscription manager: %s", exc)

# Line 612: Keyword detection
cfbd_keywords = ['cfbd', 'ingest', 'graphql', 'next api', 'rest api', 'live data']

# Line 636: GraphQL parameter
'graphql_limit': request.parameters.get('graphql_limit', 10),
```

**Fixed Code:**

```python
# Lines 105-112: Remove GraphQL subscription manager
# REMOVE entire block or comment out:
# self.subscription_manager = None
# GraphQL subscription manager not available - removed

# Line 612: Remove 'graphql' from keywords
cfbd_keywords = ['cfbd', 'ingest', 'next api', 'rest api', 'live data']  # Removed 'graphql'

# Line 636: Remove graphql_limit parameter
# REMOVE: 'graphql_limit': request.parameters.get('graphql_limit', 10),
# Or replace with:
# Note: graphql_limit removed - GraphQL not available
```

**Step-by-Step Fix Instructions:**

1. Open `agents/analytics_orchestrator.py`
2. **Lines 105-112:** Comment out or remove GraphQL subscription manager initialization
3. **Line 612:** Remove 'graphql' from `cfbd_keywords` list
4. **Line 636:** Remove `graphql_limit` parameter from workflow parameters

---

#### E. `agents/core/enhanced_cfbd_integration.py`

**Issues:**
- **Line 226:** Mentions GraphQL support in docstring
- **Lines 566-618:** `graphql_query()` method exists

**Current Broken Code:**

```python
# Line 226: Docstring
"""
Enhanced CFBD API client with optimized performance and production-grade features.
Key Enhancements:
- GraphQL support for efficient data fetching  # Remove this line
"""

# Lines 566-618: GraphQL query method
def graphql_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute GraphQL query for efficient data fetching."""
    if not self.use_graphql:
        logger.warning("⚠️ GraphQL not enabled")
        return {}
    # ... rest of implementation
```

**Fixed Code:**

```python
# Line 226: Updated docstring
"""
Enhanced CFBD API client with optimized performance and production-grade features.
Key Enhancements:
- REST API support with rate limiting
- Production-grade error handling
Note: GraphQL support removed - requires Patreon Tier 3+ access
"""

# Lines 566-618: Update graphql_query to always return empty
def graphql_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
    """GraphQL queries not available - returns empty dict."""
    logger.warning("⚠️ GraphQL queries not available - requires Patreon Tier 3+ access")
    return {}
```

**Step-by-Step Fix Instructions:**

1. Open `agents/core/enhanced_cfbd_integration.py`
2. **Line 226:** Update docstring to remove GraphQL mention
3. **Lines 566-618:** Update `graphql_query` method to return empty dict with warning

---

### 1.2 Notebook Files

#### A. `starter_pack/notebooks/CFBD_Ingestion.ipynb`

**Issues:**
- **Cell 1:** Imports `CFBDGraphQLClient`
- **Cell 2:** Creates `graphql_client` instance
- **Cell 3:** Fetches GraphQL games data
- **Cell 4:** Processes GraphQL data
- **Cell 5:** Saves GraphQL features
- **Cell 6:** Mentions GraphQL in notes

**Fixed Code for Notebook:**

```python
# Cell 1: Make GraphQL import optional
from data_sources import (
    CFBDClientConfig,
    # CFBDGraphQLClient,  # Optional - requires Patreon Tier 3+
    CFBDRESTDataSource,
)

# Cell 2: Make GraphQL client optional
try:
    from data_sources import CFBDGraphQLClient
    graphql_available = True
except ImportError:
    graphql_available = False
    print("⚠️ GraphQL client not available - requires Patreon Tier 3+ access")

if graphql_available:
    graphql_client = CFBDGraphQLClient(api_key=api_key)
else:
    graphql_client = None
    print("Using REST API only (GraphQL not available)")

# Cell 3: Wrap GraphQL calls in try/except
if graphql_client is not None:
    try:
        graphql_payload = graphql_client.fetch_games(season=season, week=week, team=team_filter)
        graphql_games = graphql_payload.get("game", [])
    except Exception as e:
        print(f"⚠️ GraphQL fetch failed: {e}")
        graphql_games = []
else:
    graphql_games = []
    print("⚠️ GraphQL not available - skipping GraphQL data fetch")

# Cell 4: Handle missing GraphQL data
if graphql_games:
    graphql_df = engineer.prepare_games_frame(graphql_games, source="graphql")
    graphql_features = engineer.build_feature_frame(graphql_df)
else:
    print("⚠️ No GraphQL data available - skipping GraphQL feature generation")

# Cell 5: Only save if GraphQL data exists
if graphql_games and 'graphql_features' in locals():
    graphql_features.to_csv(output_dir / "graphql_features.csv", index=False)
else:
    print("⚠️ Skipping GraphQL features save - no data available")

# Cell 6: Update notes
"""
## Rate-Limit & Troubleshooting Notes

- The REST clients enforce a 0.17s delay
- HTTP 429 responses indicate exceeding CFBD limits
- GraphQL access requires Patreon Tier 3+ and is optional
- All notebook outputs land in `outputs/notebooks/` and are git-ignored
"""
```

**Step-by-Step Fix Instructions:**

1. Open `starter_pack/notebooks/CFBD_Ingestion.ipynb`
2. **Cell 1:** Make GraphQL import optional with try/except
3. **Cell 2:** Add check for GraphQL availability
4. **Cell 3:** Wrap GraphQL calls in try/except
5. **Cell 4:** Handle missing GraphQL data gracefully
6. **Cell 5:** Only save if GraphQL data exists
7. **Cell 6:** Update notes to mention GraphQL is optional

---

### 1.3 Documentation Files

**Files to Update:**
- `AGENTS.md` - Lines 35, 60: Remove GraphQL capability mentions
- `starter_pack/README.md` - Lines 17, 130, 140: Remove GraphQL references
- `docs/CFBD_RUNBOOK.md` - Multiple GraphQL references
- `documentation/AGENTS.md` - GraphQL mentions

**Fix Instructions:**

1. Search each file for "graphql" or "GraphQL" (case-insensitive)
2. Remove or update references to indicate GraphQL requires Tier 3+ access
3. Update capability tables to remove GraphQL capabilities
4. Add notes that GraphQL is optional and requires Patreon Tier 3+

---

## Category 2: 2025 Season Data Issues (High Priority)

**Priority:** High  
**Impact:** Models may not have complete training data  
**Estimated Fix Time:** 3-4 hours

### 2.1 Training Data Integration

#### A. Weeks 1-12 Data Completeness

**Issue:** Need to verify all weeks 1-12 are properly integrated into training data.

**Verification Script:**

```python
import pandas as pd
from pathlib import Path

def verify_weeks_1_12_integration():
    """Verify all weeks 1-12 are present in training data."""
    training_file = Path("model_pack/updated_training_data.csv")
    
    if not training_file.exists():
        print("❌ Training data file not found")
        return False
    
    df = pd.read_csv(training_file)
    df_2025 = df[df['season'] == 2025]
    
    # Check week coverage
    weeks_present = sorted(df_2025['week'].dropna().unique().tolist())
    expected_weeks = list(range(1, 13))  # Weeks 1-12
    
    missing_weeks = set(expected_weeks) - set(weeks_present)
    
    if missing_weeks:
        print(f"❌ Missing weeks: {sorted(missing_weeks)}")
        return False
    
    print(f"✅ All weeks 1-12 present: {weeks_present}")
    
    # Check game counts
    for week in expected_weeks:
        week_games = len(df_2025[df_2025['week'] == week])
        print(f"  Week {week}: {week_games} games")
    
    return True

if __name__ == "__main__":
    verify_weeks_1_12_integration()
```

**Step-by-Step Fix Instructions:**

1. Run verification script to check week coverage
2. If weeks are missing, run integration script:
   ```bash
   python scripts/integrate_weeks_1_12_and_retrain.py
   ```
3. Verify output shows all weeks integrated
4. Re-run verification script to confirm

---

#### B. Week 12 Data Integration

**Issue:** Week 12 data may not be fully integrated into training set.

**Integration Steps:**

```bash
# Step 1: Verify week 12 data files exist
ls -la data/week12/enhanced/week12_features_86.csv
ls -la data/week12/enhanced/week12_enhanced_games.csv

# Step 2: Run integration script
python scripts/integrate_weeks_1_12_and_retrain.py

# Step 3: Verify integration
python -c "
import pandas as pd
df = pd.read_csv('model_pack/updated_training_data.csv')
week12 = df[(df['season'] == 2025) & (df['week'] == 12)]
print(f'Week 12 games in training data: {len(week12)}')
"
```

**Step-by-Step Fix Instructions:**

1. Verify week 12 data files exist in `data/week12/enhanced/`
2. Run `scripts/integrate_weeks_1_12_and_retrain.py`
3. Check logs for any errors
4. Verify week 12 games are in `updated_training_data.csv`

---

#### C. Data Schema Consistency

**Issue:** Verify 86-feature schema matches across all weeks.

**Verification Script:**

```python
import pandas as pd
from pathlib import Path

def verify_schema_consistency():
    """Verify all weeks have consistent 86-feature schema."""
    training_file = Path("model_pack/updated_training_data.csv")
    df = pd.read_csv(training_file)
    
    # Expected 86 columns (excluding id, game_key, etc.)
    expected_features = 86
    
    # Check column count
    feature_columns = [col for col in df.columns 
                      if col not in ['id', 'game_key', 'conference_game', 
                                    'start_date', 'season_type']]
    
    if len(feature_columns) != expected_features:
        print(f"❌ Expected {expected_features} features, got {len(feature_columns)}")
        return False
    
    # Check for missing values in critical features
    critical_features = ['home_elo', 'away_elo', 'home_talent', 'away_talent',
                        'home_points', 'away_points', 'margin']
    
    for feature in critical_features:
        if feature not in df.columns:
            print(f"❌ Missing critical feature: {feature}")
            return False
        
        missing_count = df[feature].isna().sum()
        if missing_count > 0:
            print(f"⚠️ {feature} has {missing_count} missing values")
    
    print("✅ Schema consistency verified")
    return True

if __name__ == "__main__":
    verify_schema_consistency()
```

**Step-by-Step Fix Instructions:**

1. Run schema verification script
2. If inconsistencies found, check data migration scripts
3. Re-run data migration if needed
4. Re-verify schema consistency

---

### 2.2 Data Quality Issues

#### A. Missing Columns Check

**Verification Script:**

```python
import pandas as pd

def check_missing_columns():
    """Check for missing required columns."""
    df = pd.read_csv("model_pack/updated_training_data.csv")
    
    required_columns = [
        'id', 'season', 'week', 'home_team', 'away_team',
        'home_points', 'away_points', 'margin', 'game_key', 'conference_game'
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        print(f"❌ Missing columns: {missing}")
        return False
    
    print("✅ All required columns present")
    return True
```

---

#### B. Duplicate Games Check

**Verification Script:**

```python
import pandas as pd

def check_duplicate_games():
    """Check for duplicate game IDs."""
    df = pd.read_csv("model_pack/updated_training_data.csv")
    
    duplicates = df[df.duplicated(subset=['id'], keep=False)]
    
    if len(duplicates) > 0:
        print(f"❌ Found {len(duplicates)} duplicate game IDs")
        print(duplicates[['id', 'season', 'week', 'home_team', 'away_team']])
        return False
    
    print("✅ No duplicate game IDs found")
    return True
```

---

#### C. Missing Values Check

**Verification Script:**

```python
import pandas as pd

def check_missing_values():
    """Check for missing values in critical features."""
    df = pd.read_csv("model_pack/updated_training_data.csv")
    
    critical_features = ['home_elo', 'away_elo', 'home_talent', 'away_talent',
                        'home_points', 'away_points', 'margin']
    
    issues = []
    for feature in critical_features:
        missing = df[feature].isna().sum()
        if missing > 0:
            issues.append(f"{feature}: {missing} missing values")
    
    if issues:
        print("⚠️ Missing values found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("✅ No missing values in critical features")
    return True
```

---

### 2.3 Week 13 Preparation

**Verification Steps:**

```bash
# Check week 13 data files exist
ls -la data/week13/enhanced/

# Verify week 13 features are generated
python -c "
import pandas as pd
df = pd.read_csv('data/week13/enhanced/week13_features_86.csv')
print(f'Week 13 games: {len(df)}')
print(f'Features: {len(df.columns)}')
"
```

---

## Category 3: Model Training Issues (High Priority)

**Priority:** High  
**Impact:** Models may not include latest 2025 data  
**Estimated Fix Time:** 3-4 hours

### 3.1 Model Retraining

#### A. Retrain All Models with Weeks 1-12

**Issue:** Models may not include latest 2025 data.

**Retraining Script:**

```bash
# Run complete integration and retraining pipeline
python scripts/integrate_weeks_1_12_and_retrain.py
```

**Step-by-Step Instructions:**

1. **Backup existing models:**
   ```bash
   cp model_pack/ridge_model_2025.joblib model_pack/ridge_model_2025.joblib.backup
   cp model_pack/xgb_home_win_model_2025.pkl model_pack/xgb_home_win_model_2025.pkl.backup
   ```

2. **Run integration script:**
   ```bash
   python scripts/integrate_weeks_1_12_and_retrain.py
   ```

3. **Verify models were retrained:**
   ```bash
   ls -la model_pack/*_2025.*
   ```

4. **Test model loading:**
   ```python
   import joblib
   import pickle
   
   # Test Ridge model
   ridge = joblib.load("model_pack/ridge_model_2025.joblib")
   print("✅ Ridge model loaded")
   
   # Test XGBoost model
   xgb = pickle.load(open("model_pack/xgb_home_win_model_2025.pkl", "rb"))
   print("✅ XGBoost model loaded")
   ```

---

#### B. FastAI Model Pickle Protocol Fix

**Issue:** FastAI model cannot be loaded due to pickle protocol mismatch.

**Location:** `agents/model_execution_engine.py` (lines 279-350)

**Current Code:**

```python
# Lines 279-350: FastAI model loading
try:
    import pickle
    with open(fastai_path, 'rb') as f:
        self.fastai_model = pickle.load(f)
except Exception as e:
    logger.warning(f"FastAI model load failed: {e}")
    # Creates mock model
```

**Fixed Code:**

```python
# Option 1: Retrain FastAI model with compatible protocol
def retrain_fastai_with_compatible_protocol():
    """Retrain FastAI model with pickle protocol 4."""
    from fastai.tabular.all import *
    import pickle
    
    # Load training data
    df = pd.read_csv("model_pack/updated_training_data.csv")
    
    # Prepare data (existing logic)
    # ... data preparation code ...
    
    # Train model
    learn = tabular_learner(dls, layers=[200, 100], metrics=accuracy)
    learn.fit_one_cycle(100, 1e-3)
    
    # Save with FastAI's native export method (recommended)
    learn.export("model_pack/fastai_home_win_model_2025.pkl")

    print("✅ FastAI model saved with native export method")

# Option 2: Update loading code to handle protocol mismatch
def load_fastai_model_safe(fastai_path):
    """Safely load FastAI model with protocol fallback."""
    import pickle
    
    try:
        # Try standard loading
        with open(fastai_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.warning(f"Standard pickle load failed: {e}")
        
        # Try with protocol 4 explicitly
        try:
            import pickle5  # May need: pip install pickle5
            with open(fastai_path, 'rb') as f:
                return pickle5.load(f)
        except ImportError:
            logger.warning("pickle5 not available, using mock model")
            return create_mock_fastai_model()
        except Exception as e2:
            logger.warning(f"pickle5 load also failed: {e2}")
            return create_mock_fastai_model()
```

**Step-by-Step Fix Instructions:**

1. **Option 1 (Recommended):** Retrain FastAI model
   ```bash
   python model_pack/fix_fastai_model.py
   ```

2. **Option 2:** Update loading code in `agents/model_execution_engine.py`
   - Add protocol 4 handling
   - Add fallback to mock model if loading fails

3. **Test loading:**
   ```python
   from agents.model_execution_engine import ModelExecutionEngine
   engine = ModelExecutionEngine("test_001")
   # Should load without errors
   ```

---

### 3.2 Model Performance Issues

#### A. XGBoost Accuracy Improvement

**Issue:** XGBoost accuracy 43.1% (expected 55-60%).

**Retraining with Improved Hyperparameters:**

```python
import xgboost as xgb
from sklearn.model_selection import GridSearchCV

def retrain_xgboost_improved():
    """Retrain XGBoost with improved hyperparameters."""
    import pandas as pd
    from sklearn.model_selection import train_test_split
    
    # Load data
    df = pd.read_csv("model_pack/updated_training_data.csv")
    
    # Prepare features and target
    feature_cols = [col for col in df.columns 
                   if col not in ['id', 'season', 'week', 'home_win', 
                                 'home_points', 'away_points', 'game_key']]
    X = df[feature_cols].fillna(0)
    y = df['home_win']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Improved hyperparameters
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1, 0.2],
        'subsample': [0.8, 0.9, 1.0]
    }
    
    xgb_model = xgb.XGBClassifier(random_state=42)
    grid_search = GridSearchCV(xgb_model, param_grid, cv=5, scoring='accuracy')
    grid_search.fit(X_train, y_train)
    
    # Save best model
    import pickle
    with open("model_pack/xgb_home_win_model_2025.pkl", 'wb') as f:
        pickle.dump(grid_search.best_estimator_, f)
    
    print(f"✅ Best accuracy: {grid_search.best_score_:.2%}")
    print(f"Best parameters: {grid_search.best_params_}")
```

---

#### B. Ridge Model MAE Improvement

**Issue:** MAE of 17.31 points (target ≤15 points).

**Retraining with Expanded Features:**

```python
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score

def retrain_ridge_improved():
    """Retrain Ridge model with expanded feature set."""
    import pandas as pd
    import numpy as np
    
    # Load data
    df = pd.read_csv("model_pack/updated_training_data.csv")
    
    # Use all available features (not just 8-13)
    feature_cols = [col for col in df.columns 
                   if col not in ['id', 'season', 'week', 'margin',
                                 'home_points', 'away_points', 'game_key']]
    X = df[feature_cols].fillna(0)
    y = df['margin']
    
    # Try different alpha values
    alphas = [0.1, 1.0, 10.0, 100.0, 1000.0]
    best_alpha = None
    best_mae = float('inf')
    
    for alpha in alphas:
        model = Ridge(alpha=alpha)
        scores = -cross_val_score(model, X, y, cv=5, scoring='neg_mean_absolute_error')
        mae = scores.mean()
        
        if mae < best_mae:
            best_mae = mae
            best_alpha = alpha
    
    # Train final model
    final_model = Ridge(alpha=best_alpha)
    final_model.fit(X, y)
    
    # Save model
    import joblib
    joblib.dump(final_model, "model_pack/ridge_model_2025.joblib")
    
    print(f"✅ Best MAE: {best_mae:.2f} points")
    print(f"Best alpha: {best_alpha}")
```

---

## Category 4: Code Quality Issues (Medium Priority)

**Priority:** Medium  
**Impact:** Development workflow, code maintainability  
**Estimated Fix Time:** 6-8 hours

### 4.1 Import Errors

#### A. VS Code Diagnostics Issues

**Issue:** 200+ VS Code diagnostic issues from import paths.

**Files Affected:**
- `agents/analytics_orchestrator.py` (130 issues)
- `agents/model_execution_engine.py` (32 issues)
- `agents/core/agent_framework.py` (15 issues)
- `agents/core/context_manager.py` (12 issues)
- `agents/core/tool_loader.py` (17 issues)

**Fix Pattern:**

```python
# WRONG (causes import errors):
from context_manager import ContextManager

# CORRECT:
from agents.core.context_manager import ContextManager
```

**Step-by-Step Fix Instructions:**

1. **Check for missing `__init__.py` files:**
   ```bash
   find agents/ -name "__init__.py" -type f
   ```

2. **Create missing `__init__.py` files:**
   ```bash
   touch agents/__init__.py
   touch agents/core/__init__.py
   touch agents/system/__init__.py
   ```

3. **Fix import paths in each file:**
   - Search for: `from context_manager import`
   - Replace with: `from agents.core.context_manager import`
   - Repeat for all incorrect imports

4. **Verify fixes:**
   ```bash
   python -m py_compile agents/analytics_orchestrator.py
   ```

---

### 4.2 Error Handling

#### A. Missing File Existence Validation

**Location:** `agents/model_execution_engine.py` (lines 92-126)

**Current Code:**

```python
def load_model(self, model_path: str):
    """Load ML model."""
    return joblib.load(model_path)  # No file existence check
```

**Fixed Code:**

```python
def load_model(self, model_path: str):
    """Load ML model with file existence validation."""
    from pathlib import Path
    
    model_file = Path(model_path)
    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    if not model_file.is_file():
        raise ValueError(f"Model path is not a file: {model_path}")
    
    try:
        return joblib.load(model_path)
    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        raise
```

---

#### B. Incomplete Feature Alignment Error Handling

**Location:** `agents/model_execution_engine.py` (lines 364-402)

**Current Code:**

```python
def predict(self, features):
    """Make prediction."""
    # Missing validation for feature alignment
    return self.model.predict(features)
```

**Fixed Code:**

```python
def predict(self, features):
    """Make prediction with feature alignment validation."""
    import numpy as np
    
    # Validate input
    if features is None:
        raise ValueError("Features cannot be None")
    
    # Convert to numpy array if needed
    if not isinstance(features, np.ndarray):
        features = np.array(features)
    
    # Check feature count
    expected_features = self.model.n_features_in_
    if features.shape[1] != expected_features:
        raise ValueError(
            f"Feature count mismatch: expected {expected_features}, "
            f"got {features.shape[1]}"
        )
    
    try:
        return self.model.predict(features)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise
```

---

#### C. Missing Input Validation

**Location:** Prediction pipeline

**Fix Implementation:**

```python
def validate_prediction_input(self, home_team: str, away_team: str, 
                             season: int, week: int) -> Dict[str, Any]:
    """Validate prediction input parameters."""
    errors = []
    
    if not home_team or not isinstance(home_team, str):
        errors.append("home_team must be a non-empty string")
    
    if not away_team or not isinstance(away_team, str):
        errors.append("away_team must be a non-empty string")
    
    if not isinstance(season, int) or season < 2016 or season > 2030:
        errors.append("season must be an integer between 2016 and 2030")
    
    if not isinstance(week, int) or week < 1 or week > 16:
        errors.append("week must be an integer between 1 and 16")
    
    if errors:
        raise ValueError("Input validation failed: " + "; ".join(errors))
    
    return {"valid": True}
```

---

### 4.3 Missing API Methods

#### A. Implement Missing Methods

**Location:** `agents/model_execution_engine.py`

**Missing Methods:**

```python
def list_available_models(self) -> List[str]:
    """List all available model IDs."""
    return list(self.models.keys())

def get_model_metadata(self, model_id: str) -> Dict[str, Any]:
    """Get metadata for a specific model."""
    if model_id not in self.models:
        raise ValueError(f"Model {model_id} not found")
    
    model = self.models[model_id]
    return {
        "model_id": model_id,
        "model_type": type(model).__name__,
        "features": getattr(model, 'n_features_in_', None),
        "loaded": True
    }

def batch_predict(self, features_list: List[np.ndarray]) -> List[Any]:
    """Make batch predictions."""
    results = []
    for features in features_list:
        try:
            prediction = self.predict(features)
            results.append(prediction)
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            results.append(None)
    return results

def model_health_check(self) -> Dict[str, Any]:
    """Check health of all loaded models."""
    health_status = {
        "total_models": len(self.models),
        "healthy_models": 0,
        "unhealthy_models": [],
        "status": "healthy"
    }
    
    for model_id, model in self.models.items():
        try:
            # Try a dummy prediction to test model
            dummy_features = np.zeros((1, getattr(model, 'n_features_in_', 10)))
            model.predict(dummy_features)
            health_status["healthy_models"] += 1
        except Exception as e:
            health_status["unhealthy_models"].append({
                "model_id": model_id,
                "error": str(e)
            })
            health_status["status"] = "degraded"
    
    return health_status
```

---

## Category 5: Data Validation Issues (Medium Priority)

**Priority:** Medium  
**Impact:** Data quality assurance  
**Estimated Fix Time:** 4-5 hours

### 5.1 Validation Scripts

#### A. Create Tests for Validation Scripts

**Files to Create:**
- `tests/test_data_validation_script.py`
- `tests/test_data_remediation_script.py`
- `tests/test_master_admin_system_audit.py`

**Example Test Structure:**

```python
# tests/test_data_validation_script.py
import pytest
from pathlib import Path
from core_tools.DATA_VALIDATION_SCRIPT import DataValidator

def test_data_validator_initialization():
    """Test DataValidator initializes correctly."""
    validator = DataValidator(Path.cwd())
    assert validator.project_root.exists()

def test_validate_training_data():
    """Test training data validation."""
    validator = DataValidator(Path.cwd())
    result = validator.validate_training_data()
    assert isinstance(result, bool)

def test_validate_week12_data():
    """Test week 12 data validation."""
    validator = DataValidator(Path.cwd())
    result = validator.validate_week12_data()
    assert isinstance(result, bool)
```

---

#### B. Talent Rating Range Validation Fix

**Issue:** Validation script flags 29 games with talent values outside 0-1000 range (false positive).

**Fix:**

```python
# Update validation script to use 0-1500 range
def validate_talent_ratings(df):
    """Validate talent ratings with appropriate range."""
    min_talent = df[['home_talent', 'away_talent']].min().min()
    max_talent = df[['home_talent', 'away_talent']].max().max()
    
    # Updated range: 0-1500 (was 0-1000)
    if min_talent < 0 or max_talent > 1500:
        return False, f"Talent out of range: {min_talent} to {max_talent}"
    
    return True, f"Talent in valid range: {min_talent} to {max_talent}"
```

---

## Category 6: Integration Issues (Medium Priority)

**Priority:** Medium  
**Impact:** System integration and testing  
**Estimated Fix Time:** 4-5 hours

### 6.1 Week 12 Integration

#### A. Integration Tests

**File to Create:** `tests/test_fixed_data_integration.py`

**Test Structure:**

```python
import pytest
import pandas as pd
from pathlib import Path

def test_week12_data_integration():
    """Test week 12 data is properly integrated."""
    training_file = Path("model_pack/updated_training_data.csv")
    df = pd.read_csv(training_file)
    
    week12 = df[(df['season'] == 2025) & (df['week'] == 12)]
    assert len(week12) >= 45, "Week 12 should have at least 45 games"

def test_game_key_populated():
    """Test game_key column is populated."""
    training_file = Path("model_pack/updated_training_data.csv")
    df = pd.read_csv(training_file)
    
    assert 'game_key' in df.columns
    assert df['game_key'].notna().all(), "All games should have game_key"

def test_conference_game_populated():
    """Test conference_game column is populated."""
    training_file = Path("model_pack/updated_training_data.csv")
    df = pd.read_csv(training_file)
    
    assert 'conference_game' in df.columns
    assert df['conference_game'].notna().all(), "All games should have conference_game"
```

---

## Category 7: Documentation Issues (Low Priority)

**Priority:** Low  
**Impact:** Developer experience  
**Estimated Fix Time:** 2-3 hours

### 7.1 Missing Documentation

#### A. Create Usage Examples

**File to Create:** `project_management/DATA_VALIDATION_GUIDE.md`

**Content Structure:**

```markdown
# Data Validation Guide

## Running Validation Scripts

### Basic Validation
\`\`\`bash
python core_tools/DATA_VALIDATION_SCRIPT.py
\`\`\`

### Specific Validations
\`\`\`python
from core_tools.DATA_VALIDATION_SCRIPT import DataValidator

validator = DataValidator(Path.cwd())
validator.validate_training_data()
validator.validate_week12_data()
\`\`\`
```

---

## Category 8: Known Limitations (Low Priority)

**Priority:** Low  
**Impact:** System capabilities  
**Estimated Fix Time:** Varies

### 8.1 Data Limitations

#### A. Spread Data All Zero

**Status:** Expected - requires external betting lines API.

**Workaround:**

```python
# Use historical spread averages as fallback
def get_spread_fallback(home_team: str, away_team: str):
    """Get spread from historical averages if not available."""
    # Load historical data
    df = pd.read_csv("model_pack/updated_training_data.csv")
    
    # Calculate average spread for similar matchups
    # ... implementation ...
    
    return estimated_spread
```

---

#### B. Opponent-Adjusted Features

**Status:** Partially resolved (Week 5-11 coverage).

**Action:** Expand coverage as data becomes available.

---

## Priority Action Plan

### Immediate (Critical - Do First) - 8-10 hours

1. **Remove GraphQL Dependencies from Agents** (8-10 hours)
   - [ ] Fix `agents/insight_generator_agent.py`
   - [ ] Fix `agents/workflow_automator_agent.py`
   - [ ] Fix `agents/cfbd_integration_agent.py`
   - [ ] Fix `agents/analytics_orchestrator.py`
   - [ ] Update `agents/core/enhanced_cfbd_integration.py`
   - [ ] Update `starter_pack/notebooks/CFBD_Ingestion.ipynb`

2. **Verify and Integrate Weeks 1-12 Data** (2-3 hours)
   - [ ] Run validation script
   - [ ] Verify week coverage
   - [ ] Check for duplicates
   - [ ] Verify schema consistency

3. **Retrain All Models with Weeks 1-12 Data** (3-4 hours)
   - [ ] Run `scripts/integrate_weeks_1_12_and_retrain.py`
   - [ ] Verify models load correctly
   - [ ] Test predictions

### Short Term (High Priority - This Week) - 8-10 hours

4. **Fix FastAI Model Pickle Protocol** (2-3 hours)
   - [ ] Retrain FastAI model with protocol 4
   - [ ] Or update loading code with fallback

5. **Update CFBD Ingestion Notebook** (1-2 hours)
   - [ ] Make GraphQL cells optional
   - [ ] Add error handling

6. **Fix Import Errors in Agent Files** (3-4 hours)
   - [ ] Fix import paths
   - [ ] Add missing `__init__.py` files
   - [ ] Verify VS Code diagnostics

7. **Add Error Handling Improvements** (3-4 hours)
   - [ ] Add file existence validation
   - [ ] Enhance feature alignment error handling
   - [ ] Add input validation

8. **Verify Week 13 Data Preparation** (1-2 hours)
   - [ ] Check week 13 files exist
   - [ ] Verify features generated correctly

### Medium Term (Medium Priority - Next 2 Weeks) - 12-16 hours

9. **Add Tests for Validation Scripts** (2-3 hours)
10. **Create Integration Tests** (2-3 hours)
11. **Implement Missing API Methods** (4-6 hours)
12. **Model Performance Monitoring** (4-6 hours)
13. **Update Documentation** (2-3 hours)

### Long Term (Low Priority - As Time Permits) - 15-20 hours

14. **Clean Up Backup Files** (1-2 hours)
15. **Automated Data Quality Monitoring** (3-4 hours)
16. **Performance Optimizations** (4-6 hours)
17. **Model Retraining Pipeline Automation** (6-8 hours)
18. **Documentation Enhancements** (2-3 hours)

---

## Summary Statistics

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| GraphQL Removal | 5 | 1 | 1 | 1 | 8 |
| 2025 Data Issues | 3 | 3 | 2 | 0 | 8 |
| Model Training | 1 | 2 | 3 | 0 | 6 |
| Code Quality | 0 | 0 | 6 | 0 | 6 |
| Data Validation | 0 | 0 | 2 | 1 | 3 |
| Integration | 0 | 1 | 2 | 0 | 3 |
| Documentation | 0 | 0 | 0 | 3 | 3 |
| Known Limitations | 0 | 0 | 0 | 5+ | 5+ |
| **TOTAL** | **9** | **7** | **16** | **10+** | **42+** |

---

## Recommended Agent Solutions

To help agents systematically solve the remaining issues, the following specialized agents are recommended. These agents can automate resolution of critical, high-priority, and medium-priority issues.

### 1. GraphQL Removal Agent

**Purpose**: Automate removal of GraphQL dependencies across the codebase to prevent system failures when GraphQL capabilities are called.

**Capabilities**:

```python
AgentCapability(
    name="detect_graphql_references",
    description="Scan codebase for GraphQL imports, calls, and references",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["ast", "grep", "file_search"],
    data_access=["agents/", "starter_pack/", "docs/"],
    execution_time_estimate=5.0
)

AgentCapability(
    name="remove_graphql_capability",
    description="Remove GraphQL capabilities from agent definitions",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["ast", "code_editor"],
    data_access=["agents/*_agent.py"],
    execution_time_estimate=2.0
)

AgentCapability(
    name="replace_graphql_with_rest",
    description="Replace GraphQL calls with REST API alternatives",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["ast", "code_editor"],
    data_access=["agents/", "starter_pack/"],
    execution_time_estimate=3.0
)

AgentCapability(
    name="update_documentation_graphql",
    description="Update documentation to remove GraphQL references",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["file_search", "text_editor"],
    data_access=["docs/", "AGENTS.md"],
    execution_time_estimate=1.5
)
```

**Priority**: Critical - Addresses Category 1 (9 critical issues)

---

### 2. Data Completeness Validator Agent

**Purpose**: Verify weeks 1-12 integration and data quality to ensure models have complete training data.

**Capabilities**:

```python
AgentCapability(
    name="verify_weeks_coverage",
    description="Verify all weeks 1-12 are present in training data",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["pandas", "pathlib"],
    data_access=["model_pack/updated_training_data.csv"],
    execution_time_estimate=2.0
)

AgentCapability(
    name="validate_schema_consistency",
    description="Verify 86-feature schema matches across all weeks",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["pandas", "numpy"],
    data_access=["model_pack/updated_training_data.csv", "data/week*/"],
    execution_time_estimate=3.0
)

AgentCapability(
    name="check_data_quality",
    description="Check for missing values, duplicates, and data integrity issues",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["pandas"],
    data_access=["model_pack/", "data/week*/"],
    execution_time_estimate=4.0
)

AgentCapability(
    name="generate_data_completeness_report",
    description="Generate comprehensive report on data completeness and quality",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["pandas", "json"],
    data_access=["model_pack/", "data/week*/"],
    execution_time_estimate=3.0
)
```

**Priority**: High - Addresses Category 2 (8 issues affecting model accuracy)

---

### 3. Model Retraining Orchestrator Agent

**Purpose**: Automate model retraining with weeks 1-12 data to ensure models include latest training data.

**Capabilities**:

```python
AgentCapability(
    name="prepare_training_data",
    description="Prepare training data with weeks 1-12 integration",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["pandas", "numpy"],
    data_access=["model_pack/", "data/week*/"],
    execution_time_estimate=10.0
)

AgentCapability(
    name="retrain_ridge_model",
    description="Retrain Ridge regression model with updated data",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["sklearn", "joblib"],
    data_access=["model_pack/"],
    execution_time_estimate=30.0
)

AgentCapability(
    name="retrain_xgb_model",
    description="Retrain XGBoost model with improved hyperparameters",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["xgboost", "pickle"],
    data_access=["model_pack/"],
    execution_time_estimate=45.0
)

AgentCapability(
    name="fix_fastai_pickle_protocol",
    description="Retrain FastAI model with compatible pickle protocol 4",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["fastai", "pickle"],
    data_access=["model_pack/"],
    execution_time_estimate=60.0
)

AgentCapability(
    name="validate_retrained_models",
    description="Validate that retrained models load and perform correctly",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["joblib", "pickle", "sklearn"],
    data_access=["model_pack/"],
    execution_time_estimate=5.0
)
```

**Priority**: High - Addresses Category 3 (6 issues affecting model performance)

---

### 4. Code Quality Repair Agent

**Purpose**: Fix import errors, add error handling, and improve code structure for better maintainability.

**Capabilities**:

```python
AgentCapability(
    name="fix_import_paths",
    description="Fix import paths to use proper module structure",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["ast", "grep", "code_editor"],
    data_access=["agents/"],
    execution_time_estimate=3.0
)

AgentCapability(
    name="add_error_handling",
    description="Add comprehensive error handling to agent methods",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["ast", "code_editor"],
    data_access=["agents/"],
    execution_time_estimate=4.0
)

AgentCapability(
    name="add_input_validation",
    description="Add input validation to agent action methods",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["ast", "code_editor"],
    data_access=["agents/"],
    execution_time_estimate=3.0
)

AgentCapability(
    name="verify_file_existence",
    description="Add file existence checks before file operations",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["ast", "code_editor", "pathlib"],
    data_access=["agents/"],
    execution_time_estimate=2.0
)

AgentCapability(
    name="fix_missing_init_files",
    description="Ensure all __init__.py files exist for proper imports",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["pathlib", "file_editor"],
    data_access=["agents/"],
    execution_time_estimate=1.0
)
```

**Priority**: Medium - Addresses Category 4 (6 code quality issues)

---

### 5. Issue Detection and Reporting Agent

**Purpose**: Automatically scan and catalog all issues across the codebase for comprehensive issue tracking.

**Capabilities**:

```python
AgentCapability(
    name="scan_codebase_issues",
    description="Scan codebase for known issue patterns",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["grep", "ast", "file_search"],
    data_access=["agents/", "model_pack/", "scripts/"],
    execution_time_estimate=10.0
)

AgentCapability(
    name="detect_graphql_patterns",
    description="Detect GraphQL references in code",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["grep", "ast"],
    data_access=["agents/", "starter_pack/"],
    execution_time_estimate=5.0
)

AgentCapability(
    name="detect_import_errors",
    description="Detect import path issues and missing dependencies",
    permission_required=PermissionLevel.READ_EXECUTE,
    tools_required=["ast", "importlib"],
    data_access=["agents/"],
    execution_time_estimate=8.0
)

AgentCapability(
    name="generate_issue_report",
    description="Generate comprehensive issue report with priorities",
    permission_required=PermissionLevel.READ_EXECUTE_WRITE,
    tools_required=["json", "markdown"],
    data_access=["project_management/"],
    execution_time_estimate=3.0
)
```

**Priority**: Medium - Provides visibility across all issue categories

---

### 6. Automated Remediation Orchestrator

**Purpose**: Coordinate multiple specialized agents to fix issues automatically in a coordinated workflow.

**Capabilities**:

```python
AgentCapability(
    name="orchestrate_graphql_removal",
    description="Coordinate GraphQL removal across all affected files",
    permission_required=PermissionLevel.ADMIN,
    tools_required=["agent_coordination"],
    data_access=["agents/", "starter_pack/", "docs/"],
    execution_time_estimate=15.0
)

AgentCapability(
    name="orchestrate_data_integration",
    description="Coordinate weeks 1-12 data integration and validation",
    permission_required=PermissionLevel.ADMIN,
    tools_required=["agent_coordination"],
    data_access=["model_pack/", "data/week*/"],
    execution_time_estimate=20.0
)

AgentCapability(
    name="orchestrate_model_retraining",
    description="Coordinate complete model retraining pipeline",
    permission_required=PermissionLevel.ADMIN,
    tools_required=["agent_coordination"],
    data_access=["model_pack/"],
    execution_time_estimate=180.0  # 3 hours for full retraining
)

AgentCapability(
    name="orchestrate_code_quality_fixes",
    description="Coordinate code quality improvements across codebase",
    permission_required=PermissionLevel.ADMIN,
    tools_required=["agent_coordination"],
    data_access=["agents/"],
    execution_time_estimate=30.0
)
```

**Priority**: Medium - Provides end-to-end automation for issue resolution

---

### Implementation Priority

**Immediate (Critical)**:
1. GraphQL Removal Agent - Addresses Category 1 (9 critical issues)
2. Data Completeness Validator Agent - Addresses Category 2 (high priority)
3. Issue Detection Agent - Provides visibility into all issues

**Short-term (High Priority)**:
4. Model Retraining Orchestrator Agent - Addresses Category 3
5. Code Quality Repair Agent - Addresses Category 4

**Medium-term (Automation)**:
6. Automated Remediation Orchestrator - Coordinates all fixes end-to-end

---

## Next Steps

**Recommended Approach**: Use specialized agents (see "Recommended Agent Solutions" section above) to automate issue resolution:

1. **Start with Critical GraphQL Removal** (Category 1) - Blocks functionality
   - **Agent Solution**: GraphQL Removal Agent can automate removal across all affected files
   - **Impact**: Prevents system failures when GraphQL capabilities are called

2. **Verify and Integrate 2025 Data** (Category 2) - Affects model accuracy
   - **Agent Solution**: Data Completeness Validator Agent can verify weeks 1-12 integration
   - **Impact**: Ensures models have complete training data

3. **Retrain Models** (Category 3) - Ensures latest data in models
   - **Agent Solution**: Model Retraining Orchestrator Agent can automate full retraining pipeline
   - **Impact**: Models include latest 2025 season data

4. **Address Code Quality Issues** (Category 4) - Improves maintainability
   - **Agent Solution**: Code Quality Repair Agent can fix imports, add error handling, improve structure
   - **Impact**: Better code maintainability and fewer runtime errors

5. **Add Tests and Validation** (Categories 5-6) - Ensures reliability
   - **Agent Solution**: Issue Detection and Reporting Agent can scan for issues and generate reports
   - **Impact**: Comprehensive issue tracking and validation

6. **Update Documentation** (Category 7) - Improves developer experience
   - **Agent Solution**: Automated Remediation Orchestrator can coordinate end-to-end fixes
   - **Impact**: Improved developer workflow and documentation

---

**Report Generated:** 2025-11-17  
**Next Review:** After critical issues are resolved  
**Maintainer:** Development Team
