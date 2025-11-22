# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the starter_pack educational components.

## 🎯 Quick Start for Educational Content

```bash
# Navigate to starter pack
cd starter_pack/

# Start Jupyter Lab for interactive learning
jupyter lab

# Begin with data dictionary (recommended first)
jupyter lab 00_data_dictionary.ipynb

# Progress through learning curriculum
jupyter lab 01_intro_to_data.ipynb
```

## Starter Pack Overview

This directory contains the educational foundation for Script Ohio 2.0, featuring 12 comprehensive Jupyter notebooks that teach college football analytics through hands-on exploration of historical data. This is designed for learning data analysis, statistics, and visualization techniques using real college football data.

### Key Components

- **12 Educational Notebooks**: Progressive learning path from data exploration to advanced analytics
- **Historical Data Archive**: College football data spanning 1869-present (games) and 2003-present (play-by-play)
- **Advanced Metrics**: EPA, success rates, explosiveness, havoc rates, and other sophisticated statistics
- **Metadata**: Teams, conferences, venues, and supporting reference data

## Educational Philosophy

### Learning Progression
The notebooks are designed as a progressive learning experience:

1. **Data Orientation** (Notebooks 00-01): Understanding data structure and basic exploration
2. **Basic Analytics** (Notebooks 02-03): Simple rankings and comparative analysis
3. **Intermediate Techniques** (Notebooks 04-07): Similarity analysis, predictions, and custom rankings
4. **Advanced Concepts** (Notebooks 08-12): Efficiency analysis, opponent adjustments, and visualization

### Hands-On Approach
- **Real Data**: Uses actual college football data from CollegeFootballData.com
- **Practical Skills**: Focus on applicable data analysis techniques
- **Progressive Complexity**: Each notebook builds on concepts from previous ones
- **Multiple Learning Styles**: Combines code, visualizations, and explanatory text

## Data Architecture

### Historical Data Scope
- **Game Results**: 1869-present (complete historical record)
- **Play-by-Play Data**: 2003-present (detailed play-level data)
- **Season Statistics**: 2007-present (team-level seasonal aggregates)
- **Advanced Metrics**: EPA, success rates, explosiveness (2003-present)

### Data Directory Structure

#### Core Data Files
- **`teams.csv`**: Team information (schools, conferences, venues, mascots)
- **`conferences.csv`**: Conference information and structure
- **`games.csv`**: Game results and basic statistics (1869-present)

#### Advanced Statistics
- **`advanced_game_stats/`**: Game-level advanced metrics by season
- **`advanced_season_stats/`**: Season-level advanced metrics by team
- **`drives/`**: Drive-level data and scoring analysis
- **`game_stats/`**: Traditional game statistics
- **`season_stats/`**: Traditional season statistics by team

#### Play-by-Play Data
- **`plays/YYYY/`**: Detailed play-by-play data organized by year (2003-present)

### Key Metrics and Concepts

#### EPA (Expected Points Added)
- **Definition**: Change in expected points from start to end of play
- **Usage**: Measures play effectiveness beyond raw yardage
- **Context**: Accounts for down, distance, and field position

#### Success Rate
- **Definition**: Percentage of plays with positive EPA
- **Usage**: Measures consistency and efficiency
- **Context**: Varies by down and distance situation

#### Explosiveness
- **Definition**: Frequency of high-impact plays (big gains)
- **Usage**: Measures big-play capability
- **Context**: Complements success rate for complete offensive picture

#### Havoc Rate
- **Definition**: Defensive disruption metrics (TFLs, PBUs, INTs, FFs)
- **Usage**: Measures defensive playmaking ability
- **Types**: Total havoc, DB havoc, front seven havoc

## Notebook Curriculum

### Foundation Courses

#### **00 - Data Dictionary** (`00_data_dictionary.ipynb`)
- **Purpose**: Complete reference for all data fields and metrics
- **Content**: Field definitions, data sources, calculation methods
- **Usage**: Reference guide for all other notebooks
- **Prerequisites**: None (starting point)

#### **01 - Introduction to Data** (`01_intro_to_data.ipynb`)
- **Purpose**: Basic data exploration and familiarization
- **Skills**: Data loading, basic filtering, summary statistics
- **Visualizations**: Basic plots and charts
- **Takeaway**: Understanding data structure and content

