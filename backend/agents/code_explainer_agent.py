import sys
import os
from typing import List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import GitRepoLoader
from langchain_community.docstore.document import Document
import tempfile

from backend.agents.model_providers.agent_llms import agent_llms
from backend.agents.prompts import CODE_EXPLAINER_PROMPT_BASE, get_structured_prompt

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
	# Use centralized prompt helper for caching
	structured_system_prompt = get_structured_prompt(model, CODE_EXPLAINER_PROMPT_BASE)
	
	prompt = ChatPromptTemplate.from_messages([
		("system", structured_system_prompt if isinstance(structured_system_prompt, (str, list)) else structured_system_prompt.content),
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
