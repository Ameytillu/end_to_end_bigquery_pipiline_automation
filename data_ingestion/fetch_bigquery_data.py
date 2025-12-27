def fetch_data_from_bigquery():
    # ...existing code...
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    query = "SELECT * FROM your_dataset.your_table"  # Update with your actual query
    print(f"DEBUG: Running BigQuery query: {query}")
    df = client.query(query).to_dataframe()
    print(f"DEBUG: Number of records fetched: {len(df)}")
    print(f"DEBUG: DataFrame columns: {df.columns.tolist()}")
    print(f"DEBUG: First 5 rows:\n{df.head()}")
    return df


import logging
import pandas as pd
import yaml


from google.cloud import bigquery
from google.oauth2 import service_account

def get_bigquery_client():
    import streamlit as st
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    project_id = st.secrets["gcp_service_account"]["project_id"]
    client = bigquery.Client(credentials=credentials, project=project_id)
    return client

def fetch_orders(start_date, end_date, limit):
    client = get_bigquery_client()
    query = f"""
        SELECT *
        FROM `bigquery-public-data.thelook_ecommerce.orders`
        WHERE created_at BETWEEN '{start_date}' AND '{end_date}'
        LIMIT {limit}
    """
    df = client.query(query).to_dataframe()
    return df
