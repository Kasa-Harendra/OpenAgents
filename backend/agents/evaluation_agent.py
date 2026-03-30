import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.agents.model_providers.agent_llms import get_agent_llm
from langchain_core.prompts import ChatPromptTemplate

class EvaluationAgent:
    """
    Evaluates if an agent's response matches the prompt it received.
    Returns 'Proceed' if the response is relevant, 'Redo' otherwise.
    """
    def __init__(self):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a strict evaluation agent for a multi-agent system. Your job is to judge if the agent's response fully and directly addresses the user's prompt, is factually correct, and is complete.\n\n"
             "Rules:\n"
             "- Respond ONLY with 'Proceed' if the response is fully relevant, correct, and complete.\n"
             "- Respond ONLY with 'Redo' if the response is incomplete, off-topic, factually incorrect, vague, or does not directly answer the prompt.\n"
             "- Do NOT explain your answer.\n"
             "- Do NOT output anything except 'Proceed' or 'Redo'.\n"
             "- Be strict: if in doubt, answer 'Redo'.\n"
             "- Ignore politeness, style, or formatting; focus only on accuracy and completeness."
            ),
            ("human", "Prompt: {prompt}\nResponse: {response}")
        ])

    @property
    def llm(self):
        """Get the latest configured LLM for the GuardianAgent"""
        return get_agent_llm("GuardianAgent")

    def evaluate(self, prompt: str, response: str) -> str:
        """
        Evaluate the response using the GuardianAgent LLM.
        Falls back to 'Proceed' if the LLM is not configured.
        """
        llm = self.llm
        if not llm:
            # print("GuardianAgent LLM not configured. Using fallback 'Proceed'.")
            return "Proceed"
            
        try:
            formatted_prompt = self.prompt.format(prompt=prompt, response=response)
            result = llm.invoke(formatted_prompt)
            # Return only 'Proceed' or 'Redo'
            return result.content.strip()
        except Exception as e:
            print(f"Error in evaluation: {e}. Falling back to 'Proceed'.")
            return "Proceed"

agent = EvaluationAgent()