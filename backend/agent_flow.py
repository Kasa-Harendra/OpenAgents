import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List, Dict, Any
import asyncio
import uuid

from backend.agents import (
    orchestrator,
    file_system_agent,
    terminal_agent,
    web_search_agent,
    evaluation_agent,
    run_browser_agent
)

from langgraph.graph.state import CompiledStateGraph
from langchain.agents.middleware.types import (AgentState, _InputAgentState, _OutputAgentState)
from langchain_core.prompts import PromptTemplate

def _get_agent(agent_name: str) -> CompiledStateGraph[AgentState[Any], Any, _InputAgentState, _OutputAgentState[Any]]:
    match(agent_name):
        case "FileSystemAgent":
            return file_system_agent
        case "TerminalAgent":
            return terminal_agent
        case "ResearchAgent":
            return web_search_agent
        case _:
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
    verdict = evaluation_agent.evaluate(
        prompt=prompt,
        response=response
    )

    return True if verdict == "Proceed" else "False"

def _invoke_agent(agent: CompiledStateGraph, prompt: str, context: list):
        MAX_RETRIES = 3

        while MAX_RETRIES > 0:
            try:
                events = agent.stream(
                    {
                        "messages": [
                            ("user", prompt)
                        ]
                    },
                    stream_mode="values",
                )

                agent_rec = {"id": str(uuid.uuid1()), "agent_name": agent.name, "response": ""}

                for event in events:
                    agent_rec["response"] = event["messages"][-1].content
                    event["messages"][-1].pretty_print()
                
                if(_evaluate_response(prompt, agent_rec["response"])):
                    context.append(agent_rec)
                    return True # Success message
                else:
                    MAX_RETRIES -= 1

            except Exception as e:
                print(f"Error occured: {e}")
                MAX_RETRIES -= 1
        return False # Failure message

async def execute(prompt):
    """
    This function is responsible for executing the task.
    This handles:
    - Task Decomposition by `Orchestartor` agent.
    - Task mapping to respective agents (`FileSystemAgent`, `TerminalAgent`, `ResearchAgent`, `BrowserAgent`)
    - Response evaluation using `Evaluation agent`.
    
    :param prompt: The Prompt from the user that needs to be decomposed, executed by agents.
    """    

    context = []

    # Get Decomposed Tasks from orchestrator
    tasks: List[Dict] = orchestrator.decompose_task(prompt)

    print(tasks)

    agents = [task["agent"] for task in tasks]
    sub_tasks = [task["subtask"] for task in tasks]
    
    # Executing in a row while evaluating
    for agent_name, sub_task in zip(agents, sub_tasks):
        agent = _get_agent(agent_name)
        processed_sub_task = _process_subtask(sub_task, context)

        if agent_name in ["FileSystemAgent", "TerminalAgent", "ResearchAgent"]:
            # Executing the sub_task by the agent with Exception Handling and Considerable Evaluation
            if not (_invoke_agent(agent, processed_sub_task, context)):
                return f"{agent_name} failed to do - {sub_task}"

        elif agent_name in ["BrowserAgent"]:
            res = await run_browser_agent(prompt=processed_sub_task)
            if res != "Failed":
                context.append({"id": str(uuid.uuid1()), "agent_name": "BrowserAgent", "response": res})        
        
        

async def main():
    await execute("""
Go to https://ui.shadcn.com/ and go to components tab and extract the list of Components and save them to `components.md`.
""")

if __name__ == "__main__":
    asyncio.run(main())