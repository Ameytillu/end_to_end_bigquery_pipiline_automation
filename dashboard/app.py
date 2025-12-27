import matplotlib.pyplot as plt



# Ensure project root is in sys.path for imports
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Streamlit Cloud: Write service account key from secrets to file and set env var
import streamlit as st
import json
import pandas as pd
from data_ingestion.fetch_bigquery_data import fetch_orders
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
	key_path = "/tmp/service_account.json"
	with open(key_path, "w") as f:
		f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
	os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
# Set Streamlit page config and show dataset info
st.set_page_config(page_title="E2E BigQuery Analytics", layout="wide")

st.title("End-to-End BigQuery Analytics Dashboard")

# --- Dataset Info and Metadata ---
st.markdown("""
**Data Source:** [Google BigQuery Public Dataset: thelook_ecommerce](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=thelook_ecommerce&page=dataset)

**Dataset:** `bigquery-public-data.thelook_ecommerce`

**Tables Available:**
- `products`: Product catalog with details like id, name, brand, category, price, etc.
- `distribution_centers`: Distribution center locations with latitude/longitude.
- `events`: User events (web/app) with event_type, session, city, etc.
- `inventory_items`: Inventory records with product, cost, category, etc.
- `order_items`: Order line items with status, price, shipment, etc.

**Note:**
This dashboard lets you explore and visualize data from the above tables. All data is simulated and for analytics demo purposes only.
""")
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

			if selected_table == "order_items":
				st.subheader("Order & Status Analysis")
				# 1. Order Status Distribution (Bar)
				if "status" in df_clean.columns:
					status_counts = df_clean["status"].value_counts()
					fig, ax = plt.subplots()
					status_counts.plot(kind="bar", ax=ax, color="skyblue")
					ax.set_xlabel("Order Status")
					ax.set_ylabel("Count")
					ax.set_title("Order Status Distribution (Bar)")
					plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig)
					# Donut/Pie chart
					fig2, ax2 = plt.subplots()
					status_counts.plot(kind="pie", ax=ax2, autopct='%1.1f%%', startangle=90)
					ax2.set_ylabel("")
					ax2.set_title("Order Status Distribution (Donut)")
					centre_circle = plt.Circle((0,0),0.70,fc='white')
					fig2.gca().add_artist(centre_circle)
					st.pyplot(fig2)

				# 2. Order Funnel (Created → Delivered → Returned)
				st.subheader("Order Funnel (Created → Delivered → Returned)")
				funnel_stages = [
					("Created", df_clean["created_at"].notnull().sum() if "created_at" in df_clean.columns else 0),
					("Delivered", df_clean["delivered_at"].notnull().sum() if "delivered_at" in df_clean.columns else 0),
					("Returned", df_clean["returned_at"].notnull().sum() if "returned_at" in df_clean.columns else 0)
				]
				funnel_labels, funnel_values = zip(*funnel_stages)
				fig3, ax3 = plt.subplots()
				ax3.barh(funnel_labels, funnel_values, color="lightgreen")
				ax3.set_xlabel("Count")
				ax3.set_title("Order Funnel")
				st.pyplot(fig3)

				# 3. Cancelled Orders Count (Bar)
				st.subheader("Cancelled Orders Count")
				if "status" in df_clean.columns:
					cancelled_count = (df_clean["status"] == "Cancelled").sum()
					fig4, ax4 = plt.subplots()
					ax4.bar(["Cancelled"], [cancelled_count], color="red")
					ax4.set_ylabel("Count")
					ax4.set_title("Cancelled Orders")
					st.pyplot(fig4)

				# 4. Returned Orders Count (Bar)
				st.subheader("Returned Orders Count")
				if "status" in df_clean.columns:
					returned_count = (df_clean["status"] == "Returned").sum()
					fig5, ax5 = plt.subplots()
					ax5.bar(["Returned"], [returned_count], color="orange")
					ax5.set_ylabel("Count")
					ax5.set_title("Returned Orders")
					st.pyplot(fig5)

			elif selected_table == "products":
				st.subheader("Product Assortment Overview")
				# 1. Product Count by Category (Bar)
				if "category" in df_clean.columns:
					cat_counts = df_clean["category"].value_counts()
					fig, ax = plt.subplots()
					cat_counts.plot(kind="bar", ax=ax, color="skyblue")
					ax.set_xlabel("Category")
					ax.set_ylabel("Product Count")
					ax.set_title("Product Count by Category")
					plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig)

				# 2. Product Count by Department (Men vs Women) (Bar and Donut)
				if "department" in df_clean.columns:
					dept_counts = df_clean["department"].value_counts()
					fig2, ax2 = plt.subplots()
					dept_counts.plot(kind="bar", ax=ax2, color="lightgreen")
					ax2.set_xlabel("Department")
					ax2.set_ylabel("Product Count")
					ax2.set_title("Product Count by Department (Bar)")
					plt.setp(ax2.get_xticklabels(), rotation=0, ha="center")
					st.pyplot(fig2)
					# Donut chart
					fig3, ax3 = plt.subplots()
					dept_counts.plot(kind="pie", ax=ax3, autopct='%1.1f%%', startangle=90)
					ax3.set_ylabel("")
					ax3.set_title("Product Count by Department (Donut)")
					centre_circle = plt.Circle((0,0),0.70,fc='white')
					fig3.gca().add_artist(centre_circle)
					st.pyplot(fig3)

				# 3. Product Count by Brand (Bar)
				if "brand" in df_clean.columns:
					brand_counts = df_clean["brand"].value_counts().head(20)
					fig4, ax4 = plt.subplots()
					brand_counts.plot(kind="bar", ax=ax4, color="orange")
					ax4.set_xlabel("Brand")
					ax4.set_ylabel("Product Count")
					ax4.set_title("Product Count by Brand (Top 20)")
					plt.setp(ax4.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig4)

				# 4. Product Count by Distribution Center (Bar)
				if "distribution_center" in df_clean.columns:
					dc_counts = df_clean["distribution_center"].value_counts()
					fig5, ax5 = plt.subplots()
					dc_counts.plot(kind="bar", ax=ax5, color="purple")
					ax5.set_xlabel("Distribution Center")
					ax5.set_ylabel("Product Count")
					ax5.set_title("Product Count by Distribution Center")
					plt.setp(ax5.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig5)

			elif selected_table == "distribution_centers":
				st.subheader("Geographic & Location Charts")
				# 1. Distribution Centers Map (US Map) – Point Map
				if "latitude" in df_clean.columns and "longitude" in df_clean.columns:
					st.markdown("**Distribution Centers Map (US)**")
					st.map(df_clean[["latitude", "longitude"]])
					# Size/color by center (if 'center_name' or similar exists)
					if "center_name" in df_clean.columns:
						fig, ax = plt.subplots()
						ax.scatter(df_clean["longitude"], df_clean["latitude"],
								   s=50, c=range(len(df_clean)), cmap="viridis", alpha=0.7)
						for i, name in enumerate(df_clean["center_name"]):
							ax.annotate(name, (df_clean["longitude"].iloc[i], df_clean["latitude"].iloc[i]), fontsize=8)
						ax.set_xlabel("Longitude")
						ax.set_ylabel("Latitude")
						ax.set_title("Distribution Centers by Location (Color by Center)")
						st.pyplot(fig)

				# 2. Distribution Centers by State (Bar and Map)
				if "state" in df_clean.columns:
					state_counts = df_clean["state"].value_counts()
					fig2, ax2 = plt.subplots()
					state_counts.plot(kind="bar", ax=ax2, color="skyblue")
					ax2.set_xlabel("State")
					ax2.set_ylabel("Center Count")
					ax2.set_title("Distribution Centers by State")
					plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig2)
					# Map by state (fallback: scatter by state centroid if available)
					if "latitude" in df_clean.columns and "longitude" in df_clean.columns:
						st.markdown("**Distribution Centers by State (Map)**")
						st.map(df_clean[["latitude", "longitude"]])

				# 3. Regional Spread of Distribution Centers (Map)
				st.markdown("**Regional Spread of Distribution Centers**")
				if "region" in df_clean.columns and "latitude" in df_clean.columns and "longitude" in df_clean.columns:
					fig3, ax3 = plt.subplots()
					regions = df_clean["region"].unique()
					colors = plt.cm.tab10(range(len(regions)))
					for i, region in enumerate(regions):
						mask = df_clean["region"] == region
						ax3.scatter(df_clean["longitude"][mask], df_clean["latitude"][mask],
									s=50, color=colors[i], label=region, alpha=0.7)
					ax3.set_xlabel("Longitude")
					ax3.set_ylabel("Latitude")
					ax3.set_title("Regional Spread of Distribution Centers")
					ax3.legend()
					st.pyplot(fig3)

				# 4. Distance Between Distribution Centers (Scatter/Map)
				st.markdown("**Distance Between Distribution Centers**")
				import numpy as np
				def haversine(lat1, lon1, lat2, lon2):
					R = 6371  # Earth radius in km
					phi1, phi2 = np.radians(lat1), np.radians(lat2)
					dphi = np.radians(lat2 - lat1)
					dlambda = np.radians(lon2 - lon1)
					a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
					return 2*R*np.arcsin(np.sqrt(a))
				if "latitude" in df_clean.columns and "longitude" in df_clean.columns:
					coords = df_clean[["latitude", "longitude"]].values
					n = len(coords)
					distances = []
					pairs = []
					for i in range(n):
						for j in range(i+1, n):
							d = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
							distances.append(d)
							pairs.append((i, j))
					if distances:
						fig4, ax4 = plt.subplots()
						ax4.scatter(range(len(distances)), distances, color="teal", alpha=0.7)
						ax4.set_xlabel("Pair Index")
						ax4.set_ylabel("Distance (km)")
						ax4.set_title("Distances Between Distribution Centers")
						st.pyplot(fig4)

			elif selected_table == "inventory_items":
				st.subheader("Inventory Overview")
				# 1. Total Inventory Items (KPI)
				total_items = len(df_clean)
				st.metric(label="Total Inventory Items", value=total_items)

				# 2. Inventory Items by Product Category (Bar)
				if "category" in df_clean.columns:
					cat_counts = df_clean["category"].value_counts()
					fig, ax = plt.subplots()
					cat_counts.plot(kind="bar", ax=ax, color="skyblue")
					ax.set_xlabel("Product Category")
					ax.set_ylabel("Inventory Count")
					ax.set_title("Inventory Items by Product Category")
					plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig)

				# 3. Inventory Items by Product Department (Bar)
				if "department" in df_clean.columns:
					dept_counts = df_clean["department"].value_counts()
					fig2, ax2 = plt.subplots()
					dept_counts.plot(kind="bar", ax=ax2, color="lightgreen")
					ax2.set_xlabel("Product Department")
					ax2.set_ylabel("Inventory Count")
					ax2.set_title("Inventory Items by Product Department")
					plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig2)

				# 4. Inventory Items by Brand (Bar)
				if "brand" in df_clean.columns:
					brand_counts = df_clean["brand"].value_counts().head(20)
					fig3, ax3 = plt.subplots()
					brand_counts.plot(kind="bar", ax=ax3, color="orange")
					ax3.set_xlabel("Brand")
					ax3.set_ylabel("Inventory Count")
					ax3.set_title("Inventory Items by Brand (Top 20)")
					plt.setp(ax3.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig3)

				# 5. Inventory Items by Distribution Center (Bar)
				if "distribution_center" in df_clean.columns:
					dc_counts = df_clean["distribution_center"].value_counts()
					fig4, ax4 = plt.subplots()
					dc_counts.plot(kind="bar", ax=ax4, color="purple")
					ax4.set_xlabel("Distribution Center")
					ax4.set_ylabel("Inventory Count")
					ax4.set_title("Inventory Items by Distribution Center")
					plt.setp(ax4.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig4)

			elif selected_table == "events":
				st.subheader("Event Volume & Activity")
				# 1. Total Events Over Time (Line)
				if "event_time" in df_clean.columns:
					df_clean["event_time"] = pd.to_datetime(df_clean["event_time"])
					events_over_time = df_clean.groupby(df_clean["event_time"].dt.date).size()
					fig, ax = plt.subplots()
					events_over_time.plot(ax=ax, kind="line", marker="o", color="blue")
					ax.set_xlabel("Date")
					ax.set_ylabel("Total Events")
					ax.set_title("Total Events Over Time")
					plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig)

				# 2. Events by Event Type (Bar and Donut)
				if "event_type" in df_clean.columns:
					event_type_counts = df_clean["event_type"].value_counts()
					fig2, ax2 = plt.subplots()
					event_type_counts.plot(kind="bar", ax=ax2, color="green")
					ax2.set_xlabel("Event Type")
					ax2.set_ylabel("Count")
					ax2.set_title("Events by Event Type (Bar)")
					plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig2)
					# Donut chart
					fig3, ax3 = plt.subplots()
					event_type_counts.plot(kind="pie", ax=ax3, autopct='%1.1f%%', startangle=90)
					ax3.set_ylabel("")
					ax3.set_title("Events by Event Type (Donut)")
					centre_circle = plt.Circle((0,0),0.70,fc='white')
					fig3.gca().add_artist(centre_circle)
					st.pyplot(fig3)

				# 3. Event Trend by Type Over Time (Stacked Area)
				if "event_time" in df_clean.columns and "event_type" in df_clean.columns:
					df_clean["event_time"] = pd.to_datetime(df_clean["event_time"])
					trend_df = df_clean.groupby([df_clean["event_time"].dt.date, "event_type"]).size().unstack(fill_value=0)
					fig4, ax4 = plt.subplots()
					trend_df.plot.area(ax=ax4, stacked=True, alpha=0.7)
					ax4.set_xlabel("Date")
					ax4.set_ylabel("Event Count")
					ax4.set_title("Event Trend by Type Over Time (Stacked Area)")
					plt.setp(ax4.get_xticklabels(), rotation=45, ha="right")
					st.pyplot(fig4)

				# 4. Events per Session (Histogram)
				if "session_id" in df_clean.columns:
					session_counts = df_clean["session_id"].value_counts()
					fig5, ax5 = plt.subplots()
					ax5.hist(session_counts, bins=30, color='purple', edgecolor='black')
					ax5.set_xlabel("Events per Session")
					ax5.set_ylabel("Frequency")
					ax5.set_title("Events per Session (Histogram)")
					st.pyplot(fig5)

				# 5. Events per User (Histogram)
				if "user_id" in df_clean.columns:
					user_counts = df_clean["user_id"].value_counts()
					fig6, ax6 = plt.subplots()
					ax6.hist(user_counts, bins=30, color='orange', edgecolor='black')
					ax6.set_xlabel("Events per User")
					ax6.set_ylabel("Frequency")
					ax6.set_title("Events per User (Histogram)")
					st.pyplot(fig6)
				status_counts.plot(kind="bar", ax=ax, color="skyblue")
				ax.set_xlabel("Order Status")
				ax.set_ylabel("Count")
				ax.set_title("Order Status Distribution (Bar)")
				plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
				st.pyplot(fig)
				# Donut/Pie chart
				fig2, ax2 = plt.subplots()
				status_counts.plot(kind="pie", ax=ax2, autopct='%1.1f%%', startangle=90)
				ax2.set_ylabel("")
				ax2.set_title("Order Status Distribution (Donut)")
				centre_circle = plt.Circle((0,0),0.70,fc='white')
				fig2.gca().add_artist(centre_circle)
				st.pyplot(fig2)

			# 2. Order Funnel (Created → Delivered → Returned)
			st.subheader("Order Funnel (Created → Delivered → Returned)")
			funnel_stages = [
				("Created", df_clean["created_at"].notnull().sum() if "created_at" in df_clean.columns else 0),
				("Delivered", df_clean["delivered_at"].notnull().sum() if "delivered_at" in df_clean.columns else 0),
				("Returned", df_clean["returned_at"].notnull().sum() if "returned_at" in df_clean.columns else 0)
			]
			funnel_labels, funnel_values = zip(*funnel_stages)
			fig3, ax3 = plt.subplots()
			ax3.barh(funnel_labels, funnel_values, color="lightgreen")
			ax3.set_xlabel("Count")
			ax3.set_title("Order Funnel")
			st.pyplot(fig3)

			# 3. Cancelled Orders Count (Bar)
			st.subheader("Cancelled Orders Count")
			if "status" in df_clean.columns:
				cancelled_count = (df_clean["status"] == "Cancelled").sum()
				fig4, ax4 = plt.subplots()
				ax4.bar(["Cancelled"], [cancelled_count], color="red")
				ax4.set_ylabel("Count")
				ax4.set_title("Cancelled Orders")
				st.pyplot(fig4)

			# 4. Returned Orders Count (Bar)
			st.subheader("Returned Orders Count")
			if "status" in df_clean.columns:
				returned_count = (df_clean["status"] == "Returned").sum()
				fig5, ax5 = plt.subplots()
				ax5.bar(["Returned"], [returned_count], color="orange")
				ax5.set_ylabel("Count")
				ax5.set_title("Returned Orders")
				st.pyplot(fig5)

		elif selected_table != "order_items":
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
				max_xticks = 20
				if chart_type == "Bar":
					if pd.api.types.is_numeric_dtype(df_clean[x_axis]):
						df_plot = df_clean[x_axis].value_counts().sort_index()
						df_plot.plot(kind="bar", ax=ax)
						ax.set_ylabel("Count")
					else:
						df_plot = df_clean.groupby(x_axis)[y_axis].mean().sort_values()
						if len(df_plot) > max_xticks:
							st.warning(f"Too many unique values in '{x_axis}' to display clearly. Showing top {max_xticks}.")
							df_plot = df_plot.head(max_xticks)
						df_plot.plot(kind="bar", ax=ax)
						ax.set_ylabel(f"Mean {y_axis}")
					ax.set_xlabel(x_axis)
					ax.set_title(f"Bar Chart: {x_axis} vs {y_axis if y_axis else 'Count'}")
					plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
				elif selected_table == "products":
					st.subheader("Product Assortment Overview")
					# 1. Product Count by Category (Bar)
					if "category" in df_clean.columns:
						cat_counts = df_clean["category"].value_counts()
						fig, ax = plt.subplots()
						cat_counts.plot(kind="bar", ax=ax, color="skyblue")
						ax.set_xlabel("Category")
						ax.set_ylabel("Product Count")
						ax.set_title("Product Count by Category")
						plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
						st.pyplot(fig)

					# 2. Product Count by Department (Men vs Women) (Bar and Donut)
					if "department" in df_clean.columns:
						dept_counts = df_clean["department"].value_counts()
						fig2, ax2 = plt.subplots()
						dept_counts.plot(kind="bar", ax=ax2, color="lightgreen")
						ax2.set_xlabel("Department")
						ax2.set_ylabel("Product Count")
						ax2.set_title("Product Count by Department (Bar)")
						plt.setp(ax2.get_xticklabels(), rotation=0, ha="center")
						st.pyplot(fig2)
						# Donut chart
						fig3, ax3 = plt.subplots()
						dept_counts.plot(kind="pie", ax=ax3, autopct='%1.1f%%', startangle=90)
						ax3.set_ylabel("")
						ax3.set_title("Product Count by Department (Donut)")
						centre_circle = plt.Circle((0,0),0.70,fc='white')
						fig3.gca().add_artist(centre_circle)
						st.pyplot(fig3)

					# 3. Product Count by Brand (Bar)
					if "brand" in df_clean.columns:
						brand_counts = df_clean["brand"].value_counts().head(20)
						fig4, ax4 = plt.subplots()
						brand_counts.plot(kind="bar", ax=ax4, color="orange")
						ax4.set_xlabel("Brand")
						ax4.set_ylabel("Product Count")
						ax4.set_title("Product Count by Brand (Top 20)")
						plt.setp(ax4.get_xticklabels(), rotation=45, ha="right")
						st.pyplot(fig4)

					# 4. Product Count by Distribution Center (Bar)
					if "distribution_center" in df_clean.columns:
						dc_counts = df_clean["distribution_center"].value_counts()
						fig5, ax5 = plt.subplots()
						dc_counts.plot(kind="bar", ax=ax5, color="purple")
						ax5.set_xlabel("Distribution Center")
						ax5.set_ylabel("Product Count")
						ax5.set_title("Product Count by Distribution Center")
						plt.setp(ax5.get_xticklabels(), rotation=45, ha="right")
						st.pyplot(fig5)
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

