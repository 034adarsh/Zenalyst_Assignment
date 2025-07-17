import os
import pandas as pd
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
import tiktoken
from openai.types.chat import ChatCompletionMessageParam

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

# Answer question with context window management using OpenRouter

def answer_question(query, llm_temperature=0, max_context_tokens=2000, api_key=None, image_url=None):
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    context = retrieve_context_with_limit(query, embedding, max_tokens=max_context_tokens)
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    msg_content = [
        {"type": "text", "text": f"Context:\n{context}\n\nQuestion: {query}"}
    ]
    if image_url:
        msg_content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })  # type: ignore
    messages = [
        {
            "role": "user",
            "content": msg_content
        }
    ]  # type: ignore
    completion = client.chat.completions.create(
        model="openai/gpt-4o-2024-11-20",
        messages=messages,  # type: ignore
        max_tokens=1000,
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>",
            "X-Title": "<YOUR_SITE_NAME>",
        }
    )
    return completion.choices[0].message.content 