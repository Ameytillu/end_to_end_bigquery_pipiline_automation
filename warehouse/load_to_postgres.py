from sqlalchemy import create_engine

def load_to_postgres(df, table_name="orders_clean"):
    engine = create_engine("postgresql://user:password@localhost:5432/pipeline")
    df.to_sql(table_name, engine, if_exists="replace", index=False)
