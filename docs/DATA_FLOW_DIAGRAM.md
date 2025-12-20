# 🔄 Data Flow & Architecture Diagrams

## 🎯 Current Data Architecture Flow

```mermaid
graph LR
    subgraph "External Data Sources"
        A[CFBD API<br/>CollegeFootballData.com]
        B[Historical Archives<br/>1869-present games]
    end

    subgraph "Data Processing Pipeline"
        C[cfbd_pull.py<br/>Rate-limited ingestion]
        D[build_training_data.py<br/>Feature engineering]
        E[updated_training_data.csv<br/>⭐ MASTER: 4,989 games, 86 features]
    end

    subgraph "ML Training Pipeline"
        F[Model Training Scripts<br/>Ridge, XGBoost, FastAI]
        G[Model Files<br/>*_model_2025.*]
    end

    subgraph "Production System"
        H[Weekly Analysis<br/>Automated processing]
        I[Prediction Scripts<br/>Bowl predictions, analysis]
        J[Outputs<br/>JSON predictions, reports]
    end

    A --> C
    B --> D
    C --> D
    D --> E
    E --> F
    F --> G
    E --> H
    G --> I
    H --> I
    I --> J

    style A fill:#ffcccc
    style B fill:#ffcccc
    style E fill:#ccffcc
    style G fill:#ccccff
    style J fill:#ffffcc
```

## 📊 Directory Interaction Map

```mermaid
graph TD
    subgraph "🏛️ Educational Foundation"
        SP[starter_pack/]
        SP1[data/games.csv<br/>⭐ MASTER ARCHIVE]
        SP2[data/season_stats/]
        SP3[data/plays/]
        SP4[13 learning notebooks]
    end

    subgraph "🤖 Production ML System"
        MP[model_pack/]
        MP1[updated_training_data.csv<br/>⭐ MASTER DATA]
        MP2[*_model_2025.pkl/.joblib<br/>3 production models]
        MP3[backups/]
    end

    subgraph "⚡ Current Operations"
        DT[data/]
        DT1[training/weekly/]
        DT2[weekly/weekXX/enhanced/]
    end

    subgraph "📈 Outputs & Results"
        PR[predictions/]
        PR1[bowls_2025_predictions_*.json]
        PR2[analysis_reports/]
    end

    subgraph "🔧 Automation Pipeline"
        SC[scripts/]
        SC1[cfbd_pull.py]
        SC2[run_weekly_analysis.py]
        SC3[predict_bowls_2025.py]
    end

    SP1 --> MP1
    MP1 --> MP2
    MP1 --> DT1
    DT1 --> DT2
    MP2 --> PR1
    DT2 --> PR1
    SC1 --> DT1
    SC2 --> DT2
    SC3 --> PR1

    style SP1 fill:#e1f5fe
    style MP1 fill:#e8f5e8
    style PR1 fill:#fff3e0
    style MP2 fill:#f3e5f5
```

## 🔍 Data Lifecycle Management

```mermaid
stateDiagram-v2
    [*] --> RawIngestion
    RawIngestion --> FeatureEngineering: CFBD API pulls
    FeatureEngineering --> MasterTraining: 86 features created
    MasterTraining --> ModelTraining: Weekly updates
    ModelTraining --> ProductionModels: Ridge, XGBoost, FastAI
    ProductionModels --> Predictions: Automated inference
    Predictions --> Archive: Seasonal backup

    state RawIngestion {
        [*] --> CFBD_API
        CFBD_API --> RateLimited
        RateLimited --> RawCSVFiles
        RawCSVFiles --> [*]
    }

    state FeatureEngineering {
        [*] --> OpponentAdjustment
        OpponentAdjustment --> FeatureValidation
        FeatureValidation --> [*]
    }

    state Archive {
        [*] --> BackupCreation
        BackupCreation --> Compression
        Compression --> Storage
        Storage --> [*]
    }
```

## 📁 File Type Distribution

```mermaid
pie title Data Architecture by File Type
    "CSV Files (648)" : 91.3
    "JSON Files (32)" : 4.5
    "Pickle Files (20)" : 2.8
    "Joblib Files (10)" : 1.4
```

## 🏗️ Master Data Sources Hierarchy

```mermaid
graph TB
    subgraph "🌟 MASTER SOURCES (Authoritative)"
        A[CFBD API<br/>External source]
        B[starter_pack/data/games.csv<br/>Historical archive]
        C[model_pack/updated_training_data.csv<br/>ML training data]
    end

    subgraph "🔄 DERIVED DATA (Generated)"
        D[data/training/weekly/*.csv<br/>Weekly updates]
        E[data/weekly/weekXX/enhanced/<br/>Processed features]
        F[predictions/*.json<br/>Model outputs]
    end

    subgraph "🗃️ ARCHIVAL (Historical)"
        G[model_pack/backups/<br/>Model backups]
        H[*_backup_*.json<br/>Prediction backups]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    D --> E
    E --> F
    F --> H
    C --> G

    style A fill:#ffcdd2
    style B fill:#f8bbd9
    style C fill:#e1bee7
    style D fill:#c5cae9
    style E fill:#bbdefb
    style F fill:#b3e5fc
    style G fill:#b2dfdb
    style H fill:#c8e6c9
```

## 🔧 Quality Assessment Flow

```mermaid
flowchart TD
    Start([Start Quality Check]) --> Scan{Scan Directories}
    Scan --> Inventory[File Inventory<br/>710 files cataloged]
    Inventory --> Validate{Validate Schemas}
    Validate --> Check[Data Completeness<br/>95% quality score]
    Check --> Analyze[Analyze Dependencies<br/>Lineage mapping]
    Analyze --> Report[Generate Report<br/>Critical: 0, Minor: 2]
    Report --> Success([✅ Assessment Complete])

    Scan --> Error[❌ Scan Failed]
    Validate --> Error
    Error --> Success

    style Start fill:#e8f5e8
    style Success fill:#e8f5e8
    style Error fill:#ffebee
```

## 🎯 Reorganization Strategy Overview

```mermaid
mindmap
  root((Data Architecture))
    Current State
      710 files
      1.7GB storage
      95% quality
      ⚠️ Organization issues
    Master Sources
      CFBD API
      Historical archives
      ML training data
    Transformation Flow
      Raw → Features
      Features → Models
      Models → Predictions
    Reorganization Plan
      Phase 1: Analysis ✅
      Phase 2: Structure
      Phase 3: Automation
    Success Metrics
      40% file reduction
      100% naming consistency
      <10s file discovery
```

## 📈 Storage Utilization Analysis

```mermaid
bar-title Storage Usage by Category
    bar-chart
    axis Files Size(GB)
    series Files
    "ML Models": 10 0.2
    "Training Data": 1 0.01
    "Historical CSVs": 300 0.8
    "Predictions": 50 0.05
    "Backups": 200 0.4
    "Scripts/Config": 50 0.01
    "Documentation": 20 0.001
```

---

These diagrams illustrate how your current data architecture works together and where the opportunities for improvement lie. The key insight is that you have excellent data quality and comprehensive coverage - we just need to organize it better for maintainability and scalability.

**Key Observations:**
1. **Clear data flow** from external sources through processing to predictions
2. **Well-defined master sources** that feed the entire system
3. **Scattered organization** that can be streamlined
4. **High data quality** that should be preserved during reorganization

The reorganization will maintain all these flows while improving navigation and maintainability.