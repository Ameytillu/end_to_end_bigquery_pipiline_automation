
import logging
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def plot_revenue(df, save_path="visualization/revenue_trend.png"):
    try:
        plt.figure()
        plt.plot(df['order_date'], df['revenue'], label='Revenue')
        plt.title("Daily Revenue")
        plt.xlabel("Date")
        plt.ylabel("Revenue")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        logging.info(f"Revenue chart saved to {save_path}")
    except Exception as e:
        logging.error(f"Failed to generate revenue chart: {e}")

def plot_orders(df, save_path="visualization/orders_trend.png"):
    try:
        plt.figure()
        plt.plot(df['order_date'], df['orders'], label='Orders', color='orange')
        plt.title("Daily Orders")
        plt.xlabel("Date")
        plt.ylabel("Number of Orders")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        logging.info(f"Orders chart saved to {save_path}")
    except Exception as e:
        logging.error(f"Failed to generate orders chart: {e}")

def plot_avg_order_value(df, save_path="visualization/avg_order_value_trend.png"):
    try:
        plt.figure()
        plt.plot(df['order_date'], df['avg_order_value'], label='Avg Order Value', color='green')
        plt.title("Average Order Value")
        plt.xlabel("Date")
        plt.ylabel("Avg Order Value")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        logging.info(f"Average order value chart saved to {save_path}")
    except Exception as e:
        logging.error(f"Failed to generate avg order value chart: {e}")
