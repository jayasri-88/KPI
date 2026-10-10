"""
Agent Service
Handles multi-turn conversation memory, executes the LangGraph workflow,
and formats structured outputs with tools and data inspectability.
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
    messages_from_dict,
    messages_to_dict,
)

from app.agent.graph import retail_agent_graph
from app.core.cache import TTL_AI_SESSION, cache_manager

# In-memory conversation store for multi-turn sessions (fallback if Redis offline)
_CONVERSATIONS: Dict[str, List[Any]] = {}
MAX_HISTORY_MESSAGES = 16


def _load_history(conversation_id: str) -> List[Any]:
    """Loads session history from Redis, falling back to local memory."""
    cache_key = cache_manager.build_key("ai:session", id=conversation_id)
    cached_dicts = cache_manager.get(cache_key)
    if cached_dicts and isinstance(cached_dicts, list):
        try:
            return messages_from_dict(cached_dicts)
        except Exception:
            pass
    return _CONVERSATIONS.get(conversation_id, [])


def _save_history(conversation_id: str, messages: List[Any]) -> None:
    """Persists session history to Redis (24h TTL) and local memory."""
    trimmed = messages[-MAX_HISTORY_MESSAGES:]
    _CONVERSATIONS[conversation_id] = trimmed

    cache_key = cache_manager.build_key("ai:session", id=conversation_id)
    try:
        dicts = messages_to_dict(trimmed)
        cache_manager.set(cache_key, dicts, ttl=TTL_AI_SESSION)
    except Exception:
        pass


def chat_with_agent(
    message: str,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a turn in the AI Retail Analyst conversation.
    Returns the grounded answer, tools called, and structured tool data.
    """
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    history = _load_history(conversation_id)


    # Append new user message
    user_msg = HumanMessage(content=message.strip())
    current_messages = history + [user_msg]

    # Run LangGraph State Machine
    final_state = retail_agent_graph.invoke({"messages": current_messages})
    all_messages = final_state["messages"]

    # Extract final answer
    last_message = all_messages[-1]
    raw_answer = last_message.content if isinstance(last_message, AIMessage) else str(last_message)
    if isinstance(raw_answer, list):
        text_parts = []
        for part in raw_answer:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
            else:
                text_parts.append(str(part))
        final_answer = "\n".join(text_parts).strip()
    elif not isinstance(raw_answer, str):
        final_answer = str(raw_answer)
    else:
        final_answer = raw_answer

    # Extract tools used and structured tool data returned in this invocation
    tools_used: List[str] = []
    structured_data: List[Dict[str, Any]] = []

    # Look through the messages generated in this run
    for m in all_messages:
        # Check for tool calls made by the model
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                t_name = tc.get("name")
                if t_name and t_name not in tools_used:
                    tools_used.append(t_name)

        # Check for ToolMessage results
        if isinstance(m, ToolMessage):
            tool_name = m.name or "tool"
            raw_content = m.content
            try:
                # If tool content is JSON string, parse it
                if isinstance(raw_content, str):
                    parsed_content = json.loads(raw_content)
                else:
                    parsed_content = raw_content
            except Exception:
                parsed_content = raw_content

            structured_data.append({
                "tool": tool_name,
                "output": parsed_content,
            })

    # Update session history in Redis and local memory
    _save_history(conversation_id, all_messages)

    return {
        "answer": final_answer,
        "tools_used": tools_used,
        "data": structured_data,
        "conversation_id": conversation_id,
    }


def clear_conversation(conversation_id: str) -> bool:
    """Clears history for a given conversation session from Redis and local memory."""
    cache_key = cache_manager.build_key("ai:session", id=conversation_id)
    cache_manager.delete(cache_key)
    if conversation_id in _CONVERSATIONS:
        del _CONVERSATIONS[conversation_id]
        return True
    return True

