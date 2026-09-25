from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.vectorstores import InMemoryVectorStore
import os
import glob
from langchain_community.docstore.document import Document
from langchain_text_splitters import ExperimentalMarkdownSyntaxTextSplitter
from langchain.embeddings import Embeddings
import pypandoc
# from pdf2docx import Converter
from backend.agents.model_providers.agent_llms import agent_llms

# def convert_pdf_to_docx(pdf_path, docx_path):
#     cv = Converter(pdf_path)
#     cv.convert(docx_path)
#     cv.close()

# Shared vector DB store
VECTORDB_STORE = {}

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
                # if not os.path.exists(docx_path):
                #     convert_pdf_to_docx(file, docx_path)
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

class RetrieveContextSchema(BaseModel):
    query: str = Field(..., description="The user query.")
    vectordb_key: str = Field(..., description="The key of the vector DB to retrieve from.")
    k: int = Field(default=3, description="Number of top results to retrieve.")
    history: list = Field(default=None, description="Optional list of previous queries.")

class RetrieveContextTool(BaseTool):
    name: str = "retrieve_context"
    description: str = "Retrieve relevant context from in-memory vector DB given a query and a vector DB key."
    args_schema: type[BaseModel] = RetrieveContextSchema

    def _run(self, query: str, vectordb_key: str, k: int = 3, history: list = None) -> str:
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

from langchain_core.tools import BaseToolkit
from typing import List

class RAGToolkit(BaseToolkit):
    def get_tools(self) -> List[BaseTool]:
        return [RetrieveContextTool()]
