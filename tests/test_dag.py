from airflow.models import DagBag


def test_dag_loading():
    dagbag = DagBag(dag_folder="orchestration/dags", safe_mode=True)
    assert len(dagbag.import_errors) == 0, f"Erros ao carregar DAGs: {dagbag.import_errors}"
    assert "marketpulse_transformation_pipeline" in dagbag.dags
    dag = dagbag.dags["marketpulse_transformation_pipeline"]
    assert dag is not None
    assert len(dag.tasks) == 2
