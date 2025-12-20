#!/usr/bin/env python3
"""
AI Assistant API Server

REST API endpoints for the AI Assistant agent, providing HTTP access
to conversational AI capabilities.

Author: Claude Code Assistant
Created: 2025-12-18
Version: 1.0
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ai_assistant_agent import AIAssistantAgent
from agents.core.agent_framework import PermissionLevel

# Initialize FastAPI app
app = FastAPI(
    title="Script Ohio 2.0 AI Assistant API",
    description="REST API for the AI Assistant conversational interface",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security (optional - can be disabled for development)
security = HTTPBearer(auto_error=False)

# Initialize AI Assistant
ai_assistant = AIAssistantAgent("api_ai_assistant")


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation persistence")
    context: Optional[Dict] = Field(None, description="Additional context for the conversation")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant response")
    intent: str = Field(..., description="Classified user intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Intent confidence score")
    session_id: str = Field(..., description="Session ID")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    timestamp: str = Field(..., description="Response timestamp")


class ConversationResponse(BaseModel):
    conversation: List[Dict] = Field(..., description="Conversation history")
    context: Dict = Field(..., description="Conversation context")
    session_id: str = Field(..., description="Session ID")


class IntentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Message to classify")


class IntentResponse(BaseModel):
    intent: str = Field(..., description="Classified intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    target_agent: str = Field(..., description="Recommended target agent")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested actions")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    timestamp: str = Field(..., description="Error timestamp")


# Helper functions
def get_session_id(request: ChatRequest) -> str:
    """Get or generate session ID"""
    if request.session_id:
        return request.session_id
    return f"api_session_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def create_error_response(message: str, error_type: str = "ValidationError") -> ErrorResponse:
    """Create standardized error response"""
    return ErrorResponse(
        error=message,
        error_type=error_type,
        timestamp=datetime.utcnow().isoformat()
    )


# Authentication dependency (optional for development)
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user (disabled for development)"""
    # In production, implement proper JWT validation here
    return {"user_id": "demo_user", "permissions": ["read", "execute"]}


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai_assistant_api",
        "version": "1.0.0"
    }


# Chat endpoint
@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Process a chat message through the AI Assistant

    Args:
        request: Chat request containing message and optional session_id
        current_user: Authenticated user information

    Returns:
        AI assistant response with intent classification and suggestions
    """
    try:
        session_id = get_session_id(request)

        # Set context if provided
        if request.context:
            ai_assistant._execute_action("conversation_management", {
                "session_id": session_id,
                "action": "set_context",
                "data": request.context
            }, current_user)

        # Process message through AI Assistant
        result = ai_assistant._execute_action("natural_language_processing", {
            "message": request.message,
            "session_id": session_id
        }, current_user)

        if result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI Assistant processing failed: {result.get('error', 'Unknown error')}"
            )

        data = result["data"]

        return ChatResponse(
            response=data["response"],
            intent=data["intent"],
            confidence=data["confidence"],
            session_id=session_id,
            suggestions=data.get("suggestions", []),
            timestamp=result["timestamp"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


# Get conversation history
@app.get("/conversation/{session_id}", response_model=ConversationResponse, tags=["Conversation"])
async def get_conversation(
    session_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get conversation history for a session

    Args:
        session_id: Session identifier
        current_user: Authenticated user information

    Returns:
        Conversation history and context
    """
    try:
        result = ai_assistant._execute_action("conversation_management", {
            "session_id": session_id,
            "action": "get"
        }, current_user)

        if result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        data = result["data"]

        return ConversationResponse(
            conversation=data["conversation"],
            context=data["context"],
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


# Clear conversation
@app.delete("/conversation/{session_id}", tags=["Conversation"])
async def clear_conversation(
    session_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Clear conversation history for a session

    Args:
        session_id: Session identifier
        current_user: Authenticated user information

    Returns:
        Success status
    """
    try:
        result = ai_assistant._execute_action("conversation_management", {
            "session_id": session_id,
            "action": "clear"
        }, current_user)

        if result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear conversation"
            )

        return {
            "status": "success",
            "message": "Conversation cleared successfully",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


# Classify intent
@app.post("/classify-intent", response_model=IntentResponse, tags=["Analysis"])
async def classify_intent(
    request: IntentRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Classify user intent without storing conversation

    Args:
        request: Intent classification request
        current_user: Authenticated user information

    Returns:
        Intent classification with confidence and recommendations
    """
    try:
        result = ai_assistant._execute_action("intent_recognition", {
            "message": request.message
        }, current_user)

        if result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Intent classification failed"
            )

        data = result["data"]

        return IntentResponse(
            intent=data["intent"],
            confidence=data["confidence"],
            target_agent=data["target_agent"],
            suggested_actions=data.get("suggested_actions", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


# Expand query
@app.post("/expand-query", tags=["Analysis"])
async def expand_query(
    request: IntentRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Expand ambiguous query with clarifications

    Args:
        request: Query expansion request
        current_user: Authenticated user information

    Returns:
        Expanded query with clarifications if needed
    """
    try:
        result = ai_assistant._execute_action("query_expansion", {
            "query": request.message,
            "context": {}
        }, current_user)

        if result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Query expansion failed"
            )

        return result["data"]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


# Get agent capabilities
@app.get("/capabilities", tags=["System"])
async def get_capabilities():
    """
    Get AI Assistant capabilities and available actions

    Returns:
        List of available capabilities
    """
    try:
        capabilities = ai_assistant._define_capabilities()

        return {
            "agent_id": ai_assistant.agent_id,
            "agent_name": ai_assistant.agent_name,
            "permission_level": ai_assistant.permission_level.value,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "execution_time_estimate": cap.execution_time_estimate,
                    "required_permissions": [p.value for p in cap.required_permissions],
                    "parameters": cap.parameters,
                    "returns": cap.returns
                }
                for cap in capabilities
            ],
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get capabilities: {str(e)}"
        )


# System status
@app.get("/status", tags=["System"])
async def get_system_status():
    """
    Get system status and health information

    Returns:
        System status and performance metrics
    """
    try:
        # Get basic agent status
        agent_status = {
            "agent_id": ai_assistant.agent_id,
            "agent_name": ai_assistant.agent_name,
            "status": "active",
            "uptime": time.time(),
            "memory_usage": "N/A",  # Could be implemented with psutil
            "api_version": "1.0.0"
        }

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_status,
            "endpoints": [
                "POST /chat - Process chat messages",
                "GET /conversation/{session_id} - Get conversation history",
                "DELETE /conversation/{session_id} - Clear conversation",
                "POST /classify-intent - Classify user intent",
                "POST /expand-query - Expand ambiguous queries",
                "GET /capabilities - Get agent capabilities",
                "GET /status - Get system status",
                "GET /health - Health check"
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            message="An unexpected error occurred",
            error_type="InternalServerError"
        ).dict()
    )


# Run the app
if __name__ == "__main__":
    import uvicorn

    print("🏈 Starting Script Ohio 2.0 AI Assistant API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔗 ReDoc Documentation: http://localhost:8000/redoc")

    uvicorn.run(
        "ai_assistant_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )