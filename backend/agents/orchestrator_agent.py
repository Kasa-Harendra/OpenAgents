"""
Orchestrator Agent - Task Decomposition and Agent Routing

This module provides an intelligent orchestrator that:
1. Receives generalized user prompts
2. Analyzes available specialized agents and their capabilities
3. Decomposes the prompt into sequential subtasks
4. Routes each subtask to the most appropriate agent
5. Returns an execution plan as a list of (agent_name, detailed_subtask)
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import List, Tuple, Dict, Any
from backend.model_providers.agent_llms import agent_llms
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import json
import os



class SubTask(BaseModel):
    """Model for a subtask in the execution plan"""
    agent: str = Field(description="Name of the agent to execute this subtask")
    subtask: str = Field(description="Detailed description of what this agent should do")


class ExecutionPlan(BaseModel):
    """Model for the complete execution plan"""
    tasks: List[SubTask] = Field(description="List of subtasks to execute sequentially")


class OrchestratorAgent:
    """
    Intelligent task orchestrator that decomposes user prompts into subtasks
    and routes them to specialized agents.
    """
    
    def __init__(self):
        """
        Initialize orchestrator with LLM and agent registry.
        Uses the configured LLM for the 'Coordinator' agent.
        """
        self.llm = agent_llms["Coordinator"]
        self.agent_registry = self._load_agent_registry()
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
        
    def _load_agent_registry(self) -> Dict[str, Any]:
        """Load agent registry from JSON file"""
        registry_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "config", 
            "agent_registry.json"
        )
        
        with open(registry_path, 'r') as f:
            return json.load(f)
    
    def _format_agent_registry(self) -> str:
        """Format agent registry for inclusion in prompt"""
        formatted = "Available Agents:\n\n"
        
        for agent_name, agent_info in self.agent_registry["agents"].items():
            status = "✅ Implemented" if agent_info["implemented"] else "⚠️ Not yet implemented"
            formatted += f"**{agent_name}** {status}\n"
            formatted += f"Description: {agent_info['description']}\n"
            formatted += f"Capabilities:\n"
            for capability in agent_info["capabilities"]:
                formatted += f"  - {capability}\n"
            formatted += "\n"
        
        return formatted
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for task decomposition"""
        agent_registry_str = self._format_agent_registry()
    
        return f"""You are an intelligent task orchestrator for a multi-agent system. Your role is to:

1. Analyze the user's request carefully
2. Break it down into sequential subtasks
3. Route each subtask to the most appropriate specialized agent
4. Ensure subtasks are detailed, actionable, and self-contained

{agent_registry_str}

IMPORTANT RULES:
- Only use agents that are marked as "✅ Implemented"
- Each subtask should be detailed enough for the agent to execute without clarification
- Subtasks should execute sequentially (output of one can feed into the next)
- Choose the MOST APPROPRIATE agent for each subtask based on capabilities
- If a task requires multiple steps, break it into separate subtasks
- Make subtask descriptions specific and actionable
- For agents like BrowserAgent, the subtask must be structured as a numbered sequence, with each step using the tool names directly. For example:
        task = "
        1. Go to https://quotes.toscrape.com/
        2. Use extract action with the query \"first 3 quotes with their authors\"
        3. Save results to quotes.csv using write_file action
        4. Do a google search for the first quote and find when it was written
        "

OUTPUT FORMAT:
Return ONLY a valid JSON object in this exact format:
{{{{
    "tasks": [
        {{{{
            "agent": "AgentName",
            "subtask": "Detailed description of what this agent should do"
        }}}}
    ]
}}}}

EXAMPLES:

Example 1 - Simple Task:
User: "Get the list of files in the current directory"
Output:
{{{{
    "tasks": [
        {{{{
            "agent": "FileSystemAgent",
            "subtask": "List all files and directories in the current working directory with full details"
        }}}}
    ]
}}}}

Example 2 - Multi-Agent Workflow:
User: "Research Python web frameworks and save a comparison to a file"
Output:
{{{{
    "tasks": [
        {{{{
            "agent": "ResearchAgent",
            "subtask": "Research the latest Python web frameworks in 2026, including FastAPI, Django, Flask. Compare their features, performance, and use cases."
        }}}},
        {{{{
            "agent": "FileSystemAgent",
            "subtask": "Create a file named 'python-frameworks-comparison.md' with the research findings in markdown format with sections for each framework including pros, cons, and best use cases."
        }}}}
    ]
}}}}

Example 3 - Browser + File:
User: "Go to OpenAI pricing page and save the pricing to a JSON file"
Output:
{{{{
    "tasks": [
        {{{{
            "agent": "BrowserAgent",
            "subtask": "
                1. Go to https://openai.com/pricing
                2. Use extract action with the query 'all pricing plan details including plan names, monthly prices, and key features'
            "
        }}}},
        {{{{
            "agent": "FileSystemAgent",
            "subtask": "Create a file named 'openai-pricing.json' with the extracted pricing data formatted as JSON with proper structure"
        }}}}
    ]
}}}}

Remember: Return ONLY the JSON output, no additional text or explanation."""


    def decompose_task(self, user_prompt: str) -> Any:
        """
        Decompose user prompt into sequential subtasks and route to agents.
        
        Args:
            user_prompt: The user's request to decompose
            
        Returns:
            List of (agent_name, detailed_subtask_prompt) tuples
        """
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._create_system_prompt()),
            ("user", "{user_request}")
        ])
        
        # Invoke the chain
        try:
            # Get LLM response
            chain = prompt | self.llm
            response = chain.invoke({"user_request": user_prompt})
            # print(response.content)
            
            # Extract content from response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Try to parse JSON from the content
            # Find JSON block in the response
            try:
                tasks = self.parser.parse(response.content)
                # print(tasks)

                execution_plan = tasks["tasks"]
                return execution_plan
            except:
                import re
                json_match = re.search(r'\{[\s\S]*"tasks"[\s\S]*\}', content)
                
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                    # Convert to list of tuples
                    execution_plan = result["tasks"]
                    return execution_plan
                else:
                    print(f"Could not find JSON in response, using fallback")
                    return self._fallback_decomposition(user_prompt)
            
        except Exception as e:
            print(f"Error during task decomposition: {e}")
            # Fallback: try to parse manually if JSON parsing fails
            return self._fallback_decomposition(user_prompt)

    
    def _fallback_decomposition(self, user_prompt: str) -> List[Tuple[str, str]]:
        """
        Fallback decomposition if JSON parsing fails.
        Simple heuristic-based routing.
        """
        # Simple keyword-based routing as fallback
        prompt_lower = user_prompt.lower()
        
        if any(word in prompt_lower for word in ["navigate", "click", "login", "browser", "website", "web page"]):
            return [{"agent": "BrowserAgent", "subtask":user_prompt}]
        elif any(word in prompt_lower for word in ["command", "execute", "run", "script", "terminal"]):
            return [{"agent": "TerminalAgent","subtask": user_prompt}]
        elif any(word in prompt_lower for word in ["file", "directory", "folder", "read", "write", "create"]):
            return [{"agent": "FileSystemAgent", "subtask": user_prompt}]
        elif any(word in prompt_lower for word in ["search", "research", "find information", "web search"]):
            return [{"agent": "ResearchAgent", "subtask": user_prompt}]
        elif any(word in prompt_lower for word in ["document", "knowledge", "indexed", "rag"]):
            return [{"agent": "RAGAgent", "subtask": user_prompt}]
        else:
            # Default to research agent for general queries
            return [{"agent": "ResearchAgent", "subtask": user_prompt}]
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """
        Get the complete agent registry with capabilities.
        
        Returns:
            Dictionary containing all agents and their capabilities
        """
        return self.agent_registry
    
    def get_implemented_agents(self) -> List[str]:
        """
        Get list of implemented agent names.
        
        Returns:
            List of agent names that are currently implemented
        """
        return [
            agent_name 
            for agent_name, agent_info in self.agent_registry["agents"].items()
            if agent_info["implemented"]
        ]
    
    def print_execution_plan(self, execution_plan: List[Tuple[str, str]]) -> None:
        """
        Print execution plan in a readable format.
        
        Args:
            execution_plan: List of (agent_name, subtask) tuples
        """
        print("\n" + "="*80)
        print("EXECUTION PLAN")
        print("="*80)
        
        for i, (agent_name, subtask) in enumerate(execution_plan, 1):
            status = "✅" if self.agent_registry["agents"][agent_name]["implemented"] else "⚠️"
            print(f"\nStep {i}: {status} {agent_name}")
            print(f"Task: {subtask}")
        
        print("\n" + "="*80)

