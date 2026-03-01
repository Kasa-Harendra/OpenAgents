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
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import json
import os

from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts import ORCHESTRATOR_PROMPT_BASE, get_structured_prompt

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
        self.llm = get_agent_llm("Coordinator")
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
        """Format agent registry for inclusion in prompt, including only configured agents"""
        formatted = "Available Agents:\n\n"
        
        for agent_name, agent_info in self.agent_registry["agents"].items():
                
            if not get_agent_llm(agent_name):
                continue
                
            formatted += f"**{agent_name}** ✅ Configured & Ready\n"
            formatted += f"Description: {agent_info['description']}\n"
            formatted += f"Capabilities:\n"
            for capability in agent_info["capabilities"]:
                formatted += f"  - {capability}\n"
            formatted += "\n"
        
        return formatted
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for task decomposition"""
        return ORCHESTRATOR_PROMPT_BASE.format(agent_registry_str=self._format_agent_registry())

    def decompose_task(self, user_prompt: str, base_directory:str, history: List[Dict] = []) -> Any:
        """
        Decompose user prompt into sequential subtasks and route to agents.
        
        Args:
            user_prompt: The user's request to decompose
            history: List of previous conversation messages
            
        Returns:
            List of (agent_name, detailed_subtask_prompt) tuples
        """
        
        if not self.llm:
            print("Coordinator LLM not configured. Using fallback decomposition.")
            return self._fallback_decomposition(user_prompt)
        
        # Format history for context
        history_context = ""
        if history:
            history_context = "PREVIOUS CONVERSATION HISTORY:\n"
            for msg in history:
                role = msg.get('role', 'unknown').upper()
                content = msg.get('content', '')
                history_context += f"{role}: {content}\n"
            history_context += "\n"

        # Create the system prompt using the base prompt and agent registry
        system_prompt_str = self._create_system_prompt()
        
        # Use centralized prompt helper for caching and structured output
        structured_system_prompt = get_structured_prompt(self.llm, system_prompt_str)

        prompt = ChatPromptTemplate.from_messages([
            structured_system_prompt,
            ("user", f"""{{history}}
             
             BASE_DIRECTORY/CURRENT DIRECTORY: {{base_directory}}   

             CURRENT REQUEST: {{user_request}}""")
        ])
        
        # Invoke the chain
        try:
            # Get LLM response
            chain = prompt | self.llm
            response = chain.invoke({"history":str(history_context), "user_request": user_prompt, "base_directory": base_directory})
            print(f"DEBUG: Orchestrator raw response: {response.content}")
            
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

    
    def _fallback_decomposition(self, user_prompt: str) -> List[Dict[str, str]]:
        """
        Fallback decomposition if JSON parsing fails.
        Simple heuristic-based routing, strictly using only configured agents.
        """
        # Simple keyword-based routing as fallback
        prompt_lower = user_prompt.lower()
        
        # Priority: Browser > Terminal > FileSystem > Research > RAG
        # Only route if the agent is configured
        
        candidates = []
        if any(word in prompt_lower for word in ["navigate", "click", "login", "browser", "website", "web page"]):
            candidates.append("BrowserAgent")
        if any(word in prompt_lower for word in ["command", "execute", "run", "script", "terminal"]):
            candidates.append("TerminalAgent")
        if any(word in prompt_lower for word in ["file", "directory", "folder", "read", "write", "create"]):
            candidates.append("FileSystemAgent")
        if any(word in prompt_lower for word in ["search", "research", "find information", "web search"]):
            candidates.append("ResearchAgent")
        if any(word in prompt_lower for word in ["document", "knowledge", "indexed", "rag"]):
            candidates.append("RAGAgent")

        # Filter candidates by configuration
        configured_candidates = [c for c in candidates if get_agent_llm(c)]
        
        if configured_candidates:
            # Pick the most relevant one (first found)
            return [{"agent": configured_candidates[0], "subtask": user_prompt}]
        
        # Final fallback: any configured agent from implemented list
        implemented_agents = self.get_implemented_agents()
        configured_agents = [a for a in implemented_agents if get_agent_llm(a) and a != "Coordinator"]
        
        if configured_agents:
            return [{"agent": configured_agents[0], "subtask": user_prompt}]
        
        # If absolutely no agents are configured, return empty
        print("CRITICAL: No specialized agents are configured for fallback.")
        return []
    
    def get_agents_capabilities(self) -> Dict[str, Any]:
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
