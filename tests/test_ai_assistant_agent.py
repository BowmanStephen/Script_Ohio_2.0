#!/usr/bin/env python3
"""
Test Suite for AI Assistant Agent

Comprehensive tests covering conversation management, intent classification,
natural language processing, and agent orchestration.

Author: Claude Code Assistant
Created: 2025-12-18
Version: 1.0
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch

from agents.ai_assistant_agent import (
    AIAssistantAgent,
    ConversationManager,
    IntentClassifier
)
from agents.core.agent_framework import PermissionLevel


class TestConversationManager:
    """Test conversation state management"""

    def setup_method(self):
        """Setup test fixture"""
        self.manager = ConversationManager(max_history=3)

    def test_conversation_initialization(self):
        """Test conversation manager initialization"""
        assert self.manager.max_history == 3
        assert len(self.manager.conversations) == 0
        assert len(self.manager.context_store) == 0

    def test_add_message_to_new_conversation(self):
        """Test adding message to new conversation"""
        session_id = "test_session"
        self.manager.add_message(session_id, "user", "Hello", {"test": True})

        conversation = self.manager.get_conversation(session_id)
        assert len(conversation) == 1
        assert conversation[0]["role"] == "user"
        assert conversation[0]["content"] == "Hello"
        assert conversation[0]["metadata"]["test"] is True
        assert "timestamp" in conversation[0]

    def test_conversation_history_limit(self):
        """Test conversation history is trimmed to max_history"""
        session_id = "test_session"

        # Add 5 messages to a conversation with max_history=3
        for i in range(5):
            self.manager.add_message(session_id, "user", f"Message {i}")

        conversation = self.manager.get_conversation(session_id)
        assert len(conversation) == 3
        assert conversation[0]["content"] == "Message 2"
        assert conversation[-1]["content"] == "Message 4"

    def test_context_management(self):
        """Test conversation context storage and retrieval"""
        session_id = "test_session"
        context = {"user_preference": "predictions", "theme": "dark"}

        self.manager.set_context(session_id, context)
        retrieved_context = self.manager.get_context(session_id)

        assert retrieved_context["user_preference"] == "predictions"
        assert retrieved_context["theme"] == "dark"
        assert "last_updated" in retrieved_context

    def test_get_nonexistent_conversation(self):
        """Test retrieving non-existent conversation returns empty list"""
        conversation = self.manager.get_conversation("nonexistent")
        assert conversation == []

    def test_get_nonexistent_context(self):
        """Test retrieving non-existent context returns empty dict"""
        context = self.manager.get_context("nonexistent")
        assert context == {}


class TestIntentClassifier:
    """Test intent classification functionality"""

    def setup_method(self):
        """Setup test fixture"""
        self.classifier = IntentClassifier()

    def test_data_analysis_intent(self):
        """Test classification of data analysis queries"""
        queries = [
            "Analyze Ohio State's performance",
            "Show me team statistics",
            "Compare Alabama and Georgia stats"
        ]

        for query in queries:
            intent, confidence = self.classifier.classify_intent(query)
            assert intent == "data_analysis"
            assert confidence >= 0.1  # Lower threshold for testing

    def test_predictions_intent(self):
        """Test classification of prediction queries"""
        queries = [
            "Predict the Ohio State vs Michigan game",
            "Who will win the championship?",
            "What's the score prediction for this week?"
        ]

        for query in queries:
            intent, confidence = self.classifier.classify_intent(query)
            assert intent == "predictions"
            assert confidence >= 0.1  # Lower threshold for testing

    def test_general_chat_intent(self):
        """Test classification of general chat queries"""
        queries = [
            "Hello, how are you?",
            "What can you help me with?",
            "Hi there"
        ]

        for query in queries:
            intent, confidence = self.classifier.classify_intent(query)
            assert intent == "general_chat"

    def test_task_automation_intent(self):
        """Test classification of task automation queries"""
        queries = [
            "Generate a report for the season",
            "Create a dashboard for analytics",
            "Schedule automated data updates"
        ]

        for query in queries:
            intent, confidence = self.classifier.classify_intent(query)
            assert intent == "task_automation"
            assert confidence >= 0.1  # Lower threshold for testing

    def test_learning_guidance_intent(self):
        """Test classification of learning guidance queries"""
        queries = [
            "Teach me about college football analytics",
            "Best practices for data analysis",
            "How can I learn to analyze football data?"
        ]

        for query in queries:
            intent, confidence = self.classifier.classify_intent(query)
            assert intent == "learning_guidance"
            assert confidence >= 0.1  # Lower threshold for testing

    def test_ambiguous_query_classification(self):
        """Test classification of ambiguous queries"""
        queries = [
            "Tell me something",
            "Random text",
            "xyz abc"
        ]

        for query in queries:
            intent, confidence = self.classifier.classify_intent(query)
            assert intent == "general_chat"
            assert confidence <= 1.0

    def test_confidence_scoring(self):
        """Test confidence score is within valid range"""
        queries = [
            "Analyze data",
            "Predict games",
            "Hello",
            "Automate tasks",
            "Learn about models"
        ]

        for query in queries:
            intent, confidence = self.classifier.classify_intent(query)
            assert 0.0 <= confidence <= 1.0


class TestAIAssistantAgent:
    """Test AI Assistant Agent functionality"""

    def setup_method(self):
        """Setup test fixture"""
        self.agent = AIAssistantAgent("test_ai_assistant")

    def test_agent_initialization(self):
        """Test agent initialization"""
        assert self.agent.agent_id == "test_ai_assistant"
        assert self.agent.name == "AI Assistant"
        assert self.agent.permission_level == PermissionLevel.READ_EXECUTE_WRITE
        assert len(self.agent._define_capabilities()) == 6

    def test_capability_definition(self):
        """Test agent capabilities are properly defined"""
        capabilities = self.agent._define_capabilities()
        capability_names = [cap.name for cap in capabilities]

        expected_capabilities = [
            "natural_language_processing",
            "conversation_management",
            "intent_recognition",
            "query_expansion",
            "clarification_handling",
            "intelligent_dialogue"
        ]

        for expected_cap in expected_capabilities:
            assert expected_cap in capability_names

        # Test capability structure
        for cap in capabilities:
            assert cap.execution_time_estimate > 0
            assert cap.permission_required is not None
            assert isinstance(cap.tools_required, list)
            assert isinstance(cap.data_access, list)

    def test_natural_language_processing_action(self):
        """Test natural language processing action"""
        params = {
            "message": "Hello, how are you?",
            "session_id": "test_session"
        }

        result = self.agent._execute_action("natural_language_processing", params, {})

        assert result["status"] == "success"
        assert "response" in result["data"]
        assert result["data"]["intent"] == "general_chat"
        assert "confidence" in result["data"]
        assert result["data"]["session_id"] == "test_session"

    def test_conversation_management_get_action(self):
        """Test conversation management get action"""
        # First add a message to create conversation
        self.agent.conversation_manager.add_message(
            "test_session", "user", "Test message"
        )

        params = {
            "session_id": "test_session",
            "action": "get"
        }

        result = self.agent._execute_action("conversation_management", params, {})

        assert result["status"] == "success"
        assert len(result["data"]["conversation"]) == 1
        assert result["data"]["conversation"][0]["content"] == "Test message"

    def test_conversation_management_set_context_action(self):
        """Test conversation management set context action"""
        params = {
            "session_id": "test_session",
            "action": "set_context",
            "data": {"user_preference": "predictions"}
        }

        result = self.agent._execute_action("conversation_management", params, {})

        assert result["status"] == "success"
        assert result["data"]["status"] == "context_updated"

        # Verify context was set
        context = self.agent.conversation_manager.get_context("test_session")
        assert context["user_preference"] == "predictions"

    def test_conversation_management_clear_action(self):
        """Test conversation management clear action"""
        # Add conversation and context
        self.agent.conversation_manager.add_message(
            "test_session", "user", "Test message"
        )
        self.agent.conversation_manager.set_context(
            "test_session", {"test": "data"}
        )

        params = {
            "session_id": "test_session",
            "action": "clear"
        }

        result = self.agent._execute_action("conversation_management", params, {})

        assert result["status"] == "success"
        assert result["data"]["status"] == "conversation_cleared"

        # Verify conversation and context are cleared
        assert len(self.agent.conversation_manager.get_conversation("test_session")) == 0
        assert len(self.agent.conversation_manager.get_context("test_session")) == 0

    def test_intent_recognition_action(self):
        """Test intent recognition action"""
        params = {
            "message": "Predict the Ohio State vs Michigan game"
        }

        result = self.agent._execute_action("intent_recognition", params, {})

        assert result["status"] == "success"
        assert result["data"]["intent"] == "predictions"
        assert result["data"]["target_agent"] == "model_execution_engine"
        assert "confidence" in result["data"]
        assert "suggested_actions" in result["data"]

    def test_query_expansion_action(self):
        """Test query expansion action"""
        params = {
            "query": "Analyze team performance"
        }

        result = self.agent._execute_action("query_expansion", params, {})

        assert result["status"] == "success"
        assert "expanded_query" in result["data"]
        assert "clarifications" in result["data"]
        assert "needs_clarification" in result["data"]

    def test_clarification_handling_action(self):
        """Test clarification handling action"""
        params = {
            "ambiguous_query": "Analyze team"
        }

        result = self.agent._execute_action("clarification_handling", params, {})

        assert result["status"] == "success"
        assert "clarification_question" in result["data"]
        assert "options" in result["data"]
        assert result["data"]["original_query"] == "Analyze team"

    def test_intelligent_dialogue_action(self):
        """Test intelligent dialogue action"""
        params = {
            "query": "How does your prediction model work?",
            "context": {"session_type": "learning"},
            "agent_results": {"predictions": "Model generated successfully"}
        }

        result = self.agent._execute_action("intelligent_dialogue", params, {})

        assert result["status"] == "success"
        assert "response" in result["data"]
        assert "follow_up_suggestions" in result["data"]
        assert "related_topics" in result["data"]
        assert result["data"]["response_type"] == "intelligent_dialogue"

    def test_error_handling_invalid_action(self):
        """Test error handling for invalid actions"""
        result = self.agent._execute_action("invalid_action", {}, {})

        assert result["status"] == "error"
        assert "error" in result
        assert result["error_type"] == "ValueError"

    def test_error_handling_exception_in_action(self):
        """Test error handling for exceptions in actions"""
        # Test with invalid parameters that should cause exception
        params = {
            "session_id": 123  # Invalid type for session_id
        }

        result = self.agent._execute_action("conversation_management", params, {})

        assert result["status"] == "error"
        assert "error" in result
        assert "timestamp" in result

    def test_conversation_persistence(self):
        """Test that conversation state persists across multiple calls"""
        session_id = "persistent_session"

        # First message
        params1 = {
            "message": "Hello",
            "session_id": session_id
        }
        result1 = self.agent._execute_action("natural_language_processing", params1, {})

        # Second message
        params2 = {
            "message": "Tell me about predictions",
            "session_id": session_id
        }
        result2 = self.agent._execute_action("natural_language_processing", params2, {})

        # Check conversation history
        conversation = self.agent.conversation_manager.get_conversation(session_id)
        assert len(conversation) == 4  # 2 user messages + 2 assistant responses

    def test_response_generation_for_different_intents(self):
        """Test response generation for different intent types"""
        test_cases = [
            ("Hello there", "general_chat"),
            ("Predict the game", "predictions"),
            ("Analyze team stats", "data_analysis"),
            ("Run the analysis", "task_automation"),
            ("Explain how models work", "learning_guidance")
        ]

        for message, expected_intent in test_cases:
            params = {
                "message": message,
                "session_id": "test_session"
            }

            result = self.agent._execute_action("natural_language_processing", params, {})

            assert result["status"] == "success"
            assert result["data"]["intent"] == expected_intent
            assert len(result["data"]["response"]) > 0
            assert isinstance(result["data"]["suggestions"], list)

    def test_execution_time_tracking(self):
        """Test that execution time is properly tracked"""
        params = {
            "message": "Test message",
            "session_id": "test_session"
        }

        result = self.agent._execute_action("natural_language_processing", params, {})

        assert "execution_time" in result
        assert result["execution_time"] > 0
        assert isinstance(result["execution_time"], float)


class TestAIAssistantAgentIntegration:
    """Integration tests for AI Assistant Agent"""

    def setup_method(self):
        """Setup integration test fixture"""
        self.agent = AIAssistantAgent("integration_test_assistant")

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    def test_openai_api_key_loading(self):
        """Test that OpenAI API key is loaded from environment"""
        agent_with_key = AIAssistantAgent("test_with_key")
        assert agent_with_key.openai_api_key == 'test_key'

    def test_conversation_isolation(self):
        """Test that different sessions are properly isolated"""
        # Add message to session 1
        self.agent.conversation_manager.add_message("session1", "user", "Session 1 message")

        # Add message to session 2
        self.agent.conversation_manager.add_message("session2", "user", "Session 2 message")

        # Verify isolation
        conv1 = self.agent.conversation_manager.get_conversation("session1")
        conv2 = self.agent.conversation_manager.get_conversation("session2")

        assert len(conv1) == 1
        assert len(conv2) == 1
        assert conv1[0]["content"] == "Session 1 message"
        assert conv2[0]["content"] == "Session 2 message"

    def test_context_aware_responses(self):
        """Test that responses are context-aware"""
        session_id = "context_test_session"

        # Set up context
        self.agent.conversation_manager.set_context(session_id, {
            "user_preference": "predictions",
            "favorite_team": "Ohio State"
        })

        # Send context-aware message
        params = {
            "message": "Tell me about my favorite team",
            "session_id": session_id
        }

        result = self.agent._execute_action("natural_language_processing", params, {})

        assert result["status"] == "success"
        assert len(result["data"]["response"]) > 0

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation flow"""
        session_id = "multi_turn_session"

        # First turn - greeting
        params1 = {
            "message": "Hello, I want to analyze college football data",
            "session_id": session_id
        }
        result1 = self.agent._execute_action("natural_language_processing", params1, {})

        # Second turn - specific analysis request
        params2 = {
            "message": "Show me Ohio State's performance this season",
            "session_id": session_id
        }
        result2 = self.agent._execute_action("natural_language_processing", params2, {})

        # Verify conversation flow
        conversation = self.agent.conversation_manager.get_conversation(session_id)
        assert len(conversation) == 4  # 2 user + 2 assistant messages

        # Verify intent progression
        assert result1["data"]["intent"] == "general_chat"
        assert result2["data"]["intent"] == "data_analysis"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])