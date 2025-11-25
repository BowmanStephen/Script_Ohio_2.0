# Consolidation Plan - TOON Format

This is the complete consolidation plan in TOON format for easy LLM consumption.

```toon
consolidation_plan:
  analysis_date: 2025-11-19
  status: Phase 1 Complete
  purpose: Identify unused patterns and consolidation opportunities
  
  actually_used[4	]{component	usage_level	used_in	status}:
    BaseAgent Framework	high	all weekly agents scripts/run_weekly_analysis.py scripts/generate_comprehensive_week13_analysis.py	critical
    WeeklyAnalysisOrchestrator	high	scripts/run_weekly_analysis.py	production
    Model Execution Engine	high	scripts/generate_comprehensive_week13_analysis.py	critical
    CFBD Integration	medium	scripts/cfbd_pull.py scripts/validate_cfbd_pipeline.py	critical
  
  barely_used[6	]{component	usage_level	used_in	not_used_in	recommendation}:
    ContextManager Role System	low	agents/analytics_orchestrator.py scripts/validate_cfbd_pipeline.py	generate_comprehensive_week13_analysis.py run_weekly_analysis.py	remove unless role filtering needed
    StateAwareAnalyticsSession	low	agents/analytics_orchestrator.py only	all production scripts	remove unless conversation history needed
    AnalyticsOrchestrator	low	scripts/validate_cfbd_pipeline.py only	weekly analysis scripts	remove or simplify
    WorkflowAutomatorAgent	zero	defined but never called	all production scripts	remove unless reusable workflows needed
    AsyncAgentOrchestrator	zero	defined but never used	all production code	remove unless async processing needed
    ToolLoader	minimal	inherited but rarely called	weekly agents do work directly	remove unless tools actually used
  
  actions_completed[6	]{action	status	file}:
    Add deprecation warnings	completed	agents/core/context_manager.py agents/state_aware_analytics_system.py agents/workflow_automator_agent.py agents/async_agent_framework.py
    Create simplified orchestrator	completed	agents/simplified_analytics_orchestrator.py
    Create orchestrator template	completed	agents/orchestrator_template.py
    Update validation script	completed	scripts/validate_cfbd_pipeline.py
    Create migration guide	completed	CONSOLIDATION_MIGRATION_GUIDE.md
    Create checklist	completed	CONSOLIDATION_CHECKLIST.md
  
  next_steps[4	]{phase	action	timeline}:
    Phase 2	Replace AnalyticsOrchestrator with simplified version	Week 2
    Phase 2	Remove ContextManager imports from production code	Week 2-3
    Phase 3	Remove deprecated files after 30-day period	Week 4
    Phase 3	Final validation and cleanup	Week 4
  
  metrics:
    current_complexity:
      orchestrators: 2
      context_systems: 1
      state_systems: 1
      workflow_systems: 1
      async_systems: 1
      total_patterns: 100
    after_consolidation:
      orchestrators: 1
      context_systems: 0
      state_systems: 0
      workflow_systems: 0
      async_systems: 0
      total_patterns: 20
      reduction_percent: 80
  
  files_created[5	]{file	purpose}:
    agents/simplified_analytics_orchestrator.py	Simplified orchestrator matching WeeklyAnalysisOrchestrator pattern
    agents/orchestrator_template.py	Template for creating new orchestrators
    CONSOLIDATION_CHECKLIST.md	Step-by-step consolidation plan
    CONSOLIDATION_MIGRATION_GUIDE.md	Migration paths for deprecated components
    CONSOLIDATION_SUMMARY.md	Execution summary and status
  
  files_deprecated[4	]{file	deprecation_date	removal_date}:
    agents/core/context_manager.py	2025-11-19	2025-12-19
    agents/state_aware_analytics_system.py	2025-11-19	2025-12-19
    agents/workflow_automator_agent.py	2025-11-19	2025-12-19
    agents/async_agent_framework.py	2025-11-19	2025-12-19
  
  key_insights[3]:
    - WeeklyAnalysisOrchestrator already implements the simplified pattern you need
    - Use it as the template for all future orchestrators
    - Direct agent instantiation and execute_task calls work fine without context/state complexity
```

