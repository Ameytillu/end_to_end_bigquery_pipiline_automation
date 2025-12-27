from google.cloud import bigquery
client = bigquery.Client()
query = "SELECT * FROM `bigquery-public-data.thelook_ecommerce.orders` LIMIT 5"
df = client.query(query).to_dataframe()
print(df.columns)
print(df.head())