# 🚀 High-Performance Backup Game Extraction Plan
## Multi-Agent Parallel Processing with Modern Tooling

**Objective:** Extract missing games from backup training data using parallel agent processing with UV/Astral for maximum speed.

**Expected Performance:** 5-10x faster than sequential processing
**Target:** Process 4,520 backup games + 5,279 missing games in <2 minutes

---

## 📊 Architecture Overview

```markdown:project_management/EXTRACTION_PLAN_BACKUP_GAMES.md
```
┌─────────────────────────────────────────────────────────┐
│          Analytics Orchestrator (Main Coordinator)      │
│         - Routes requests to specialized agents          │
│         - Manages context and state                      │
│         - Coordinates parallel execution                 │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──────┐ ┌──▼──────┐ ┌─▼──────────────┐
│ Workflow     │ │ Data    │ │ Feature        │
│ Automator    │ │ Loader  │ │ Validator      │
│ Agent        │ │ Agent   │ │ Agent          │
└───────┬──────┘ └──┬──────┘ └─┬──────────────┘
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────┴───────────┐
        │   Parallel Sub-Agents  │
        ├────────────────────────┤
        │  ┌──────────────────┐ │
        │  │ Chunk Processor 1│ │ Process Season 2016-2018
        │  └──────────────────┘ │
        │  ┌──────────────────┐ │
        │  │ Chunk Processor 2│ │ Process Season 2019-2021
        │  └──────────────────┘ │
        │  ┌──────────────────┐ │
        │  │ Chunk Processor 3│ │ Process Season 2022-2024
        │  └──────────────────┘ │
        │  ┌──────────────────┐ │
        │  │ Chunk Processor 4│ │ Process Season 2025 (if any)
        │  └──────────────────┘ │
        └────────────────────────┘
