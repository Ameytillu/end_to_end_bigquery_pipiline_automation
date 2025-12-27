
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        logging.warning("Input DataFrame is empty or None.")
        return pd.DataFrame()
    try:
        df = df.copy()
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        missing_dates = df['created_at'].isna().sum()
        if missing_dates > 0:
            logging.warning(f"{missing_dates} rows have invalid 'created_at' values.")
        df['order_date'] = df['created_at'].dt.date
        df['total_order_value'] = pd.to_numeric(df['total_order_value'], errors='coerce').fillna(0)
        logging.info(f"Cleaned DataFrame: {len(df)} rows, columns: {list(df.columns)}")
        return df
    except Exception as e:
        logging.error(f"Error during cleaning: {e}")
        return pd.DataFrame()
