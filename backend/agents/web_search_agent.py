import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain_community.tools import DuckDuckGoSearchResults
from langchain.tools import tool
from langchain.agents import create_agent
import os

from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts.prompts import RESEARCH_PROMPT, get_structured_prompt, get_agent_system_prompt

search = DuckDuckGoSearchResults(output_format="list")

@tool
def intermediate_answer(query: str) -> str:
    """Useful for when you need to ask with search."""
    results = search.invoke(query)
    # Format results as a readable string
    if isinstance(results, list):
        return "\n".join([
            f"Title: {r.get('title','')}, Link: {r.get('link','')}, Snippet: {r.get('snippet','')}" for r in results
        ])
    return str(results)

tools = [intermediate_answer]

def get_agent():
    model = get_agent_llm('ResearchAgent')
    if not model:
        return None
        
    prompt_str = get_agent_system_prompt('ResearchAgent', RESEARCH_PROMPT)
    structured_system_prompt = get_structured_prompt(model, prompt_str)

    return create_agent(
        model, 
        tools,
        system_prompt=structured_system_prompt,
        name="ResearchAgent"
    )

agent = None # Deprecated, use get_agent()

def main():
    events = agent.stream(
        {
            "messages": [
                ("user", "What DSA concepts are covered in geeksforgeeks.org")
            ]
        },
        stream_mode="values",
    )

    for event in events:
        event["messages"][-1].pretty_print()

if __name__ == "__main__":
    main()