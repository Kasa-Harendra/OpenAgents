from backend.model_providers.agent_llms import agent_llms
from langchain_core.prompts import ChatPromptTemplate

class EvaluationAgent:
	"""
	Evaluates if an agent's response matches the prompt it received.
	Returns 'Proceed' if the response is relevant, 'Redo' otherwise.
	"""
	def __init__(self):
		# Use the configured LLM for EvaluationAgent
		self.llm = agent_llms["GuardianAgent"]
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

	def evaluate(self, prompt: str, response: str) -> str:
		formatted_prompt = self.prompt.format(prompt=prompt, response=response)
		result = self.llm.invoke(formatted_prompt)
		# Return only 'Proceed' or 'Redo'
		return result.content.strip()

agent = EvaluationAgent()