import pandas as pd
def compute_inventory_turnover(cogs, avg_inventory):
    return round(cogs / avg_inventory, 2) if avg_inventory else None

def compute_sales_growth(df):
    df['date'] = pd.to_datetime(df['date'])
    monthly_sales = df.groupby(df['date'].dt.to_period("M"))['price'].sum()
    growth = monthly_sales.pct_change().fillna(0)
    return growth

def compute_stockout_rate(df):
    return (df['stock_level'] == 0).sum() / len(df)