# ADR-0001: Runtime: Docker Engine dentro do WSL2

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

A máquina de desenvolvimento tem 7,9 GB de RAM e um i5-7300U (2 núcleos, 4 threads). O projeto precisa rodar 100% local e com custo zero. O WSL2 com Ubuntu já está instalado.

## Decisão

Usar o **Docker Engine instalado dentro do Ubuntu no WSL2**, sem Docker Desktop. A memória do WSL2 será limitada pelo arquivo `.wslconfig` do Windows. O código Python também roda dentro do WSL2, para que Makefile, scripts e containers usem o mesmo ambiente Linux.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| Docker Engine no WSL2 | Mais leve, sem interface gráfica consumindo RAM, igual ao Docker de servidores Linux | Tudo via terminal |
| Docker Desktop | Instalação simples, interface gráfica | Consome mais RAM; gratuito só para uso pessoal e empresas pequenas |

## Consequências

Menos memória gasta com ferramenta e mais sobrando para o pipeline. Em troca, tudo é operado pelo terminal, o que também é o dia a dia em produção.
