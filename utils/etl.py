import pandas as pd

def load_data(file_path):
    return pd.read_csv(file_path)

def clean_sales_data(df):
    df = df.dropna()
    df = df[df['quantity'] > 0]
    df = df[df['price'] > 0]
    return df.copy() 


def clean_inventory_data(df):
    df.dropna(inplace=True)
    df = df[df['stock_level'] >= 0]
    return df