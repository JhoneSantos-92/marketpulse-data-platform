# ADR-0010: BI: Power BI Desktop

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

A camada gold precisa virar um dashboard com insights (OHLCV, volatilidade, volume por par, spread). O público-alvo do portfólio inclui vagas de BI em bancos e fintechs.

## Decisão

Usar o **Power BI Desktop**, rodando no Windows fora do Docker. O portfólio mostra prints do dashboard e o arquivo `.pbix`. A forma de conexão com a gold será definida na Fase 8.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Power BI Desktop | Ferramenta usada em bancos, não consome RAM do Docker | Publicar na web exige licença |
| Metabase | Roda no Docker, visual pronto | JVM; sem número oficial confirmado de consumo de memória |

## Consequências

Alinha o projeto às vagas de Analista de BI e Analista de Dados. Em troca, o dashboard não fica publicado on-line.
