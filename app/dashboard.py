import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.etl import clean_sales_data
from utils.kpi import compute_sales_growth

st.set_page_config(layout="wide")
st.title("Sales Insights Dashboard")

with st.expander("How to Use This Dashboard", expanded=False):
    st.markdown("""
    1. Upload your CSV file (must include Sales date, Sales amount, Product ID and Quantity sold).
    2. Map the required and optional columns in the sidebar.
    3. Filter data using the sidebar (e.g., by date, region, channel).
    4. View revenue KPIs and sales graphs.
    5. Use the custom comparison to explore relationships.
    6. Download the filtered dataset.
    """)


st.subheader("Upload Your Sales Data")
st.markdown("Minimum Required Columns: Date of Sale, Amount of sale, Product ID, QuantitySold")

uploaded_file = st.file_uploader("Upload a CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    st.sidebar.header("Column Mapping")
    base_required = {
         'Date of sale': 'date',
        'Amount of sale': 'price',
        'Product ID': 'product_id',
        'Quantity': 'quantity'
    }
    optional_fields = {
        'Unit Cost (cost/unit)': 'unit_cost',
        'Unit Price (price/unit)': 'unit_price',
        'Discount (%)': 'discount',
        'No. of Representatives': 'sales_rep',
        'Region': 'region',
        'Sales Channel': 'sales_channel',
        'Customer Type': 'customer_type',
        'Payment Method': 'payment_method',
        'Product Category': 'product_category'
    }

    user_column_map = {}

    st.sidebar.markdown("Required Columns")
    for label, internal in base_required.items():
        options = ["None"] + list(df.columns)
        selected = st.sidebar.selectbox(f"{label}", options=options, key=f"req_{internal}")
        if selected != "None":
            user_column_map[selected] = internal

    st.sidebar.markdown("Optional Columns")
    for label, internal in optional_fields.items():
        options = ["None"] + list(df.columns)
        selected = st.sidebar.selectbox(f"{label}", options=options, key=f"opt_{internal}")
        if selected != "None":
            user_column_map[selected] = internal

    df.rename(columns=user_column_map, inplace=True)

    if not {'date', 'price', 'product_id', 'quantity'}.issubset(df.columns):
        st.error("Please map all four required columns correctly to proceed.")
    else:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)
        df = clean_sales_data(df)

        st.success("Data Loaded & Cleaned")
        st.dataframe(df.head())

        st.sidebar.header("Filters")

        # Date filter — Always works (uses required 'date')
        date_range = st.sidebar.date_input("Select Date Range", [df['date'].min(), df['date'].max()])
        if len(date_range) == 2:
            df = df[(df['date'] >= pd.to_datetime(date_range[0])) & (df['date'] <= pd.to_datetime(date_range[1]))]

        # Optional Filters — Only if user mapped the column
        for col_key in ['region', 'sales_channel', 'sales_rep', 'product_category', 'customer_type', 'payment_method']:
            if col_key in user_column_map.values():
                unique_vals = df[col_key].unique()
                selected = st.sidebar.multiselect(f"Filter by {col_key.replace('_', ' ').title()}", unique_vals, default=unique_vals)
                df = df[df[col_key].isin(selected)]

        st.subheader("Key Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"₹ {df['price'].sum():,.2f}")
        col2.metric("Total Units Sold", int(df['quantity'].sum()))

        # Average Discount
        if 'discount' in user_column_map.values():
            col3.metric("Average Discount (%)", f"{df['discount'].mean():.2f}")
        else:
            col3.metric("Average Discount (%)", "N/A")

        # Gross Profit and Profit Margin
        if 'unit_price' in user_column_map.values() and 'unit_cost' in user_column_map.values():
            df['profit'] = (df['unit_price'] - df['unit_cost']) * df['quantity']
            profit = df['profit'].sum()
            margin = profit / df['price'].sum() * 100 if df['price'].sum() > 0 else 0
            st.metric("Gross Profit", f"₹ {profit:,.2f}")
            st.metric("Profit Margin (%)", f"{margin:.2f}%")
        else:
            st.metric("Gross Profit", "N/A")
            st.metric("Profit Margin (%)", "N/A")


        st.header("Visualizations")

        # Monthly Revenue — Always works (uses required columns)
        monthly = df.groupby(df['date'].dt.to_period('M'))['price'].sum().reset_index()
        monthly['date'] = monthly['date'].dt.to_timestamp()
        st.plotly_chart(px.bar(monthly, x='date', y='price', title="Monthly Revenue"), use_container_width=True)

        # Sales Growth — Always works (uses required columns)
        growth = compute_sales_growth(df).reset_index()
        growth.columns = ['date', 'growth']
        growth['date'] = growth['date'].dt.to_timestamp()
        growth['growth'] *= 100
        st.plotly_chart(px.line(growth, x='date', y='growth', title="Sales Growth (%)"), use_container_width=True)


        if 'region' in user_column_map.values():
            region_rev = df.groupby('region')['price'].sum().reset_index()
            st.plotly_chart(px.pie(region_rev, values='price', names='region', title="Revenue by Region"), use_container_width=True)

        if 'sales_channel' in user_column_map.values():
            channel_rev = df.groupby('sales_channel')['price'].sum().reset_index()
            st.plotly_chart(px.pie(channel_rev, values='price', names='sales_channel', title="Revenue by Sales Channel"), use_container_width=True)

        if 'product_category' in user_column_map.values():
            cat_rev = df.groupby('product_category')['price'].sum().reset_index()
            st.plotly_chart(px.bar(cat_rev, x='product_category', y='price', title="Revenue by Product Category"), use_container_width=True)

        if 'sales_rep' in user_column_map.values():
            rep_rev = df.groupby('sales_rep')['price'].sum().reset_index()
            st.plotly_chart(px.bar(rep_rev, x='sales_rep', y='price', title="Revenue by Sales Rep"), use_container_width=True)

        if 'customer_type' in user_column_map.values():
            cust_rev = df.groupby('customer_type')['price'].sum().reset_index()
            st.plotly_chart(px.pie(cust_rev, values='price', names='customer_type', title="Revenue by Customer Type"), use_container_width=True)

        if 'payment_method' in user_column_map.values():
            pay_rev = df.groupby('payment_method')['price'].sum().reset_index()
            st.plotly_chart(px.bar(pay_rev, x='payment_method', y='price', title="Revenue by Payment Method"), use_container_width=True)

        if 'discount' in user_column_map.values():
            st.plotly_chart(px.scatter(df, x='discount', y='price', title="Discount vs Sales Amount"), use_container_width=True)

        if 'unit_cost' in user_column_map.values() and 'unit_price' in user_column_map.values():
            st.plotly_chart(px.scatter(df, x='unit_cost', y='unit_price',
                                color='product_category' if 'product_category' in user_column_map.values() else None,
                                title="Unit Cost vs Unit Price"), use_container_width=True)

        # # Custom Compare — Works always with any available columns
        # st.subheader("Compare Any Two Columns")
        # col_x = st.selectbox("X-axis", df.columns)
        # col_y = st.selectbox("Y-axis", df.columns, index=1)
        # if col_x != col_y:
        #     st.plotly_chart(px.scatter(df, x=col_x, y=col_y, title=f"{col_y} vs {col_x}"), use_container_width=True)

        st.download_button("Download Processed Data", df.to_csv(index=False), file_name="processed_sales_data.csv")
else:
    st.info("Please upload a sales CSV to begin.")
