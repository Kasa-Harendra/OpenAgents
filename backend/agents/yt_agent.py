import sys
import os
from typing import List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.model_providers.agent_llms import agent_llms
from backend.agents.prompts import YT_PROMPT_BASE, get_structured_prompt
from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.docstore.document import Document

def load_and_chunk_youtube(video_url: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
	loader = YoutubeLoader(video_url=video_url, add_video_info=True)
	docs = loader.load()
	text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
	documents = []
	for doc in docs:
		chunks = text_splitter.split_text(doc.page_content)
		for chunk in chunks:
			documents.append(Document(page_content=chunk, metadata=doc.metadata))
	return documents

def main():
	video_url = input("Enter YouTube video URL to load and query: ")
	chunks = load_and_chunk_youtube(video_url)
	print(f"Loaded {len(chunks)} transcript chunks from video.")
	embedding_model: Embeddings = agent_llms['EmbeddingModel']
	vector_store = InMemoryVectorStore.from_documents(chunks, embedding=embedding_model)
	retriever = vector_store.as_retriever()
	model: BaseChatModel = agent_llms['RAGAgent']
	# Use centralized prompt helper for caching
	structured_system_prompt = get_structured_prompt(model, YT_PROMPT_BASE)
	
	prompt = ChatPromptTemplate.from_messages([
		("system", structured_system_prompt if isinstance(structured_system_prompt, (str, list)) else structured_system_prompt.content),
		("human", "{input}"),
	])
	history = []  # Store last 3 user queries
	while True:
		query = input("Ask a question about the video (or type 'exit'): ")
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
