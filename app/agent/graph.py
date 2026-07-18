import os
from langgraph.prebuilt import create_react_agent
from app.agent.tools import (
    log_interaction,
    edit_interaction,
    get_hcp_history,
    summarize_interaction,
    get_all_interactions
)

from app.agent.llm import llm

tools = [log_interaction, edit_interaction, get_all_interactions, summarize_interaction, get_hcp_history]

system_prompt = """You are a CRM assistant for pharmaceutical field representatives.
You help log and manage interactions with Healthcare Professionals (HCPs/doctors).
Use only ONE tool per user request. Do not chain multiple tool calls.
After calling a tool, return the result directly to the user without calling more tools.
Always extract rep_id from the user message."""

agent = create_react_agent(llm, tools, prompt=system_prompt)

def run_agent(message: str, rep_id: int) -> str:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"{message}. My rep_id is {rep_id}"}]},
        config={"recursion_limit": 50}
    )
    return result["messages"][-1].content