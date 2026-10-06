import os
import sys
from datetime import UTC, datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# Adiciona o diretório raiz ao path para importar as transformações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from transformations.gold import main as run_gold_transformation
from transformations.silver import main as run_silver_transformation

default_args = {
    "owner": "marketpulse",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="marketpulse_transformation_pipeline",
    default_args=default_args,
    description="Pipeline Airflow para as camadas Silver e Gold do MarketPulse",
    schedule="@hourly",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    max_active_runs=1,
) as dag:

    silver_task = PythonOperator(
        task_id="run_silver_layer",
        python_callable=run_silver_transformation,
    )

    gold_task = PythonOperator(
        task_id="run_gold_layer",
        python_callable=run_gold_transformation,
    )

    silver_task >> gold_task
