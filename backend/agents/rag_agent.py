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
# from pdf2docx import Converter

from backend.agents.model_providers.agent_llms import agent_llms
from backend.agents.prompts.prompts import RAG_PROMPT_BASE, get_structured_prompt

# def convert_pdf_to_docx(pdf_path, docx_path):
#     cv = Converter(pdf_path)
#     cv.convert(docx_path)
#     cv.close()

from backend.agents.toolkits.rag_toolkit import VECTORDB_STORE, RAGToolkit, load_vectordb


def run_rag_agent():
    folder = input("Enter folder path to load files: ")
    vectordb_key = load_vectordb(folder)
    print(f"Vector DB loaded from folder: {folder}")
    model: BaseChatModel = agent_llms['RAGAgent']
    # Use centralized prompt helper for caching
    structured_system_prompt = get_structured_prompt(model, RAG_PROMPT_BASE)

    toolkit = RAGToolkit()
    tools = toolkit.get_tools()

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
