"""The assistant as a LangGraph state machine: agent <-> tools loop with a hard step limit."""
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.tools import ToolKit
from app.core.config import get_settings
from app.llm import LLMProvider
from app.models import User

SYSTEM = (
    "You are the CRM assistant for a pharmaceutical field rep, {name}. Today is {today}.\n"
    "You help log and review interactions with doctors (HCPs), schedule follow-ups, and decide who to visit next.\n"
    "Rules:\n"
    "- To record or change data, call a propose_* tool. Those only create a proposal the rep must confirm, so after "
    "calling one, tell the rep briefly what you proposed and that they need to confirm it. Never claim it is saved.\n"
    "- Use read tools for questions about history, follow-ups, products or who needs a visit. Never invent data.\n"
    "- If a doctor can't be found, say so and ask for clarification instead of guessing.\n"
    "- Be concise and practical."
)


def build_graph(llm: LLMProvider, toolkit: ToolKit):
    tools = toolkit.tools()
    model = llm.chat.bind_tools(tools)

    async def agent(state: MessagesState):
        return {"messages": [await model.ainvoke(state["messages"])]}

    g = StateGraph(MessagesState)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(tools))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    g.add_edge("tools", "agent")
    return g.compile()


async def run_agent(llm: LLMProvider, toolkit: ToolKit, user: User, history: list[dict], message: str) -> AsyncIterator[dict]:
    """Yields UI events: tool_call, tool_result, token, error."""
    from datetime import date

    msgs = [SystemMessage(SYSTEM.format(name=user.name, today=date.today().isoformat()))]
    for m in history[-8:]:
        msgs.append(HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]))
    msgs.append(HumanMessage(message))
    graph = build_graph(llm, toolkit)
    cfg = {"recursion_limit": get_settings().agent_max_steps * 2 + 1}
    streamed_any = False
    last_text = ""
    try:
        async for mode, payload in graph.astream({"messages": msgs}, config=cfg, stream_mode=["messages", "updates"]):
            if mode == "messages":
                chunk, meta = payload
                if meta.get("langgraph_node") == "agent" and isinstance(chunk, AIMessageChunk) and chunk.content and not chunk.tool_call_chunks:
                    streamed_any = True
                    yield {"type": "token", "text": str(chunk.content)}
            else:
                for node, update in payload.items():
                    for m in update.get("messages", []):
                        if node == "agent" and isinstance(m, AIMessage):
                            for tc in m.tool_calls:
                                yield {"type": "tool_call", "name": tc["name"], "args": tc["args"]}
                            if not m.tool_calls:
                                last_text = str(m.content)
                        elif isinstance(m, ToolMessage):
                            yield {"type": "tool_result", "name": m.name, "content": str(m.content)[:500]}
        if not streamed_any and last_text:   # models/fakes that don't stream still deliver the answer
            yield {"type": "token", "text": last_text}
    except Exception as e:
        yield {"type": "error", "message": f"The assistant hit a problem: {str(e)[:200]}"}
