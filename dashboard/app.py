


# Ensure project root is in sys.path for imports
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Streamlit Cloud: Write service account key from secrets to file and set env var
import streamlit as st
import json
from data_ingestion.fetch_bigquery_data import fetch_orders
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
	key_path = "/tmp/service_account.json"
	with open(key_path, "w") as f:
		f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
	os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
st.set_page_config(page_title="E2E BigQuery Analytics", layout="wide")
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

# --- Use session_state to persist data and query state ---
if 'df_clean' not in st.session_state:
	st.session_state.df_clean = None
	st.session_state.kpis = None
	st.session_state.selected_table = None
	st.session_state.limit = None

run_query = st.sidebar.button("Run Query")

if run_query or (
	st.session_state.df_clean is not None and
	st.session_state.selected_table == selected_table and
	st.session_state.limit == limit
):
	if run_query:
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
			st.session_state.df_clean = df_clean
			st.session_state.kpis = kpis
			st.session_state.selected_table = selected_table
			st.session_state.limit = limit
	else:
		df_clean = st.session_state.df_clean
		kpis = st.session_state.kpis

	if df_clean is not None and not df_clean.empty:
		st.subheader("Raw Data Preview")
		st.dataframe(df_clean.head(50))
		# --- Interactive Charting Section ---
		st.subheader("Explore Data Visually")
		chart_types = ["Bar", "Line", "Scatter", "Histogram", "Box"]
		chart_type = st.selectbox("Chart type", chart_types, index=0)

		numeric_cols = df_clean.select_dtypes(include=['number']).columns.tolist()
		categorical_cols = df_clean.select_dtypes(include=['object', 'category']).columns.tolist()
		all_cols = df_clean.columns.tolist()

		default_x = numeric_cols[0] if numeric_cols else (categorical_cols[0] if categorical_cols else all_cols[0])
		default_y = numeric_cols[1] if len(numeric_cols) > 1 else (numeric_cols[0] if numeric_cols else None)

		if chart_type in ["Bar", "Line", "Scatter"]:
			x_axis = st.selectbox("X axis", all_cols, index=all_cols.index(default_x) if default_x in all_cols else 0)
			y_axis = st.selectbox("Y axis", numeric_cols, index=numeric_cols.index(default_y) if default_y in numeric_cols else 0) if numeric_cols else None
		elif chart_type == "Histogram":
			x_axis = st.selectbox("Column", numeric_cols, index=0) if numeric_cols else None
			y_axis = None
		elif chart_type == "Box":
			x_axis = st.selectbox("X (category)", categorical_cols, index=0) if categorical_cols else None
			y_axis = st.selectbox("Y (numeric)", numeric_cols, index=0) if numeric_cols else None
		else:
			x_axis, y_axis = None, None

		if (
			(chart_type in ["Bar", "Line", "Scatter"] and x_axis and y_axis) or
			(chart_type == "Histogram" and x_axis) or
			(chart_type == "Box" and x_axis and y_axis)
		):
			fig, ax = plt.subplots()
			if chart_type == "Bar":
				if pd.api.types.is_numeric_dtype(df_clean[x_axis]):
					df_plot = df_clean[x_axis].value_counts().sort_index()
					df_plot.plot(kind="bar", ax=ax)
					ax.set_ylabel("Count")
				else:
					df_plot = df_clean.groupby(x_axis)[y_axis].mean().sort_values()
					df_plot.plot(kind="bar", ax=ax)
					ax.set_ylabel(f"Mean {y_axis}")
				ax.set_xlabel(x_axis)
				ax.set_title(f"Bar Chart: {x_axis} vs {y_axis if y_axis else 'Count'}")
			elif chart_type == "Line":
				ax.plot(df_clean[x_axis], df_clean[y_axis], marker='o')
				ax.set_xlabel(x_axis)
				ax.set_ylabel(y_axis)
				ax.set_title(f"Line Chart: {x_axis} vs {y_axis}")
			elif chart_type == "Scatter":
				ax.scatter(df_clean[x_axis], df_clean[y_axis], alpha=0.7)
				ax.set_xlabel(x_axis)
				ax.set_ylabel(y_axis)
				ax.set_title(f"Scatter Plot: {x_axis} vs {y_axis}")
			elif chart_type == "Histogram":
				ax.hist(df_clean[x_axis], bins=30, color='skyblue', edgecolor='black')
				ax.set_xlabel(x_axis)
				ax.set_ylabel("Frequency")
				ax.set_title(f"Histogram: {x_axis}")
			elif chart_type == "Box":
				df_clean.boxplot(column=y_axis, by=x_axis, ax=ax)
				ax.set_title(f"Box Plot: {y_axis} by {x_axis}")
				ax.set_xlabel(x_axis)
				ax.set_ylabel(y_axis)
				plt.suptitle("")
			st.pyplot(fig)
		else:
			st.info("Select valid columns for the chosen chart type.")

		# --- End Interactive Charting Section ---

		# Optionally show KPIs/charts only for orders
		if selected_table == "orders" and kpis is not None and not kpis.empty:
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

