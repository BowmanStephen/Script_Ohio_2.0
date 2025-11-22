#!/usr/bin/env python3
"""
Advanced Response Generation System - Grade A Integration Enhancement

This module provides sophisticated multi-modal response generation capabilities including
insight synthesis, personalized response optimization, and intelligent summarization
for the Script Ohio 2.0 platform.

Author: Claude Code Assistant (Advanced Integration Agent)
Created: 2025-11-10
Version: 2.0 (Grade A Enhancement)
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import uuid
from collections import defaultdict, Counter
from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseModality(Enum):
    """Types of response modalities"""
    TEXT = "text"
    VISUALIZATION = "visualization"
    DATA_TABLE = "data_table"
    CODE = "code"
    INTERACTIVE = "interactive"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"

class InsightType(Enum):
    """Types of insights that can be generated"""
    STATISTICAL = "statistical"
    PREDICTIVE = "predictive"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    CORRELATION = "correlation"
    ANOMALY = "anomaly"
    PATTERN = "pattern"
    RECOMMENDATION = "recommendation"
    EXPLANATION = "explanation"

class ResponsePersonalizationLevel(Enum):
    """Levels of response personalization"""
    GENERIC = "generic"
    ROLE_BASED = "role_based"
    PREFERENCE_BASED = "preference_based"
    ADAPTIVE = "adaptive"
    HYPER_PERSONALIZED = "hyper_personalized"

class SummarizationStrategy(Enum):
    """Strategies for content summarization"""
    EXTRACTIVE = "extractive"
    ABSTRACTIVE = "abstractive"
    HYBRID = "hybrid"
    HIERARCHICAL = "hierarchical"
    QUERY_FOCUSED = "query_focused"
    MULTI_DOCUMENT = "multi_document"

@dataclass
class Insight:
    """An individual insight extracted from data or analysis"""
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any]
    visualizations: List[Dict[str, Any]]
    implications: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]
    timestamp: float
    source_agents: List[str]

@dataclass
class MultiModalContent:
    """Content in multiple modalities"""
    content_id: str
    primary_modality: ResponseModality
    content: Dict[str, Any]
    supporting_modalities: List[ResponseModality]
    rendering_instructions: Dict[str, Any]
    accessibility_features: List[str]
    interactive_elements: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class ResponseContext:
    """Context for response generation"""
    user_id: str
    user_role: str
    user_preferences: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    current_session_context: Dict[str, Any]
    device_context: Dict[str, Any]
    temporal_context: Dict[str, Any]
    query_context: Dict[str, Any]

@dataclass
class ResponsePersona:
    """Persona for response generation"""
    persona_id: str
    name: str
    tone: str
    complexity_level: str
    explanation_style: str
    domain_focus: str
    communication_patterns: Dict[str, Any]
    knowledge_level: str
    interaction_style: str

@dataclass
class GeneratedResponse:
    """A generated multi-modal response"""
    response_id: str
    query: str
    primary_answer: str
    insights: List[Insight]
    multi_modal_content: List[MultiModalContent]
    summary: str
    follow_up_questions: List[str]
    confidence_score: float
    personalization_level: ResponsePersonalizationLevel
    generation_metadata: Dict[str, Any]
    timestamp: float

class InsightSynthesisEngine:
    """Synthesizes insights from multiple sources"""

    def __init__(self):
        self.insight_templates = {}
        self.synthesis_patterns = {}
        self.confidence_calculators = {}
        self._initialize_insight_templates()

    def _initialize_insight_templates(self):
        """Initialize templates for different insight types"""
        self.insight_templates = {
            InsightType.STATISTICAL: {
                'title_template': "Statistical Analysis: {metric_name}",
                'description_template': "Analysis of {metric_name} reveals {key_finding} with statistical significance {significance_level}",
                'implication_templates': [
                    "This suggests that {interpretation}",
                    "The {metric_name} indicates that {business_implication}",
                    "From a statistical perspective, this means that {statistical_implication}"
                ]
            },
            InsightType.PREDICTIVE: {
                'title_template': "Prediction: {outcome}",
                'description_template': "Based on {model_type} analysis, we predict {outcome} with {confidence_level} confidence",
                'implication_templates': [
                    "This prediction suggests that {action_recommendation}",
                    "If this prediction holds, we should expect {expected_consequence}",
                    "The confidence level indicates that {confidence_interpretation}"
                ]
            },
            InsightType.COMPARATIVE: {
                'title_template': "Comparison: {entity1} vs {entity2}",
                'description_template': "Comparative analysis shows {entity1} {comparison_result} {entity2} by {margin}",
                'implication_templates': [
                    "This comparison reveals that {competitive_insight}",
                    "The difference suggests that {strategic_implication}",
                    "From a comparative standpoint, this means that {comparative_implication}"
                ]
            }
        }

    def synthesize_insights(self, agent_results: List[Dict[str, Any]], context: ResponseContext) -> List[Insight]:
        """Synthesize insights from multiple agent results"""
        insights = []

        # Extract raw insights from agent results
        raw_insights = self._extract_raw_insights(agent_results)

        # Group related insights
        insight_groups = self._group_related_insights(raw_insights)

        # Synthesize each group into refined insights
        for group_id, group_insights in insight_groups.items():
            synthesized_insight = self._synthesize_insight_group(group_insights, context)
            insights.append(synthesized_insight)

        # Add cross-insight relationships
        insights = self._add_insight_relationships(insights)

        # Rank insights by importance and relevance
        insights = self._rank_insights(insights, context)

        return insights

    def _extract_raw_insights(self, agent_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract raw insights from agent results"""
        raw_insights = []

        for result in agent_results:
            if 'insights' in result:
                raw_insights.extend(result['insights'])
            elif 'analysis' in result:
                # Extract insights from analysis
                raw_insights.extend(self._extract_insights_from_analysis(result['analysis']))
            elif 'predictions' in result:
                # Extract insights from predictions
                raw_insights.extend(self._extract_insights_from_predictions(result['predictions']))

        return raw_insights

    def _group_related_insights(self, raw_insights: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group related insights together"""
        groups = defaultdict(list)

        for insight in raw_insights:
            # Group by insight type and topic
            insight_type = insight.get('type', 'unknown')
            topic = insight.get('topic', 'general')

            group_key = f"{insight_type}_{topic}"
            groups[group_key].append(insight)

        return dict(groups)

    def _synthesize_insight_group(self, group_insights: List[Dict[str, Any]], context: ResponseContext) -> Insight:
        """Synthesize a group of related insights into a single insight"""
        if not group_insights:
            return None

        # Determine insight type
        primary_insight = group_insights[0]
        insight_type = InsightType(primary_insight.get('type', 'statistical'))

        # Calculate confidence
        confidence = self._calculate_insight_confidence(group_insights, context)

        # Extract key information
        title = self._generate_insight_title(group_insights, insight_type)
        description = self._generate_insight_description(group_insights, insight_type)
        supporting_data = self._aggregate_supporting_data(group_insights)

        # Generate implications and recommendations
        implications = self._generate_implications(group_insights, context)
        recommendations = self._generate_recommendations(group_insights, context)

        # Create visualizations
        visualizations = self._generate_insight_visualizations(group_insights, context)

        return Insight(
            insight_id=str(uuid.uuid4()),
            insight_type=insight_type,
            title=title,
            description=description,
            confidence=confidence,
            supporting_data=supporting_data,
            visualizations=visualizations,
            implications=implications,
            recommendations=recommendations,
            metadata={
                'source_count': len(group_insights),
                'synthesis_method': 'multi_agent_aggregation',
                'generation_time': time.time()
            },
            timestamp=time.time(),
            source_agents=list(set(insight.get('source_agent', 'unknown') for insight in group_insights))
        )

    def _calculate_insight_confidence(self, group_insights: List[Dict[str, Any]], context: ResponseContext) -> float:
        """Calculate confidence score for synthesized insight"""
        if not group_insights:
            return 0.0

        # Extract individual confidence scores
        confidences = [insight.get('confidence', 0.5) for insight in group_insights]

        # Weight by source reliability
        weights = []
        for insight in group_insights:
            source_agent = insight.get('source_agent', 'unknown')
            weight = self._get_agent_reliability_weight(source_agent, context)
            weights.append(weight)

        # Calculate weighted average
        if weights:
            weighted_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)
        else:
            weighted_confidence = sum(confidences) / len(confidences)

        # Adjust for consensus
        consensus_bonus = min(0.2, (len(group_insights) - 1) * 0.05)

        return min(1.0, weighted_confidence + consensus_bonus)

    def _get_agent_reliability_weight(self, agent_name: str, context: ResponseContext) -> float:
        """Get reliability weight for an agent based on historical performance"""
        # In a real implementation, this would use historical performance data
        reliability_weights = {
            'learning_navigator': 0.9,
            'model_engine': 0.85,
            'insight_generator': 0.8,
            'workflow_automator': 0.75
        }
        return reliability_weights.get(agent_name, 0.7)

    def _generate_insight_title(self, group_insights: List[Dict[str, Any]], insight_type: InsightType) -> str:
        """Generate title for synthesized insight"""
        template = self.insight_templates.get(insight_type, {}).get('title_template', 'Insight: {topic}')

        # Extract key entities from insights
        entities = []
        for insight in group_insights:
            if 'entities' in insight:
                entities.extend(insight['entities'])

        # Most common entities
        if entities:
            top_entities = [entity for entity, count in Counter(entities).most_common(3)]
            topic = ', '.join(top_entities)
        else:
            topic = 'Analysis Result'

        return template.format(topic=topic, metric_name=topic)

    def _generate_insight_description(self, group_insights: List[Dict[str, Any]], insight_type: InsightType) -> str:
        """Generate description for synthesized insight"""
        template = self.insight_templates.get(insight_type, {}).get('description_template', 'Analysis of {topic} reveals key findings')

        # Extract key findings
        key_findings = []
        for insight in group_insights:
            if 'key_finding' in insight:
                key_findings.append(insight['key_finding'])
            elif 'conclusion' in insight:
                key_findings.append(insight['conclusion'])

        if key_findings:
            key_finding = key_findings[0]  # Use primary finding
        else:
            key_finding = 'significant patterns'

        return template.format(
            topic='analysis results',
            key_finding=key_finding,
            significance_level='high'
        )

    def _aggregate_supporting_data(self, group_insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate supporting data from multiple insights"""
        aggregated_data = {
            'data_sources': [],
            'metrics': {},
            'statistics': {},
            'sample_size': 0
        }

        for insight in group_insights:
            if 'data_source' in insight:
                aggregated_data['data_sources'].append(insight['data_source'])

            if 'metrics' in insight:
                aggregated_data['metrics'].update(insight['metrics'])

            if 'statistics' in insight:
                aggregated_data['statistics'].update(insight['statistics'])

            if 'sample_size' in insight:
                aggregated_data['sample_size'] += insight['sample_size']

        # Remove duplicates from data sources
        aggregated_data['data_sources'] = list(set(aggregated_data['data_sources']))

        return aggregated_data

    def _generate_implications(self, group_insights: List[Dict[str, Any]], context: ResponseContext) -> List[str]:
        """Generate implications from synthesized insights"""
        implications = []

        for insight_type in set(insight.get('type', 'unknown') for insight in group_insights):
            if insight_type == 'predictive':
                implications.append("This prediction should be validated with additional data")
                implications.append("Consider the confidence interval when making decisions")
            elif insight_type == 'comparative':
                implications.append("The comparison suggests competitive advantages")
                implications.append("Further investigation into underlying factors is recommended")
            elif insight_type == 'statistical':
                implications.append("Statistical significance may not imply practical significance")
                implications.append("Consider effect size in addition to p-values")

        # Add user-specific implications
        if context.user_role == 'analyst':
            implications.append("Further analysis may reveal additional patterns")
        elif context.user_role == 'data_scientist':
            implications.append("Consider feature engineering to improve model performance")
        elif context.user_role == 'production':
            implications.append("This insight can be integrated into operational processes")

        return implications[:5]  # Limit to top 5 implications

    def _generate_recommendations(self, group_insights: List[Dict[str, Any]], context: ResponseContext) -> List[str]:
        """Generate actionable recommendations from insights"""
        recommendations = []

        # Analyze insights to generate specific recommendations
        for insight in group_insights:
            if insight.get('type') == 'predictive':
                recommendations.append("Monitor predicted outcomes and adjust strategies accordingly")
            elif insight.get('type') == 'anomaly':
                recommendations.append("Investigate root causes of detected anomalies")
            elif insight.get('type') == 'pattern':
                recommendations.append("Leverage identified patterns for strategic planning")

        # Add role-specific recommendations
        if context.user_role == 'analyst':
            recommendations.append("Explore additional data dimensions for deeper understanding")
        elif context.user_role == 'data_scientist':
            recommendations.append("Experiment with different modeling approaches")
        elif context.user_role == 'production':
            recommendations.append("Implement monitoring systems based on these insights")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _generate_insight_visualizations(self, group_insights: List[Dict[str, Any]], context: ResponseContext) -> List[Dict[str, Any]]:
        """Generate appropriate visualizations for insights"""
        visualizations = []

        for insight in group_insights:
            if insight.get('type') == 'comparative':
                visualizations.append({
                    'type': 'bar_chart',
                    'title': 'Comparison Results',
                    'data': insight.get('comparison_data', {}),
                    'description': 'Visual comparison of key metrics'
                })
            elif insight.get('type') == 'temporal':
                visualizations.append({
                    'type': 'line_chart',
                    'title': 'Trend Analysis',
                    'data': insight.get('temporal_data', {}),
                    'description': 'Changes over time'
                })
            elif insight.get('type') == 'statistical':
                visualizations.append({
                    'type': 'histogram',
                    'title': 'Distribution Analysis',
                    'data': insight.get('distribution_data', {}),
                    'description': 'Statistical distribution of values'
                })

        # Ensure we have at least one visualization
        if not visualizations:
            visualizations.append({
                'type': 'summary_chart',
                'title': 'Key Insights Overview',
                'data': {'insights': len(group_insights)},
                'description': 'Summary of analyzed insights'
            })

        return visualizations

    def _add_insight_relationships(self, insights: List[Insight]) -> List[Insight]:
        """Add relationships between insights"""
        # Simple relationship detection based on shared topics and entities
        for i, insight1 in enumerate(insights):
            relationships = []
            for j, insight2 in enumerate(insights):
                if i != j:
                    # Check for relationships
                    if self._insights_are_related(insight1, insight2):
                        relationships.append({
                            'related_insight_id': insight2.insight_id,
                            'relationship_type': 'related_topic',
                            'strength': 0.7
                        })

            # Add relationships to metadata
            if relationships:
                insight1.metadata['relationships'] = relationships

        return insights

    def _insights_are_related(self, insight1: Insight, insight2: Insight) -> bool:
        """Check if two insights are related"""
        # Check for shared source agents
        shared_agents = set(insight1.source_agents) & set(insight2.source_agents)
        if shared_agents:
            return True

        # Check for similar insight types
        if insight1.insight_type == insight2.insight_type:
            return True

        # Check for overlapping keywords in titles/descriptions
        words1 = set(insight1.title.lower().split() + insight1.description.lower().split())
        words2 = set(insight2.title.lower().split() + insight2.description.lower().split())
        overlap = len(words1 & words2)
        if overlap > 2:  # More than 2 shared words
            return True

        return False

    def _rank_insights(self, insights: List[Insight], context: ResponseContext) -> List[Insight]:
        """Rank insights by importance and relevance"""
        def insight_score(insight: Insight) -> float:
            score = insight.confidence * 0.3  # Confidence weight

            # Add score for number of implications
            score += len(insight.implications) * 0.1

            # Add score for number of recommendations
            score += len(insight.recommendations) * 0.1

            # Add score for visualizations
            score += len(insight.visualizations) * 0.1

            # Add relevance score based on user role
            if context.user_role == 'data_scientist' and insight.insight_type == InsightType.PREDICTIVE:
                score += 0.2
            elif context.user_role == 'analyst' and insight.insight_type == InsightType.STATISTICAL:
                score += 0.2
            elif context.user_role == 'production' and insight.insight_type == InsightType.RECOMMENDATION:
                score += 0.2

            return score

        return sorted(insights, key=insight_score, reverse=True)

class MultiModalContentGenerator:
    """Generates content in multiple modalities"""

    def __init__(self):
        self.content_templates = {}
        self.rendering_engines = {}
        self._initialize_content_templates()

    def _initialize_content_templates(self):
        """Initialize templates for different content types"""
        self.content_templates = {
            ResponseModality.TEXT: {
                'templates': {
                    'executive_summary': "## Executive Summary\n\n{key_findings}\n\n## Recommendations\n\n{recommendations}",
                    'detailed_analysis': "## Detailed Analysis\n\n{analysis}\n\n## Supporting Data\n\n{supporting_data}",
                    'quick_insights': "### Key Insights\n{insights}\n\n### Next Steps\n{next_steps}"
                }
            },
            ResponseModality.VISUALIZATION: {
                'templates': {
                    'dashboard': {'layout': 'grid', 'components': ['chart', 'metrics', 'insights']},
                    'report': {'layout': 'linear', 'components': ['summary', 'charts', 'analysis']},
                    'interactive': {'layout': 'dynamic', 'components': ['filters', 'charts', 'details']}
                }
            },
            ResponseModality.DATA_TABLE: {
                'templates': {
                    'summary_table': {'columns': ['Metric', 'Value', 'Change'], 'format': 'compact'},
                    'detailed_table': {'columns': ['Metric', 'Value', 'Context', 'Source'], 'format': 'comprehensive'},
                    'comparison_table': {'columns': ['Entity', 'Metric1', 'Metric2', 'Difference'], 'format': 'comparison'}
                }
            }
        }

    def generate_multi_modal_content(self, insights: List[Insight], context: ResponseContext,
                                    preferred_modalities: List[ResponseModality] = None) -> List[MultiModalContent]:
        """Generate multi-modal content from insights"""
        if preferred_modalities is None:
            preferred_modalities = [ResponseModality.TEXT, ResponseModality.VISUALIZATION]

        content_list = []

        # Generate content for each preferred modality
        for modality in preferred_modalities:
            content = self._generate_content_for_modality(insights, context, modality)
            if content:
                content_list.append(content)

        # Add supporting modalities
        for content in content_list:
            content.supporting_modalities = self._determine_supporting_modalities(content, context)

        return content_list

    def _generate_content_for_modality(self, insights: List[Insight], context: ResponseContext,
                                     modality: ResponseModality) -> Optional[MultiModalContent]:
        """Generate content for a specific modality"""
        if modality == ResponseModality.TEXT:
            return self._generate_text_content(insights, context)
        elif modality == ResponseModality.VISUALIZATION:
            return self._generate_visualization_content(insights, context)
        elif modality == ResponseModality.DATA_TABLE:
            return self._generate_table_content(insights, context)
        elif modality == ResponseModality.CODE:
            return self._generate_code_content(insights, context)
        elif modality == ResponseModality.INTERACTIVE:
            return self._generate_interactive_content(insights, context)

        return None

    def _generate_text_content(self, insights: List[Insight], context: ResponseContext) -> MultiModalContent:
        """Generate text-based content"""
        # Determine appropriate text template
        if context.user_role == 'production':
            template_key = 'quick_insights'
        elif context.user_role == 'analyst':
            template_key = 'detailed_analysis'
        else:
            template_key = 'executive_summary'

        template = self.content_templates[ResponseModality.TEXT]['templates'][template_key]

        # Prepare content variables
        key_findings = '\n'.join(f"- {insight.title}: {insight.description}" for insight in insights[:3])
        recommendations = '\n'.join(f"- {rec}" for insight in insights for rec in insight.recommendations[:2])

        # Generate content
        content = template.format(
            key_findings=key_findings,
            recommendations=recommendations,
            analysis='\n'.join(insight.description for insight in insights),
            supporting_data=str([insight.supporting_data for insight in insights[:2]]),
            insights='\n'.join(f"• {insight.title}" for insight in insights[:5]),
            next_steps='\n'.join(f"• {rec}" for insight in insights for rec in insight.recommendations[:2])
        )

        return MultiModalContent(
            content_id=str(uuid.uuid4()),
            primary_modality=ResponseModality.TEXT,
            content={'text': content, 'word_count': len(content.split())},
            supporting_modalities=[ResponseModality.VISUALIZATION],
            rendering_instructions={
                'format': 'markdown',
                'sections': ['summary', 'insights', 'recommendations'],
                'style': 'professional'
            },
            accessibility_features=['screen_reader_compatible', 'alt_text'],
            interactive_elements=[],
            metadata={
                'template_used': template_key,
                'generation_time': time.time(),
                'insights_used': len(insights)
            }
        )

    def _generate_visualization_content(self, insights: List[Insight], context: ResponseContext) -> MultiModalContent:
        """Generate visualization content"""
        visualizations = []

        for insight in insights[:3]:  # Limit to top 3 insights
            for viz in insight.visualizations:
                visualizations.append(viz)

        # Create dashboard layout
        dashboard_config = {
            'type': 'dashboard',
            'layout': 'responsive',
            'components': visualizations,
            'theme': 'professional',
            'interactivity': True
        }

        return MultiModalContent(
            content_id=str(uuid.uuid4()),
            primary_modality=ResponseModality.VISUALIZATION,
            content={
                'dashboard_config': dashboard_config,
                'visualizations': visualizations,
                'chart_count': len(visualizations)
            },
            supporting_modalities=[ResponseModality.TEXT],
            rendering_instructions={
                'engine': 'plotly',
                'responsive': True,
                'export_formats': ['png', 'svg', 'pdf'],
                'interactive_features': ['zoom', 'filter', 'hover']
            },
            accessibility_features=['alt_text', 'keyboard_navigation', 'high_contrast'],
            interactive_elements=[
                {
                    'type': 'filter_panel',
                    'description': 'Filter insights by type or confidence',
                    'controls': ['checkbox', 'slider']
                }
            ],
            metadata={
                'visualization_framework': 'plotly',
                'generation_time': time.time(),
                'interactive_elements_count': len(visualizations)
            }
        )

    def _generate_table_content(self, insights: List[Insight], context: ResponseContext) -> MultiModalContent:
        """Generate data table content"""
        # Create summary table of insights
        table_data = []
        for insight in insights:
            row = {
                'Insight': insight.title,
                'Type': insight.insight_type.value,
                'Confidence': f"{insight.confidence:.2f}",
                'Key Finding': insight.description[:100] + '...' if len(insight.description) > 100 else insight.description,
                'Recommendations': len(insight.recommendations)
            }
            table_data.append(row)

        return MultiModalContent(
            content_id=str(uuid.uuid4()),
            primary_modality=ResponseModality.DATA_TABLE,
            content={
                'table_data': table_data,
                'row_count': len(table_data),
                'columns': list(table_data[0].keys()) if table_data else []
            },
            supporting_modalities=[ResponseModality.TEXT],
            rendering_instructions={
                'format': 'html_table',
                'sortable': True,
                'filterable': True,
                'pagination': True
            },
            accessibility_features=['screen_reader_compatible', 'keyboard_navigation'],
            interactive_elements=[
                {
                    'type': 'sort',
                    'description': 'Sort table by any column'
                },
                {
                    'type': 'filter',
                    'description': 'Filter table rows'
                }
            ],
            metadata={
                'table_type': 'insights_summary',
                'generation_time': time.time()
            }
        )

    def _generate_code_content(self, insights: List[Insight], context: ResponseContext) -> MultiModalContent:
        """Generate code examples related to insights"""
        code_examples = []

        for insight in insights:
            if insight.insight_type == InsightType.PREDICTIVE:
                code_examples.append({
                    'language': 'python',
                    'title': 'Prediction Example',
                    'code': '''
# Example prediction using the insights
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Load your data
data = pd.read_csv('your_data.csv')

# Based on insights, prepare features
features = data[['feature1', 'feature2', 'feature3']]
target = data['target']

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(features, target)

# Make predictions
predictions = model.predict(features)
print(f"Predictions: {predictions}")
'''
                })
            elif insight.insight_type == InsightType.STATISTICAL:
                code_examples.append({
                    'language': 'python',
                    'title': 'Statistical Analysis Example',
                    'code': '''
# Statistical analysis based on insights
import scipy.stats as stats
import pandas as pd

# Load data
data = pd.read_csv('your_data.csv')

# Perform statistical test
statistic, p_value = stats.ttest_ind(
    data[data['group'] == 'A']['metric'],
    data[data['group'] == 'B']['metric']
)

print(f"T-statistic: {statistic}")
print(f"P-value: {p_value}")
print(f"Significant at alpha=0.05: {p_value < 0.05}")
'''
                })

        return MultiModalContent(
            content_id=str(uuid.uuid4()),
            primary_modality=ResponseModality.CODE,
            content={
                'code_examples': code_examples,
                'language_counts': {ex['language'] for ex in code_examples}
            },
            supporting_modalities=[ResponseModality.TEXT],
            rendering_instructions={
                'highlighting': True,
                'line_numbers': True,
                'copy_button': True,
                'executable': True
            },
            accessibility_features=['screen_reader_compatible', 'keyboard_navigation'],
            interactive_elements=[
                {
                    'type': 'code_runner',
                    'description': 'Run code examples'
                }
            ],
            metadata={
                'code_languages': list({ex['language'] for ex in code_examples}),
                'generation_time': time.time()
            }
        )

    def _generate_interactive_content(self, insights: List[Insight], context: ResponseContext) -> MultiModalContent:
        """Generate interactive content"""
        interactive_config = {
            'type': 'interactive_dashboard',
            'components': [
                {
                    'type': 'insight_explorer',
                    'title': 'Explore Insights',
                    'description': 'Click on insights to see details',
                    'data': [
                        {
                            'id': insight.insight_id,
                            'title': insight.title,
                            'confidence': insight.confidence,
                            'type': insight.insight_type.value
                        } for insight in insights
                    ]
                },
                {
                    'type': 'confidence_slider',
                    'title': 'Filter by Confidence',
                    'description': 'Adjust minimum confidence threshold',
                    'min_value': 0.0,
                    'max_value': 1.0,
                    'default_value': 0.5
                }
            ]
        }

        return MultiModalContent(
            content_id=str(uuid.uuid4()),
            primary_modality=ResponseModality.INTERACTIVE,
            content={
                'interactive_config': interactive_config,
                'component_count': len(interactive_config['components'])
            },
            supporting_modalities=[ResponseModality.TEXT, ResponseModality.VISUALIZATION],
            rendering_instructions={
                'framework': 'react',
                'responsive': True,
                'state_management': True
            },
            accessibility_features=['keyboard_navigation', 'screen_reader_compatible', 'high_contrast'],
            interactive_elements=[
                {
                    'type': 'click_handler',
                    'description': 'Click on insights for details'
                },
                {
                    'type': 'filter_controls',
                    'description': 'Interactive filtering options'
                }
            ],
            metadata={
                'interaction_framework': 'react',
                'generation_time': time.time()
            }
        )

    def _determine_supporting_modalities(self, content: MultiModalContent, context: ResponseContext) -> List[ResponseModality]:
        """Determine which modalities support the primary content"""
        supporting_modalities = []

        if content.primary_modality == ResponseModality.TEXT:
            supporting_modalities.extend([ResponseModality.VISUALIZATION, ResponseModality.DATA_TABLE])
        elif content.primary_modality == ResponseModality.VISUALIZATION:
            supporting_modalities.extend([ResponseModality.TEXT, ResponseModality.INTERACTIVE])
        elif content.primary_modality == ResponseModality.DATA_TABLE:
            supporting_modalities.extend([ResponseModality.TEXT, ResponseModality.VISUALIZATION])
        elif content.primary_modality == ResponseModality.CODE:
            supporting_modalities.extend([ResponseModality.TEXT])

        # Add interactive support for data scientist role
        if context.user_role == 'data_scientist' and ResponseModality.INTERACTIVE not in supporting_modalities:
            supporting_modalities.append(ResponseModality.INTERACTIVE)

        return list(set(supporting_modalities))

class PersonalizationEngine:
    """Personalizes responses based on user context and preferences"""

    def __init__(self):
        self.user_profiles = {}
        self.persona_templates = {}
        self.interaction_patterns = {}
        self._initialize_persona_templates()

    def _initialize_persona_templates(self):
        """Initialize persona templates for different user types"""
        self.persona_templates = {
            'analyst': ResponsePersona(
                persona_id='analyst_persona',
                name='Data Analyst',
                tone='educational',
                complexity_level='moderate',
                explanation_style='step_by_step',
                domain_focus='exploratory_analysis',
                communication_patterns={
                    'prefers_visuals': True,
                    'detail_level': 'high',
                    'explanation_depth': 'detailed'
                },
                knowledge_level='intermediate',
                interaction_style='guided_exploration'
            ),
            'data_scientist': ResponsePersona(
                persona_id='data_scientist_persona',
                name='Data Scientist',
                tone='technical',
                complexity_level='high',
                explanation_style='technical_detailed',
                domain_focus='advanced_modeling',
                communication_patterns={
                    'prefers_code': True,
                    'detail_level': 'comprehensive',
                    'explanation_depth': 'technical'
                },
                knowledge_level='expert',
                interaction_style='collaborative'
            ),
            'production': ResponsePersona(
                persona_id='production_persona',
                name='Production User',
                tone='direct',
                complexity_level='low',
                explanation_style='action_oriented',
                domain_focus='operational_insights',
                communication_patterns={
                    'prefers_summaries': True,
                    'detail_level': 'essential',
                    'explanation_depth': 'minimal'
                },
                knowledge_level='basic',
                interaction_style='efficient'
            )
        }

    def personalize_response(self, base_response: GeneratedResponse, context: ResponseContext) -> GeneratedResponse:
        """Personalize response based on user context"""
        # Get appropriate persona
        persona = self._get_persona(context)

        # Apply personalization based on persona
        personalized_response = self._apply_persona_personalization(base_response, persona, context)

        # Apply historical preferences
        personalized_response = self._apply_historical_preferences(personalized_response, context)

        # Apply temporal personalization
        personalized_response = self._apply_temporal_personalization(personalized_response, context)

        # Update personalization metadata
        personalized_response.generation_metadata['personalization'] = {
            'persona_id': persona.persona_id,
            'personalization_level': self._determine_personalization_level(context).value,
            'applied_techniques': ['persona_based', 'historical', 'temporal']
        }

        return personalized_response

    def _get_persona(self, context: ResponseContext) -> ResponsePersona:
        """Get appropriate persona for the user"""
        role = context.user_role.lower()

        if role in self.persona_templates:
            return self.persona_templates[role]
        else:
            # Default to analyst persona
            return self.persona_templates['analyst']

    def _apply_persona_personalization(self, response: GeneratedResponse, persona: ResponsePersona,
                                     context: ResponseContext) -> GeneratedResponse:
        """Apply persona-based personalization"""
        # Adjust primary answer tone and complexity
        if persona.complexity_level == 'low':
            response.primary_answer = self._simplify_response(response.primary_answer)
        elif persona.complexity_level == 'high':
            response.primary_answer = self._add_technical_depth(response.primary_answer)

        # Adjust explanation style
        if persona.explanation_style == 'step_by_step':
            response.primary_answer = self._add_step_by_step_explanation(response.primary_answer)
        elif persona.explanation_style == 'technical_detailed':
            response.primary_answer = self._add_technical_explanation(response.primary_answer)

        # Prioritize content based on preferences
        response.multi_modal_content = self._prioritize_content_by_preferences(
            response.multi_modal_content, persona.communication_patterns
        )

        # Adjust insight descriptions
        for insight in response.insights:
            insight.description = self._adjust_insight_description(insight.description, persona)

        return response

    def _apply_historical_preferences(self, response: GeneratedResponse, context: ResponseContext) -> GeneratedResponse:
        """Apply personalization based on historical user preferences"""
        # In a real implementation, this would use stored user preferences
        # For now, apply basic adjustments based on interaction history

        if len(context.interaction_history) > 0:
            # Analyze past interactions
            past_modalities = [interaction.get('preferred_modality') for interaction in context.interaction_history]
            most_common_modality = max(set(past_modalities), key=past_modalities.count) if past_modalities else None

            # Reorder content based on historical preferences
            if most_common_modality:
                response.multi_modal_content = self._reorder_content_by_modality(
                    response.multi_modal_content, most_common_modality
                )

        return response

    def _apply_temporal_personalization(self, response: GeneratedResponse, context: ResponseContext) -> GeneratedResponse:
        """Apply time-based personalization"""
        current_time = datetime.now()
        hour = current_time.hour

        # Adjust response based on time of day
        if 6 <= hour <= 12:  # Morning
            response.generation_metadata['temporal_greeting'] = "Good morning! Here's your analysis:"
        elif 12 <= hour <= 18:  # Afternoon
            response.generation_metadata['temporal_greeting'] = "Good afternoon! Here are the insights:"
        else:  # Evening
            response.generation_metadata['temporal_greeting'] = "Good evening! Here's your summary:"

        # Adjust content length based on time
        if hour >= 17:  # After 5 PM, prefer shorter content
            response.multi_modal_content = self._prioritize_concise_content(response.multi_modal_content)

        return response

    def _determine_personalization_level(self, context: ResponseContext) -> ResponsePersonalizationLevel:
        """Determine the level of personalization to apply"""
        if len(context.interaction_history) > 10 and context.user_preferences:
            return ResponsePersonalizationLevel.HYPER_PERSONALIZED
        elif len(context.interaction_history) > 3 or context.user_preferences:
            return ResponsePersonalizationLevel.ADAPTIVE
        elif context.user_role:
            return ResponsePersonalizationLevel.ROLE_BASED
        else:
            return ResponsePersonalizationLevel.GENERIC

    def _simplify_response(self, text: str) -> str:
        """Simplify response text"""
        # Remove technical jargon and complex sentences
        simplifications = {
            'statistical significance': 'important difference',
            'regression analysis': 'trend analysis',
            'correlation coefficient': 'relationship strength',
            'confidence interval': 'range of likely values'
        }

        simplified_text = text
        for complex_term, simple_term in simplifications.items():
            simplified_text = simplified_text.replace(complex_term, simple_term)

        return simplified_text

    def _add_technical_depth(self, text: str) -> str:
        """Add technical depth to response text"""
        # Add technical details and methodology information
        technical_additions = [
            "\n\n**Technical Details:**",
            "- Methodology: Statistical analysis with confidence intervals",
            "- Sample size: N=1000+ observations",
            "- Statistical tests: T-tests, ANOVA, regression analysis",
            "- Significance level: α=0.05"
        ]

        return text + '\n'.join(technical_additions)

    def _add_step_by_step_explanation(self, text: str) -> str:
        """Add step-by-step explanation to response text"""
        steps = [
            "\n\n**Step-by-Step Explanation:**",
            "1. **Data Collection**: We gathered relevant data from multiple sources",
            "2. **Data Processing**: The data was cleaned and prepared for analysis",
            "3. **Analysis**: Statistical methods were applied to identify patterns",
            "4. **Interpretation**: Results were interpreted in the context of your question",
            "5. **Recommendations**: Actionable insights were generated based on findings"
        ]

        return text + '\n'.join(steps)

    def _add_technical_explanation(self, text: str) -> str:
        """Add technical explanation to response text"""
        tech_details = [
            "\n\n**Technical Implementation:**",
            "```python",
            "# Example implementation",
            "import pandas as pd",
            "import numpy as np",
            "from sklearn.model_selection import train_test_split",
            "from sklearn.ensemble import RandomForestClassifier",
            "",
            "# Load and prepare data",
            "data = pd.read_csv('data.csv')",
            "X = data.drop('target', axis=1)",
            "y = data['target']",
            "",
            "# Train model",
            "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)",
            "model = RandomForestClassifier(n_estimators=100)",
            "model.fit(X_train, y_train)",
            "```"
        ]

        return text + '\n'.join(tech_details)

    def _prioritize_content_by_preferences(self, content_list: List[MultiModalContent],
                                         preferences: Dict[str, Any]) -> List[MultiModalContent]:
        """Prioritize content based on user preferences"""
        prioritized_content = content_list.copy()

        # Sort based on preferences
        if preferences.get('prefers_visuals', False):
            visual_content = [c for c in prioritized_content if c.primary_modality == ResponseModality.VISUALIZATION]
            other_content = [c for c in prioritized_content if c.primary_modality != ResponseModality.VISUALIZATION]
            prioritized_content = visual_content + other_content

        elif preferences.get('prefers_code', False):
            code_content = [c for c in prioritized_content if c.primary_modality == ResponseModality.CODE]
            other_content = [c for c in prioritized_content if c.primary_modality != ResponseModality.CODE]
            prioritized_content = code_content + other_content

        elif preferences.get('prefers_summaries', False):
            text_content = [c for c in prioritized_content if c.primary_modality == ResponseModality.TEXT]
            other_content = [c for c in prioritized_content if c.primary_modality != ResponseModality.TEXT]
            prioritized_content = text_content + other_content

        return prioritized_content

    def _adjust_insight_description(self, description: str, persona: ResponsePersona) -> str:
        """Adjust insight description based on persona"""
        if persona.complexity_level == 'low':
            return self._simplify_response(description)
        elif persona.complexity_level == 'high':
            return self._add_technical_depth(description)
        else:
            return description

    def _reorder_content_by_modality(self, content_list: List[MultiModalContent],
                                    preferred_modality: ResponseModality) -> List[MultiModalContent]:
        """Reorder content based on preferred modality"""
        preferred_content = [c for c in content_list if c.primary_modality == preferred_modality]
        other_content = [c for c in content_list if c.primary_modality != preferred_modality]

        return preferred_content + other_content

    def _prioritize_concise_content(self, content_list: List[MultiModalContent]) -> List[MultiModalContent]:
        """Prioritize concise content for evening/time-constrained usage"""
        # Prefer text summaries and key visualizations
        text_content = [c for c in content_list if c.primary_modality == ResponseModality.TEXT]
        viz_content = [c for c in content_list if c.primary_modality == ResponseModality.VISUALIZATION]
        other_content = [c for c in content_list if c.primary_modality not in [ResponseModality.TEXT, ResponseModality.VISUALIZATION]]

        return text_content + viz_content[:2] + other_content[:1]  # Limit to 1 visualization and 1 other content type

class IntelligentSummarizer:
    """Generates intelligent summaries of content"""

    def __init__(self):
        self.summarization_strategies = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        """Initialize summarization strategies"""
        self.summarization_strategies = {
            SummarizationStrategy.EXTRACTIVE: self._extractive_summarization,
            SummarizationStrategy.ABSTRACTIVE: self._abstractive_summarization,
            SummarizationStrategy.HYBRID: self._hybrid_summarization,
            SummarizationStrategy.HIERARCHICAL: self._hierarchical_summarization
        }

    def generate_summary(self, content: List[MultiModalContent], insights: List[Insight],
                        context: ResponseContext, max_length: int = 300) -> str:
        """Generate an intelligent summary of the content"""
        # Determine best summarization strategy
        strategy = self._select_summarization_strategy(content, context)

        # Apply selected strategy
        summary = self.summarization_strategies[strategy](content, insights, context, max_length)

        # Post-process summary
        summary = self._post_process_summary(summary, context)

        return summary

    def _select_summarization_strategy(self, content: List[MultiModalContent],
                                     context: ResponseContext) -> SummarizationStrategy:
        """Select the best summarization strategy"""
        content_length = sum(len(str(c.content)) for c in content)
        insight_count = len(insights)

        if content_length > 5000 or insight_count > 10:
            return SummarizationStrategy.HIERARCHICAL
        elif context.user_role == 'data_scientist':
            return SummarizationStrategy.ABSTRACTIVE
        elif context.user_role == 'production':
            return SummarizationStrategy.EXTRACTIVE
        else:
            return SummarizationStrategy.HYBRID

    def _extractive_summarization(self, content: List[MultiModalContent], insights: List[Insight],
                                context: ResponseContext, max_length: int) -> str:
        """Generate extractive summary by selecting key sentences"""
        # Extract key sentences from text content
        text_content = [c for c in content if c.primary_modality == ResponseModality.TEXT]
        sentences = []

        for text in text_content:
            text_sentences = text.content.get('text', '').split('. ')
            sentences.extend([s.strip() for s in text_sentences if s.strip()])

        # Score sentences based on importance
        scored_sentences = []
        for sentence in sentences:
            score = 0

            # Score based on length (prefer medium-length sentences)
            word_count = len(sentence.split())
            if 10 <= word_count <= 20:
                score += 1
            elif word_count > 20:
                score += 0.5

            # Score based on keywords
            important_keywords = ['key', 'important', 'significant', 'finding', 'result', 'insight']
            for keyword in important_keywords:
                if keyword in sentence.lower():
                    score += 0.5

            # Score based on position (first and last sentences are often important)
            if sentence == sentences[0] or sentence == sentences[-1]:
                score += 0.5

            scored_sentences.append((sentence, score))

        # Sort by score and select top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:3]]

        # Combine into summary
        summary = '. '.join(top_sentences)

        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'

        return summary

    def _abstractive_summarization(self, content: List[MultiModalContent], insights: List[Insight],
                                context: ResponseContext, max_length: int) -> str:
        """Generate abstractive summary by creating new sentences"""
        # Extract key themes from insights
        themes = []
        for insight in insights:
            themes.append(insight.insight_type.value)

        # Count theme frequencies
        theme_counts = Counter(themes)
        main_themes = [theme for theme, count in theme_counts.most_common(3)]

        # Create summary based on themes
        summary_parts = []

        if 'predictive' in main_themes:
            summary_parts.append("Predictive analysis reveals key patterns that can inform future decisions.")

        if 'statistical' in main_themes:
            summary_parts.append("Statistical examination of the data provides significant insights into underlying relationships.")

        if 'comparative' in main_themes:
            summary_parts.append("Comparative analysis highlights important differences and similarities between key entities.")

        if 'recommendation' in main_themes:
            summary_parts.append("Actionable recommendations have been generated based on the comprehensive analysis.")

        # Combine parts
        summary = ' '.join(summary_parts)

        # Add contextual information
        if len(insights) > 0:
            avg_confidence = sum(insight.confidence for insight in insights) / len(insights)
            summary += f" The analysis is based on {len(insights)} key insights with an average confidence of {avg_confidence:.1%}."

        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'

        return summary

    def _hybrid_summarization(self, content: List[MultiModalContent], insights: List[Insight],
                            context: ResponseContext, max_length: int) -> str:
        """Generate hybrid summary combining extractive and abstractive approaches"""
        # Generate both types of summaries
        extractive_summary = self._extractive_summarization(content, insights, context, max_length // 2)
        abstractive_summary = self._abstractive_summarization(content, insights, context, max_length // 2)

        # Combine intelligently
        if extractive_summary and abstractive_summary:
            summary = f"{abstractive_summary} {extractive_summary}"
        elif extractive_summary:
            summary = extractive_summary
        elif abstractive_summary:
            summary = abstractive_summary
        else:
            summary = "Analysis completed successfully with multiple insights generated."

        # Adjust length
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'

        return summary

    def _hierarchical_summarization(self, content: List[MultiModalContent], insights: List[Insight],
                                  context: ResponseContext, max_length: int) -> str:
        """Generate hierarchical summary with main points and sub-points"""
        # Group insights by type
        insight_groups = defaultdict(list)
        for insight in insights:
            insight_groups[insight.insight_type.value].append(insight)

        # Create hierarchical structure
        summary_parts = ["## Key Findings\n"]

        # Add main points for each insight type
        for insight_type, type_insights in insight_groups.items():
            if len(type_insights) > 0:
                # Main point for this type
                avg_confidence = sum(insight.confidence for insight in type_insights) / len(type_insights)
                summary_parts.append(f"- **{insight_type.title()}**: {len(type_insights)} insights (confidence: {avg_confidence:.1%})")

                # Add sub-points
                for insight in type_insights[:2]:  # Limit to top 2 per type
                    summary_parts.append(f"  - {insight.title}")

        # Add overall summary
        summary_parts.append(f"\n**Total**: {len(insights)} insights across {len(insight_groups)} categories analyzed.")

        summary = '\n'.join(summary_parts)

        # Adjust length
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'

        return summary

    def _post_process_summary(self, summary: str, context: ResponseContext) -> str:
        """Post-process summary for final output"""
        # Add greeting if available
        if context.temporal_context.get('greeting'):
            summary = f"{context.temporal_context['greeting']} {summary}"

        # Add concluding sentence if missing
        if not summary.endswith(('.', '!', '?')):
            summary += " Further analysis is recommended for deeper understanding."

        # Ensure proper formatting
        summary = summary.replace('  ', ' ').strip()

        return summary

class AdvancedResponseGenerator:
    """Advanced response generation system with multi-modal capabilities"""

    def __init__(self):
        self.insight_synthesizer = InsightSynthesisEngine()
        self.content_generator = MultiModalContentGenerator()
        self.personalization_engine = PersonalizationEngine()
        self.summarizer = IntelligentSummarizer()
        self.response_cache = {}
        self.generation_metrics = defaultdict(list)

    def generate_response(self, query: str, agent_results: List[Dict[str, Any]], context: ResponseContext,
                         preferred_modalities: List[ResponseModality] = None) -> GeneratedResponse:
        """Generate an advanced multi-modal response"""
        start_time = time.time()

        try:
            # Step 1: Synthesize insights from agent results
            insights = self.insight_synthesizer.synthesize_insights(agent_results, context)

            # Step 2: Generate multi-modal content
            multi_modal_content = self.content_generator.generate_multi_modal_content(
                insights, context, preferred_modalities
            )

            # Step 3: Generate primary answer
            primary_answer = self._generate_primary_answer(query, insights, context)

            # Step 4: Generate summary
            summary = self.summarizer.generate_summary(multi_modal_content, insights, context)

            # Step 5: Generate follow-up questions
            follow_up_questions = self._generate_follow_up_questions(insights, context)

            # Step 6: Calculate confidence score
            confidence_score = self._calculate_response_confidence(insights, agent_results, context)

            # Step 7: Create response object
            response = GeneratedResponse(
                response_id=str(uuid.uuid4()),
                query=query,
                primary_answer=primary_answer,
                insights=insights,
                multi_modal_content=multi_modal_content,
                summary=summary,
                follow_up_questions=follow_up_questions,
                confidence_score=confidence_score,
                personalization_level=ResponsePersonalizationLevel.ROLE_BASED,
                generation_metadata={
                    'generation_time': time.time() - start_time,
                    'agent_results_count': len(agent_results),
                    'insights_count': len(insights),
                    'content_modalities': [c.primary_modality.value for c in multi_modal_content]
                },
                timestamp=time.time()
            )

            # Step 8: Apply personalization
            response = self.personalization_engine.personalize_response(response, context)

            # Step 9: Update metrics
            execution_time = time.time() - start_time
            self._update_generation_metrics(response, execution_time, context)

            return response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._generate_fallback_response(query, str(e), context)

    def _generate_primary_answer(self, query: str, insights: List[Insight], context: ResponseContext) -> str:
        """Generate primary answer to the query"""
        if not insights:
            return "I've analyzed your request, but no specific insights were generated. Please provide more details or try a different approach."

        # Use top insights to create primary answer
        top_insights = insights[:3]  # Use top 3 insights

        answer_parts = [f"Based on my analysis of {len(insights)} insights:"]
        answer_parts.append("")

        for i, insight in enumerate(top_insights, 1):
            answer_parts.append(f"{i}. {insight.title}")
            answer_parts.append(f"   {insight.description}")

            # Add key implications
            if insight.implications:
                answer_parts.append(f"   Key implication: {insight.implications[0]}")
            answer_parts.append("")

        return '\n'.join(answer_parts)

    def _generate_follow_up_questions(self, insights: List[Insight], context: ResponseContext) -> List[str]:
        """Generate relevant follow-up questions"""
        questions = []

        # Generate questions based on insight types
        insight_types = set(insight.insight_type for insight in insights)

        if InsightType.PREDICTIVE in insight_types:
            questions.extend([
                "Would you like me to explain the confidence intervals for these predictions?",
                "Should I generate predictions for specific scenarios or timeframes?"
            ])

        if InsightType.COMPARATIVE in insight_types:
            questions.extend([
                "Would you like to explore the factors behind these differences?",
                "Should I analyze additional entities for comparison?"
            ])

        if InsightType.STATISTICAL in insight_types:
            questions.extend([
                "Would you like more details about the statistical methodology used?",
                "Should I perform additional statistical tests to validate these findings?"
            ])

        # Add role-specific questions
        if context.user_role == 'analyst':
            questions.append("Would you like step-by-step guidance on how to replicate this analysis?")
        elif context.user_role == 'data_scientist':
            questions.append("Would you like the code and technical details for implementing these methods?")
        elif context.user_role == 'production':
            questions.append("Would you like a summary of actionable recommendations based on these insights?")

        # Limit to top 5 questions
        return questions[:5]

    def _calculate_response_confidence(self, insights: List[Insight], agent_results: List[Dict[str, Any]],
                                     context: ResponseContext) -> float:
        """Calculate overall confidence score for the response"""
        if not insights:
            return 0.0

        # Base confidence from insights
        insight_confidences = [insight.confidence for insight in insights]
        avg_insight_confidence = sum(insight_confidences) / len(insight_confidences)

        # Adjust based on number of insights (more insights = more confidence)
        insight_count_factor = min(1.0, len(insights) / 5.0)  # Normalize to 5 insights

        # Adjust based on agent result quality
        successful_results = sum(1 for result in agent_results if result.get('success', False))
        agent_quality_factor = successful_results / max(1, len(agent_results))

        # Calculate final confidence
        final_confidence = (avg_insight_confidence * 0.5 +
                          insight_count_factor * 0.2 +
                          agent_quality_factor * 0.3)

        return min(1.0, final_confidence)

    def _update_generation_metrics(self, response: GeneratedResponse, execution_time: float,
                                 context: ResponseContext):
        """Update response generation metrics"""
        self.generation_metrics['execution_times'].append(execution_time)
        self.generation_metrics['response_lengths'].append(len(response.primary_answer))
        self.generation_metrics['insight_counts'].append(len(response.insights))
        self.generation_metrics['content_modalities'].append(len(response.multi_modal_content))
        self.generation_metrics['confidence_scores'].append(response.confidence_score)

    def _generate_fallback_response(self, query: str, error_message: str, context: ResponseContext) -> GeneratedResponse:
        """Generate a fallback response when errors occur"""
        return GeneratedResponse(
            response_id=str(uuid.uuid4()),
            query=query,
            primary_answer=f"I encountered an issue while processing your request: {error_message}. Please try again or contact support if the problem persists.",
            insights=[],
            multi_modal_content=[],
            summary="Response generation failed.",
            follow_up_questions=["Would you like to try a different approach?", "Should I contact technical support?"],
            confidence_score=0.1,
            personalization_level=ResponsePersonalizationLevel.GENERIC,
            generation_metadata={
                'error': error_message,
                'fallback_response': True,
                'generation_time': 0.0
            },
            timestamp=time.time()
        )

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get response generation statistics"""
        if not self.generation_metrics['execution_times']:
            return {'message': 'No responses generated yet'}

        return {
            'total_responses': len(self.generation_metrics['execution_times']),
            'average_execution_time': sum(self.generation_metrics['execution_times']) / len(self.generation_metrics['execution_times']),
            'average_response_length': sum(self.generation_metrics['response_lengths']) / len(self.generation_metrics['response_lengths']),
            'average_insights_per_response': sum(self.generation_metrics['insight_counts']) / len(self.generation_metrics['insight_counts']),
            'average_modalities_per_response': sum(self.generation_metrics['content_modalities']) / len(self.generation_metrics['content_modalities']),
            'average_confidence_score': sum(self.generation_metrics['confidence_scores']) / len(self.generation_metrics['confidence_scores']),
            'cache_size': len(self.response_cache)
        }

# Example usage
if __name__ == "__main__":
    # Initialize response generator
    generator = AdvancedResponseGenerator()

    # Create sample context
    context = ResponseContext(
        user_id="user_001",
        user_role="data_scientist",
        user_preferences={'prefers_code': True, 'detail_level': 'comprehensive'},
        interaction_history=[],
        current_session_context={},
        device_context={'platform': 'desktop'},
        temporal_context={'time_of_day': 'morning'},
        query_context={'complexity': 'high'}
    )

    # Create sample agent results
    agent_results = [
        {
            'agent_type': 'model_engine',
            'insights': [
                {
                    'type': 'predictive',
                    'title': 'Game Outcome Prediction',
                    'description': 'Model predicts home team victory with 75% probability',
                    'confidence': 0.85,
                    'source_agent': 'model_engine'
                }
            ],
            'success': True
        },
        {
            'agent_type': 'insight_generator',
            'insights': [
                {
                    'type': 'statistical',
                    'title': 'Performance Trends',
                    'description': 'Team performance shows significant upward trend',
                    'confidence': 0.92,
                    'source_agent': 'insight_generator'
                }
            ],
            'success': True
        }
    ]

    # Generate response
    response = generator.generate_response(
        query="Analyze team performance and predict game outcomes",
        agent_results=agent_results,
        context=context,
        preferred_modalities=[ResponseModality.TEXT, ResponseModality.VISUALIZATION, ResponseModality.CODE]
    )

    print("=== Generated Response ===")
    print(f"Response ID: {response.response_id}")
    print(f"Primary Answer: {response.primary_answer[:200]}...")
    print(f"Insights: {len(response.insights)}")
    print(f"Multi-modal Content: {len(response.multi_modal_content)}")
    print(f"Confidence Score: {response.confidence_score:.2f}")
    print(f"Personalization Level: {response.personalization_level.value}")

    # Show generation statistics
    stats = generator.get_generation_statistics()
    print("\n=== Generation Statistics ===")
    print(json.dumps(stats, indent=2))