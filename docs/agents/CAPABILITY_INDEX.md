# Agent Capability Index

Alphabetical list of all capabilities across the agent fleet.

| Capability | Description | Agent | Permission |
| --- | --- | --- | --- |
| `analyze_matchups` | Analyze Week 12 matchups and generate insights. | [Week12MatchupAnalysis Agent](week12_matchup_analysis.md) | READ_EXECUTE_WRITE |
| `analyze_matchups` | Analyze Week 13 matchups and generate insights. | [Week 13 Matchup Analysis Agent](weekly_matchup_analysis.md) | READ_EXECUTE_WRITE |
| `batch_predictions` | Process multiple predictions in batch | [Model Execution Engine](model_engine.md) | READ_EXECUTE_WRITE |
| `benchmark_performance` | Run comprehensive performance benchmarks | [Performance Monitor](performance_monitor.md) | READ_EXECUTE |
| `betting_opportunity_analysis` | Comprehensive betting analysis with confidence intervals | [Model Execution Engine](model_engine.md) | READ_EXECUTE_WRITE |
| `calculate_confidence` | Calculate confidence metrics for predictions | [Week 13 Prediction Generation Agent](weekly_prediction_generation.md) | READ_EXECUTE_WRITE |
| `calculate_confidence` | Calculate confidence metrics for predictions | [Week12PredictionGeneration Agent](week12_prediction_generation.md) | READ_EXECUTE_WRITE |
| `cfbd_health_check` | Summarize CFBD client telemetry and error rates | [Quality Assurance Agent](quality_assurance.md) | READ_EXECUTE |
| `cfbd_real_time_analysis` | Pull live CFBD REST/NEXT data and align it with the 86-feature schema. | [Insight Generator](insight_generator.md) | READ_EXECUTE_WRITE |
| `cfbd_recent_events` | Return the latest telemetry events for inspection | [Quality Assurance Agent](quality_assurance.md) | READ_EXECUTE |
| `check_compatibility` | Assess compatibility between enhanced data and models. | [Week 13 Model Validation Agent](weekly_model_validation.md) | READ_EXECUTE_WRITE |
| `check_compatibility` | Assess compatibility between enhanced data and models. | [Week12ModelValidation Agent](week12_model_validation.md) | READ_EXECUTE_WRITE |
| `clarification_handling` | Handle clarification requests and ambiguous queries | [Conversational AI](conversational_ai.md) | READ_EXECUTE |
| `classify_root_files` | Identify and categorize misplaced files in root directory | [File Organization Agent](file_organization.md) | READ_ONLY |
| `comparative_analysis` | Compare teams, players, and seasons using advanced metrics | [Insight Generator](insight_generator.md) | READ_EXECUTE_WRITE |
| `conversation_management` | Manage multi-turn conversations with context tracking | [Conversational AI](conversational_ai.md) | READ_EXECUTE_WRITE |
| `coordinate_validation` | Coordinate validation phases and sub-agent execution | [Validation Orchestrator](validation_orchestrator.md) | ADMIN |
| `create_ensemble` | Create ensemble predictions from model outputs | [Week 13 Prediction Generation Agent](weekly_prediction_generation.md) | READ_EXECUTE_WRITE |
| `create_ensemble` | Create ensemble predictions from model outputs | [Week12PredictionGeneration Agent](week12_prediction_generation.md) | READ_EXECUTE_WRITE |
| `create_missing_directories` | Create missing directory structure per CLAUDE.md | [File Organization Agent](file_organization.md) | READ_EXECUTE_WRITE |
| `create_visualizations` | Generate sophisticated data visualizations and charts | [Insight Generator](insight_generator.md) | READ_EXECUTE_WRITE |
| `detect_performance_bottlenecks` | Identify system performance bottlenecks | [Performance Monitor](performance_monitor.md) | READ_EXECUTE |
| `discover_system` | Discover and analyze activation fix system architecture | [Validation Orchestrator](validation_orchestrator.md) | READ_EXECUTE |
| `document_system` | Create comprehensive documentation and educational content | [Validation Orchestrator](validation_orchestrator.md) | READ_EXECUTE_WRITE |
| `enhance_mock_data` | Enhance mock datasets with Week 12 patterns. | [Week 12 Mock Enhancement Agent](week12_mock_enhancement.md) | READ_EXECUTE_WRITE |
| `generate_analysis` | Generate advanced analytics insights and statistical analysis | [Insight Generator](insight_generator.md) | READ_EXECUTE_WRITE |
| `generate_infographic` | Generate interactive infographic components for documentation and reports | [Insight Generator](insight_generator.md) | READ_EXECUTE_WRITE |
| `generate_optimization_recommendations` | Generate performance optimization recommendations | [Performance Monitor](performance_monitor.md) | READ_EXECUTE_WRITE |
| `generate_predictions` | Generate predictions using validated ML models | [Week 13 Prediction Generation Agent](weekly_prediction_generation.md) | READ_EXECUTE_WRITE |
| `generate_predictions` | Generate predictions for Week 13 | [Week 13 Analysis Orchestrator](weekly_analysis_orchestrator.md) | READ_EXECUTE_WRITE |
| `generate_predictions` | Generate predictions using validated ML models | [Week12PredictionGeneration Agent](week12_prediction_generation.md) | READ_EXECUTE_WRITE |
| `generate_validation_report` | Create comprehensive validation and organization report | [System Validation Agent](validation_agent.md) | READ_ONLY |
| `generate_weekly_report` | Generate comprehensive weekly report with visualizations | [Report Generator Agent](report_generator.md) | READ_EXECUTE_WRITE |
| `graphql_trend_scan` | Analyze recruiting/talent trends using GraphQL API (requires Patreon Tier 3+ access). | [Insight Generator](insight_generator.md) | READ_EXECUTE_WRITE |
| `guide_learning_path` | Guide users through starter pack notebooks | [Learning Navigator](learning_navigator.md) | READ_EXECUTE |
| `intent_recognition` | Identify user intent from conversational queries | [Conversational AI](conversational_ai.md) | READ_ONLY |
| `kelly_criterion_analysis` | Calculate optimal bet sizes using Kelly Criterion | [Model Execution Engine](model_engine.md) | READ_EXECUTE_WRITE |
| `live_scoreboard` | Return the latest live scoreboard events (REST-based) | [CFBD Integration Agent](cfbd_integration.md) | READ_EXECUTE |
| `model_comparison` | Compare predictions across multiple models | [Model Execution Engine](model_engine.md) | READ_EXECUTE_WRITE |
| `model_performance_analysis` | Analyze model performance and metrics | [Model Execution Engine](model_engine.md) | READ_EXECUTE |
| `monitor_system_performance` | Real-time system performance monitoring | [Performance Monitor](performance_monitor.md) | READ_EXECUTE |
| `natural_language_processing` | Process and understand natural language queries with context awareness | [Conversational AI](conversational_ai.md) | READ_EXECUTE |
| `organize_into_directories` | Move files to appropriate subdirectories with proper naming | [File Organization Agent](file_organization.md) | READ_EXECUTE_WRITE |
| `performance_test` | Benchmark model performance metrics. | [Week 13 Model Validation Agent](weekly_model_validation.md) | READ_EXECUTE_WRITE |
| `performance_test` | Benchmark model performance metrics. | [Week12ModelValidation Agent](week12_model_validation.md) | READ_EXECUTE_WRITE |
| `predict_game_outcome` | Predict game outcomes using trained ML models | [Model Execution Engine](model_engine.md) | READ_EXECUTE_WRITE |
| `quality_assurance` | Execute quality assurance testing and grading | [Validation Orchestrator](validation_orchestrator.md) | READ_EXECUTE |
| `query_expansion` | Intelligently expand and reformulate user queries | [Conversational AI](conversational_ai.md) | READ_EXECUTE |
| `recommend_content` | Recommend content based on user skill level | [Learning Navigator](learning_navigator.md) | READ_EXECUTE |
| `run_weekly_analysis` | Run complete Week 13 analysis pipeline | [Week 13 Analysis Orchestrator](weekly_analysis_orchestrator.md) | ADMIN |
| `statistical_analysis` | Perform comprehensive statistical analysis and hypothesis testing | [Insight Generator](insight_generator.md) | READ_EXECUTE_WRITE |
| `synthesize_results` | Synthesize all findings and create final recommendations | [Validation Orchestrator](validation_orchestrator.md) | READ_EXECUTE_WRITE |
| `team_snapshot` | Return normalized CFBD snapshot for a single team | [CFBD Integration Agent](cfbd_integration.md) | READ_EXECUTE |
| `trend_analysis` | Analyze temporal trends and patterns in college football data | [Insight Generator](insight_generator.md) | READ_EXECUTE_WRITE |
| `update_gitignore` | Update .gitignore with new exclusions for organized files | [System Validation Agent](validation_agent.md) | READ_EXECUTE_WRITE |
| `validate_comprehensive` | Execute comprehensive validation across all components | [Validation Orchestrator](validation_orchestrator.md) | READ_EXECUTE |
| `validate_file_moves` | Verify all files moved correctly and exist in destinations | [System Validation Agent](validation_agent.md) | READ_ONLY |
| `validate_import_integrity` | Check Python imports still work after file reorganization | [System Validation Agent](validation_agent.md) | READ_EXECUTE |
| `validate_models` | Run validation suite across Week 13 ML models. | [Week 13 Model Validation Agent](weekly_model_validation.md) | READ_EXECUTE_WRITE |
| `validate_models` | Run validation suite across Week 12 ML models. | [Week12ModelValidation Agent](week12_model_validation.md) | READ_EXECUTE_WRITE |
| `validate_models` | Validate models for Week 13 | [Week 13 Analysis Orchestrator](weekly_analysis_orchestrator.md) | READ_EXECUTE_WRITE |
| `value_betting_detection` | Identify value betting opportunities using 86-feature pipeline | [Model Execution Engine](model_engine.md) | READ_EXECUTE_WRITE |
