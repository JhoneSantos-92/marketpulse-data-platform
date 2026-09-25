# ADR-0008: Observabilidade e custo: Prometheus + Grafana + tabela de execuções

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

É preciso enxergar lag do consumer, throughput, latência e falhas, e medir o custo de processamento de cada execução.

## Decisão

Usar **Prometheus** para coletar métricas e **Grafana** para os painéis. Cada execução de job grava em uma tabela de execuções: duração, bytes lidos e escritos, linhas processadas e custo estimado. O custo estimado usa um preço de referência de nuvem que será definido na Fase 7, com a fonte citada nesta ADR.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Prometheus + Grafana | Padrão de mercado, métricas em tempo real | Dois serviços a mais |
| Logs estruturados + tabela de execuções | Mais leve | Sem métricas em tempo real |

## Consequências

O projeto mostra observabilidade de verdade e consciência de custo, dois pontos valorizados por bancos e fintechs.
