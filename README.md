# RAC Data Pipeline: Revenue & Churn Analysis

This project provides a modular, interactive data pipeline for analyzing geographical revenue and client churn from Excel files, with a user-friendly Streamlit interface.

## Features
- **Task 1: Geographical Revenue Analysis**
  - Revenue breakdown by entity and region for each quarter
  - Entity-wise total revenue summary
- **Task 2: Client Churn Analysis**
  - Churn and revenue gain/loss by region and quarter
  - Total revenue by client, region, and quarter
- **Drag-and-Drop File Upload**
  - Upload your Excel file directly in the web UI
- **Interactive Filtering**
  - Filter churn and client revenue tables by region and quarter in the UI
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
   (If you use Streamlit, pandas, openpyxl, langchain, faiss-cpu, sentence-transformers, openai, etc.)
3. **Run the Streamlit app:**
   ```bash
   streamlit run main.py
   ```
4. **Upload your Excel file** (must include columns: `Customer Name`, `Entity grouped`, `Region`, and monthly columns as dates).

## Usage
- After uploading your file, the app will display:
  - Revenue by entity and region for each quarter
  - Entity-wise total revenue
  - Churn analysis (with region/quarter filters)
  - Client-by-quarter revenue (with region/quarter filters)
- Use the filters to focus on specific regions or quarters.
- Download any table as a CSV for further analysis.

## Notes
- The Excel file must have at least these columns: `Customer Name`, `Entity grouped`, `Region`, and monthly columns with date-like names (e.g., `1/1/2024`).
- All code is modularized for easy extension and maintenance.

## License
MIT 