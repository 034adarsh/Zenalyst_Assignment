# =======================
# STEP 0: Requirements
# =======================
# Install with:
# pip install pandas openpyxl streamlit langchain faiss-cpu sentence-transformers openai

import pandas as pd
import os
from datetime import datetime

# =======================
# STEP 1: Load the Excel Data
# =======================
def load_data(filepath):
    """Load Excel file and validate its structure."""
    try:
        df = pd.read_excel(filepath, parse_dates=True)
        # Required columns based on Excel structure
        required_cols = ['Customer Name', 'Entity grouped']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Excel file missing required columns: {', '.join(required_cols)}")
        
        # Identify monthly revenue columns (handle both string and datetime)
        month_cols = []
        for col in df.columns:
            if col not in required_cols and col != 'q1 sum':
                # Check if column is a datetime object or a string with date-like format
                if isinstance(col, datetime):
                    month_cols.append(col)
                elif isinstance(col, str) and col.endswith('-24'):
                    month_cols.append(col)
        
        if not month_cols:
            raise ValueError("No monthly revenue columns found (e.g., 'Jan-24' or datetime columns)")
        
        return df
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        raise

# =======================
# STEP 2: Prepare Data – Convert monthly columns
# =======================
def melt_monthly_revenue(df):
    """Melt monthly revenue columns into a long format with quarter labels."""
    def is_date_string(s):
        try:
            pd.to_datetime(s, errors='raise')
            return True
        except Exception:
            return False

    revenue_cols = [col for col in df.columns if is_date_string(col)]
    id_vars = ['Customer Name', 'Entity grouped']
    df_melt = df.melt(id_vars=id_vars, value_vars=revenue_cols,
                      var_name='Date', value_name='Revenue')
    df_melt.dropna(subset=['Revenue'], inplace=True)
    df_melt['Date'] = pd.to_datetime(df_melt['Date'])
    df_melt['Quarter'] = df_melt['Date'].dt.month.apply(
        lambda m: 'Q1' if m in [1,2,3] else
                  'Q2' if m in [4,5,6] else
                  'Q3' if m in [7,8,9] else 'Q4')
    return df_melt

# =======================
# STEP 3: Task 1 – Revenue by Entity and Region per Quarter (4 separate tables)
# =======================
def revenue_by_region_per_quarter(df):
    """Generate separate revenue tables for each quarter by Entity grouped."""
    # Group by Entity grouped and Quarter, summing Revenue
    table = df.groupby(['Entity grouped', 'Quarter'])["Revenue"].sum().reset_index()
    
    # Create separate DataFrames for each quarter
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    quarter_tables = {}
    
    for quarter in quarters:
        quarter_data = table[table['Quarter'] == quarter][['Entity grouped', 'Revenue']].copy()
        quarter_data.rename(columns={'Revenue': f'{quarter}_Revenue'}, inplace=True)
        quarter_data[f'{quarter}_Revenue'] = quarter_data[f'{quarter}_Revenue'].round(2)  # Round for clarity
        quarter_tables[quarter] = quarter_data.set_index(['Entity grouped'])
    
    return quarter_tables

# =======================
# STEP 4: Task 2 – Churn Analysis
# =======================
def quarterly_revenue_by_client(df):
    """Calculate total revenue by client for each quarter."""
    return df.groupby(['Quarter', 'Customer Name'])['Revenue'].sum().reset_index()

def churn_analysis(client_df):
    """Perform churn analysis between consecutive quarters."""
    results = []
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    quarter_pairs = [(quarters[i], quarters[i+1]) for i in range(len(quarters)-1)]
    
    for q1, q2 in quarter_pairs:
        df1 = client_df[client_df['Quarter'] == q1]
        df2 = client_df[client_df['Quarter'] == q2]

        clients1 = set(df1['Customer Name'])
        clients2 = set(df2['Customer Name'])

        # Identify lost and new clients
        lost = clients1 - clients2
        new = clients2 - clients1

        # Calculate revenue for lost and new clients
        rev_lost = df1[df1['Customer Name'].isin(lost)]['Revenue'].sum() if lost else 0
        rev_gain = df2[df2['Customer Name'].isin(new)]['Revenue'].sum() if new else 0

        results.append({
            'From': q1, 'To': q2,
            'Lost Clients': len(lost),
            'New Clients': len(new),
            'Revenue Lost': round(rev_lost, 2),
            'Revenue Gained': round(rev_gain, 2)
        })
    
    return pd.DataFrame(results)

# ==============================
# STEP 5: RAC Chatbot Components
# ==============================
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

# Directory Setup
RAC_DIR = "./rac_docs"
VECTOR_DIR = "./faiss_index"

# ==============================
# STEP 6: Build FAISS Index for Text + Tabular Notes
# ==============================
def build_vector_index():
    """Build FAISS vector index from text documents in RAC_DIR."""
    try:
        documents = []
        if not os.path.exists(RAC_DIR):
            print(f"Directory {RAC_DIR} does not exist. Skipping vector index build.")
            return
        for file in os.listdir(RAC_DIR):
            if file.endswith(".txt"):
                loader = TextLoader(os.path.join(RAC_DIR, file))
                documents.extend(loader.load())

        if not documents:
            print("No text files found in RAC_DIR. Skipping vector index build.")
            return

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = splitter.split_documents(documents)
        embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = FAISS.from_documents(docs, embedding)
        db.save_local(VECTOR_DIR)
        print("FAISS index built successfully.")
    except Exception as e:
        print(f"Error building FAISS index: {e}")

# ==============================
# STEP 7: Setup QA Chain
# ==============================
def get_rac_qa_chain():
    """Set up RetrievalQA chain for RAC chatbot."""
    try:
        embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = FAISS.load_local(VECTOR_DIR, embedding, allow_dangerous_deserialization=True)
        retriever = db.as_retriever()
        llm = OpenAI(temperature=0)  # Switch to ChatOpenAI or local LLM if needed
        return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    except Exception as e:
        print(f"Error setting up QA chain: {e}")
        return None

# ==============================
# STEP 8: Running the Full Pipeline
# ==============================
if __name__ == "__main__":
    try:
        # Load and prepare data
        df = load_data("/Users/adarshsingh/Desktop/zenalyst/ar 2 (1).xlsx")
        df_melted = melt_monthly_revenue(df)

        # Task 1: Generate and save separate tables for each quarter
        quarter_tables = revenue_by_region_per_quarter(df_melted)
        for quarter, table in quarter_tables.items():
            table.to_csv(f"region_revenue_{quarter}.csv")
            print(f"Saved region_revenue_{quarter}.csv")
            print(f"\n{quarter} Revenue by Entity and Region:\n{table}\n")

        # Task 2: Perform churn analysis and save results
        client_quarterly = quarterly_revenue_by_client(df_melted)
        churn_df = churn_analysis(client_quarterly)
        churn_df.to_csv("churn_analysis.csv", index=False)
        print("Saved churn_analysis.csv")
        print("\nChurn Analysis:\n", churn_df)

        # Optional: Build RAC Vector Index
        build_vector_index()

    except Exception as e:
        print(f"Pipeline failed: {e}")