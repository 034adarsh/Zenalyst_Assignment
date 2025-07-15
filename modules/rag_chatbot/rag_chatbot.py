import os
import pandas as pd
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
import tiktoken

VECTOR_DIR = "./faiss_index"

# Utility: Convert DataFrames to text chunks for indexing
def dataframe_to_text_chunks(df, name):
    # Each row as a summary sentence
    return [f"{name} | " + ", ".join(f"{col}: {row[col]}" for col in df.columns) for _, row in df.iterrows()]

# Build vector index from pipeline results (list of DataFrames)
def build_vector_index_from_results(results_dict):
    documents = []
    for name, df in results_dict.items():
        if isinstance(df, pd.DataFrame):
            documents.extend(dataframe_to_text_chunks(df, name))
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.create_documents(documents)
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = FAISS.from_documents(docs, embedding)
    db.save_local(VECTOR_DIR)

# Retrieve context with token limit
def retrieve_context_with_limit(query, embedding, max_tokens=2000):
    db = FAISS.load_local(VECTOR_DIR, embedding, allow_dangerous_deserialization=True)
    retriever = db.as_retriever()
    docs = retriever.get_relevant_documents(query)
    # Token counting
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    context = ""
    total_tokens = 0
    for doc in docs:
        chunk = doc.page_content
        chunk_tokens = len(enc.encode(chunk))
        if total_tokens + chunk_tokens > max_tokens:
            break
        context += chunk + "\n"
        total_tokens += chunk_tokens
    return context

# Answer question with context window management
def answer_question(query, llm_temperature=0, max_context_tokens=2000):
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    context = retrieve_context_with_limit(query, embedding, max_tokens=max_context_tokens)
    llm = OpenAI(temperature=llm_temperature)
    prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
    return llm(prompt) 