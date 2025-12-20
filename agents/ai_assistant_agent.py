#!/usr/bin/env python3
"""
AI Assistant Agent - General Purpose Conversational Interface

This agent provides a natural language interface to the Script Ohio 2.0 platform,
integrating with the existing agent ecosystem to provide conversational access
to college football analytics, predictions, and data insights.

Author: Claude Code Assistant
Created: 2025-12-18
Version: 1.0
"""

import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from agents.core.agent_framework import (
    AgentCapability,
    BaseAgent,
    PermissionLevel,
)
from src.observability import (
    configure_logging,
    get_logger,
    ErrorCategory,
    ErrorSeverity
)

configure_logging(service_name="agents")
logger = get_logger(__name__, component="ai_assistant", service_name="agents")


class ConversationManager:
    """Manages conversation state and context"""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict]] = {}
        self.context_store: Dict[str, Dict] = {}

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        self.conversations[session_id].append(message)

        # Trim history if needed
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]

    def get_conversation(self, session_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(session_id, [])

    def set_context(self, session_id: str, context: Dict):
        """Set conversation context"""
        self.context_store[session_id] = context
        self.context_store[session_id]["last_updated"] = datetime.utcnow().isoformat()

    def get_context(self, session_id: str) -> Dict:
        """Get conversation context"""
        return self.context_store.get(session_id, {})


class IntentClassifier:
    """Classifies user intent and routes to appropriate agents"""

    def __init__(self):
        self.intent_patterns = {
            "data_analysis": [
                r"\banalyze\b|\bstatistics\b|\bstats\b|\bdata\b|\bperformance\b",
                r"\bcompare\b|\bcomparison\b|\bshow me\b.*\bstats\b|\bteam.*performance\b",
                r"\bhow.*did.*perform\b|\bwhat.*are.*stats\b|\bshow.*me.*data\b"
            ],
            "predictions": [
                r"\bpredict\b|\bprediction\b|\bforecast\b|\bwho.*will.*win\b|\boutcome\b",
                r"\bscore.*prediction\b|\bgame.*prediction\b|\bbetting.*odds\b|\bbet.*recommendation\b",
                r"\bwin.*probability\b|\bprobability\b.*\bwin\b|\bconfidence.*interval\b"
            ],
            "general_chat": [
                r"\bhello\b|\bhi\b|\bhey\b|\bwhat.*up\b|\bgreetings\b",
                r"\bhow.*are.*you\b|\bwhat.*can.*you.*do\b|\bnice.*to.*meet.*you\b",
                r"\bgood.*morning\b|\bgood.*afternoon\b|\bgood.*evening\b"
            ],
            "task_automation": [
                r"\brun.*analysis\b|\bgenerate.*report\b|\bcreate.*dashboard\b",
                r"\bupdate.*data\b|\brefresh.*models\b|\bretrain\b|\bschedule.*task\b",
                r"\bautomate.*process\b|\bbatch.*process\b|\bcron.*job\b"
            ],
            "learning_guidance": [
                r"\blearn.*how\b|\btutorial\b|\bguide\b|\bexplain.*concept\b",
                r"\bhow.*to\b|\bbest.*practice\b|\brecommendation\b|\bteach.*me\b",
                r"\bexplain.*how\b|\bdemonstrate\b|\bshow.*me.*how\b"
            ]
        }

    def classify_intent(self, message: str) -> Tuple[str, float]:
        """Classify user intent with confidence score"""
        message_lower = message.lower()
        intent_scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, message_lower))
                score += matches
            intent_scores[intent] = score

        if not any(intent_scores.values()):
            return "general_chat", 0.5

        best_intent = max(intent_scores, key=intent_scores.get)
        # Normalize to 0-1 range with minimum threshold
        max_score = max(intent_scores.values())
        confidence = min(max_score / 1.0, 1.0)  # Lower threshold for better confidence

        return best_intent, confidence


