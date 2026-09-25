# ADR-0007: Qualidade de dados: checagens em Polars + pytest, testes dbt na gold

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

O pipeline precisa falhar rápido quando o dado vier errado (schema quebrado, preço negativo, duplicado, atraso) e avisar.

## Decisão

Usar **checagens escritas em Polars** entre as camadas e **pytest** para as regras. Se o dbt-duckdb for adotado na gold (ADR-0005), usar **testes do dbt** nessa camada.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Great Expectations | Conhecido, gera relatórios | Pesado e verboso para o tamanho do projeto |
| Testes do dbt | Simples, em SQL | Só cobre o que passa pelo dbt |
| Checagens em Polars + pytest | Leve, junto do código | Menos vitrine que o GX |

## Consequências

Qualidade de dados fica próxima do código que transforma o dado, sem ferramenta extra pesada.
