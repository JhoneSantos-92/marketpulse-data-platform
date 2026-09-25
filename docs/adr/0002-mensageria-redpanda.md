# ADR-0002: Mensageria: Redpanda

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

Os eventos da Binance chegam em tempo real e precisam de um buffer durável entre a ingestão e o processamento, com particionamento por symbol, consumer groups e fila de erros (DLQ).

## Decisão

Usar o **Redpanda** em modo de desenvolvimento (`--mode dev-container`, `--smp 1`, conforme a documentação oficial do Redpanda). Toda a integração usa a API do Kafka, então o código do producer e do consumer é o mesmo que rodaria num cluster Kafka.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Redpanda | API do Kafka, binário único, sem JVM | Nome menos citado em vagas do que Kafka |
| Apache Kafka (KRaft) | O mais citado em vagas de bancos | JVM, mais pesado para 8 GB de RAM |
| Fila no Postgres | Muito leve | Não demonstra streaming, que é o foco do projeto |

## Consequências

O conhecimento é o de Kafka (tópicos, partições, offsets, consumer groups) sem o custo da JVM. Se um dia for preciso trocar para Kafka, o código cliente não muda.
