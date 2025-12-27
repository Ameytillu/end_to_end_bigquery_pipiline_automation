# End-to-End BigQuery Pipeline Automation

## Overview
This project demonstrates a production-style, end-to-end data pipeline built using BigQuery public datasets and Python.  
The pipeline automates data ingestion, transformation, analytics, and visualization, and is orchestrated using Prefect.

The goal of this project is to showcase real-world data engineering and analytics practices, including secure cloud authentication, workflow automation, and dashboarding.

---

## Architecture
1. Fetch raw data from BigQuery public datasets
2. Clean and transform the data using Python
3. Generate business KPIs
4. Automatically create visualizations
5. Orchestrate the workflow using Prefect
6. Serve results through a Streamlit dashboard

---

## Data Source
BigQuery Public Dataset:
- Dataset: bigquery-public-data.thelook_ecommerce
- Table: orders

This dataset is used as a proxy for real-world transactional data.

---

## Technology Stack
- Python
- Google BigQuery
- Prefect (workflow orchestration)
- Pandas
- SQL
- Streamlit
- Matplotlib
- PostgreSQL (optional, for persistence)

---