class AIAssistantAgent(BaseAgent):
    """
    General Purpose Conversational AI Assistant

    Provides natural language interface to college football analytics,
    data insights, and prediction capabilities through agent orchestration.
    """

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            name="AI Assistant",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE
        )

        self.conversation_manager = ConversationManager()
        self.intent_classifier = IntentClassifier()

        # Cache for agent responses
        self.response_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes

        # Load OpenAI API key if available
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        logger.info(f"AI Assistant Agent {agent_id} initialized")

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define AI assistant capabilities"""
        return [
            AgentCapability(
                name="natural_language_processing",
                description="Process and understand natural language queries",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=[],
                data_access=["conversation_history"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="conversation_management",
                description="Maintain conversation context and history",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=[],
                data_access=["conversation_history", "context_store"],
                execution_time_estimate=0.5
            ),
            AgentCapability(
                name="intent_recognition",
                description="Classify user intent and route to appropriate agents",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=[],
                data_access=["intent_patterns"],
                execution_time_estimate=1.0
            ),
            AgentCapability(
                name="query_expansion",
                description="Expand and clarify ambiguous user queries",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=[],
                data_access=["query_templates"],
                execution_time_estimate=1.5
            ),
            AgentCapability(
                name="clarification_handling",
                description="Handle ambiguous requests by asking clarifying questions",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=[],
                data_access=["clarification_templates"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="intelligent_dialogue",
                description="Generate contextual, intelligent responses",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["language_model"],
                data_access=["conversation_history", "context_store"],
                execution_time_estimate=3.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        """Execute AI assistant actions"""
        try:
            start_time = time.time()

            if action == "natural_language_processing":
                result = self._process_natural_language(parameters)
            elif action == "conversation_management":
                result = self._manage_conversation(parameters)
            elif action == "intent_recognition":
                result = self._recognize_intent(parameters)
            elif action == "query_expansion":
                result = self._expand_query(parameters)
            elif action == "clarification_handling":
                result = self._handle_clarification(parameters)
            elif action == "intelligent_dialogue":
                result = self._generate_intelligent_dialogue(parameters)
            else:
                raise ValueError(f"Unknown action: {action}")

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "data": result,
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in AI Assistant {action}: {str(e)}",
                        extra={"error_category": ErrorCategory.AGENT_EXECUTION,
                              "error_severity": ErrorSeverity.HIGH})
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }

    def _process_natural_language(self, params: Dict) -> Dict:
        """Process natural language query"""
        message = params.get("message", "")
        session_id = params.get("session_id", "default")

        # Add user message to conversation
        self.conversation_manager.add_message(session_id, "user", message)

        # Classify intent
        intent, confidence = self.intent_classifier.classify_intent(message)

        # Get conversation context
        context = self.conversation_manager.get_context(session_id)

        # Generate response based on intent
        response_data = self._generate_response(message, intent, confidence, context, session_id)

        # Add assistant response to conversation
        self.conversation_manager.add_message(
            session_id,
            "assistant",
            response_data["response"],
            {"intent": intent, "confidence": confidence}
        )

        return {
            "response": response_data["response"],
            "intent": intent,
            "confidence": confidence,
            "session_id": session_id,
            "suggestions": response_data.get("suggestions", [])
        }

    def _manage_conversation(self, params: Dict) -> Dict:
        """Manage conversation state and context"""
        session_id = params.get("session_id", "default")
        action = params.get("action", "get")
        data = params.get("data", {})

        if action == "get":
            conversation = self.conversation_manager.get_conversation(session_id)
            context = self.conversation_manager.get_context(session_id)
            return {
                "conversation": conversation,
                "context": context,
                "session_id": session_id
            }

        elif action == "set_context":
            self.conversation_manager.set_context(session_id, data)
            return {
                "status": "context_updated",
                "session_id": session_id
            }

        elif action == "clear":
            if session_id in self.conversation_manager.conversations:
                del self.conversation_manager.conversations[session_id]
            if session_id in self.conversation_manager.context_store:
                del self.conversation_manager.context_store[session_id]
            return {
                "status": "conversation_cleared",
                "session_id": session_id
            }

        else:
            raise ValueError(f"Unknown conversation action: {action}")

    def _recognize_intent(self, params: Dict) -> Dict:
        """Classify user intent"""
        message = params.get("message", "")
        intent, confidence = self.intent_classifier.classify_intent(message)

        # Map intent to target agent
        agent_mapping = {
            "data_analysis": "cfbd_integration",
            "predictions": "model_execution_engine",
            "task_automation": "workflow_automator",
            "learning_guidance": "learning_navigator",
            "general_chat": "ai_assistant"
        }

        target_agent = agent_mapping.get(intent, "ai_assistant")

        return {
            "intent": intent,
            "confidence": confidence,
            "target_agent": target_agent,
            "suggested_actions": self._get_suggested_actions(intent)
        }

    def _expand_query(self, params: Dict) -> Dict:
        """Expand ambiguous user queries"""
        query = params.get("query", "")
        context = params.get("context", {})

        # Simple query expansion based on keywords
        expanded_query = query
        clarifications = []

        # Check for ambiguous team names
        if any(word in query.lower() for word in ["team", "game", "matchup"]):
            if "season" not in query.lower() and "week" not in query.lower():
                clarifications.append("Which season and week are you interested in?")

        # Check for prediction requests without specifics
        if "predict" in query.lower() and len(query.split()) < 5:
            clarifications.append("Which teams or matchup would you like me to predict?")

        return {
            "expanded_query": expanded_query,
            "clarifications": clarifications,
            "needs_clarification": len(clarifications) > 0
        }

    def _handle_clarification(self, params: Dict) -> Dict:
        """Handle ambiguous requests by asking clarifying questions"""
        ambiguous_query = params.get("ambiguous_query", "")
        context = params.get("context", {})

        # Generate clarification question based on ambiguity
        if "team" in ambiguous_query.lower() and "season" not in ambiguous_query.lower():
            question = "Which college football season are you interested in? (e.g., 2025)"
            options = ["2025", "2024", "2023", "2022"]

        elif "predict" in ambiguous_query.lower() and len(ambiguous_query.split()) < 5:
            question = "What would you like me to predict? Please specify the teams involved."
            options = [
                "Specify home and away teams",
                "Get predictions for all games this week",
                "Predict bowl game outcomes"
            ]

        else:
            question = "Could you provide more details about what you're looking for?"
            options = [
                "Team performance analysis",
                "Game predictions",
                "Statistics and data",
                "Betting insights"
            ]

        return {
            "clarification_question": question,
            "options": options,
            "original_query": ambiguous_query
        }

    def _generate_intelligent_dialogue(self, params: Dict) -> Dict:
        """Generate contextual, intelligent responses"""
        query = params.get("query", "")
        context = params.get("context", {})
        agent_results = params.get("agent_results", {})

        # Generate contextual response
        response = self._create_contextual_response(query, context, agent_results)

        # Generate follow-up suggestions
        suggestions = self._generate_follow_up_suggestions(query, context)

        # Generate related topics
        related_topics = self._generate_related_topics(query, agent_results)

        return {
            "response": response,
            "follow_up_suggestions": suggestions,
            "related_topics": related_topics,
            "response_type": "intelligent_dialogue"
        }

    def _generate_response(self, message: str, intent: str, confidence: float,
                          context: Dict, session_id: str) -> Dict:
        """Generate appropriate response based on intent"""

        if intent == "general_chat":
            return self._generate_chat_response(message, context)
        elif intent == "data_analysis":
            return self._generate_data_analysis_response(message, context)
        elif intent == "predictions":
            return self._generate_prediction_response(message, context)
        elif intent == "task_automation":
            return self._generate_automation_response(message, context)
        elif intent == "learning_guidance":
            return self._generate_learning_response(message, context)
        else:
            return self._generate_default_response(message, context)

    def _generate_chat_response(self, message: str, context: Dict) -> Dict:
        """Generate conversational response"""
        message_lower = message.lower()

        if any(greeting in message_lower for greeting in ["hello", "hi", "hey"]):
            return {
                "response": "Hello! I'm your AI assistant for college football analytics. I can help you analyze team performance, generate predictions, and provide insights from our data. What would you like to explore today?",
                "suggestions": [
                    "Show me team statistics",
                    "Generate game predictions",
                    "Analyze upcoming matchups",
                    "Explain prediction models"
                ]
            }

        elif "what can you do" in message_lower or "help" in message_lower:
            return {
                "response": "I can help you with college football analytics through natural language conversation! Here's what I can do:\n\n📊 **Data Analysis**: Analyze team performance, compare statistics, and identify trends\n🏈 **Predictions**: Generate game outcome predictions using our ML models\n🤖 **Task Automation**: Run analyses, generate reports, and update data\n📚 **Learning**: Guide you through understanding our models and analytics\n\nJust ask me anything in plain language!",
                "suggestions": [
                    "Analyze Ohio State's performance this season",
                    "Predict the Ohio State vs Michigan game",
                    "Compare top 25 teams",
                    "Explain how your prediction models work"
                ]
            }

        else:
            return {
                "response": "I'm here to help with college football analytics! Feel free to ask me about team performance, game predictions, statistical analysis, or any other football-related questions. What interests you most?",
                "suggestions": [
                    "Team statistics and performance",
                    "Game predictions and betting insights",
                    "Matchup analysis",
                    "Model explanations"
                ]
            }

    def _generate_data_analysis_response(self, message: str, context: Dict) -> Dict:
        """Generate data analysis response"""
        return {
            "response": f"I can help you analyze that data! Based on your request about '{message}', I'll connect with our CFBD integration agent to pull the latest college football data and provide comprehensive analysis. This will include team performance metrics, statistical trends, and comparative insights.",
            "suggestions": [
                "Show me offensive statistics",
                "Analyze defensive performance",
                "Compare team rankings",
                "Look at season trends"
            ]
        }

    def _generate_prediction_response(self, message: str, context: Dict) -> Dict:
        """Generate prediction response"""
        return {
            "response": f"I'll help you with predictions for '{message}'! I can use our machine learning models (Ridge Regression, XGBoost, and FastAI) to generate game outcome predictions with confidence intervals. Would you like me to include betting insights and value betting analysis?",
            "suggestions": [
                "Predict this week's games",
                "Analyze championship matchups",
                "Include betting odds analysis",
                "Show prediction confidence"
            ]
        }

    def _generate_automation_response(self, message: str, context: Dict) -> Dict:
        """Generate automation response"""
        return {
            "response": f"I can help automate '{message}'! I'll coordinate with our workflow automation system to handle tasks like data updates, report generation, and scheduled analyses. This ensures you always have the most current insights without manual effort.",
            "suggestions": [
                "Update team statistics",
                "Generate weekly report",
                "Refresh prediction models",
                "Schedule regular analysis"
            ]
        }

    def _generate_learning_response(self, message: str, context: Dict) -> Dict:
        """Generate learning response"""
        return {
            "response": f"I'd be happy to help you learn about '{message}'! I can provide tutorials, explain our analytical methodologies, and guide you through understanding our prediction models. I'll make sure to explain complex concepts in simple, easy-to-understand terms.",
            "suggestions": [
                "Explain prediction models",
                "Guide me through data analysis",
                "Teach me about college football analytics",
                "Show me how to interpret results"
            ]
        }

    def _generate_default_response(self, message: str, context: Dict) -> Dict:
        """Generate default response for unknown intents"""
        return {
            "response": f"I understand you're asking about '{message}'. Let me help you with that! I can assist with college football analytics, predictions, and data insights. Could you tell me a bit more about what specific information you're looking for?",
            "suggestions": [
                "Analyze team performance",
                "Generate game predictions",
                "Show statistical insights",
                "Explain our capabilities"
            ]
        }

    def _create_contextual_response(self, query: str, context: Dict, agent_results: Dict) -> str:
        """Create contextual response based on query and agent results"""
        base_response = f"Based on your query about '{query}', I've analyzed the available information"

        if agent_results:
            base_response += " and gathered insights from our specialized analytics agents"

        base_response += ". Here's what I found:\n\n"

        # Add specific insights from agent results if available
        if "data_analysis" in agent_results:
            base_response += "📊 **Data Analysis**: Our analysis reveals interesting patterns in the data.\n"

        if "predictions" in agent_results:
            base_response += "🏈 **Predictions**: Our models show the following probability distributions.\n"

        return base_response + "\nWould you like me to dive deeper into any specific aspect?"

    def _generate_follow_up_suggestions(self, query: str, context: Dict) -> List[str]:
        """Generate relevant follow-up suggestions"""
        suggestions = [
            "Tell me more about these insights",
            "How does this compare to historical trends?",
            "What are the key factors driving these results?",
            "Can you visualize this data?"
        ]

        # Context-aware suggestions
        if "predictions" in query.lower():
            suggestions.extend([
                "What's the confidence level?",
                "How do different models compare?",
                "What are the betting implications?"
            ])

        return suggestions[:4]  # Return max 4 suggestions

    def _generate_related_topics(self, query: str, agent_results: Dict) -> List[str]:
        """Generate related topics based on query and results"""
        topics = [
            "Team Performance Metrics",
            "Statistical Trends Analysis",
            "Predictive Modeling",
            "College Football Rankings"
        ]

        if "predictions" in query.lower():
            topics.extend([
                "Betting Odds Analysis",
                "Model Accuracy Metrics",
                "Historical Prediction Performance"
            ])

        return topics[:3]  # Return max 3 related topics

    def _get_suggested_actions(self, intent: str) -> List[str]:
        """Get suggested actions for each intent"""
        action_map = {
            "data_analysis": [
                "Analyze team statistics",
                "Compare team performance",
                "Show season trends"
            ],
            "predictions": [
                "Predict game outcomes",
                "Generate probability distributions",
                "Include confidence intervals"
            ],
            "task_automation": [
                "Run automated analysis",
                "Generate reports",
                "Update datasets"
            ],
            "learning_guidance": [
                "Explain methodologies",
                "Provide tutorials",
                "Guide through analysis"
            ]
        }

        return action_map.get(intent, ["Start conversation", "Ask for clarification"])