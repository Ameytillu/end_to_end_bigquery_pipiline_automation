

import logging
import pandas as pd
import yaml

import os
import json
from google.cloud import bigquery
from google.oauth2 import service_account

def get_bigquery_client():
    # Try Streamlit secrets first (for cloud), else fallback to config/service_account.json (for local)
    try:
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )
            project_id = st.secrets["gcp_service_account"]["project_id"]
        else:
            raise Exception("No Streamlit secret found")
    except Exception:
        # Local: load from config/service_account.json
        key_path = os.path.join(os.path.dirname(__file__), '../config/service_account.json')
        with open(key_path, 'r') as f:
            key_dict = json.load(f)
        credentials = service_account.Credentials.from_service_account_info(key_dict)
        project_id = key_dict["project_id"]
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
