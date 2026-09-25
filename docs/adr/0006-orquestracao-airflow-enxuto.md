# ADR-0006: Orquestração: Airflow enxuto (LocalExecutor)

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

O docker-compose oficial do Airflow sobe 8 serviços (incluindo Redis e worker Celery) e a documentação pede pelo menos 4 GB de memória para o Docker, idealmente 8 GB.

## Decisão

Usar **Apache Airflow com LocalExecutor**, sem Redis e sem worker Celery, com o Postgres como banco de metadados. O consumo real será medido com `docker stats` durante a Fase 6.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Airflow completo (compose oficial) | Padrão de mercado, configuração pronta | Inviável na memória disponível |
| Airflow enxuto | Mantém o Airflow na stack com bem menos serviços | Configuração própria, não o compose oficial |
| Prefect ou Dagster | Mais leves e modernos | Menos presentes em vagas de bancos |

## Consequências

O Airflow continua no projeto, mas com uma configuração que cabe na máquina. A escolha do executor passa a ser um tema de entrevista que o projeto demonstra na prática.
