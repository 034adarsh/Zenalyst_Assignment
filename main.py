import os
from modules.task_one.revenue_analysis import load_data, melt_monthly_revenue, revenue_by_region_per_quarter, entity_total_revenue
from modules.task_two.churn_analysis import quarterly_revenue_by_client, churn_analysis
from modules.drag_and_drop.drag_and_drop import drag_and_drop_file
from modules.rag_chatbot.rag_chatbot import build_vector_index_from_results, answer_question

import streamlit as st
import pandas as pd

def main():
    st.title("Business Revenue & Client Churn Dashboard")
    st.write("Upload your Excel file and run analyses.")

    # --- OpenAI API Key Input ---
    if 'openai_api_key' not in st.session_state:
        st.session_state['openai_api_key'] = ''
    st.session_state['openai_api_key'] = st.text_input(
        "Enter your OpenAI API Key (required for chatbot)",
        type="password",
        value=st.session_state['openai_api_key']
    )
    if st.session_state['openai_api_key']:
        os.environ["OPENAI_API_KEY"] = st.session_state['openai_api_key']
    else:
        st.warning("Please enter your OpenAI API key above to use the chatbot.")

    uploaded_file = drag_and_drop_file()
    if uploaded_file is not None:
        # Save uploaded file to a temp location
        temp_path = os.path.join("./", uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File saved to {temp_path}")

        # Load and process data
        df = load_data(temp_path)
        df_melted = melt_monthly_revenue(df)

        # Task 1: Revenue by region per quarter
        st.header("Task 1: Geographical Revenue Analysis")
        quarter_tables = revenue_by_region_per_quarter(df_melted)
        for quarter, table in quarter_tables.items():
            st.subheader(f"{quarter} Revenue by Entity and Region")
            st.dataframe(table.reset_index())
            csv = table.reset_index().to_csv(index=False).encode('utf-8')
            st.download_button(f"Download {quarter} Revenue CSV", csv, file_name=f"region_revenue_{quarter}.csv")

        # Entity-wise total revenue
        st.subheader("Entity-wise Total Revenue (All Regions, All Quarters)")
        entity_total = entity_total_revenue(df_melted)
        st.dataframe(entity_total)
        entity_csv = entity_total.to_csv(index=False).encode('utf-8')
        st.download_button("Download Entity-wise Total Revenue CSV", entity_csv, file_name="entity_total_revenue.csv")

        # Task 2: Churn analysis
        st.header("Task 2: Client Churn Analysis")
        client_quarterly = quarterly_revenue_by_client(df_melted)
        churn_df = churn_analysis(client_quarterly)

        # Filters for churn analysis
        st.subheader("Filters for Churn Analysis")
        region_options = sorted(churn_df['Region'].unique())
        quarter_options = sorted(set(churn_df['From']).union(set(churn_df['To'])))
        selected_regions = st.multiselect("Select Region(s)", region_options, default=region_options)
        selected_quarters = st.multiselect("Select Quarter(s) (From/To)", quarter_options, default=quarter_options)
        filtered_churn = churn_df[
            churn_df['Region'].isin(selected_regions) &
            (churn_df['From'].isin(selected_quarters) | churn_df['To'].isin(selected_quarters))
        ]
        st.dataframe(filtered_churn)
        churn_csv = filtered_churn.to_csv(index=False).encode('utf-8')
        st.download_button("Download Churn Analysis CSV", churn_csv, file_name="churn_analysis.csv")

        # Client-by-quarter revenue table with filters
        st.header("Client Revenue by Quarter and Region")
        client_region_options = sorted(client_quarterly['Region'].unique())
        client_quarter_options = sorted(client_quarterly['Quarter'].unique())
        selected_client_regions = st.multiselect("Select Region(s) for Client Revenue", client_region_options, default=client_region_options, key="client_region")
        selected_client_quarters = st.multiselect("Select Quarter(s) for Client Revenue", client_quarter_options, default=client_quarter_options, key="client_quarter")
        filtered_client = client_quarterly[
            client_quarterly['Region'].isin(selected_client_regions) &
            client_quarterly['Quarter'].isin(selected_client_quarters)
        ]
        st.dataframe(filtered_client)
        client_csv = filtered_client.to_csv(index=False).encode('utf-8')
        st.download_button("Download Client Revenue by Quarter CSV", client_csv, file_name="client_revenue_by_quarter.csv")

        # --- RAG Chatbot Section ---
        st.header("Ask Questions About Your Data (Chatbot)")
        st.info("This chatbot uses your uploaded and processed data to answer questions. Example: 'Which entity had the highest revenue in Q2?' or 'Show churn for APAC region.'")

        # Build the vector index from all results (only once per upload)
        results_dict = {
            'Entity Total Revenue': entity_total,
            'Churn Analysis': churn_df,
            'Client Revenue by Quarter': client_quarterly
        }
        for q, t in quarter_tables.items():
            results_dict[f'Revenue {q}'] = t.reset_index()
        build_vector_index_from_results(results_dict)

        # Chatbot UI
        user_question = st.text_input("Ask a question about your data:")
        if user_question:
            if not st.session_state['openai_api_key']:
                st.error("Please enter your OpenAI API key above to use the chatbot.")
            else:
                with st.spinner("Generating answer..."):
                    answer = answer_question(user_question)
                st.success(answer)

if __name__ == "__main__":
    main() 