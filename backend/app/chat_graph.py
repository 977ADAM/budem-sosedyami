"""Request-scoped LangGraph chat; all conversation history comes from the client."""
from __future__ import annotations

from typing import Any, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.pregel import Pregel

from app.agents import build_system_prompt

AgentId = Literal["anton", "marina", "pavel", "vera"]


class ChatTurn(TypedDict):
    message: str
    reply: str


def build_chat_graph(model: Any) -> Pregel:
    async def call_model(state: MessagesState, config: RunnableConfig) -> dict[str, list]:
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
    return builder.compile()


async def invoke_chat(graph: Pregel, agent_id: AgentId, message: str, history: list[ChatTurn]) -> str:
    messages = []
    for turn in history:
        messages.extend([HumanMessage(content=turn["message"]), AIMessage(content=turn["reply"])])
    messages.append(HumanMessage(content=message))
    result = await graph.ainvoke(
        {"messages": messages}, {"configurable": {"agent_id": agent_id}}
    )
    reply = result["messages"][-1].content
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("Empty model response")
    return reply.strip()
