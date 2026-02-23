import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List, Dict, Any
import asyncio
import uuid
import subprocess

# Imports moved to local scope to prevent eager initialization crash


from backend.models.models import websocket_message

from langgraph.graph.state import CompiledStateGraph
from langchain.agents.middleware.types import (AgentState, _InputAgentState, _OutputAgentState)
from langchain_core.prompts import PromptTemplate

def _get_agent(agent_name: str) -> CompiledStateGraph[AgentState[Any], Any, _InputAgentState, _OutputAgentState[Any]]:
    match(agent_name):
        case "FileSystemAgent":
            from backend.agents.file_system_agent import agent as file_system_agent
            return file_system_agent
        case "TerminalAgent":
            from backend.agents.terminal_agent import agent as terminal_agent
            return terminal_agent
        case "ResearchAgent":
            from backend.agents.web_search_agent import agent as web_search_agent
            return web_search_agent
        case _:
            from backend.agents.orchestrator_agent import orchestrator
            return orchestrator
        
def _process_subtask(sub_task: str, context: List[Dict]) -> str:
    context_prompt_template = """
Previous Agent:
{agent}

Response from Previous Agent:
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
    verdict = evaluation_agent.evaluate(
        prompt=prompt,
        response=response
    )

    return True if verdict == "Proceed" else "False"

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
                            # We send tool output as a whole, but it's "streaming" in the sense that it appears as soon as it's ready
                            await callback(websocket_message(
                                type="tool_output",
                                agent_name=agent.name,
                                content=str(tool_output)
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
                print(f"Error occured: {e}")
                if callback:
                    await callback(websocket_message(
                        type="error",
                        content=str(e)
                     ))
                MAX_RETRIES -= 1
        return False # Failure message

async def execute(prompt, history: List[Dict] = [], callback=None):
    """
    This function is responsible for executing the task.
    This handles:
    - Task Decomposition by `Orchestartor` agent.
    - Task mapping to respective agents (`FileSystemAgent`, `TerminalAgent`, `ResearchAgent`, `BrowserAgent`)
    - Response evaluation using `Evaluation agent`.
    
    :param prompt: The Prompt from the user that needs to be decomposed, executed by agents.
    :param history: List of conversation history items.
    :param callback: Async function to handle streaming events.
    """    

    context = []

    # Get Decomposed Tasks from orchestrator
    if callback:
        await callback(websocket_message(type="status", content="Decomposing task..."))
    
    print(f"DEBUG: calling decompose_task with prompt: {prompt}")
    try:
        from backend.agents.orchestrator_agent import orchestrator
        loop = asyncio.get_running_loop()
        tasks: List[Dict] = await loop.run_in_executor(None, orchestrator.decompose_task, prompt, history)
        print(f"DEBUG: decomposed tasks: {tasks}")
    except Exception as e:
        print(f"DEBUG: Error in decompose_task: {e}")
        if callback:
            await callback(websocket_message(type="error", content=f"Decomposition failed: {e}"))
        return

    if callback:
        await callback(websocket_message(type="tasks_decomposed", content=tasks))

    print(tasks)

    agents = [task["agent"] for task in tasks]
    sub_tasks = [task["subtask"] for task in tasks]
    
    # Executing in a row while evaluating
    for agent_name, sub_task in zip(agents, sub_tasks):
        print(f"DEBUG: processing task for agent: {agent_name}")
        agent = _get_agent(agent_name)
        processed_sub_task = _process_subtask(sub_task, context)

        if callback:
            await callback(websocket_message(type="agent_start", agent_name=agent_name, content=sub_task))

        if agent_name in ["FileSystemAgent", "TerminalAgent", "ResearchAgent"]:
            # Executing the sub_task by the agent with Exception Handling and Considerable Evaluation
            print(f"DEBUG: invoking {agent_name}")
            if not (await _invoke_agent(agent, processed_sub_task, context, callback)):
                error_msg = f"{agent_name} failed to do - {sub_task}"
                if callback:
                    await callback(websocket_message(type="error", content=error_msg))
                return error_msg

        elif agent_name in ["BrowserAgent"]:
            print(f"DEBUG: invoking BrowserAgent subprocess")
            try:
                # Use the current python executable to ensure we're in the same environment
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
                        await callback(websocket_message(type="error", content=error_msg))
                    return error_msg
            except Exception as e:
                error_msg = f"Error launching BrowserAgent subprocess: {e}"
                print(f"DEBUG: {error_msg}")
                if callback:
                    await callback(websocket_message(type="error", content=error_msg))
                return error_msg

    if callback:
        await callback(websocket_message(type="complete", content="All tasks completed successfully."))
        
        

async def main():
    await execute("""
Web Search about AI and save the results to `results.md`.
""")

if __name__ == "__main__":
    asyncio.run(main())