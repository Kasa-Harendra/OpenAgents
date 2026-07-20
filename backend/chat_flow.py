import sys
import os
from typing import List, Dict, Any, TypedDict

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.models import websocket_message
from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts.prompts import get_agent_system_prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

class ChatState(TypedDict):
    prompt: str
    history: List[Dict[str, Any]]
    messages: List[BaseMessage]
    response: str
    error: str

async def chat_node(state: ChatState, config: RunnableConfig) -> Dict:
    callback = config.get("configurable", {}).get("callback")
    
    model = get_agent_llm('Coordinator')
    if not model:
        error_msg = "Coordinator LLM not configured for chat."
        if callback:
            await callback(websocket_message(type="error", content=error_msg))
        return {"error": error_msg}
        
    system_prompt_str = get_agent_system_prompt("ChatMode", "You are helpful assistant")
    messages = [SystemMessage(content=system_prompt_str)]
    
    for msg in state.get("history", []):
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "agent":
            messages.append(AIMessage(content=content))
            
    messages.append(HumanMessage(content=state["prompt"]))
    
    try:
        response_content = ""
        async for chunk in model.astream(messages):
            if chunk.content:
                response_content += chunk.content
                if callback:
                    await callback(websocket_message(
                        type="content_chunk",
                        agent_name="Coordinator (Chat)",
                        chunk=chunk.content
                    ))
        
        if callback:
            await callback(websocket_message(
                type="agent_response",
                agent_name="Coordinator (Chat)",
                content=response_content
            ))
            await callback(websocket_message(type="complete", content="Chat completed."))
            
        return {"response": response_content, "error": ""}
        
    except Exception as e:
        error_msg = f"Chat error: {str(e)}"
        if callback:
            await callback(websocket_message(type="error", content=error_msg))
        return {"error": error_msg}


# --- Graph Compilation ---
workflow = StateGraph(ChatState)
workflow.add_node("chat_node", chat_node)
workflow.add_edge(START, "chat_node")
workflow.add_edge("chat_node", END)

chat_graph = workflow.compile()

async def handle_general_chat(prompt: str, history: List[Dict[str, Any]], callback):
    initial_state = {
        "prompt": prompt,
        "history": history,
        "messages": [],
        "response": "",
        "error": ""
    }
    config = {"configurable": {"callback": callback}}
    
    await chat_graph.ainvoke(initial_state, config=config)
