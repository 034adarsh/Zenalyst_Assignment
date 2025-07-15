import pandas as pd

def quarterly_revenue_by_client(df):
    """Calculate total revenue by client and region for each quarter."""
    return df.groupby(['Quarter', 'Region', 'Customer Name'])['Revenue'].sum().reset_index()

def churn_analysis(client_df):
    """Perform churn analysis between consecutive quarters, region-wise."""
    results = []
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    quarter_pairs = [(quarters[i], quarters[i+1]) for i in range(len(quarters)-1)]
    regions = client_df['Region'].unique()
    for region in regions:
        region_df = client_df[client_df['Region'] == region]
        for q1, q2 in quarter_pairs:
            df1 = region_df[region_df['Quarter'] == q1]
            df2 = region_df[region_df['Quarter'] == q2]
            clients1 = set(df1['Customer Name'])
            clients2 = set(df2['Customer Name'])
            lost = clients1 - clients2
            new = clients2 - clients1
            rev_lost = df1[df1['Customer Name'].isin(lost)]['Revenue'].sum() if lost else 0
            rev_gain = df2[df2['Customer Name'].isin(new)]['Revenue'].sum() if new else 0
            results.append({
                'Region': region,
                'From': q1, 'To': q2,
                'Lost Clients': len(lost),
                'New Clients': len(new),
                'Revenue Lost': round(rev_lost, 2),
                'Revenue Gained': round(rev_gain, 2)
            })
    return pd.DataFrame(results) 