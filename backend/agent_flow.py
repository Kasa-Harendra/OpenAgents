import sys
import os
import asyncio
import uuid
from typing import List, Dict, Any, TypedDict, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.models import websocket_message
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph, START, END
from langchain.agents.middleware.types import (AgentState, _InputAgentState, _OutputAgentState)
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

# --- Helper Functions ---
def _is_agent_config_error(error_str: str) -> bool:
    """Helper to determine if an error is likely a configuration or provider issue."""
    error_lower = error_str.lower()
    keywords = [
        "api_key", "api key", "auth", "unauthorized", "quota", "limit", 
        "unreachable", "connection", "timeout", "model", "not found", 
        "does not exist", "404", "status code", "refused", "rate", "token", 
        "invalid", "forbidden", "dns", "proxy", "bad request", "service unavailable"
    ]
    return any(kw in error_lower for kw in keywords)

async def _get_agent(agent_name: str) -> CompiledStateGraph[AgentState[Any], Any, _InputAgentState, _OutputAgentState[Any]]:
    match(agent_name):
        case "FileSystemAgent":
            from backend.agents.file_system_agent import get_agent as get_file_system_agent
            return get_file_system_agent()
        case "TerminalAgent":
            from backend.agents.terminal_agent import get_agent as get_terminal_agent
            return get_terminal_agent()
        case "ResearchAgent":
            from backend.agents.web_search_agent import get_agent as get_web_search_agent
            return get_web_search_agent()
        case "IntegratorAgent":
            from backend.agents.integrator_agent import get_agent as get_integrator_agent
            return await get_integrator_agent()
        case _:
            from backend.agents.orchestrator_agent import orchestrator
            return orchestrator
        
def _process_subtask(sub_task: str, context: List[Dict]) -> str:
    context_prompt_template = """
{response}
"""
    prompt_template = PromptTemplate.from_template(context_prompt_template)

    if len(context) != 0:
        prev_rec = context[-1]
        print(prev_rec)
        processed_prompt = prompt_template.invoke(
            {'agent': prev_rec['agent_name'], 'response': prev_rec['response']}
        )

    return sub_task if len(context) == 0 else sub_task + "\n" + str(processed_prompt)

def _evaluate_response(prompt: str, response: str):
    from backend.agents.evaluation_agent import agent as evaluation_agent
    try:
        verdict = evaluation_agent.evaluate(
            prompt=prompt,
            response=response
        )

        return True if verdict == "Proceed" else False
    except Exception as e:
        print(f"Error in evaluation_agent: {e}")
        return True

async def _invoke_agent(agent: CompiledStateGraph, prompt: str, context: list, callback=None):
    MAX_RETRIES = 3

    while MAX_RETRIES > 0:
        try:
            agent_rec = {"id": str(uuid.uuid1()), "agent_name": agent.name, "response": ""}
            
            # Using astream_events to capture tokens and tool outputs
            async for event in agent.astream_events(
                {
                    "messages": [
                        ("user", prompt)
                    ]
                },
                version="v2",
                config={"recursion_limit": 100}
            ):
                kind = event["event"]
                
                # Token streaming for the final response
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        agent_rec["response"] += content
                        if callback:
                            await callback(websocket_message(
                                type="content_chunk",
                                agent_name=agent.name,
                                chunk=content
                            ))
                
                # Tool output streaming
                elif kind == "on_tool_end":
                    tool_output = event["data"]["output"]
                    if callback:
                        await callback(websocket_message(
                            type="tool_output",
                            agent_name=agent.name,
                            content=str(tool_output)
                        ))
                
                elif kind == "on_tool_error":
                    tool_error = event["data"]["error"]
                    if callback:
                        await callback(websocket_message(
                            type="tool_error",
                            agent_name=agent.name,
                            content=str(tool_error)
                        ))

                # Status updates
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    if callback:
                        await callback(websocket_message(
                            type="status",
                            content=f"Agent {agent.name} is running tool: {tool_name}..."
                        ))

            if(_evaluate_response(prompt, agent_rec["response"])):
                context.append(agent_rec)
                if callback:
                    await callback(websocket_message(
                        type="agent_response",
                        agent_name=agent.name,
                        content=agent_rec["response"]
                    ))
                return True # Success message
            else:
                MAX_RETRIES -= 1

        except Exception as e:
            error_str = str(e)
            print(f"Error occured in {agent.name}: {error_str}")
            
            is_agent_error = _is_agent_config_error(error_str)
            
            if callback:
                await callback(websocket_message(
                    type="agent_error" if is_agent_error else "error",
                    agent_name=agent.name,
                    content=error_str
                 ))
            MAX_RETRIES -= 1
    return False # Failure message


# --- State Definition ---
class SubTask(TypedDict):
    agent: str
    subtask: str

class OpenAgentsState(TypedDict):
    prompt: str
    base_directory: str
    history: List[Dict]
    
    tasks: List[SubTask]
    current_task_index: int
    context: List[Dict]
    
    error: str
    status: str

