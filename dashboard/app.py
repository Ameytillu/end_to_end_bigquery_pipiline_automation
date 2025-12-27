


# Ensure project root is in sys.path for imports
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Streamlit Cloud: Write service account key from secrets to file and set env var
import streamlit as st
import json
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
	key_path = "/tmp/service_account.json"
	with open(key_path, "w") as f:
		f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
	os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from data_ingestion.fetch_bigquery_data import fetch_orders, get_bigquery_client
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


# Diagnostic: Show min/max created_at date in the dataset
with st.spinner("Checking available data range in BigQuery..."):
	client = get_bigquery_client()
	diag_query = """
		SELECT MIN(created_at) as min_date, MAX(created_at) as max_date
		FROM `bigquery-public-data.thelook_ecommerce.orders`
	"""
	diag_result = client.query(diag_query).to_dataframe()
	min_date = diag_result['min_date'][0].date() if not diag_result.empty else None
	max_date = diag_result['max_date'][0].date() if not diag_result.empty else None
	if min_date and max_date:
		st.info(f"Available data range: **{min_date}** to **{max_date}**")
	else:
		st.warning("Could not determine available data range.")

st.sidebar.header("Query Parameters")


# Table selector and row limit
table_options = [
	"products",
	"distribution_centers",
	"events",
	"inventory_items",
	"order_items"
]
selected_table = st.sidebar.selectbox("Select table", table_options)
limit = st.sidebar.number_input("Row limit", min_value=100, max_value=100000, value=1000, step=100)

st.write(f"DEBUG: selected_table={selected_table}, limit={limit}")

if st.sidebar.button("Run Query"):
	with st.spinner("Fetching data from BigQuery..."):
		st.write(f"DEBUG: Querying table={selected_table} with limit={limit}")
		df = fetch_orders(table_name=selected_table, limit=limit)
		# Optionally, apply cleaning/analytics only for orders/products
		if selected_table == "orders":
			df_clean = clean_orders(df)
			kpis = calculate_daily_kpis(df_clean)
		else:
			df_clean = df
			kpis = pd.DataFrame()  # No KPIs for non-orders

	if not df_clean.empty:
		st.subheader("Raw Data Preview")
		st.dataframe(df_clean.head(50))

		# Visualizations for each table
		if selected_table == "products":
			st.subheader("Product Category Distribution")
			if "category" in df_clean.columns:
				cat_counts = df_clean["category"].value_counts()
				st.bar_chart(cat_counts)
		elif selected_table == "distribution_centers":
			st.subheader("Distribution Centers Locations")
			if "latitude" in df_clean.columns and "longitude" in df_clean.columns:
				st.map(df_clean[["latitude", "longitude"]].rename(columns={"latitude": "lat", "longitude": "lon"}))
		elif selected_table == "events":
			st.subheader("Event Type Counts")
			if "event_type" in df_clean.columns:
				event_counts = df_clean["event_type"].value_counts()
				st.bar_chart(event_counts)
		elif selected_table == "inventory_items":
			st.subheader("Product Category in Inventory Items")
			if "product_category" in df_clean.columns:
				inv_cat_counts = df_clean["product_category"].value_counts()
				st.bar_chart(inv_cat_counts)
		elif selected_table == "order_items":
			st.subheader("Order Status Distribution")
			if "status" in df_clean.columns:
				status_counts = df_clean["status"].value_counts()
				st.bar_chart(status_counts)

		# Optionally show KPIs/charts only for orders
		if selected_table == "orders" and not kpis.empty:
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
	else:
		st.warning("No data found for the selected parameters.")
else:
	st.info("Select table and row limit, then click 'Run Query' to view data.")
