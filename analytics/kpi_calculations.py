
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_daily_kpis(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        logging.warning("Input DataFrame is empty or None for KPI calculation.")
        return pd.DataFrame()
    try:
        grouped = df.groupby("order_date").agg(
            revenue=("total_order_value", "sum"),
            orders=("order_id", "count"),
            avg_order_value=("total_order_value", "mean")
        ).reset_index()
        logging.info(f"Calculated KPIs for {len(grouped)} days.")
        return grouped
    except Exception as e:
        logging.error(f"Error during KPI calculation: {e}")
        return pd.DataFrame()
