# Data Pipeline: Revenue & Churn Analysis

![Dashboard Screenshot](./Screenshot%202025-07-16%20at%205.09.30%E2%80%AFPM.png)

This project provides an interactive Streamlit dashboard for analyzing business revenue and client churn from Excel files.

## Features
- **Quarterly Revenue by Entity**
  - Revenue breakdown by entity for each quarter (Q1, Q2, Q3, Q4)
  - CSV export for each quarter's summary
- **Client Churn Analysis**
  - Churn summary table: new/lost clients and revenue gained/lost for Q1→Q2, Q2→Q3, Q3→Q4 (overall, not by region)
- **Client Lifetime Value (LTV)**
  - Table of total revenue per client across all months
- **Monthly Revenue Trend**
  - Line chart of total revenue per month
- **Top Gaining and Losing Clients per Quarter**
  - Table showing clients with the largest revenue increases and decreases quarter-over-quarter
- **Downloadable Results**
  - Download all tables as CSV files

## Folder Structure
```
modules/
  task_one/
    revenue_analysis.py
  task_two/
    churn_analysis.py
  drag_and_drop/
    drag_and_drop.py
main.py
requirements.txt
README.md
```

## Setup Instructions
1. **Clone the repository and navigate to the project folder.**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   (Includes: streamlit, pandas, openpyxl, langchain, faiss-cpu, sentence-transformers, openai, etc.)
3. **Run the Streamlit app:**
   ```bash
   streamlit run main.py
   ```
4. **Upload your Excel file** (must include columns: `Customer Name`, `Entity grouped`, and monthly columns as dates, e.g., `Jan-24`).

## Usage
- After uploading your file, the app will display:
  - Revenue by entity for each quarter (Q1–Q4)
  - Churn summary table (new/lost clients and revenue, Q1→Q2, Q2→Q3, Q3→Q4)
  - Client Lifetime Value (total revenue per client)
  - Monthly revenue trend (line chart)
  - Top gaining/losing clients per quarter
- Download any table as a CSV for further analysis.

## Notes
- The Excel file must have at least these columns: `Customer Name`, `Entity grouped`, and monthly columns with date-like names (e.g., `Jan-24`).
- All code is modularized for easy extension and maintenance.

## License
MIT 
