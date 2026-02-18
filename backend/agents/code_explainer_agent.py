import sys
import os
from typing import List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.model_providers.agent_llms import agent_llms
from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import GitRepoLoader
from langchain_community.docstore.document import Document
import tempfile

def load_and_chunk_repo(repo_url: str, branch: str = "main", chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
	with tempfile.TemporaryDirectory() as temp_dir:
		loader = GitRepoLoader(
			clone_url=repo_url,
			repo_path=temp_dir,
			branch=branch,
			file_filter=lambda f: f.endswith('.py') or f.endswith('.md') or f.endswith('.txt'),
			clean_up=True
		)
		docs = loader.load()
		text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
		documents = []
		for doc in docs:
			# doc.page_content is the file content
			chunks = text_splitter.split_text(doc.page_content)
			for chunk in chunks:
				documents.append(Document(page_content=chunk, metadata=doc.metadata))
		return documents

def main():
	repo_url = input("Enter GitHub repository URL to clone and explain: ")
	branch = input("Enter branch name (default: main): ") or "main"
	chunks = load_and_chunk_repo(repo_url, branch)
	print(f"Loaded {len(chunks)} code/document chunks from repo.")
	embedding_model: Embeddings = agent_llms['EmbeddingModel']
	vector_store = InMemoryVectorStore.from_documents(chunks, embedding=embedding_model)
	retriever = vector_store.as_retriever()
	model: BaseChatModel = agent_llms['RAGAgent']
	system_prompt = (
		"You are a Codebase Explainer Agent. Your job is to answer questions about the code and documentation in a cloned GitHub repository.",
		"",
		"CORE FUNCTION:",
		"Search through indexed code and docs to provide accurate, context-aware answers with source citations.",
		"",
		"RETRIEVAL PROCESS:",
		"1. Understand the user's question",
		"2. Retrieve relevant code/doc chunks from vector store",
		"3. Analyze retrieved context for relevance",
		"4. Synthesize answer based ONLY on retrieved information",
		"5. Cite source files",
		"",
		"ANSWER GUIDELINES:",
		"- Answer based EXCLUSIVELY on retrieved context",
		"- Keep answers concise (3-4 sentences maximum)",
		"- If information is insufficient, say: 'Not found in indexed code/docs'",
		"- Never hallucinate or add external knowledge",
		"- Always cite source files",
		"",
		"CONTEXT MANAGEMENT:",
		"- Consider chat history for context",
		"- Handle follow-up questions appropriately",
		"- Reformulate query if no results found",
		"",
		"RESPONSE TEMPLATES:",
		"✅ Information Found: 'Based on the code/docs: [answer]. Source: [filename]'",
		"❌ Information Not Found: 'I couldn't find information about [topic] in the indexed code/docs.'",
		"",
		"CRITICAL: If retrieved context doesn't contain the answer, explicitly state this.",
		"Never guess or add information not in the code/docs.",
		"",
		"Context: {context}"
	)
	prompt = ChatPromptTemplate.from_messages([
		("system", system_prompt),
		("human", "{input}"),
	])
	history = []  # Store last 3 user queries
	while True:
		query = input("Ask a question about the codebase (or type 'exit'): ")
		if query.lower() == 'exit':
			break
		# Add to history and keep only last 3
		history.append(query)
		if len(history) > 3:
			history = history[-3:]
		# Retrieve relevant docs
		docs = retriever.invoke(query, k=3)
		context = "\n".join([doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in docs])
		# Add history to context
		if history:
			history_text = "\n".join([f"Previous user query: {h}" for h in history[:-1]])
			if history_text:
				context = history_text + "\n" + context
		# Format prompt
		formatted_prompt = prompt.format(context=context, input=query)
		# Call the model
		answer = model.invoke(formatted_prompt)
		print("Answer:", answer.content)

if __name__ == "__main__":
	main()
