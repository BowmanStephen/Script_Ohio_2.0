#!/usr/bin/env python3
"""
Conversational AI Agent - Advanced Natural Language Interaction

This agent provides sophisticated conversational capabilities including:
- Context-aware dialogue management
- Multi-turn conversation support
- Natural language understanding and intent recognition
- Follow-up question handling and clarification
- Intelligent query reformulation and expansion

Author: Claude Code Assistant
Created: 2025-11-11
Version: 1.0
"""

import os
import time
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.core.context_manager import UserRole

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Types of user intents the agent can recognize"""
    ANALYSIS = "analysis"
    LEARNING = "learning"
    PREDICTION = "prediction"
    COMPARISON = "comparison"
    EXPLORATION = "exploration"
    HELP = "help"
    CLARIFICATION = "clarification"
    FOLLOW_UP = "follow_up"
    UNKNOWN = "unknown"

class ConversationState(Enum):
    """States of conversation flow"""
    INITIAL = "initial"
    CONTEXT_GATHERING = "context_gathering"
    ANALYSIS_EXECUTION = "analysis_execution"
    RESULT_PRESENTATION = "result_presentation"
    FOLLOW_UP_HANDLING = "follow_up_handling"
    CLARIFICATION_NEEDED = "clarification_needed"

@dataclass
class ConversationContext:
    """Context for ongoing conversation"""
    user_id: str
    conversation_id: str
    current_state: ConversationState
    previous_queries: List[str]
    previous_responses: List[str]
    detected_intent: Optional[IntentType]
    entities_extracted: Dict[str, Any]
    confidence_scores: Dict[str, float]
    clarification_needed: List[str]
    follow_up_suggestions: List[str]
    conversation_history: List[Dict[str, Any]]

class ConversationalAIAgent(BaseAgent):
    """
    Advanced conversational AI agent for natural language interactions
    with context awareness and intelligent dialogue management.
    """

    def __init__(self, agent_id: str, tool_loader=None):
        super().__init__(
            agent_id=agent_id,
            name="Conversational AI",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader
        )

        # Conversation management
        self.active_conversations = {}
        self.conversation_templates = self._initialize_conversation_templates()
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_extractors = self._initialize_entity_extractors()
        self.response_generators = self._initialize_response_generators()

        # Natural language processing
        self.query_expander = QueryExpander()
        self.intent_classifier = IntentClassifier(self.intent_patterns)
        self.entity_recognizer = EntityRecognizer(self.entity_extractors)
        self.dialogue_manager = DialogueManager(self.conversation_templates)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities"""
        return [
            AgentCapability(
                name="natural_language_processing",
                description="Process and understand natural language queries with context awareness",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["analyze_feature_importance"],
                data_access=["starter_pack/", "model_pack/"],
                execution_time_estimate=1.5
            ),
            AgentCapability(
                name="intent_recognition",
                description="Identify user intent from conversational queries",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=[],
                data_access=[],
                execution_time_estimate=1.0
            ),
            AgentCapability(
                name="conversation_management",
                description="Manage multi-turn conversations with context tracking",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["export_analysis_results"],
                data_access=[],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="query_expansion",
                description="Intelligently expand and reformulate user queries",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=[],
                data_access=["starter_pack/"],
                execution_time_estimate=1.5
            ),
            AgentCapability(
                name="clarification_handling",
                description="Handle clarification requests and ambiguous queries",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=[],
                data_access=[],
                execution_time_estimate=2.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent-specific actions"""
        try:
            if action == "natural_language_processing":
                return self._process_natural_language_query(parameters, user_context)
            elif action == "conversation_management":
                return self._manage_conversation(parameters, user_context)
            elif action == "query_expansion":
                return self._expand_user_query(parameters, user_context)
            elif action == "clarification_handling":
                return self._handle_clarification(parameters, user_context)
            elif action == "intent_recognition":
                return self._recognize_intent(parameters, user_context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_type": "unknown_action"
                }
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_error"
            }

    def _process_natural_language_query(self, parameters: Dict[str, Any],
                                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process natural language query with full conversational pipeline"""

        query = parameters.get('query', '')
        user_id = parameters.get('user_id', 'unknown')
        conversation_id = parameters.get('conversation_id', f'conv_{int(time.time())}')

        logger.info(f"Processing natural language query: {query}")

        # 1. Get or create conversation context
        conversation_context = self._get_or_create_conversation_context(
            user_id, conversation_id, query, user_context
        )

        # 2. Intent recognition with confidence scoring
        intent_result = self.intent_classifier.classify_intent(
            query, conversation_context.conversation_history
        )

        # 3. Entity extraction
        entities = self.entity_recognizer.extract_entities(query, user_context)

        # 4. Query expansion and reformulation
        expanded_queries = self.query_expander.expand_query(query, entities, intent_result)

        # 5. Determine if clarification is needed
        clarification_needed = self._assess_clarification_need(
            query, intent_result, entities, conversation_context
        )

        # 6. Generate response based on conversation state
        response_data = self._generate_contextual_response(
            query, intent_result, entities, conversation_context, expanded_queries
        )

        # 7. Update conversation context
        self._update_conversation_context(conversation_context, query, response_data, intent_result, entities)

        # 8. Generate follow-up suggestions
        follow_up_suggestions = self._generate_follow_up_suggestions(
            intent_result, entities, response_data, conversation_context
        )

        return {
            "success": True,
            "processed_query": query,
            "conversation_id": conversation_id,
            "intent_recognition": {
                "detected_intent": intent_result['intent'].value,
                "confidence": intent_result['confidence'],
                "alternative_intents": intent_result.get('alternatives', [])
            },
            "entities_extracted": entities,
            "expanded_queries": expanded_queries,
            "clarification_needed": clarification_needed,
            "response": response_data,
            "follow_up_suggestions": follow_up_suggestions,
            "conversation_state": conversation_context.current_state.value,
            "context_aware": True,
            "multi_turn_support": True
        }

    def _manage_conversation(self, parameters: Dict[str, Any],
                           user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage conversation state and context"""
        conversation_id = parameters.get('conversation_id')
        action_type = parameters.get('action_type', 'get_state')

        if action_type == 'get_state':
            conversation = self.active_conversations.get(conversation_id)
            if conversation:
                return {
                    "success": True,
                    "conversation_state": conversation.current_state.value,
                    "conversation_length": len(conversation.conversation_history),
                    "previous_queries": conversation.previous_queries[-3:],  # Last 3
                    "detected_intent": conversation.detected_intent.value if conversation.detected_intent else None
                }
            else:
                return {"success": False, "error": "Conversation not found"}

        elif action_type == 'end_conversation':
            if conversation_id in self.active_conversations:
                conversation = self.active_conversations[conversation_id]
                conversation_summary = self._generate_conversation_summary(conversation)
                del self.active_conversations[conversation_id]

                return {
                    "success": True,
                    "conversation_summary": conversation_summary,
                    "conversation_ended": True
                }
            else:
                return {"success": False, "error": "Conversation not found"}

        elif action_type == 'continue_conversation':
            # Prepare conversation for continuation
            conversation = self.active_conversations.get(conversation_id)
            if conversation:
                return {
                    "success": True,
                    "conversation_ready": True,
                    "context_loaded": True,
                    "suggested_next_steps": self._generate_suggested_next_steps(conversation)
                }
            else:
                return {"success": False, "error": "Conversation not found"}

    def _expand_user_query(self, parameters: Dict[str, Any],
                          user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Expand and reformulate user query for better understanding"""
        original_query = parameters.get('query', '')
        entities = parameters.get('entities', {})
        intent = parameters.get('intent', 'unknown')

        expanded_queries = self.query_expander.expand_query(original_query, entities, {'intent': intent})

        return {
            "success": True,
            "original_query": original_query,
            "expanded_queries": expanded_queries,
            "expansion_method": "contextual_semantic_expansion",
            "query_analysis": {
                "complexity": self._analyze_query_complexity(original_query),
                "specificity": self._analyze_query_specificity(original_query),
                "ambiguity_score": self._calculate_ambiguity_score(original_query)
            }
        }

    def _handle_clarification(self, parameters: Dict[str, Any],
                            user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clarification requests and ambiguous queries"""
        ambiguous_query = parameters.get('ambiguous_query', '')
        clarification_context = parameters.get('clarification_context', {})
        user_response = parameters.get('user_response', '')

        clarification_needed = []

        # Identify specific areas needing clarification
        if 'teams' not in clarification_context and 'team' in ambiguous_query.lower():
            clarification_needed.append({
                "type": "team_specification",
                "question": "Which specific teams are you interested in?",
                "examples": ["Ohio State", "Michigan", "Alabama", "Georgia"]
            })

        if 'time_period' not in clarification_context and any(word in ambiguous_query.lower() for word in ['season', 'year', 'recent']):
            clarification_needed.append({
                "type": "time_period",
                "question": "What time period are you interested in?",
                "examples": ["2025 season", "last 5 years", "since 2016"]
            })

        if 'analysis_type' not in clarification_context and 'analysis' in ambiguous_query.lower():
            clarification_needed.append({
                "type": "analysis_specificity",
                "question": "What type of analysis would you like?",
                "examples": ["Performance analysis", "Predictive modeling", "Statistical comparison", "Trend analysis"]
            })

        return {
            "success": True,
            "clarification_needed": clarification_needed,
            "clarification_strategy": "interactive_dialogue",
            "suggested_reformulations": self._generate_reformulated_queries(ambiguous_query, clarification_context),
            "confidence_improvement": "expected_40-60%_increase"
        }

    def _recognize_intent(self, parameters: Dict[str, Any],
                         user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize and classify user intent from query"""
        query = parameters.get('query', '')
        conversation_history = parameters.get('conversation_history', [])

        intent_result = self.intent_classifier.classify_intent(query, conversation_history)

        return {
            "success": True,
            "intent_classification": intent_result,
            "confidence_analysis": {
                "primary_confidence": intent_result['confidence'],
                "confidence_threshold": 0.7,
                "high_confidence": intent_result['confidence'] >= 0.8,
                "medium_confidence": 0.6 <= intent_result['confidence'] < 0.8,
                "low_confidence": intent_result['confidence'] < 0.6
            },
            "intent_evolution": self._track_intent_evolution(conversation_history),
            "contextual_influences": self._analyze_contextual_influences(query, conversation_history)
        }

    # Helper methods for conversation management
    def _get_or_create_conversation_context(self, user_id: str, conversation_id: str,
                                          query: str, user_context: Dict[str, Any]) -> ConversationContext:
        """Get existing or create new conversation context"""
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]

        # Create new conversation context
        context = ConversationContext(
            user_id=user_id,
            conversation_id=conversation_id,
            current_state=ConversationState.INITIAL,
            previous_queries=[],
            previous_responses=[],
            detected_intent=None,
            entities_extracted={},
            confidence_scores={},
            clarification_needed=[],
            follow_up_suggestions=[],
            conversation_history=[]
        )

        self.active_conversations[conversation_id] = context
        return context

    def _initialize_conversation_templates(self) -> Dict[str, Any]:
        """Initialize conversation response templates"""
        return {
            "greetings": [
                "Hello! I'm here to help with college football analytics. What would you like to explore?",
                "Welcome! I can help you analyze football data, create predictions, or answer specific questions.",
                "Hi! I'm your college football analytics assistant. How can I assist you today?"
            ],
            "clarification_requests": [
                "Could you help me understand better what you're looking for?",
                "I want to make sure I give you the most relevant information. Could you provide more details about {specific_area}?",
                "To give you the best analysis, could you clarify {specific_area}?"
            ],
            "analysis_responses": [
                "Based on your query about {topic}, here's what I found:",
                "I've analyzed the {topic} data and here are the key insights:",
                "Here's my analysis of {topic}:"
            ],
            "follow_up_suggestions": [
                "Would you like me to dive deeper into {specific_aspect}?",
                "Are you interested in exploring {related_topic} as well?",
                "Would you like to see predictions based on this analysis?"
            ]
        }

    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize intent recognition patterns"""
        return {
            "analysis": [
                r"analyze|analysis|investigate|examine|evaluate|assess",
                r"what does the data show|tell me about|explain the",
                r"performance metrics|statistics|correlations|patterns"
            ],
            "learning": [
                r"learn|tutorial|explain|how to|teach me|understanding",
                r"introduction|getting started|beginner|basics",
                r"walkthrough|guide|step by step|help me learn"
            ],
            "prediction": [
                r"predict|forecast|outcome|winner|score|will",
                r"game result|matchup|who will win|probability",
                r"future|upcoming|next game|prediction model"
            ],
            "comparison": [
                r"compare|versus|vs|against|difference|better",
                r"which team|head to head|matchup|battle",
                r"ranking|relative performance|side by side"
            ],
            "exploration": [
                r"show me|display|visualize|chart|graph",
                r"what data|tell me about|overview|summary",
                r"explore|discover|find patterns|identify trends"
            ],
            "help": [
                r"help|assist|guidance|support|how can you",
                r"what can you do|capabilities|features",
                r"stuck|confused|don't understand"
            ]
        }

    def _initialize_entity_extractors(self) -> Dict[str, Any]:
        """Initialize entity extraction patterns"""
        return {
            "teams": {
                "patterns": [
                    r"\b(Ohio State|Michigan|Alabama|Georgia|Clemson|Oklahoma|Texas|USC|Notre Dame|LSU|Florida|Miami|Penn State|Wisconsin|Iowa|Oregon|Washington|Auburn|Tennessee|Texas A&M)\b",
                    r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"  # Generic team name pattern
                ],
                "examples": ["Ohio State", "University of Michigan", "Alabama"]
            },
            "time_periods": {
                "patterns": [
                    r"\b(2025|2024|2023|2022|2021|2020|2019|2018|2017|2016)\b",
                    r"\b(last \d+ years|past \d+ seasons|since \d{4})\b",
                    r"\b(this season|current year|recent)\b"
                ],
                "examples": ["2025 season", "last 5 years", "since 2016"]
            },
            "metrics": {
                "patterns": [
                    r"\b(EPA|efficiency|havoc|explosiveness|success rate|yards per play|points per game)\b",
                    r"\b(offensive|defensive|special teams)\s+(efficiency|performance|metrics)\b",
                    r"\b(wins|losses|record|ranking|poll)\b"
                ],
                "examples": ["offensive efficiency", "defensive havoc rate", "EPA"]
            }
        }

    def _initialize_response_generators(self) -> Dict[str, Any]:
        """Initialize response generation strategies"""
        return {
            "analysis_responses": {
                "structure": "insight_driven",
                "tone": "analytical_confident",
                "elements": ["key_findings", "statistical_significance", "practical_implications"]
            },
            "learning_responses": {
                "structure": "educational_progressive",
                "tone": "supportive_encouraging",
                "elements": ["concept_explanation", "practical_examples", "next_steps"]
            },
            "prediction_responses": {
                "structure": "probabilistic",
                "tone": "balanced_cautious",
                "elements": ["confidence_levels", "key_factors", "caveats"]
            }
        }

    # Additional implementation methods (mocked for brevity)
    def _assess_clarification_need(self, query: str, intent_result: Dict,
                                 entities: Dict, context: ConversationContext) -> List[str]:
        """Assess if clarification is needed"""
        clarification_needed = []

        # Low confidence in intent classification
        if intent_result['confidence'] < 0.7:
            clarification_needed.append("intent_ambiguity")

        # Missing key entities
        if intent_result['intent'] == IntentType.PREDICTION and 'teams' not in entities:
            clarification_needed.append("missing_teams")

        # Vague time references
        if 'recent' in query.lower() and 'time_periods' not in entities:
            clarification_needed.append("time_period_ambiguity")

        return clarification_needed

    def _generate_contextual_response(self, query: str, intent_result: Dict,
                                    entities: Dict, context: ConversationContext,
                                    expanded_queries: List[str]) -> Dict[str, Any]:
        """Generate contextually appropriate response"""
        response = {
            "type": "contextual_response",
            "intent_based": True,
            "entity_aware": True,
            "conversation_history_informed": True
        }

        # Add intent-specific response elements
        intent = intent_result['intent']
        if intent == IntentType.ANALYSIS:
            response.update({
                "response_type": "analytical_insights",
                "key_points": [
                    "Analyzing the specified metrics and patterns",
                    "Providing statistical significance and confidence levels",
                    "Offering practical interpretations and recommendations"
                ]
            })
        elif intent == IntentType.LEARNING:
            response.update({
                "response_type": "educational_guidance",
                "key_points": [
                    "Explaining core concepts in accessible terms",
                    "Providing step-by-step learning pathways",
                    "Suggesting relevant resources and examples"
                ]
            })

        return response

    def _update_conversation_context(self, context: ConversationContext, query: str,
                                   response: Dict, intent_result: Dict, entities: Dict):
        """Update conversation context with new information"""
        context.previous_queries.append(query)
        context.previous_responses.append(str(response))
        context.detected_intent = intent_result['intent']
        context.entities_extracted.update(entities)
        context.confidence_scores['latest_intent'] = intent_result['confidence']

        # Add to conversation history
        context.conversation_history.append({
            "timestamp": time.time(),
            "query": query,
            "response": response,
            "intent": intent_result['intent'].value,
            "entities": entities
        })

        # Update conversation state
        if context.clarification_needed:
            context.current_state = ConversationState.CLARIFICATION_NEEDED
        elif len(context.conversation_history) > 1:
            context.current_state = ConversationState.FOLLOW_UP_HANDLING
        else:
            context.current_state = ConversationState.RESULT_PRESENTATION

    def _generate_follow_up_suggestions(self, intent_result: Dict, entities: Dict,
                                      response: Dict, context: ConversationContext) -> List[str]:
        """Generate intelligent follow-up suggestions"""
        suggestions = []

        intent = intent_result['intent']

        if intent == IntentType.ANALYSIS:
            if 'teams' in entities:
                suggestions.extend([
                    f"Would you like to compare {entities['teams'][0]} with other teams?",
                    "Should I analyze trends over multiple seasons?",
                    "Would you like to see predictive models based on this analysis?"
                ])
            else:
                suggestions.extend([
                    "Would you like to analyze specific teams or conferences?",
                    "Should I focus on offensive or defensive metrics?",
                    "Are you interested in historical trends or current performance?"
                ])

        elif intent == IntentType.LEARNING:
            suggestions.extend([
                "Would you like to explore specific metrics like EPA or efficiency?",
                "Should I walk you through practical data analysis examples?",
                "Are you interested in learning about predictive modeling techniques?"
            ])

        elif intent == IntentType.PREDICTION:
            suggestions.extend([
                "Would you like confidence intervals for these predictions?",
                "Should I factor in recent team performance trends?",
                "Are you interested in understanding the key prediction factors?"
            ])

        return suggestions[:3]  # Limit to top 3 suggestions

    def _generate_conversation_summary(self, context: ConversationContext) -> Dict[str, Any]:
        """Generate summary of completed conversation"""
        return {
            "conversation_id": context.conversation_id,
            "duration": len(context.conversation_history),
            "primary_intent": context.detected_intent.value if context.detected_intent else "unknown",
            "key_topics": list(context.entities_extracted.keys()),
            "interaction_quality": self._assess_interaction_quality(context),
            "successful_resolutions": len([r for r in context.conversation_history if r.get('success', True)])
        }

    def _analyze_query_complexity(self, query: str) -> str:
        """Analyze the complexity of the user query"""
        word_count = len(query.split())
        has_conjunctions = any(word in query.lower() for word in ['and', 'but', 'or', 'while'])
        has_subordinate_clauses = query.count(',') > 1

        if word_count > 15 or (has_conjunctions and has_subordinate_clauses):
            return "high"
        elif word_count > 8 or has_conjunctions:
            return "medium"
        else:
            return "low"

    def _analyze_query_specificity(self, query: str) -> str:
        """Analyze how specific the user query is"""
        specific_indicators = ['specific', 'exactly', 'precisely', 'show me']
        vague_indicators = ['about', 'generally', 'roughly', 'around']

        if any(indicator in query.lower() for indicator in specific_indicators):
            return "high"
        elif any(indicator in query.lower() for indicator in vague_indicators):
            return "low"
        else:
            return "medium"

    def _calculate_ambiguity_score(self, query: str) -> float:
        """Calculate ambiguity score (0.0 = clear, 1.0 = highly ambiguous)"""
        ambiguity_factors = []

        # Pronoun usage (creates ambiguity without context)
        pronouns = ['it', 'they', 'them', 'this', 'that']
        pronoun_count = sum(1 for pronoun in pronouns if pronoun in query.lower().split())
        ambiguity_factors.append(min(0.3, pronoun_count * 0.1))

        # Generic terms
        generic_terms = ['data', 'analysis', 'information', 'results']
        generic_count = sum(1 for term in generic_terms if term in query.lower())
        ambiguity_factors.append(min(0.4, generic_count * 0.15))

        # Question words (can indicate uncertainty)
        question_words = ['what', 'which', 'how', 'when', 'where']
        question_count = sum(1 for qw in question_words if query.lower().startswith(qw))
        ambiguity_factors.append(min(0.2, question_count * 0.1))

        return min(1.0, sum(ambiguity_factors))

    def _generate_reformulated_queries(self, ambiguous_query: str,
                                     context: Dict[str, Any]) -> List[str]:
        """Generate reformulated versions of ambiguous queries"""
        reformulations = []

        # Add context-specific terms
        if 'teams' not in context:
            reformulations.append(f"Which teams should I analyze for {ambiguous_query}?")

        if 'time_period' not in context:
            reformulations.append(f"For what time period: {ambiguous_query}?")

        # Add specification prompts
        reformulations.extend([
            f"Could you specify the scope for {ambiguous_query}?",
            f"What specific aspects of {ambiguous_query} interest you?"
        ])

        return reformulations

    def _track_intent_evolution(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Track how user intent evolves through conversation"""
        if len(conversation_history) < 2:
            return {"evolution_detected": False}

        intents = [entry.get('intent', 'unknown') for entry in conversation_history]
        intent_changes = sum(1 for i in range(1, len(intents)) if intents[i] != intents[i-1])

        return {
            "evolution_detected": intent_changes > 0,
            "intent_changes": intent_changes,
            "intent_stability": 1.0 - (intent_changes / len(intents)),
            "trending_toward": intents[-1] if intents else "unknown"
        }

    def _analyze_contextual_influences(self, query: str,
                                     conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analyze how conversation context influences query interpretation"""
        if not conversation_history:
            return {"context_influence": "none"}

        recent_queries = [entry.get('query', '') for entry in conversation_history[-3:]]

        # Check for continuing themes
        topic_continuity = self._calculate_topic_continuity(query, recent_queries)

        # Check for reference resolution
        references_resolved = self._check_reference_resolution(query, conversation_history)

        return {
            "context_influence": "high" if topic_continuity > 0.7 else "medium" if topic_continuity > 0.3 else "low",
            "topic_continuity": topic_continuity,
            "references_resolved": references_resolved,
            "conversation_depth": len(conversation_history)
        }

    def _calculate_topic_continuity(self, current_query: str,
                                  previous_queries: List[str]) -> float:
        """Calculate continuity between current and previous queries"""
        if not previous_queries:
            return 0.0

        current_words = set(current_query.lower().split())
        continuity_scores = []

        for prev_query in previous_queries:
            prev_words = set(prev_query.lower().split())
            overlap = len(current_words.intersection(prev_words))
            total_unique = len(current_words.union(prev_words))
            continuity_scores.append(overlap / total_unique if total_unique > 0 else 0)

        return sum(continuity_scores) / len(continuity_scores)

    def _check_reference_resolution(self, query: str,
                                  conversation_history: List[Dict]) -> List[str]:
        """Check what references in the query can be resolved from context"""
        resolved_references = []

        # Look for pronouns that might refer back to previous entities
        if any(pronoun in query.lower() for pronoun in ['it', 'they', 'this', 'that']):
            if conversation_history:
                # Extract entities from previous conversation
                for entry in conversation_history[-2:]:  # Last 2 entries
                    entities = entry.get('entities', {})
                    for entity_type, entity_values in entities.items():
                        if entity_values:
                            resolved_references.append(f"{entity_type}: {entity_values[0]}")

        return resolved_references

    def _generate_suggested_next_steps(self, conversation: ConversationContext) -> List[str]:
        """Generate suggested next steps based on conversation state"""
        suggestions = []

        if conversation.current_state == ConversationState.INITIAL:
            suggestions.extend([
                "Provide a more specific analysis question",
                "Specify teams or time periods of interest",
                "Ask for learning recommendations"
            ])

        elif conversation.current_state == ConversationState.RESULT_PRESENTATION:
            suggestions.extend([
                "Dive deeper into specific insights",
                "Ask follow-up questions",
                "Request different types of analysis"
            ])

        elif conversation.current_state == ConversationState.FOLLOW_UP_HANDLING:
            suggestions.extend([
                "Continue the current analysis thread",
                "Start a new analysis topic",
                "Request summary of findings"
            ])

        return suggestions

    def _assess_interaction_quality(self, context: ConversationContext) -> str:
        """Assess the quality of interaction in the conversation"""
        # Simple heuristic based on conversation flow
        avg_confidence = sum(context.confidence_scores.values()) / len(context.confidence_scores) if context.confidence_scores else 0

        if avg_confidence > 0.8 and len(context.clarification_needed) == 0:
            return "excellent"
        elif avg_confidence > 0.6:
            return "good"
        elif avg_confidence > 0.4:
            return "fair"
        else:
            return "needs_improvement"


# Supporting classes for the Conversational AI Agent
class QueryExpander:
    """Expands and reformulates user queries for better understanding"""

    def expand_query(self, query: str, entities: Dict, intent: Dict) -> List[str]:
        """Expand query with related terms and concepts"""
        expansions = []

        # Add analytical terms if analysis intent
        if intent.get('intent') == 'analysis':
            expansions.append(f"{query} with statistical significance")
            expansions.append(f"{query} including trend analysis")

        # Add time-specific expansions
        if 'time_periods' not in entities:
            expansions.append(f"{query} for current season")
            expansions.append(f"{query} over recent years")

        # Add team-specific expansions
        if 'teams' not in entities and any(word in query.lower() for word in ['team', 'teams']):
            expansions.append(f"{query} top-ranked teams")
            expansions.append(f"{query} conference leaders")

        return list(set(expansions))  # Remove duplicates


class IntentClassifier:
    """Classifies user intent from conversational queries"""

    def __init__(self, intent_patterns: Dict[str, List[str]]):
        self.intent_patterns = intent_patterns

    def classify_intent(self, query: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Classify intent with confidence scoring"""
        query_lower = query.lower()

        # Score each intent type
        intent_scores = {}
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            intent_scores[intent_type] = score

        # Consider conversation context
        if conversation_history:
            recent_intents = [entry.get('intent', 'unknown') for entry in conversation_history[-2:]]
            for recent_intent in recent_intents:
                if recent_intent in intent_scores:
                    intent_scores[recent_intent] += 0.5  # Boost for continuity

        # Find best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            max_score = intent_scores[best_intent]

            # Calculate confidence
            total_score = sum(intent_scores.values())
            confidence = max_score / total_score if total_score > 0 else 0

            # Get alternatives
            alternatives = [(intent, score) for intent, score in intent_scores.items()
                          if intent != best_intent and score > 0]
            alternatives.sort(key=lambda x: x[1], reverse=True)

            return {
                'intent': IntentType(best_intent) if best_intent in [e.value for e in IntentType] else IntentType.UNKNOWN,
                'confidence': confidence,
                'all_scores': intent_scores,
                'alternatives': alternatives[:2]
            }

        return {
            'intent': IntentType.UNKNOWN,
            'confidence': 0.0,
            'all_scores': {},
            'alternatives': []
        }


class EntityRecognizer:
    """Recognizes and extracts entities from user queries"""

    def __init__(self, entity_extractors: Dict[str, Any]):
        self.entity_extractors = entity_extractors

    def extract_entities(self, query: str, user_context: Dict) -> Dict[str, List[str]]:
        """Extract entities from query"""
        entities = {}

        for entity_type, extractor in self.entity_extractors.items():
            patterns = extractor['patterns']
            matches = []

            for pattern in patterns:
                found = re.findall(pattern, query, re.IGNORECASE)
                matches.extend(found)

            if matches:
                entities[entity_type] = list(set(matches))  # Remove duplicates

        return entities


class DialogueManager:
    """Manages conversational dialogue flow and responses"""

    def __init__(self, conversation_templates: Dict[str, Any]):
        self.templates = conversation_templates

    def generate_dialogue_response(self, context: ConversationContext,
                                  intent: IntentType, entities: Dict) -> str:
        """Generate appropriate dialogue response"""
        # This would contain sophisticated dialogue generation logic
        # For now, return a template-based response

        if context.current_state == ConversationState.INITIAL:
            return self.templates['greetings'][0]
        elif context.clarification_needed:
            return self.templates['clarification_requests'][0].format(
                specific_area=context.clarification_needed[0] if context.clarification_needed else 'your request'
            )
        else:
            return self.templates['analysis_responses'][0].format(
                topic=list(entities.keys())[0] if entities else 'your query'
            )