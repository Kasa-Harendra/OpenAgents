import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_community.tools import DuckDuckGoSearchResults
from langchain.tools import tool
from langchain.agents import create_agent
import os

from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts import RESEARCH_PROMPT, get_structured_prompt

model = get_agent_llm('ResearchAgent')

if model:
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
    # Use centralized prompt helper for caching
    structured_system_prompt = get_structured_prompt(model, RESEARCH_PROMPT)

    agent = create_agent(
        model, 
        tools,
        system_prompt=structured_system_prompt,
        name="ResearchAgent"
    )
else:
    agent = None

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