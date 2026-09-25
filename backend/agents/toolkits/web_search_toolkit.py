from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults

search = DuckDuckGoSearchResults(output_format="list")

class IntermediateAnswerSchema(BaseModel):
    query: str = Field(..., description="The query to search.")

class IntermediateAnswerTool(BaseTool):
    name: str = "intermediate_answer"
    description: str = "Useful for when you need to ask with search."
    args_schema: type[BaseModel] = IntermediateAnswerSchema

    def _run(self, query: str) -> str:
        results = search.invoke(query)
        # Format results as a readable string
        if isinstance(results, list):
            return "\n".join([
                f"Title: {r.get('title','')}, Link: {r.get('link','')}, Snippet: {r.get('snippet','')}" for r in results
            ])
        return str(results)

from langchain_core.tools import BaseToolkit
from typing import List

class WebSearchToolkit(BaseToolkit):
    def get_tools(self) -> List[BaseTool]:
        return [IntermediateAnswerTool()]
