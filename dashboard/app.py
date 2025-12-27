

# Ensure project root is in sys.path for imports
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from data_ingestion.fetch_bigquery_data import fetch_orders
from transformations.clean_transform import clean_orders
from analytics.kpi_calculations import calculate_daily_kpis
from visualization.generate_charts import plot_revenue, plot_orders, plot_avg_order_value
import matplotlib.pyplot as plt


st.set_page_config(page_title="E2E BigQuery Analytics", layout="wide")
st.title("End-to-End BigQuery Analytics Dashboard")

# Show dataset and metadata info
st.markdown("""
**Dataset:** `bigquery-public-data.thelook_ecommerce.orders`  
This dashboard uses the [BigQuery public dataset: thelook_ecommerce.orders](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=thelook_ecommerce&page=dataset) which contains simulated e-commerce order data for analytics and demo purposes.

**Table columns:**
- `order_id`, `user_id`, `status`, `gender`, `created_at`, `returned_at`, `shipped_at`, `delivered_at`, `num_of_item`, `sale_price` (via join with order_items)

**Source:** [Google Cloud Public Datasets](https://cloud.google.com/bigquery/public-data)
""")

# Sidebar controls
st.sidebar.header("Query Parameters")
today = date.today()
default_start = today - timedelta(days=30)
start_date = st.sidebar.date_input("Start date", default_start)
end_date = st.sidebar.date_input("End date", today)
limit = st.sidebar.number_input("Row limit", min_value=100, max_value=100000, value=1000, step=100)

if st.sidebar.button("Run Query"):
	with st.spinner("Fetching data from BigQuery..."):
		df = fetch_orders(start_date=start_date, end_date=end_date, limit=limit)
		df_clean = clean_orders(df)
		kpis = calculate_daily_kpis(df_clean)

	if not kpis.empty:
		st.subheader("Key Performance Indicators (KPIs)")
		kpi1, kpi2, kpi3 = st.columns(3)
		total_revenue = kpis['revenue'].sum()
		total_orders = kpis['orders'].sum()
		avg_order_value = kpis['avg_order_value'].mean()
		kpi1.metric("Total Revenue", f"${total_revenue:,.2f}")
		kpi2.metric("Total Orders", f"{total_orders}")
		kpi3.metric("Avg Order Value", f"${avg_order_value:,.2f}")

		st.subheader("Revenue Trend")
		fig1 = plt.figure()
		plt.plot(kpis['order_date'], kpis['revenue'], label='Revenue')
		plt.xlabel('Date')
		plt.ylabel('Revenue')
		plt.title('Daily Revenue')
		plt.xticks(rotation=45)
		plt.tight_layout()
		st.pyplot(fig1)

		st.subheader("Orders Trend")
		fig2 = plt.figure()
		plt.plot(kpis['order_date'], kpis['orders'], label='Orders', color='orange')
		plt.xlabel('Date')
		plt.ylabel('Orders')
		plt.title('Daily Orders')
		plt.xticks(rotation=45)
		plt.tight_layout()
		st.pyplot(fig2)

		st.subheader("Average Order Value Trend")
		fig3 = plt.figure()
		plt.plot(kpis['order_date'], kpis['avg_order_value'], label='Avg Order Value', color='green')
		plt.xlabel('Date')
		plt.ylabel('Avg Order Value')
		plt.title('Average Order Value by Day')
		plt.xticks(rotation=45)
		plt.tight_layout()
		st.pyplot(fig3)

		st.subheader("Raw Data Preview")
		st.dataframe(df_clean.head(50))
	else:
		st.warning("No data found for the selected parameters.")
else:
	st.info("Select parameters and click 'Run Query' to view analytics.")
