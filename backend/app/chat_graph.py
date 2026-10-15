"""LangGraph chat state and thread helpers."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Literal, TypedDict
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.pregel import Pregel

from app.agents import AGENTS, build_system_prompt

AgentId = Literal["anton", "marina", "pavel", "vera"]
logger = logging.getLogger(__name__)


class ChatTurn(TypedDict):
    message: str
    reply: str
    question_id: str | None


def build_chat_graph(model: Any, checkpointer: BaseCheckpointSaver) -> Pregel:
    async def call_model(state: MessagesState, config: dict[str, Any]) -> dict[str, list]:
        agent_id: AgentId = config["configurable"]["agent_id"]
        result = await model.ainvoke(
            [SystemMessage(content=build_system_prompt(agent_id)), *state["messages"]]
        )
        if not isinstance(result.content, str) or not result.content.strip():
            raise ValueError("Empty model response")
        return {"messages": [result]}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")
    builder.add_edge("call_model", END)
    return builder.compile(checkpointer=checkpointer)


def thread_id_for(session_id: UUID, agent_id: AgentId) -> str:
    digest = hashlib.sha256(f"{session_id}:{agent_id}".encode("utf-8")).hexdigest()
    return f"chat-{digest}"


def graph_config(session_id: UUID, agent_id: AgentId) -> dict[str, dict[str, str]]:
    return {
        "configurable": {
            "thread_id": thread_id_for(session_id, agent_id),
            "agent_id": agent_id,
        }
    }


async def invoke_chat(
    graph: Pregel,
    session_id: UUID,
    agent_id: AgentId,
    message: str,
    question_id: str | None,
) -> str:
    config = graph_config(session_id, agent_id)
    before = await graph.aget_state(config)
    previous_messages = before.values.get("messages", [])
    metadata = {"question_id": question_id} if question_id else {}
    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=message, additional_kwargs=metadata)]},
            config,
        )
    except Exception:
        try:
            await graph.aupdate_state(
                config,
                {
                    "messages": [
                        RemoveMessage(id=REMOVE_ALL_MESSAGES),
                        *previous_messages,
                    ]
                },
            )
        except Exception:
            logger.exception("Failed to roll back an incomplete chat turn")
        raise

    reply = result["messages"][-1].content
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("Empty model response")
    return reply.strip()


async def load_history(
    graph: Pregel, session_id: UUID, agent_id: AgentId
) -> list[ChatTurn]:
    snapshot = await graph.aget_state(graph_config(session_id, agent_id))
    turns: list[ChatTurn] = []
    pending_message: HumanMessage | None = None
    for message in snapshot.values.get("messages", []):
        if isinstance(message, HumanMessage):
            pending_message = message
        elif isinstance(message, AIMessage) and pending_message is not None:
            if isinstance(pending_message.content, str) and isinstance(message.content, str):
                turns.append(
                    {
                        "message": pending_message.content,
                        "reply": message.content,
                        "question_id": pending_message.additional_kwargs.get("question_id"),
                    }
                )
            pending_message = None
    return turns


async def clear_session_threads(checkpointer: BaseCheckpointSaver, session_id: UUID) -> None:
    for agent_id in AGENTS:
        await checkpointer.adelete_thread(thread_id_for(session_id, agent_id))
