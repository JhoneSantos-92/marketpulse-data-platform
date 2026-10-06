# ADR-0013: Ambiente Python: uv com Python 3.13

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

A stack prevê Python 3.13, mas o Ubuntu 24.04 do ambiente de desenvolvimento vem com Python 3.12. O projeto precisa de ambiente isolado e de dependências com versões travadas, para que qualquer pessoa que clonar o repositório reproduza o mesmo ambiente.

## Decisão

Usar o **uv** para instalar o Python 3.13 (sem alterar o Python do sistema), criar o `.venv` e gerenciar as dependências. As dependências ficam declaradas no `pyproject.toml` e travadas no `uv.lock`, ambos versionados. A versão do Python fica fixada no `.python-version`. Dependências só de desenvolvimento (pytest, ruff) ficam no grupo `dev`.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| uv | Instala a versão de Python pedida, lockfile nativo, uma ferramenta só, muito rápido | Ferramenta mais nova que pip e venv |
| Python 3.12 do sistema + venv + pip-tools | Ferramentas clássicas | Fora da versão planejada; duas ferramentas para o que o uv faz sozinho |

## Consequências

O ambiente é reproduzível com um único comando (`uv sync`). Comandos do projeto passam a ser executados com `uv run`, garantindo que rodam dentro do `.venv` certo.
