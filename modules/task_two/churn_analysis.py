import pandas as pd

def overall_churn_analysis(df):
    # Step 1: Fix column names (convert datetime columns to string)
    df.columns = [col.strftime('%Y-%m-%d') if isinstance(col, pd.Timestamp) else str(col) for col in df.columns]

    # Step 2: Identify all month columns (2024 monthly revenue columns)
    month_cols = [col for col in df.columns if col.startswith('2024')]

    # Step 3: Clean and convert monthly revenue columns
    df[month_cols] = df[month_cols].replace('-', 0).fillna(0)
    df[month_cols] = df[month_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Step 4: Detect start and end month of non-zero revenue for each customer
    def detect_start_month(row):
        for col in month_cols:
            if row[col] > 0:
                return col
        return None

    def detect_end_month(row):
        for col in reversed(month_cols):
            if row[col] > 0:
                return col
        return None

    df['Start_Month'] = df.apply(detect_start_month, axis=1)
    df['End_Month'] = df.apply(detect_end_month, axis=1)

    # Step 5: Map start/end months to quarters
    month_to_quarter = {
        '01': 'Q1', '02': 'Q1', '03': 'Q1',
        '04': 'Q2', '05': 'Q2', '06': 'Q2',
        '07': 'Q3', '08': 'Q3', '09': 'Q3',
        '10': 'Q4', '11': 'Q4', '12': 'Q4'
    }

    df['Start_Quarter'] = df['Start_Month'].apply(lambda x: month_to_quarter.get(x.split('-')[1]) if pd.notna(x) else None)
    df['End_Quarter'] = df['End_Month'].apply(lambda x: month_to_quarter.get(x.split('-')[1]) if pd.notna(x) else None)

    # Step 6: Churn analysis between consecutive quarters
    quarter_pairs = [('Q1', 'Q2'), ('Q2', 'Q3'), ('Q3', 'Q4')]
    churn_data = []

    for q1, q2 in quarter_pairs:
        new_clients = df[df['Start_Quarter'] == q2]
        new_clients_rev = new_clients[month_cols].sum(axis=1).sum()

        lost_clients = df[df['End_Quarter'] == q1]
        lost_clients_rev = lost_clients[month_cols].sum(axis=1).sum()

        churn_data.append({
            'From Quarter': q1,
            'To Quarter': q2,
            'New Clients': new_clients.shape[0],
            'Revenue Gained': new_clients_rev,
            'Lost Clients': lost_clients.shape[0],
            'Revenue Lost': lost_clients_rev
        })

    # Step 7: Format result
    churn_df = pd.DataFrame(churn_data)
    churn_df['Revenue Gained'] = churn_df['Revenue Gained'].apply(lambda x: f"{x:,.2f}")
    churn_df['Revenue Lost'] = churn_df['Revenue Lost'].apply(lambda x: f"{x:,.2f}")
    return churn_df
