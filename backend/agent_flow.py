import sys
import os
import asyncio
import uuid
import json
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
from backend.mods.mod_manager import ModManager
from backend.utils.context_compactor import compact_context

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
    compacted = compact_context(context, max_chars_per_record=3000)
    context_prompt_template = """{response}"""
    prompt_template = PromptTemplate.from_template(context_prompt_template)

    if len(compacted) != 0:
        prev_rec = compacted[-1]
        processed_prompt = prompt_template.invoke(
            {'agent': prev_rec['agent_name'], 'response': prev_rec['response']}
        )
        return sub_task + "\n\nContext from previous step:\n" + str(processed_prompt)
    return sub_task

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
    MAX_RETRIES = 2

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
                
                # Tool output streaming with Claude Code-style interceptors
                elif kind == "on_tool_end":
                    tool_output = event["data"]["output"]
                    tool_name = event.get("name", "")
                    tool_args = event.get("data", {}).get("input", {})
                    after_ctx = await ModManager.get_instance().trigger_after_tool_execution(
                        tool_name=tool_name,
                        tool_args=tool_args,
                        tool_result=tool_output,
                        agent_name=agent.name
                    )
                    if after_ctx.tool_result is not None:
                        tool_output = after_ctx.tool_result

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
                    tool_args = event.get("data", {}).get("input", {})
                    tool_ctx = await ModManager.get_instance().trigger_before_tool_execution(
                        tool_name=tool_name,
                        tool_args=tool_args,
                        agent_name=agent.name
                    )
                    if tool_ctx.cancelled:
                        if callback:
                            await callback(websocket_message(
                                type="tool_error",
                                agent_name=agent.name,
                                content=f"Mod Blocked Tool Execution: {tool_ctx.cancel_reason or 'Blocked by active mod.'}"
                            ))
                        raise RuntimeError(f"Mod Guard Blocked: {tool_ctx.cancel_reason}")

                    if callback:
                        for log_msg in tool_ctx.logs:
                            await callback(websocket_message(
                                type="status",
                                content=f"[Mod] {log_msg}"
                            ))
                        await callback(websocket_message(
                            type="status",
                            content=f"Agent {agent.name} is running tool: {tool_name}..."
                        ))

            if _evaluate_response(prompt, agent_rec["response"]):
                context.append(agent_rec)
                if callback:
                    await callback(websocket_message(
                        type="agent_response",
                        agent_name=agent.name,
                        content=agent_rec["response"]
                    ))
                return True
            else:
                MAX_RETRIES -= 1

        except Exception as e:
            error_str = str(e)
            print(f"Error occurred in {agent.name}: {error_str}")
            is_agent_error = _is_agent_config_error(error_str)
            if callback:
                await callback(websocket_message(
                    type="agent_error" if is_agent_error else "error",
                    agent_name=agent.name,
                    content=error_str
                ))
            MAX_RETRIES -= 1

    return False

# --- Graph State Definition ---
class OpenAgentsState(TypedDict):
    prompt: str
    base_directory: str
    history: List[Dict]
    
    tasks: List[Dict[str, Any]]
    current_task_index: int
    context: List[Dict]
    
    error: str
    status: str
    replan_count: int

# --- Nodes ---
async def decompose_task_node(state: OpenAgentsState, config: RunnableConfig) -> Dict:
    callback = config.get("configurable", {}).get("callback")
    
    prompt = state["prompt"]
    base_directory = state["base_directory"]
    history = state["history"]

    if callback:
        await callback(websocket_message(type="status", content="Planning task execution graph..."))
        
    try:
        from backend.agents.orchestrator_agent import orchestrator
        loop = asyncio.get_running_loop()
        tasks = await loop.run_in_executor(None, orchestrator.decompose_task, prompt, base_directory, history)
        
        if callback:
            await callback(websocket_message(type="tasks_decomposed", content=tasks))
            await callback(websocket_message(type="tasks_updated", content=tasks))
            
        return {"tasks": tasks, "current_task_index": 0, "error": "", "replan_count": 0}
    except Exception as e:
        error_str = str(e)
        is_agent_error = _is_agent_config_error(error_str)
        if callback:
            await callback(websocket_message(
                type="agent_error" if is_agent_error else "error", 
                content=f"Decomposition failed: {error_str}"
            ))
        return {"error": error_str}