### Core Analytics

#### **02 - Simple Rankings** (`02_build_simple_rankings.ipynb`)
- **Purpose**: Create basic team rankings using various metrics
- **Skills**: Data aggregation, ranking algorithms, comparison methods
- **Methods**: Points per game, win percentage, simple power ratings
- **Outcome**: Custom ranking systems and team comparisons

#### **03 - Metrics Comparison** (`03_metrics_comparison.ipynb`)
- **Purpose**: Compare different team performance metrics
- **Skills**: Correlation analysis, statistical comparison, visualization
- **Metrics**: EPA vs. traditional stats, efficiency vs. volume
- **Insight**: Understanding which metrics best predict success

### Intermediate Analysis

#### **04 - Team Similarity** (`04_team_similarity.ipynb`)
- **Purpose**: Find teams with similar playing styles and profiles
- **Skills**: Clustering algorithms, similarity metrics, dimensional analysis
- **Methods**: Euclidean distance, cosine similarity, clustering
- **Application**: Matchup analysis, team comparisons

#### **05 - Matchup Predictor** (`05_matchup_predictor.ipynb`)
- **Purpose**: Basic game outcome prediction using historical data
- **Skills**: Logistic regression, feature engineering, model evaluation
- **Factors**: Team strength, home advantage, recent performance
- **Foundation**: Prepares for advanced modeling in model_pack

#### **06 - Custom Rankings by Metric** (`06_custom_rankings_by_metric.ipynb`)
- **Purpose**: Create specialized rankings based on specific metrics
- **Skills**: Weighted scoring systems, custom ranking algorithms
- **Examples**: Efficiency rankings, explosive offense rankings, defensive rankings
- **Application**: Tailored analysis for specific use cases

#### **07 - Drive Efficiency** (`07_drive_efficiency.ipynb`)
- **Purpose**: Analyze team efficiency at the drive level
- **Skills**: Drive-level analysis, efficiency metrics, scoring analysis
- **Metrics**: Points per drive, drive success rate, explosive drives
- **Insight**: Understanding offensive and defensive efficiency

### Advanced Topics

#### **08 - Offense vs Defense Comparison** (`08_offense_vs_defense_comparison.ipynb`)
- **Purpose**: Compare offensive and defensive performance across teams
- **Skills**: Multi-dimensional analysis, balance metrics, team profiling
- **Concepts**: Offensive efficiency vs. defensive efficiency, team balance
- **Application**: Identifying well-rounded vs. specialized teams

#### **09 - Opponent Adjustments** (`09_opponent_adjustments.ipynb`)
- **Purpose**: Adjust team statistics based on opponent quality
- **Skills**: Strength of schedule calculations, adjustment algorithms
- **Methods**: Opponent-adjusted EPA, strength-based weighting
- **Importance**: Critical for fair team comparisons and predictions

#### **10 - SRS Adjusted Metrics** (`10_srs_adjusted_metrics.ipynb`)
- **Purpose**: Implement Simple Rating System (SRS) adjustments
- **Skills**: Rating system calculations, iterative adjustments
- **Concepts**: Strength-based scheduling, rating systems
- **Foundation**: Advanced rating and ranking methodologies

#### **11 - Metric Distribution Explorer** (`11_metric_distribution_explorer.ipynb`)
- **Purpose**: Explore statistical distributions of various metrics
- **Skills**: Statistical analysis, distribution fitting, outlier detection
- **Analysis**: Normality tests, distribution comparisons, statistical significance
- **Application**: Understanding metric behavior and appropriate usage

#### **12 - Efficiency Dashboards** (`12_efficiency_dashboards.ipynb`)
- **Purpose**: Create comprehensive dashboards for team analysis
- **Skills**: Interactive visualization, dashboard design, data presentation
- **Tools**: Advanced plotting, interactive elements, multi-panel layouts
- **Outcome**: Professional-quality analytical dashboards

## Usage Patterns

### For Beginners
1. **Start Here**: Begin with `00_data_dictionary.ipynb` for terminology
2. **Progress Sequentially**: Work through notebooks 01-12 in order
3. **Focus on Concepts**: Understanding analytics concepts before code details
4. **Experiment**: Modify parameters and explore different approaches

