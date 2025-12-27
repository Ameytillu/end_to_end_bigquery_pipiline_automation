
import logging
from prefect import flow, task
from data_ingestion.fetch_bigquery_data import fetch_orders
from transformations.clean_transform import clean_orders
from analytics.kpi_calculations import calculate_daily_kpis
from visualization.generate_charts import plot_revenue, plot_orders, plot_avg_order_value
from warehouse.load_to_postgres import load_to_postgres

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@task
def ingest():
    return fetch_orders()

@task
def transform(df):
    return clean_orders(df)

@task
def analyze(df):
    return calculate_daily_kpis(df)

@task
def visualize(kpis):
    plot_revenue(kpis)
    plot_orders(kpis)
    plot_avg_order_value(kpis)
    logging.info("Charts generated and saved.")


#@task
#def persist_data(df, kpis):
#    load_to_postgres(df, table_name="orders_clean")
#    load_to_postgres(kpis, table_name="daily_kpis")
#    logging.info("Data persisted to PostgreSQL.")


@flow
def run_pipeline():
    df = ingest()
    df = transform(df)
    kpis = analyze(df)
    visualize(kpis)
    # persist_data(df, kpis)  # Disabled for now
    return kpis

if __name__ == "__main__":
    run_pipeline()