# --- Nodes ---
async def decompose_task_node(state: OpenAgentsState, config: RunnableConfig) -> Dict:
    callback = config.get("configurable", {}).get("callback")
    
    prompt = state["prompt"]
    base_directory = state["base_directory"]
    history = state["history"]

    if callback:
        await callback(websocket_message(type="status", content="Decomposing task..."))
        
    print(f"DEBUG: calling decompose_task with prompt: {prompt}")
    try:
        from backend.agents.orchestrator_agent import orchestrator
        loop = asyncio.get_running_loop()
        tasks = await loop.run_in_executor(None, orchestrator.decompose_task, prompt, base_directory, history)
        print(f"DEBUG: decomposed tasks: {tasks}")
        
        if callback:
            await callback(websocket_message(type="tasks_decomposed", content=tasks))
            
        return {"tasks": tasks, "current_task_index": 0, "error": ""}
    except Exception as e:
        error_str = str(e)
        print(f"DEBUG: Error in decompose_task: {error_str}")
        is_agent_error = _is_agent_config_error(error_str)
        if callback:
            await callback(websocket_message(
                type="agent_error" if is_agent_error else "error", 
                content=f"Decomposition failed: {error_str}"
            ))
        return {"error": error_str}

async def execute_subtask_node(state: OpenAgentsState, config: RunnableConfig) -> Dict:
    callback = config.get("configurable", {}).get("callback")
    
    tasks = state.get("tasks", [])
    current_index = state.get("current_task_index", 0)
    context = list(state.get("context", []))
    
    if current_index >= len(tasks):
        return {}
        
    task = tasks[current_index]
    agent_name = task.get("agent")
    sub_task = task.get("subtask")
    
    print(f"DEBUG: processing task for agent: {agent_name}")
    
    # Check if agent is configured
    from backend.agents.model_providers.agent_llms import get_agent_llm
    if agent_name != "Coordinator" and not get_agent_llm(agent_name):
        error_msg = f"Agent '{agent_name}' is not configured. Please go to Settings to set it up."
        if callback:
            await callback(websocket_message(type="agent_error", content=error_msg))
        return {"error": error_msg}

    agent = await _get_agent(agent_name)
    if agent is None:
        error_msg = f"Agent '{agent_name}' failed to initialize. Please check its configuration."
        if callback:
            await callback(websocket_message(type="agent_error", content=error_msg))
        return {"error": error_msg}
        
    processed_sub_task = _process_subtask(sub_task, context)

    if callback:
        await callback(websocket_message(type="agent_start", agent_name=agent_name, content=sub_task))

    if agent_name in ["FileSystemAgent", "TerminalAgent", "ResearchAgent", "IntegratorAgent"]:
        print(f"DEBUG: invoking {agent_name}")
        if not (await _invoke_agent(agent, processed_sub_task, context, callback)):
            error_msg = f"{agent_name} failed to do - {sub_task}"
            return {"error": error_msg}

    elif agent_name in ["BrowserAgent"]:
        print(f"DEBUG: invoking BrowserAgent subprocess")
        try:
            python_exe = sys.executable
            script_path = os.path.join(os.path.dirname(__file__), 'agents', 'browser_agent.py')
            
            process = await asyncio.create_subprocess_exec(
                python_exe, script_path, processed_sub_task,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            res = stdout.decode().strip()
            err = stderr.decode().strip()
            
            if process.returncode == 0 and res != "Failed":
                print(f"DEBUG: BrowserAgent subprocess output: {res}")
                context.append({"id": str(uuid.uuid1()), "agent_name": "BrowserAgent", "response": res})
                if callback:
                    await callback(websocket_message(type="agent_response", agent_name="BrowserAgent", content=res))
            else:
                error_msg = f"BrowserAgent failed: {err if err else res}"
                print(f"DEBUG: {error_msg}")
                if callback:
                    await callback(websocket_message(type="agent_error", content=error_msg))
                return {"error": error_msg}
        except Exception as e:
            error_msg = f"Error launching BrowserAgent subprocess: {e}"
            print(f"DEBUG: {error_msg}")
            if callback:
                await callback(websocket_message(type="agent_error", content=error_msg))
            return {"error": error_msg}

    return {"context": context, "current_task_index": current_index + 1}

def router_node(state: OpenAgentsState):
    if state.get("error"):
        return END
    
    tasks = state.get("tasks", [])
    current_index = state.get("current_task_index", 0)
    
    if current_index < len(tasks):
        return "execute_subtask_node"
    
    return END

async def final_node(state: OpenAgentsState, config: RunnableConfig):
    callback = config.get("configurable", {}).get("callback")
    if not state.get("error"):
        if callback:
            await callback(websocket_message(type="complete", content="All tasks completed successfully."))
    return {}

# --- Graph Compilation ---
workflow = StateGraph(OpenAgentsState)

workflow.add_node("decompose_task_node", decompose_task_node)
workflow.add_node("execute_subtask_node", execute_subtask_node)
workflow.add_node("final_node", final_node)

workflow.add_edge(START, "decompose_task_node")
workflow.add_conditional_edges(
    "decompose_task_node",
    router_node,
    {
        "execute_subtask_node": "execute_subtask_node",
        END: END
    }
)
workflow.add_conditional_edges(
    "execute_subtask_node",
    router_node,
    {
        "execute_subtask_node": "execute_subtask_node",
        END: "final_node"
    }
)
workflow.add_edge("final_node", END)

multi_agent_graph = workflow.compile()

async def execute(prompt, base_directory, history: List[Dict] = [], callback=None):
    initial_state = {
        "prompt": prompt,
        "base_directory": base_directory,
        "history": history,
        "tasks": [],
        "current_task_index": 0,
        "context": [],
        "error": "",
        "status": ""
    }
    config = {"configurable": {"callback": callback}}
    
    await multi_agent_graph.ainvoke(initial_state, config=config)

async def main():
    await execute("Web Search about AI and save the results to `results.md`.", base_directory=".")

if __name__ == "__main__":
    asyncio.run(main())