orchestrator = OrchestratorAgent()

# Example usage
async def main():
    """Example usage of the orchestrator agent"""
    
    # Example 1: Simple single-agent task
    print("\n### Example 1: Simple Task ###")
    user_prompt_1 = "List all files in the current directory"
    plan_1 = orchestrator.decompose_task(user_prompt_1)
    # orchestrator.print_execution_plan(plan_1)
    
    # Example 2: Multi-agent workflow
    print("\n### Example 2: Multi-Agent Workflow ###")
    user_prompt_2 = "Research the latest Python AI frameworks, create a comparison document, and save it"
    plan_2 = orchestrator.decompose_task(user_prompt_2)
    # orchestrator.print_execution_plan(plan_2)
    
    # Example 3: Browser + File
    print("\n### Example 3: Browser + File ###")
    user_prompt_3 = "Go to GitHub trending page and extract the top 5 repositories, then save to trending.json"
    plan_3 = orchestrator.decompose_task(user_prompt_3)
    # orchestrator.print_execution_plan(plan_3)
    
    # Example 4: Complex workflow
    print("\n### Example 4: Complex Workflow ###")
    user_prompt_4 = "Research LangChain documentation, create a summary report, and save it to my computer"
    plan_4 = orchestrator.decompose_task(user_prompt_4)
    # orchestrator.print_execution_plan(plan_4)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
