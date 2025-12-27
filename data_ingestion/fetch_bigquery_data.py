
import os
import logging
import pandas as pd
from google.cloud import bigquery
import yaml

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load config
def load_config(config_path="config/config.yaml"):
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        raise

def fetch_orders(start_date=None, end_date=None, limit=100000, config_path="config/config.yaml"):
    """
    Fetch orders from BigQuery with optional date filtering and row limit.
    Args:
        start_date (str): 'YYYY-MM-DD' or None
        end_date (str): 'YYYY-MM-DD' or None
        limit (int): max rows to fetch
        config_path (str): path to config file
    Returns:
        pd.DataFrame
    """
    config = load_config(config_path)
    dataset = config.get('project', {}).get('dataset', 'thelook_ecommerce')
    project_id = config.get('project', {}).get('gcp_project', 'bigquery-public-data')

    # Optionally set GOOGLE_APPLICATION_CREDENTIALS from config
    credentials_path = config.get('project', {}).get('gcp_credentials')
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

    client = bigquery.Client()
    where_clauses = []
    if start_date:
        where_clauses.append(f"o.created_at >= '{start_date}'")
    if end_date:
        where_clauses.append(f"o.created_at <= '{end_date}'")
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    SELECT
        o.order_id,
        o.user_id,
        o.status,
        o.gender,
        o.created_at,
        o.returned_at,
        o.shipped_at,
        o.delivered_at,
        o.num_of_item,
        SUM(oi.sale_price) AS total_order_value
    FROM `{project_id}.{dataset}.orders` o
    LEFT JOIN `{project_id}.{dataset}.order_items` oi
        ON o.order_id = oi.order_id
    {where_sql}
    GROUP BY o.order_id, o.user_id, o.status, o.gender, o.created_at, o.returned_at, o.shipped_at, o.delivered_at, o.num_of_item
    ORDER BY o.created_at DESC
    LIMIT {limit}
    """
    try:
        logging.info(f"Running query: {query}")
        df = client.query(query).to_dataframe()
        logging.info(f"Fetched {len(df)} rows from BigQuery.")
        return df
    except Exception as e:
        logging.error(f"BigQuery fetch failed: {e}")
        raise
