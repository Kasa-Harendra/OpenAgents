import sys
import os
import glob
from typing import List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain.tools import tool
from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from langchain_text_splitters import ExperimentalMarkdownSyntaxTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from langchain_community.docstore.document import Document
import pypandoc
from pdf2docx import Converter

from backend.agents.model_providers.agent_llms import agent_llms
from backend.agents.prompts import RAG_PROMPT_BASE, get_structured_prompt

def convert_pdf_to_docx(pdf_path, docx_path):
    cv = Converter(pdf_path)
    cv.convert(docx_path)
    cv.close()

VECTORDB_STORE = {}

# @tool("load_vectordb")
def load_vectordb(folder: str, embedding_model_name: str = 'EmbeddingModel') -> str:
    """
    Load all files in a folder, split into chunks, and return an InMemoryVectorStore for retrieval.
    """
    files = glob.glob(os.path.join(folder, "*.*"))
    documents = []
    dir_description = f"This directory is named '{os.path.basename(folder)}'. It contains the following files: " + ", ".join([os.path.basename(f) for f in files])
    documents.append(Document(page_content=dir_description, metadata={"file": "__directory__"}))
    text_splitter = ExperimentalMarkdownSyntaxTextSplitter(headers_to_split_on=[("#", "Header1"), ("##", "Header2"), ("###", "Header3")])
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        base = os.path.splitext(file)[0]
        try:
            if ext == ".pdf":
                docx_path = base + ".docx"
                if not os.path.exists(docx_path):
                    convert_pdf_to_docx(file, docx_path)
                file_text = pypandoc.convert_file(docx_path, 'markdown')
            else:
                file_text = pypandoc.convert_file(file, 'markdown')
        except:
            with open(file, 'r', encoding="utf-8") as f:
                file_text = f.read()
        chunks = text_splitter.split_text(file_text)
        for chunk in chunks:
            documents.append(Document(page_content=chunk.page_content, metadata={"file": str(os.path.basename(file))}))
    embedding_model: Embeddings = agent_llms[embedding_model_name]
    vectordb = InMemoryVectorStore.from_documents(documents, embedding=embedding_model)
    db_key = os.path.abspath(folder)
    VECTORDB_STORE[db_key] = vectordb
    return db_key

@tool("retrieve_context")
def retrieve_context(query: str, vectordb_key: str, k: int = 3, history: list = None) -> str:
    """
    Retrieve relevant context from in-memory vector DB given a query and a vector DB.
    Args:
        query: The user query.
        vectordb: InMemoryVectorStore object (from load_vectordb).
        k: Number of top results.
        history: Optional list of previous queries.
    Returns:
        Retrieved context as a string.
    """
    vectordb: InMemoryVectorStore = VECTORDB_STORE.get(vectordb_key)
    if vectordb is None:
        return "Vector DB not loaded. Please load the vector DB first."
    retriever = vectordb.as_retriever()
    if history and len(history) >= 2:
        retrieval_query = "\n".join(history[-2:] + [query])
    else:
        retrieval_query = query
    docs = retriever.invoke(retrieval_query, k=k)
    context = "\n".join([doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in docs])
    return context


def run_rag_agent():
    folder = input("Enter folder path to load files: ")
    vectordb_key = load_vectordb(folder)
    print(f"Vector DB loaded from folder: {folder}")
    model: BaseChatModel = agent_llms['RAGAgent']
    # Use centralized prompt helper for caching
    structured_system_prompt = get_structured_prompt(model, RAG_PROMPT_BASE)

    tools = [retrieve_context]

    rag_agent = create_agent(
        model,
        tools,
        system_prompt=structured_system_prompt,
        name="RAGAgent"
    )
    
    history = []
    while True:
        query = input("Ask a question (or type 'exit'): ")
        if query.lower() == 'exit':
            break
        history.append(query)
        if len(history) > 3:
            history = history[-3:]
        # context = retrieve_context(query, vectordb_key=vectordb_key, history=history)
        result = rag_agent.invoke({
            "query": query,
            "vectordb_key": vectordb_key,
            "history": history
        })
        print("Answer:", result)



if __name__ == "__main__":
    run_rag_agent()
