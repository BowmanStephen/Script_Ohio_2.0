#!/usr/bin/env python3
"""
Week 13 Intelligence Consolidation Agent

Intelligently consolidates and catalogs all Week 13 analysis assets including
predictions, comprehensive analysis, dashboards, and strategic recommendations.

This agent transforms 80+分散的 Week 13 files into an organized, accessible
intelligence system that provides unified access to all Week 13 insights.

Author: Claude Code Assistant
Created: 2025-11-20
Version: 1.0
"""

import json
import os
import time
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Import base agent framework
try:
    from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
except ImportError:
    # Try importing from current directory structure
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Week13Asset:
    """Represents a Week 13 asset with metadata"""
    file_path: str
    asset_type: str  # 'prediction', 'analysis', 'dashboard', 'report', 'data'
    file_size: int
    created_time: str
    modified_time: str
    description: str
    key_metrics: Dict[str, Any]
    quality_score: float

@dataclass
class ConsolidationSummary:
    """Summary of Week 13 consolidation results"""
    total_assets_found: int
    assets_by_type: Dict[str, int]
    total_games_analyzed: int
    model_performance: Dict[str, float]
    quality_metrics: Dict[str, float]
    consolidation_timestamp: str
    processing_time: float

class Week13ConsolidationAgent(BaseAgent):
    """
    Week 13 Intelligence Consolidation Agent

    Consolidates and catalogs all Week 13 analysis assets into an organized
    intelligence system with quality validation and smart organization.
    """

    def __init__(self, agent_id: str, tool_loader=None):
        super().__init__(
            agent_id=agent_id,
            name="Week 13 Intelligence Consolidation Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader
        )

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities for Week 13 asset consolidation"""
        return [
            AgentCapability(
                name="asset_discovery",
                description="Discover and catalog all Week 13 assets across the project",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["pandas", "pathlib", "json"],
                data_access=["predictions/week13/", "analysis/week13/", "data/week13/", "scripts/"],
                execution_time_estimate=3.0
            ),
            AgentCapability(
                name="quality_validation",
                description="Validate data quality and consistency across Week 13 assets",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["pandas", "json"],
                data_access=["predictions/week13/", "analysis/week13/"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="intelligent_organization",
                description="Organize assets by type, quality, and importance with smart categorization",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["pandas", "json", "pathlib"],
                data_access=["predictions/week13/", "analysis/week13/", "data/week13/"],
                execution_time_estimate=2.5
            ),
            AgentCapability(
                name="summary_generation",
                description="Generate comprehensive summaries and insights from consolidated data",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["pandas", "json"],
                data_access=["predictions/week13/", "analysis/week13/"],
                execution_time_estimate=1.5
            ),
            AgentCapability(
                name="full_consolidation",
                description="Perform complete Week 13 consolidation process including discovery, validation, organization, and summary",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["pandas", "pathlib", "json"],
                data_access=["predictions/week13/", "analysis/week13/", "data/week13/", "scripts/"],
                execution_time_estimate=9.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Week 13 consolidation actions"""
        start_time = time.time()

        try:
            if action == "asset_discovery":
                return self._discover_week13_assets(parameters, user_context)
            elif action == "quality_validation":
                return self._validate_asset_quality(parameters, user_context)
            elif action == "intelligent_organization":
                return self._organize_assets_intelligently(parameters, user_context)
            elif action == "summary_generation":
                return self._generate_consolidation_summary(parameters, user_context)
            elif action == "full_consolidation":
                return self._perform_full_consolidation(parameters, user_context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "execution_time": time.time() - start_time
            }

    def _discover_week13_assets(self, parameters: Dict[str, Any],
                              user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover all Week 13 assets across the project"""
        start_time = time.time()
        project_root = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")

        # Asset discovery patterns
        asset_patterns = {
            'predictions': [
                'predictions/week13/*.csv',
                'predictions/week13/*.json'
            ],
            'analysis': [
                'analysis/week13/*.json',
                'analysis/week13/*.md',
                'analysis/week13/*.html',
                'analysis/week13/*.csv'
            ],
            'data': [
                'data/week13/**/*.csv',
                'model_pack/*week13*.csv'
            ],
            'scripts': [
                'scripts/*week13*.py'
            ],
            'reports': [
                'reports/*week13*.*',
                'validation/week13/*.*'
            ]
        }

        discovered_assets = []

        for asset_type, patterns in asset_patterns.items():
            for pattern in patterns:
                try:
                    for file_path in project_root.glob(pattern):
                        if file_path.is_file():
                            asset = self._create_asset_metadata(file_path, asset_type)
                            discovered_assets.append(asset)
                except Exception as e:
                    logger.warning(f"Error discovering assets with pattern {pattern}: {e}")

        # Sort by creation time (newest first)
        discovered_assets.sort(key=lambda x: x.created_time, reverse=True)

        execution_time = time.time() - start_time
        logger.info(f"Discovered {len(discovered_assets)} Week 13 assets in {execution_time:.2f}s")

        return {
            "status": "success",
            "data": {
                "discovered_assets": [asdict(asset) for asset in discovered_assets],
                "total_count": len(discovered_assets),
                "discovery_time": execution_time,
                "asset_types": list(set(asset.asset_type for asset in discovered_assets))
            },
            "execution_time": execution_time
        }

    def _create_asset_metadata(self, file_path: Path, asset_type: str) -> Week13Asset:
        """Create metadata for a discovered asset"""
        try:
            stat = file_path.stat()

            # Extract key metrics based on file type
            key_metrics = {}
            quality_score = 0.5  # Default score

            if file_path.suffix == '.json':
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        key_metrics = self._extract_json_metrics(data)
                        quality_score = self._assess_json_quality(data)
                except:
                    pass

            elif file_path.suffix == '.csv':
                try:
                    df = pd.read_csv(file_path)
                    key_metrics = self._extract_csv_metrics(df)
                    quality_score = self._assess_csv_quality(df)
                except:
                    pass

            # Generate description
            description = self._generate_asset_description(file_path, asset_type, key_metrics)

            return Week13Asset(
                file_path=str(file_path.relative_to(Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"))),
                asset_type=asset_type,
                file_size=stat.st_size,
                created_time=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified_time=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                description=description,
                key_metrics=key_metrics,
                quality_score=quality_score
            )

        except Exception as e:
            logger.warning(f"Error creating metadata for {file_path}: {e}")
            return Week13Asset(
                file_path=str(file_path.relative_to(Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"))),
                asset_type=asset_type,
                file_size=0,
                created_time=datetime.now().isoformat(),
                modified_time=datetime.now().isoformat(),
                description=f"Week 13 {asset_type} file",
                key_metrics={},
                quality_score=0.0
            )

    def _extract_json_metrics(self, data: Dict) -> Dict[str, Any]:
        """Extract key metrics from JSON data"""
        metrics = {}

        if isinstance(data, dict):
            # Look for common Week 13 metrics
            if 'total_games' in data:
                metrics['total_games'] = data['total_games']
            if 'models_used' in data:
                metrics['models_used'] = data['models_used']
            if 'analysis_metadata' in data:
                metadata = data['analysis_metadata']
                if 'total_games_analyzed' in metadata:
                    metrics['games_analyzed'] = metadata['total_games_analyzed']
                if 'week' in metadata:
                    metrics['week'] = metadata['week']
                if 'season' in metadata:
                    metrics['season'] = metadata['season']

            # Check for team rankings
            if 'team_rankings' in data and isinstance(data['team_rankings'], list):
                metrics['ranked_teams'] = len(data['team_rankings'])

            # Check for predictions
            if 'predictions' in data and isinstance(data['predictions'], list):
                metrics['predictions_count'] = len(data['predictions'])

        return metrics

    def _extract_csv_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract key metrics from CSV data"""
        metrics = {
            'rows': len(df),
            'columns': len(df.columns),
            'file_size_kb': len(df.to_csv().encode()) / 1024
        }

        # Look for common Week 13 columns
        if 'home_team' in df.columns:
            metrics['has_teams'] = True
            metrics['unique_home_teams'] = df['home_team'].nunique()

        if 'prediction' in df.columns or 'predicted_home_win' in df.columns:
            metrics['has_predictions'] = True

        if 'confidence' in df.columns:
            metrics['has_confidence'] = True
            metrics['avg_confidence'] = df['confidence'].mean() if 'confidence' in df.columns else None

        return metrics

    def _assess_json_quality(self, data: Dict) -> float:
        """Assess quality of JSON data"""
        quality_score = 0.5

        try:
            if isinstance(data, dict):
                # Check for required fields
                required_fields = ['analysis_metadata', 'total_games', 'models_used']
                fields_present = sum(1 for field in required_fields if field in data)
                quality_score += (fields_present / len(required_fields)) * 0.3

                # Check for structured data
                if 'team_rankings' in data and isinstance(data['team_rankings'], list):
                    quality_score += 0.1

                # Check for comprehensive analysis
                if 'analysis_components' in data:
                    quality_score += 0.1

        except:
            quality_score = 0.0

        return min(1.0, quality_score)

    def _assess_csv_quality(self, df: pd.DataFrame) -> float:
        """Assess quality of CSV data"""
        quality_score = 0.5

        try:
            # Check for minimum data
            if len(df) > 0:
                quality_score += 0.2

            # Check for required columns
            required_columns = ['home_team', 'away_team']
            columns_present = sum(1 for col in required_columns if col in df.columns)
            if columns_present > 0:
                quality_score += (columns_present / len(required_columns)) * 0.2

            # Check for data completeness
            if len(df) > 0:
                completeness = 1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))
                quality_score += completeness * 0.1

        except:
            quality_score = 0.0

        return min(1.0, quality_score)

    def _generate_asset_description(self, file_path: Path, asset_type: str,
                                   metrics: Dict[str, Any]) -> str:
        """Generate description for asset based on filename and metrics"""
        filename = file_path.name

        # Base description by type
        descriptions = {
            'predictions': "Week 13 predictions and analysis",
            'analysis': "Week 13 comprehensive analysis report",
            'data': "Week 13 dataset and features",
            'scripts': "Week 13 processing and analysis script",
            'reports': "Week 13 validation and reporting"
        }

        base_desc = descriptions.get(asset_type, f"Week 13 {asset_type}")

        # Add specific details from filename
        if 'comprehensive' in filename.lower():
            base_desc += " - Comprehensive coverage"
        elif 'enhanced' in filename.lower():
            base_desc += " - Enhanced analysis"
        elif 'summary' in filename.lower():
            base_desc += " - Executive summary"
        elif 'dashboard' in filename.lower():
            base_desc += " - Interactive dashboard"
        elif 'validation' in filename.lower():
            base_desc += " - Quality validation"

        # Add metric details
        if metrics.get('total_games') or metrics.get('games_analyzed'):
            games = metrics.get('total_games') or metrics.get('games_analyzed')
            base_desc += f" ({games} games)"

        if metrics.get('models_used'):
            models = metrics.get('models_used')
            base_desc += f" using {models} models"

        return base_desc

    def _validate_asset_quality(self, parameters: Dict[str, Any],
                               user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data quality across all Week 13 assets"""
        start_time = time.time()

        # Get discovered assets (either from parameters or run discovery)
        if 'discovered_assets' in parameters:
            assets_data = parameters['discovered_assets']
            assets = [Week13Asset(**asset) for asset in assets_data]
        else:
            discovery_result = self._discover_week13_assets({}, user_context)
            assets = [Week13Asset(**asset) for asset in discovery_result['data']['discovered_assets']]

        quality_report = {
            'total_assets': len(assets),
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'quality_issues': [],
            'recommendations': []
        }

        # Analyze quality distribution
        for asset in assets:
            if asset.quality_score >= 0.8:
                quality_report['quality_distribution']['high'] += 1
            elif asset.quality_score >= 0.5:
                quality_report['quality_distribution']['medium'] += 1
            else:
                quality_report['quality_distribution']['low'] += 1
                quality_report['quality_issues'].append({
                    'file': asset.file_path,
                    'issue': f"Low quality score: {asset.quality_score:.2f}",
                    'recommendation': "Review and enhance data quality"
                })

        # Generate recommendations
        high_quality_pct = quality_report['quality_distribution']['high'] / len(assets) * 100
        if high_quality_pct < 70:
            quality_report['recommendations'].append(
                "Consider improving data quality standards across assets"
            )

        if quality_report['quality_distribution']['low'] > 5:
            quality_report['recommendations'].append(
                "Address low-quality assets to improve overall system reliability"
            )

        execution_time = time.time() - start_time
        logger.info(f"Quality validation completed in {execution_time:.2f}s")

        return {
            "status": "success",
            "data": quality_report,
            "execution_time": execution_time
        }

    def _organize_assets_intelligently(self, parameters: Dict[str, Any],
                                     user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Organize assets by type, quality, and importance"""
        start_time = time.time()

        # Get discovered assets
        if 'discovered_assets' in parameters:
            assets_data = parameters['discovered_assets']
            assets = [Week13Asset(**asset) for asset in assets_data]
        else:
            discovery_result = self._discover_week13_assets({}, user_context)
            assets = [Week13Asset(**asset) for asset in discovery_result['data']['discovered_assets']]

        # Organize by multiple dimensions
        organization = {
            'by_type': {},
            'by_quality': {'high': [], 'medium': [], 'low': []},
            'by_importance': {'critical': [], 'important': [], 'supplementary': []},
            'recommendations': {}
        }

        for asset in assets:
            # Organize by type
            if asset.asset_type not in organization['by_type']:
                organization['by_type'][asset.asset_type] = []
            organization['by_type'][asset.asset_type].append(asdict(asset))

            # Organize by quality
            if asset.quality_score >= 0.8:
                organization['by_quality']['high'].append(asdict(asset))
            elif asset.quality_score >= 0.5:
                organization['by_quality']['medium'].append(asdict(asset))
            else:
                organization['by_quality']['low'].append(asdict(asset))

            # Determine importance based on content and quality
            importance = self._assess_asset_importance(asset)
            organization['by_importance'][importance].append(asdict(asset))

        # Generate recommendations
        organization['recommendations'] = {
            'priority_assets': [asset['file_path'] for asset in organization['by_importance']['critical'][:5]],
            'quality_improvements': [asset['file_path'] for asset in organization['by_quality']['low']],
            'consolidation_opportunities': self._identify_consolidation_opportunities(organization['by_type'])
        }

        execution_time = time.time() - start_time
        logger.info(f"Asset organization completed in {execution_time:.2f}s")

        return {
            "status": "success",
            "data": organization,
            "execution_time": execution_time
        }

    def _assess_asset_importance(self, asset: Week13Asset) -> str:
        """Assess the importance level of an asset"""
        filename = Path(asset.file_path).name.lower()

        # Critical assets
        critical_keywords = ['comprehensive', 'master', 'summary', 'ensemble', 'unified']
        if any(keyword in filename for keyword in critical_keywords):
            return 'critical'

        # Important assets
        important_keywords = ['predictions', 'analysis', 'dashboard', 'report']
        if any(keyword in filename for keyword in important_keywords):
            return 'important'

        # Supplementary assets
        return 'supplementary'

    def _identify_consolidation_opportunities(self, by_type: Dict) -> List[str]:
        """Identify opportunities for asset consolidation"""
        opportunities = []

        # Look for similar files that could be consolidated
        for asset_type, assets in by_type.items():
            if len(assets) > 5:  # Many files of same type
                opportunities.append(f"Consider consolidating {len(assets)} {asset_type} files")

        # Look for duplicate functionality
        prediction_files = [asset for asset in by_type.get('predictions', [])
                          if 'prediction' in Path(asset['file_path']).name.lower()]
        if len(prediction_files) > 3:
            opportunities.append("Multiple prediction files could be unified")

        return opportunities

    def _generate_consolidation_summary(self, parameters: Dict[str, Any],
                                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive consolidation summary"""
        start_time = time.time()

        # Get organized assets
        if 'organized_assets' in parameters:
            organization = parameters['organized_assets']
        else:
            organization_result = self._organize_assets_intelligently({}, user_context)
            organization = organization_result['data']

        # Create comprehensive summary
        summary = {
            'overview': {
                'total_assets': sum(len(assets) for assets in organization['by_type'].values()),
                'asset_types': len(organization['by_type']),
                'high_quality_assets': len(organization['by_quality']['high']),
                'critical_assets': len(organization['by_importance']['critical'])
            },
            'key_insights': self._extract_key_insights(organization),
            'recommendations': organization['recommendations'],
            'next_steps': self._generate_next_steps(organization),
            'quality_metrics': self._calculate_quality_metrics(organization)
        }

        execution_time = time.time() - start_time
        logger.info(f"Consolidation summary generated in {execution_time:.2f}s")

        return {
            "status": "success",
            "data": summary,
            "execution_time": execution_time
        }

    def _extract_key_insights(self, organization: Dict) -> List[str]:
        """Extract key insights from organized assets"""
        insights = []

        total_assets = sum(len(assets) for assets in organization['by_type'].values())
        insights.append(f"Discovered {total_assets} Week 13 assets across {len(organization['by_type'])} categories")

        high_quality_pct = len(organization['by_quality']['high']) / total_assets * 100
        insights.append(f"{high_quality_pct:.1f}% of assets meet high quality standards")

        if len(organization['by_importance']['critical']) > 0:
            insights.append(f"Identified {len(organization['by_importance']['critical'])} critical assets for immediate attention")

        # Most valuable asset type
        most_valuable_type = max(organization['by_type'].items(),
                               key=lambda x: len(x[1]))[0]
        insights.append(f"Largest asset category: {most_valuable_type} with {len(organization['by_type'][most_valuable_type])} files")

        return insights

    def _generate_next_steps(self, organization: Dict) -> List[str]:
        """Generate recommended next steps"""
        steps = []

        steps.append("Review critical assets for immediate integration")

        if len(organization['by_quality']['low']) > 0:
            steps.append("Improve quality of low-scoring assets")

        steps.append("Create unified dashboard from top assets")
        steps.append("Document consolidation process for future weeks")

        consolidation_ops = organization['recommendations'].get('consolidation_opportunities', [])
        if consolidation_ops:
            steps.append("Execute consolidation opportunities to reduce redundancy")

        return steps

    def _calculate_quality_metrics(self, organization: Dict) -> Dict[str, float]:
        """Calculate overall quality metrics"""
        total_assets = sum(len(assets) for assets in organization['by_type'].values())

        metrics = {
            'overall_quality_score': 0.0,
            'high_quality_percentage': 0.0,
            'asset_coverage_score': 0.0,
            'organization_efficiency': 0.0
        }

        if total_assets > 0:
            # Overall quality (weighted average)
            high_weight = len(organization['by_quality']['high']) * 1.0
            medium_weight = len(organization['by_quality']['medium']) * 0.5
            low_weight = len(organization['by_quality']['low']) * 0.1

            metrics['overall_quality_score'] = (high_weight + medium_weight + low_weight) / total_assets
            metrics['high_quality_percentage'] = len(organization['by_quality']['high']) / total_assets * 100

            # Asset coverage (diversity of asset types)
            metrics['asset_coverage_score'] = len(organization['by_type']) / 5.0 * 100  # 5 expected types

            # Organization efficiency (critical assets identified)
            critical_percentage = len(organization['by_importance']['critical']) / total_assets
            metrics['organization_efficiency'] = critical_percentage * 100

        return metrics

    def _perform_full_consolidation(self, parameters: Dict[str, Any],
                                  user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform complete Week 13 consolidation process"""
        start_time = time.time()

        logger.info("Starting full Week 13 consolidation process")

        # Step 1: Asset Discovery
        discovery_result = self._discover_week13_assets({}, user_context)
        discovered_assets = discovery_result['data']['discovered_assets']

        # Step 2: Quality Validation
        quality_result = self._validate_asset_quality(
            {'discovered_assets': discovered_assets}, user_context
        )

        # Step 3: Intelligent Organization
        organization_result = self._organize_assets_intelligently(
            {'discovered_assets': discovered_assets}, user_context
        )

        # Step 4: Summary Generation
        summary_result = self._generate_consolidation_summary(
            {'organized_assets': organization_result['data']}, user_context
        )

        # Create final consolidation report
        consolidation_report = {
            'consolidation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_processing_time': time.time() - start_time,
                'agent_id': self.agent_id,
                'week': 13,
                'season': 2025
            },
            'asset_discovery': discovery_result['data'],
            'quality_validation': quality_result['data'],
            'asset_organization': organization_result['data'],
            'executive_summary': summary_result['data'],
            'file_manifest': discovered_assets
        }

        # Save consolidation report
        output_path = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/analysis/week13/week13_intelligence_consolidation.json"

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(consolidation_report, f, indent=2)

        logger.info(f"Full consolidation completed and saved to {output_path}")

        return {
            "status": "success",
            "data": {
                "consolidation_report": consolidation_report,
                "output_file": output_path,
                "summary": {
                    "total_assets": len(discovered_assets),
                    "processing_time": time.time() - start_time,
                    "high_quality_assets": len(organization_result['data']['by_quality']['high']),
                    "critical_assets": len(organization_result['data']['by_importance']['critical'])
                }
            },
            "execution_time": time.time() - start_time
        }

# Register the agent with the factory
if __name__ == "__main__":
    try:
        from agents.core.agent_framework import AgentFactory
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent))
        from core.agent_framework import AgentFactory

    # Register the Week 13 consolidation agent
    factory = AgentFactory()
    factory.register_agent_class(Week13ConsolidationAgent, "week13_consolidation")

    # Test the agent
    agent = factory.create_agent("week13_consolidation", "week13_consolidation_001")

    # Create a proper agent request
    from core.agent_framework import AgentRequest
    import time

    request = AgentRequest(
        request_id="test_001",
        agent_type="week13_consolidation",
        action="full_consolidation",
        parameters={},
        user_context={"user_id": "test_user"},
        timestamp=time.time(),
        priority=2
    )

    # Test full consolidation
    result = agent.execute_request(request, PermissionLevel.ADMIN)

    print("✅ Week 13 Consolidation Agent Test Results:")
    print(f"Status: {result.status}")
    if result.status.value == 'success':
        summary = result.result['summary']
        print(f"Total Assets: {summary['total_assets']}")
        print(f"Processing Time: {summary['processing_time']:.2f}s")
        print(f"Output File: {result.result['output_file']}")
    else:
        print(f"Error: {result.error_message}")

    print("🎯 Week 13 Intelligence Consolidation Agent registered successfully!")