```

---

## 🤖 Agent Structure

### 1. **Main Orchestrator Agent**
- **Type:** `WorkflowAutomatorAgent`
- **Role:** Coordinate entire extraction workflow
- **Responsibilities:**
  - Load and validate input files
  - Split data into parallel chunks
  - Launch parallel sub-agents
  - Aggregate results
  - Handle timezone normalization
  - Merge and save final dataset

### 2. **Data Loader Sub-Agent**
- **Type:** Custom sub-agent
- **Role:** Fast parallel data loading with modern tooling
- **Responsibilities:**
  - Load backup CSV using Polars/Arrow (10x faster than pandas)
  - Load missing games list
  - Load current training data
  - Validate schemas
  - Return dataframes for processing

### 3. **Chunk Processor Sub-Agents** (Parallel)
- **Type:** Multiple parallel instances
- **Role:** Process data chunks in parallel
- **Responsibilities:**
  - Match game IDs within chunk
  - Extract matching games
  - Normalize timestamps (chunk-specific)
  - Deduplicate against current data
  - Return processed chunk

### 4. **Feature Validator Sub-Agent**
- **Type:** `QualityAssuranceAgent`
- **Role:** Validate extracted games
- **Responsibilities:**
  - Verify 86 features present
  - Check data integrity
  - Validate schema compliance
  - Generate quality report

### 5. **Integration Sub-Agent**
- **Type:** Custom sub-agent
- **Role:** Final merge and save
- **Responsibilities:**
  - Combine all processed chunks
  - Final deduplication
  - Sort by season/week/date
  - Create backup
  - Save final dataset

---

## ⚡ Modern Tooling Integration

### **UV Package Manager** (Astral)
- **Purpose:** Lightning-fast Python package installation and execution
- **Benefits:**
  - 10-100x faster than pip
  - Rust-based, ultra-fast
  - Better dependency resolution
  - Virtual environment management

### **Polars** (Alternative to Pandas)
- **Purpose:** Parallel DataFrame processing
- **Benefits:**
  - 10-50x faster than pandas for large datasets
  - Native parallel execution
  - Arrow-based, memory efficient
  - Lazy evaluation for optimization

### **Ray** (Optional, for extreme parallelism)
- **Purpose:** Distributed computing for very large datasets
- **Benefits:**
  - Multi-machine parallel processing
  - Automatic load balancing
  - Fault tolerance

---

## 🔄 Workflow Steps

### **Phase 1: Initialization** (Sequential)
1. **Orchestrator Agent** starts workflow
2. **Data Loader Sub-Agent** loads files in parallel:
   - Load backup training data (4,520 games)
   - Load missing games list (5,279 IDs)
   - Load current training data
3. Validate all files exist and schemas match
4. Create output directories

### **Phase 2: Chunking** (Sequential)
1. **Orchestrator** splits backup data into chunks by season:
   - Chunk 1: 2016-2018 (~1,500 games)
   - Chunk 2: 2019-2021 (~1,500 games)
   - Chunk 3: 2022-2024 (~1,500 games)
   - Chunk 4: 2025 (~20 games if any)
2. Split missing games list into matching chunks

### **Phase 3: Parallel Processing** (Concurrent)
1. Launch 4 parallel **Chunk Processor Sub-Agents**:
   - Each processes one season chunk
   - Match game IDs within chunk
   - Extract matching games
   - Normalize timestamps
   - Deduplicate
2. All processors run simultaneously (true parallelism)

### **Phase 4: Aggregation** (Sequential)
1. **Orchestrator** collects results from all chunk processors
2. Combine all extracted games
3. Final deduplication across chunks

### **Phase 5: Validation** (Parallel with Integration)
1. **Feature Validator Sub-Agent** validates extracted games
2. **Integration Sub-Agent** merges with current data
3. Both run simultaneously

### **Phase 6: Finalization** (Sequential)
1. Create backup of current training data
2. Sort combined dataset
3. Save final training data
4. Generate completion report

---

## 💻 Implementation Code Structure

### **Main Script:** `scripts/extract_games_from_backup_parallel.py`

```python
#!/usr/bin/env python3
"""
High-Performance Parallel Game Extraction from Backup
Uses UV/Astral and multi-agent parallel processing
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

# Modern tooling imports
try:
    import polars as pl  # 10x faster than pandas for large datasets
    USE_POLARS = True
except ImportError:
    import pandas as pd
    USE_POLARS = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
from agents.workflow_automator_agent import WorkflowAutomatorAgent, WorkflowStep, WorkflowStepType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
BACKUP_TRAINING_PATH = PROJECT_ROOT / 'model_pack copy' / 'training_data.csv'
MISSING_GAMES_PATH = PROJECT_ROOT / 'reports' / 'missing_games.csv'
CURRENT_TRAINING_PATH = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
OUTPUT_PATH = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'


class ParallelGameExtractor:
    """
    High-performance parallel game extraction using agent framework
    """
    
    def __init__(self):
        self.orchestrator = AnalyticsOrchestrator()
        self.workflow_agent = None
        
    async def create_workflow(self) -> Dict[str, Any]:
        """Create the parallel extraction workflow"""
        
        workflow_steps = [
            # Step 1: Load all data files in parallel
            WorkflowStep(
                step_id="load_data",
                step_type=WorkflowStepType.PARALLEL_EXECUTION,
                description="Load backup, missing games, and current training data in parallel",
                parallel_steps=[
                    WorkflowStep(
                        step_id="load_backup",
                        step_type=WorkflowStepType.DATA_PROCESSING,
                        description="Load backup training data",
                        action="load_backup_data",
                        parameters={"path": str(BACKUP_TRAINING_PATH)}
                    ),
                    WorkflowStep(
                        step_id="load_missing",
                        step_type=WorkflowStepType.DATA_PROCESSING,
                        description="Load missing games list",
                        action="load_missing_games",
                        parameters={"path": str(MISSING_GAMES_PATH)}
                    ),
                    WorkflowStep(
                        step_id="load_current",
                        step_type=WorkflowStepType.DATA_PROCESSING,
                        description="Load current training data",
                        action="load_current_data",
                        parameters={"path": str(CURRENT_TRAINING_PATH)}
                    )
                ]
            ),
            
            # Step 2: Chunk data by season for parallel processing
            WorkflowStep(
                step_id="chunk_data",
                step_type=WorkflowStepType.DATA_PROCESSING,
                description="Split data into season chunks for parallel processing",
                action="chunk_by_season",
                parameters={
                    "chunks": [
                        {"seasons": [2016, 2017, 2018], "name": "chunk_2016_2018"},
                        {"seasons": [2019, 2020, 2021], "name": "chunk_2019_2021"},
                        {"seasons": [2022, 2023, 2024], "name": "chunk_2022_2024"},
                        {"seasons": [2025], "name": "chunk_2025"}
                    ]
                }
            ),
            
            # Step 3: Process chunks in parallel
            WorkflowStep(
                step_id="process_chunks",
                step_type=WorkflowStepType.PARALLEL_EXECUTION,
                description="Process all chunks simultaneously",
                parallel_steps=[
                    WorkflowStep(
                        step_id=f"process_chunk_{i}",
                        step_type=WorkflowStepType.DATA_PROCESSING,
                        description=f"Process chunk {i}",
                        action="process_chunk",
                        parameters={"chunk_id": f"chunk_2016_2018" if i == 0 else 
                                   f"chunk_2019_2021" if i == 1 else 
                                   f"chunk_2022_2024" if i == 2 else "chunk_2025"}
                    )
                    for i in range(4)
                ]
            ),
            
            # Step 4: Aggregate and validate
            WorkflowStep(
                step_id="aggregate_results",
                step_type=WorkflowStepType.PARALLEL_EXECUTION,
                description="Aggregate chunks and validate in parallel",
                parallel_steps=[
                    WorkflowStep(
                        step_id="aggregate_chunks",
                        step_type=WorkflowStepType.DATA_PROCESSING,
                        description="Combine all processed chunks",
                        action="aggregate_chunks"
                    ),
                    WorkflowStep(
                        step_id="validate_extracted",
                        step_type=WorkflowStepType.ANALYSIS,
                        description="Validate extracted games have 86 features",
                        action="validate_features",
                        agent_type="quality_assurance"
                    )
                ]
            ),
            
            # Step 5: Integrate and save
            WorkflowStep(
                step_id="integrate_and_save",
                step_type=WorkflowStepType.DATA_PROCESSING,
                description="Merge with current data and save",
                action="integrate_and_save",
                parameters={
                    "output_path": str(OUTPUT_PATH),
                    "create_backup": True
                }
            )
        ]
        
        return {
            "workflow_id": "backup_game_extraction",
            "name": "Parallel Backup Game Extraction",
            "description": "Extract missing games from backup using parallel processing",
            "steps": workflow_steps
        }
    
    async def execute_extraction(self) -> Dict[str, Any]:
        """Execute the parallel extraction workflow"""
        logger.info("=" * 80)
        logger.info("PARALLEL BACKUP GAME EXTRACTION - HIGH PERFORMANCE MODE")
        logger.info("=" * 80)
        
        # Create workflow
        workflow_def = await self.create_workflow()
        
        # Execute via WorkflowAutomatorAgent
        request = AnalyticsRequest(
            user_id="system",
            query="Execute parallel backup game extraction",
            query_type="workflow",
            parameters={
                "workflow_definition": workflow_def,
                "use_polars": USE_POLARS,
                "parallel_workers": 4
            },
            context_hints={"role": "system", "priority": "high"}
        )
        
        response = self.orchestrator.process_analytics_request(request)
        
        return {
            "success": response.status == "success",
            "execution_time": response.execution_time,
            "results": response.results,
            "insights": response.insights
        }


async def main():
    """Main execution"""
    extractor = ParallelGameExtractor()
    result = await extractor.execute_extraction()
    
    if result["success"]:
        logger.info("✅ SUCCESS: Games extracted and integrated!")
        logger.info(f"   Execution time: {result['execution_time']:.2f}s")
    else:
        logger.error("❌ FAILED: Extraction failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📦 Dependencies & Setup

### **Update requirements.txt:**
```txt
# Modern high-performance tooling
polars>=0.19.0  # 10x faster DataFrame operations
pyarrow>=14.0.0  # Arrow-based memory format
ray[default]>=2.8.0  # Optional: distributed computing
```

### **Installation with UV:**
```bash
# Install UV (Astral's package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment with UV (lightning fast)
uv venv

# Install dependencies with UV (10-100x faster than pip)
uv pip install -r requirements.txt

# Or install specific packages
uv pip install polars pyarrow pandas
```

### **Run with UV:**
```bash
# Execute script with UV's optimized Python
uv run python scripts/extract_games_from_backup_parallel.py

# Or use UV's built-in execution
uv run --with polars --with pyarrow scripts/extract_games_from_backup_parallel.py
```

---

## ⚡ Performance Optimizations

### **1. Polars for Data Loading** (10-50x faster)
- Native parallel execution
- Lazy evaluation
- Arrow-based memory format
- Columnar processing

### **2. Parallel Chunk Processing**
- Process 4 season chunks simultaneously
- True parallelism with asyncio/threading
- No sequential bottlenecks

### **3. Memory Optimization**
- Stream processing for large files
- Chunked operations
- Garbage collection hints

### **4. Caching Strategy**
- Cache loaded dataframes in memory
- Reuse parsed timestamps
- Avoid redundant operations

---

## 📊 Expected Performance

### **Sequential Processing:**
- Load backup: ~15s
- Match IDs: ~10s
- Normalize timestamps: ~5s
- Merge and save: ~10s
- **Total: ~40-60s**

### **Parallel Processing with UV/Polars:**
- Load all files (parallel): ~2s
- Process 4 chunks (parallel): ~3s
- Aggregate and validate (parallel): ~2s
- Merge and save: ~2s
- **Total: ~9-12s** (4-5x faster)

---

## 🎯 Success Criteria

1. ✅ All 4,520 backup games processed
2. ✅ All matching games from missing list extracted
3. ✅ 86 features preserved for all games
4. ✅ Timestamps normalized correctly
5. ✅ No duplicates in final dataset
6. ✅ Execution time < 15 seconds
7. ✅ Memory usage < 2GB
8. ✅ Quality report generated

---

## 🔧 Sub-Agent Implementation Details

### **Data Loader Sub-Agent** (`data_loader_agent.py`)
```python
class DataLoaderAgent(BaseAgent):
    """Fast parallel data loading with Polars"""
    
    async def load_backup_data(self, path: str) -> pl.DataFrame:
        """Load backup using Polars (10x faster)"""
        return pl.read_csv(path, low_memory=False)
    
    async def load_missing_games(self, path: str) -> pl.DataFrame:
        """Load missing games list"""
        return pl.read_csv(path)
```

### **Chunk Processor Sub-Agent** (`chunk_processor_agent.py`)
```python
class ChunkProcessorAgent(BaseAgent):
    """Process data chunks in parallel"""
    
    async def process_chunk(self, chunk_data: Dict) -> pl.DataFrame:
        """Process one chunk, extract matching games"""
        # Match IDs, extract, normalize, deduplicate
        return processed_chunk
```

---

## 🚀 Execution Commands

### **Standard Execution:**
```bash
python3 scripts/extract_games_from_backup_parallel.py
```

### **With UV (Recommended):**
```bash
uv run scripts/extract_games_from_backup_parallel.py
```

### **With Performance Monitoring:**
```bash
uv run --profile scripts/extract_games_from_backup_parallel.py
```

---

## 📝 Next Steps

1. **Install UV:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **Install Polars:** `uv pip install polars pyarrow`
3. **Create workflow agent implementation**
4. **Implement sub-agents**
5. **Test with small data sample**
6. **Run full extraction**
7. **Validate results**
8. **Generate performance report**

---

## 🔄 Future Enhancements

- **Ray Integration:** For distributed processing across machines
- **Streaming Processing:** For extremely large datasets
- **Incremental Updates:** Only process new games
- **Real-time Monitoring:** Dashboard for extraction progress
- **Auto-retry:** Handle failures gracefully
- **Checkpointing:** Resume from interruptions
```

## Quick Start Implementation

1. Install UV (Astral):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Add to requirements.txt:
```txt
polars>=0.19.0
pyarrow>=14.0.0
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Create the main script (structure above)

5. Run:
```bash
uv run scripts/extract_games_from_backup_parallel.py
```

This plan uses:
- **4 parallel sub-agents** for chunk processing
- **Polars** for 10-50x faster DataFrame ops
- **UV** for fast package management
- **WorkflowAutomatorAgent** for orchestration
- **Asyncio** for true parallelism

Expected speedup: 4-5x faster (9-12 seconds vs 40-60 seconds)

Should I implement any specific component first?
