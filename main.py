import os
from modules.task_one.revenue_analysis import load_data, melt_monthly_revenue, revenue_by_region_per_quarter, entity_total_revenue
from modules.task_two.churn_analysis import overall_churn_analysis
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
        "Enter your OpenRouter API Key (required for chatbot)",
        type="password",
        value=st.session_state['openai_api_key']
    )
    if st.session_state['openai_api_key']:
        os.environ["OPENAI_API_KEY"] = st.session_state['openai_api_key']
    else:
        st.warning("Please enter your OpenRouter API key above to use the chatbot.")

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

        # Task 2: Churn analysis (overall summary only)
        st.header("Task 2: Client Churn Analysis")
        st.subheader("Overall Churn Summary")
        overall_churn_df = overall_churn_analysis(df)
        st.dataframe(overall_churn_df)
        overall_churn_csv = overall_churn_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Overall Churn Summary CSV", overall_churn_csv, file_name="overall_churn_summary.csv")

        # Client Lifetime Value (LTV) Table ---
        st.header("Client Lifetime Value (LTV)")
        # Identify month columns
        month_cols = [col for col in df.columns if col.startswith('2024')]
        ltv_df = df[['Customer Name'] + month_cols].copy()
        ltv_df['Lifetime Revenue'] = ltv_df[month_cols].sum(axis=1)
        ltv_summary = ltv_df.groupby('Customer Name')['Lifetime Revenue'].sum().reset_index().sort_values('Lifetime Revenue', ascending=False)
        st.dataframe(ltv_summary)
        ltv_csv = ltv_summary.to_csv(index=False).encode('utf-8')
        st.download_button("Download Client LTV CSV", ltv_csv, file_name="client_lifetime_value.csv")

        # Monthly Revenue Trend (Line Chart) ---
        st.header("Monthly Revenue Trend")
        monthly_revenue = df[month_cols].sum().reset_index()
        monthly_revenue.columns = ['Month', 'Total Revenue']
        st.line_chart(monthly_revenue.set_index('Month'))
        st.dataframe(monthly_revenue)
        monthly_csv = monthly_revenue.to_csv(index=False).encode('utf-8')
        st.download_button("Download Monthly Revenue CSV", monthly_csv, file_name="monthly_revenue_trend.csv")

        # Top Gaining and Losing Clients per Quarter ---
        st.header("Top Gaining and Losing Clients per Quarter")
        # Prepare quarter-month mapping
        quarter_months = {
            'Q1': [m for m in month_cols if '-01-' in m or '-02-' in m or '-03-' in m],
            'Q2': [m for m in month_cols if '-04-' in m or '-05-' in m or '-06-' in m],
            'Q3': [m for m in month_cols if '-07-' in m or '-08-' in m or '-09-' in m],
            'Q4': [m for m in month_cols if '-10-' in m or '-11-' in m or '-12-' in m],
        }
        gain_loss_tables = []
        for q_idx, q in enumerate(['Q1', 'Q2', 'Q3', 'Q4']):
            if q_idx == 0:
                continue  # Skip Q1 (no previous quarter)
            prev_q = ['Q1', 'Q2', 'Q3', 'Q4'][q_idx-1]
            # Skip if no month columns for this quarter
            if not quarter_months[prev_q] or not quarter_months[q]:
                continue
            prev_rev = df[['Customer Name'] + quarter_months[prev_q]].copy()
            prev_rev['Prev_Quarter_Revenue'] = prev_rev[quarter_months[prev_q]].sum(axis=1)
            curr_rev = df[['Customer Name'] + quarter_months[q]].copy()
            curr_rev['Curr_Quarter_Revenue'] = curr_rev[quarter_months[q]].sum(axis=1)
            prev_merge = pd.DataFrame(prev_rev[['Customer Name', 'Prev_Quarter_Revenue']])
            curr_merge = pd.DataFrame(curr_rev[['Customer Name', 'Curr_Quarter_Revenue']])
            merged = pd.merge(prev_merge, curr_merge, on='Customer Name', how='outer').fillna(0)
            merged['Change'] = merged['Curr_Quarter_Revenue'] - merged['Prev_Quarter_Revenue']
            top_gainers = merged.sort_values('Change', ascending=False).head(5)
            top_losers = merged.sort_values('Change').head(5)
            st.subheader(f"{prev_q} to {q} - Top Gainers")
            st.dataframe(top_gainers[['Customer Name', 'Prev_Quarter_Revenue', 'Curr_Quarter_Revenue', 'Change']])
            st.subheader(f"{prev_q} to {q} - Top Losers")
            st.dataframe(top_losers[['Customer Name', 'Prev_Quarter_Revenue', 'Curr_Quarter_Revenue', 'Change']])
            gain_loss_tables.append((f"{prev_q} to {q}", top_gainers, top_losers))

        # --- RAG Chatbot Section ---
        st.header("Ask Questions About Your Data (Chatbot)")
        st.info("This chatbot uses your uploaded and processed data to answer questions. Example: 'Which entity had the highest revenue in Q2?' or 'Show churn for APAC region.'")

        # Build the vector index from all results (only once per upload)
        results_dict = {
            'Entity Total Revenue': entity_total,
            'Overall Churn Summary': overall_churn_df,
            'Client LTV': ltv_summary,
            'Monthly Revenue Trend': monthly_revenue
        }
        for q, t in quarter_tables.items():
            results_dict[f'Revenue {q}'] = t.reset_index()
        build_vector_index_from_results(results_dict)

        # Chatbot UI
        user_question = st.text_input("Ask a question about your data:")
        if user_question:
            if not st.session_state['openai_api_key']:
                st.error("Please enter your OpenRouter API key above to use the chatbot.")
            else:
                with st.spinner("Generating answer..."):
                    answer = answer_question(user_question, max_context_tokens=2000, api_key=st.session_state['openai_api_key'])
                st.success(answer)

if __name__ == "__main__":
    main() 