"""
AI Retail Analyst Agent API Endpoints
Provides multi-turn conversational intelligence powered by LangGraph, Gemini, and database tools.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.models import User
from app.schemas import AgentChatRequest, AgentChatResponse
from app.agent.agent_service import chat_with_agent, clear_conversation

router = APIRouter()


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Chat with AI Retail Analyst",
    description="Invokes LangGraph workflow with Gemini and domain analytics tools. Returns grounded response, tools invoked, and structured domain data.",
)
def chat(
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        response = chat_with_agent(
            message=payload.message,
            conversation_id=payload.conversation_id,
        )
        return AgentChatResponse(
            answer=response["answer"],
            tools_used=response["tools_used"],
            data=response["data"],
            conversation_id=response["conversation_id"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Analyst engine error: {str(e)}",
        )


@router.delete(
    "/conversations/{conversation_id}",
    summary="Clear conversation history",
    description="Resets the in-memory context for a given conversation session.",
)
def reset_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    cleared = clear_conversation(conversation_id)
    return {"status": "success", "cleared": cleared, "conversation_id": conversation_id}
