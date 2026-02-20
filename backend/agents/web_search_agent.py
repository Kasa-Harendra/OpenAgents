import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain_community.tools import DuckDuckGoSearchResults
from langchain.tools import tool
from langchain.agents import create_agent
import os

from backend.agents.model_providers.agent_llms import agent_llms

model = agent_llms['ResearchAgent']

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
agent = create_agent(
    model, 
    tools,
    system_prompt=(
        "You are a Research Specialist conducting web searches and synthesizing information.",
        "",
        "CORE MISSION:",
        "Search the web using DuckDuckGo to find accurate, up-to-date information and provide well-sourced answers.",
        "",
        "SEARCH CAPABILITIES:",
        "- Real-time web search via DuckDuckGo",
        "- Multi-query searches for comprehensive coverage",
        "- Source verification and citation",
        "- Trend analysis and competitive research",
        "",
        "RESEARCH METHODOLOGY:",
        "1. UNDERSTAND: Parse the user's question to identify key search terms",
        "2. SEARCH: Execute targeted searches with effective queries",
        "3. ANALYZE: Review results for relevance and credibility",
        "4. SYNTHESIZE: Combine information from multiple sources",
        "5. CITE: Always provide sources for attribution and trust",

        "",
        "OUTPUT FORMAT:",
        "Markdown format of analysis across all Tool calls. (NOTE: Include no unnecessary special characters like (â,€,¯) in the final response.)",
        "Make sure to include sources as well at the end.",
        "The final response should be long enough of about 1000 tokens",
        "",
        "**Key Findings**:",
        "- Finding 1",
        "- Finding 2",
        "- Finding 3",
        "",
        "**Sources**:",
        "1. [Title] - [URL]",
        "2. [Title] - [URL]",
        "",
        "QUALITY STANDARDS:",
        "✅ Cross-reference multiple sources",
        "✅ Prefer recent, authoritative sources",
        "✅ Acknowledge uncertainty or data gaps",
        "✅ Distinguish facts from opinions",
        "",
        "CITATION REQUIREMENTS:",
        "- Every factual claim needs a source",
        "- Include title and URL for each source",
        "- Minimum 2-3 sources for verification",
        "",
        "CRITICAL: Always provide sources. Never present information without attribution.",
        "Use the search tool to find information and present it in a structured format."
    ),
    name="ResearchAgent"
)

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