async def execute_subtask_node(state: OpenAgentsState, config: RunnableConfig) -> Dict:
    callback = config.get("configurable", {}).get("callback")
    
    tasks = [dict(t) for t in state.get("tasks", [])]
    current_index = state.get("current_task_index", 0)
    context = list(state.get("context", []))
    
    if current_index >= len(tasks):
        return {}
        
    task = tasks[current_index]
    agent_name = task.get("agent")
    sub_task = task.get("subtask")
    
    # Mark task as in-progress and stream checklist update
    task["status"] = "in_progress"
    if callback:
        await callback(websocket_message(type="tasks_updated", content=tasks))
        await callback(websocket_message(type="agent_start", agent_name=agent_name, content=sub_task))

    from backend.agents.model_providers.agent_llms import get_agent_llm
    if agent_name != "Coordinator" and not get_agent_llm(agent_name):
        error_msg = f"Agent '{agent_name}' is not configured. Please check Settings."
        task["status"] = "failed"
        if callback:
            await callback(websocket_message(type="agent_error", content=error_msg))
            await callback(websocket_message(type="tasks_updated", content=tasks))
        return {"error": error_msg, "tasks": tasks}

    agent = await _get_agent(agent_name)
    if agent is None:
        error_msg = f"Agent '{agent_name}' failed to initialize."
        task["status"] = "failed"
        if callback:
            await callback(websocket_message(type="agent_error", content=error_msg))
            await callback(websocket_message(type="tasks_updated", content=tasks))
        return {"error": error_msg, "tasks": tasks}
        
    processed_sub_task = _process_subtask(sub_task, context)

    success = False
    if agent_name in ["FileSystemAgent", "TerminalAgent", "ResearchAgent", "IntegratorAgent"]:
        success = await _invoke_agent(agent, processed_sub_task, context, callback)

    elif agent_name in ["BrowserAgent"]:
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
                context.append({"id": str(uuid.uuid1()), "agent_name": "BrowserAgent", "response": res})
                if callback:
                    await callback(websocket_message(type="agent_response", agent_name="BrowserAgent", content=res))
                success = True
            else:
                err_msg = err if err else res
                if callback:
                    await callback(websocket_message(type="agent_error", content=f"Browser error: {err_msg}"))
        except Exception as e:
            if callback:
                await callback(websocket_message(type="agent_error", content=f"Browser launch failed: {e}"))

    if success:
        task["status"] = "completed"
        if callback:
            await callback(websocket_message(type="tasks_updated", content=tasks))
        return {"context": context, "tasks": tasks, "current_task_index": current_index + 1, "error": ""}
    else:
        task["status"] = "failed"
        error_msg = f"{agent_name} failed to complete: {sub_task}"
        if callback:
            await callback(websocket_message(type="tasks_updated", content=tasks))
        return {"error": error_msg, "tasks": tasks}

async def replan_node(state: OpenAgentsState, config: RunnableConfig) -> Dict:
    """Self-healing node: dynamically recalculates tasks upon encountering a failure."""
    callback = config.get("configurable", {}).get("callback")
    replan_count = state.get("replan_count", 0) + 1
    current_index = state.get("current_task_index", 0)
    tasks = state.get("tasks", [])
    context = state.get("context", [])
    error = state.get("error", "Unknown error")
    prompt = state.get("prompt", "")

    failed_task = tasks[current_index] if current_index < len(tasks) else {}
    failed_subtask = failed_task.get("subtask", "Unknown step")

    if callback:
        await callback(websocket_message(
            type="status",
            content=f"⚠️ Step failed ({error}). Self-healing replanning attempt {replan_count}/2..."
        ))

    from backend.agents.orchestrator_agent import orchestrator
    loop = asyncio.get_running_loop()
    new_subtasks = await loop.run_in_executor(
        None, orchestrator.replan_subtasks, prompt, failed_subtask, error, context
    )

    # Keep completed tasks and append new replanned tasks
    completed_tasks = tasks[:current_index]
    merged_tasks = completed_tasks + new_subtasks

    if callback:
        await callback(websocket_message(type="tasks_updated", content=merged_tasks))

    return {
        "tasks": merged_tasks,
        "current_task_index": current_index,
        "replan_count": replan_count,
        "error": ""
    }

def router_node(state: OpenAgentsState):
    if state.get("error"):
        if state.get("replan_count", 0) < 2:
            return "replan_node"
        return "final_node"
    
    tasks = state.get("tasks", [])
    current_index = state.get("current_task_index", 0)
    
    if current_index < len(tasks):
        return "execute_subtask_node"
    
    return "final_node"

async def final_node(state: OpenAgentsState, config: RunnableConfig):
    callback = config.get("configurable", {}).get("callback")
    if not state.get("error"):
        if callback:
            await callback(websocket_message(type="complete", content="All workflow goals completed successfully."))
    else:
        if callback:
            await callback(websocket_message(type="error", content=f"Workflow halted: {state.get('error')}"))
    return {}

# --- Graph Compilation ---
workflow = StateGraph(OpenAgentsState)

workflow.add_node("decompose_task_node", decompose_task_node)
workflow.add_node("execute_subtask_node", execute_subtask_node)
workflow.add_node("replan_node", replan_node)
workflow.add_node("final_node", final_node)

workflow.add_edge(START, "decompose_task_node")
workflow.add_conditional_edges(
    "decompose_task_node",
    router_node,
    {
        "execute_subtask_node": "execute_subtask_node",
        "replan_node": "replan_node",
        "final_node": "final_node"
    }
)
workflow.add_conditional_edges(
    "execute_subtask_node",
    router_node,
    {
        "execute_subtask_node": "execute_subtask_node",
        "replan_node": "replan_node",
        "final_node": "final_node"
    }
)
workflow.add_edge("replan_node", "execute_subtask_node")
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
        "status": "",
        "replan_count": 0
    }
    config = {"configurable": {"callback": callback}}
    await multi_agent_graph.ainvoke(initial_state, config=config)