### For Data Scientists
1. **Jump Ahead**: Start with notebooks matching your skill level
2. **Reference Data Dictionary**: Use `00_data_dictionary.ipynb` as field reference
3. **Customize Analysis**: Adapt notebook techniques to your own research questions
4. **Bridge to Modeling**: Use starter_pack skills to prepare for model_pack work

### For Academic Researchers
1. **Methodology Focus**: Study analytical approaches and statistical methods
2. **Reproducibility**: Follow notebook workflows for reproducible research
3. **Extension Ideas**: Use notebooks as starting points for original research
4. **Citation Ready**: Well-documented methods suitable for academic work

### For Sports Fans and Analysts
1. **Practical Insights**: Focus on notebooks that answer specific questions
2. **Team Analysis**: Use notebooks 02, 06, 08 for team-specific analysis
3. **Game Predictions**: Notebook 05 provides basic prediction methodology
4. **Visualization**: Notebook 12 for creating compelling visual content

## Data Access and Manipulation

### Loading Data
```python
# Load game data
import pandas as pd
games = pd.read_csv('data/games.csv')

# Load advanced season stats
adv_stats = pd.read_csv('data/advanced_season_stats/2023.csv')

# Load team metadata
teams = pd.read_csv('data/teams.csv')
```

### Common Data Operations
- **Filtering by Season**: `df[df['season'] == 2023]`
- **Team Filtering**: `df[df['team'] == 'Ohio State']`
- **Conference Analysis**: `df[df['conference'] == 'Big Ten']`
- **Date Range Selection**: Filter by start_date for time-based analysis

### Data Quality Notes
- **Missing Data**: Earlier seasons have less complete data
- **Metric Consistency**: Advanced metrics available from 2003 onward
- **Team Names**: Use consistent team names across datasets
- **Conference Realignment**: Be aware of conference changes over time

## Integration with Model Pack

### Pathway to Advanced Modeling
- **Foundation**: Starter_pack provides data understanding and basic analytics
- **Bridge**: Notebooks 05, 09, 10 introduce concepts used in model_pack
- **Advanced Skills**: Data manipulation and analysis techniques transfer directly
- **Feature Engineering**: Starter_pack metrics become features in ML models

### Recommended Learning Path
1. **Complete Starter Pack**: Work through all 12 notebooks
2. **Focus on Key Concepts**: Emphasize opponent adjustments (09) and prediction (05)
3. **Review Model Pack**: Study model_pack documentation and approaches
4. **Combine Skills**: Use starter_pack insights to inform model_pack usage

## 🚀 Development Commands

### Environment Setup
```bash
# Core dependencies for starter pack notebooks (Python 3.13+)
pip install pandas numpy matplotlib seaborn scikit-learn jupyter

# For advanced statistical analysis
pip install scipy

# Start Jupyter environment
jupyter lab
# or
jupyter notebook

# Access at http://localhost:8888
```

### Running Notebooks
```bash
# Navigate to starter pack directory
cd starter_pack/

# Start with data dictionary (recommended first step)
jupyter lab 00_data_dictionary.ipynb

# Or begin with introductory notebook
jupyter lab 01_intro_to_data.ipynb

# Progress through curriculum sequentially
jupyter lab 02_build_simple_rankings.ipynb
```

## Technical Requirements

### Python Dependencies
```python
# Core data analysis
import pandas as pd
import numpy as np

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Statistics and modeling (advanced notebooks)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from scipy.stats import pearsonr, spearmanr
```

### Computational Resources
- **Memory**: Most notebooks run with 8GB RAM
- **Processing**: Basic analysis - any modern laptop sufficient
- **Large Data**: Play-by-play analysis may require more memory
- **Visualization**: GPU not required but can improve plot rendering

## File Organization Standards

### Naming Conventions
- **Notebooks**: `{sequence_number}_{description}.ipynb` (e.g., `01_intro_to_data.ipynb`)
- **Data Files**: `{category}_{year}.csv` (e.g., `advanced_season_stats/2023.csv`)
- **Documentation**: Descriptive names with clear purpose

