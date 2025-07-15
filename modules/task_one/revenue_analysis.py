import pandas as pd
from datetime import datetime

def load_data(filepath):
    """Load Excel file and validate its structure."""
    try:
        df = pd.read_excel(filepath, parse_dates=True)
        required_cols = ['Customer Name', 'Entity grouped', 'Region']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Excel file missing required columns: {', '.join(required_cols)}")
        return df
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        raise

def melt_monthly_revenue(df):
    """Melt monthly revenue columns into a long format with quarter labels."""
    def is_date_string(s):
        try:
            pd.to_datetime(s, errors='raise')
            return True
        except Exception:
            return False
    revenue_cols = [col for col in df.columns if is_date_string(col)]
    id_vars = ['Customer Name', 'Entity grouped', 'Region']
    df_melt = df.melt(id_vars=id_vars, value_vars=revenue_cols,
                      var_name='Date', value_name='Revenue')
    df_melt.dropna(subset=['Revenue'], inplace=True)
    df_melt['Date'] = pd.to_datetime(df_melt['Date'])
    df_melt['Quarter'] = df_melt['Date'].dt.month.apply(
        lambda m: 'Q1' if m in [1,2,3] else
                  'Q2' if m in [4,5,6] else
                  'Q3' if m in [7,8,9] else 'Q4')
    return df_melt

def revenue_by_region_per_quarter(df):
    """Generate separate revenue tables for each quarter by Entity grouped and Region."""
    table = df.groupby(['Entity grouped', 'Region', 'Quarter'])["Revenue"].sum().reset_index()
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    quarter_tables = {}
    for quarter in quarters:
        quarter_data = table[table['Quarter'] == quarter][['Entity grouped', 'Region', 'Revenue']].copy()
        quarter_data.rename(columns={'Revenue': f'{quarter}_Revenue'}, inplace=True)
        quarter_data[f'{quarter}_Revenue'] = quarter_data[f'{quarter}_Revenue'].round(2)
        quarter_tables[quarter] = quarter_data.set_index(['Entity grouped', 'Region'])
    return quarter_tables

def entity_total_revenue(df):
    """Compute total revenue for each entity across all regions and quarters."""
    total = df.groupby('Entity grouped')["Revenue"].sum().reset_index()
    total.rename(columns={"Revenue": "Total Revenue"}, inplace=True)
    total["Total Revenue"] = total["Total Revenue"].round(2)
    return total 