### Data Versioning
- **Static Historical Data**: Historical data doesn't change
- **Annual Updates**: New seasons added as they become available
- **Metric Consistency**: Maintain consistent calculations across years
- **Documentation Updates**: Update documentation as metrics evolve

## 🔗 Integration with Agent System

The starter pack integrates with the **intelligent agent system** for enhanced learning:

### Learning Navigator Agent Integration
```python
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()

# Get personalized learning guidance
request = AnalyticsRequest(
    user_id='student_001',
    query='I want to learn college football analytics',
    query_type='learning',
    parameters={'current_notebook': '01_intro_to_data.ipynb'},
    context_hints={'skill_level': 'beginner'}
)

response = orchestrator.process_analytics_request(request)
# Returns: personalized learning path, notebook recommendations, concept explanations
```

### Role-Based Learning Experience
- **Analyst Role (50% tokens)**: Educational guidance and basic analytics
- **Data Scientist Role (75% tokens)**: Full access to advanced notebooks and techniques
- **Production Role (25% tokens)**: Quick reference for established analysts

### Smart Learning Features
- **Progressive Difficulty**: Automatic difficulty adjustment based on user progress
- **Context Hints**: Intelligent assistance based on current notebook
- **Skill Assessment**: Automatic evaluation and next-step recommendations
- **Resource Curation**: Personalized learning materials and external resources

## 🛠️ Development Environment

### Required Dependencies
```bash
# Core data analysis stack
pip install pandas numpy matplotlib seaborn scikit-learn jupyter

# Advanced statistical analysis
pip install scipy

# Optional for advanced visualizations
pip install plotly dash

# Verify installation
python -c "import pandas, numpy, matplotlib, seaborn; print('✅ Starter pack dependencies OK')"
```

### Jupyter Configuration
```bash
# Start with specific configuration for optimal experience
jupyter lab --NotebookApp.max_buffer_size=1073741824  # 1GB buffer

# Or create jupyter_lab_config.json for persistent settings
```

## 📊 Data Access Patterns

### Efficient Data Loading
```python
# Recommended pattern for large datasets
import pandas as pd

# Load specific years to manage memory
games_2023 = pd.read_csv('data/games.csv')
games_2023 = games_2023[games_2023['season'] == 2023]

# Use dtype optimization for better performance
dtypes = {
    'season': 'int16',
    'week': 'int8',
    'home_points': 'int16',
    'away_points': 'int16'
}
games = pd.read_csv('data/games.csv', dtype=dtypes)
```

### Common Analysis Patterns
```python
# Team-specific analysis
osu_games = games[
    (games['home_team'] == 'Ohio State') |
    (games['away_team'] == 'Ohio State')
]

# Conference analysis
big_ten_teams = pd.read_csv('data/teams.csv')
big_ten_teams = big_ten_teams[big_ten_teams['conference'] == 'Big Ten']

# Advanced metrics loading
adv_stats_2023 = pd.read_csv('data/advanced_season_stats/2023.csv')
```

## 🚚 Pathway to Advanced Analytics

### Bridge to Model Pack
1. **Complete Foundation**: Work through notebooks 00-07 for core concepts
2. **Advanced Techniques**: Notebooks 08-12 introduce opponent adjustments and efficiency
3. **Model Preparation**: Focus on notebooks 05 (prediction) and 09 (opponent adjustments)
4. **Feature Engineering**: Understanding of EPA and success rates transfers to ML features

### Key Learning Milestones
- **Notebook 01**: Basic data manipulation and exploration
- **Notebook 05**: First exposure to prediction concepts
- **Notebook 09**: Critical opponent adjustment understanding
- **Notebook 12**: Professional visualization and presentation

### Integration with Production Tools
- **CFBD API**: Understanding data structure enables effective API usage
- **Agent System**: Concepts transfer to intelligent analytics workflows
- **Model Pack**: Feature engineering skills directly applicable to ML

---

**Starter Pack Philosophy**: This directory provides a comprehensive educational foundation that balances accessibility with analytical rigor. The progressive curriculum enables users to develop from data novices to competent analysts, with real-world applicable skills that transfer directly to advanced modeling and research applications.

**Enhanced with AI**: Integration with the intelligent agent system provides personalized learning guidance, progress tracking, and seamless transition to advanced analytics and machine learning components.