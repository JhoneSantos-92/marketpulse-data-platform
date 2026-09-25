# ADR-0003: Object storage: SeaweedFS

- **Status:** Aceito
- **Data:** 2026-09-25

## Contexto

O plano original usava MinIO, mas a edição comunitária parou de publicar imagens Docker em outubro de 2025 e o repositório foi arquivado em fevereiro de 2026. O Delta Lake (via delta-rs 1.x) usa escritas condicionais do S3 para garantir commits seguros.

## Decisão

Usar o **SeaweedFS** com o gateway S3. O endereço do storage fica na variável `STORAGE_URI`, então o código não depende do SeaweedFS. Se houver incompatibilidade, a alternativa é o disco local, trocando só essa variável. A compatibilidade com o delta-rs será validada na Fase 3 com um teste de escrita.

## Opções consideradas

| Opção | Prós | Contras |
|---|---|---|
| SeaweedFS | API S3, projeto ativo, suporte a escritas condicionais | Mais peças de configuração que o disco local |
| Garage | API S3, feito para hardware modesto | Documentação de compatibilidade não menciona escritas condicionais |
| Disco local | Zero RAM extra, o mais simples | Não exercita a API S3 |

## Consequências

O pipeline usa a mesma API de object storage de uma nuvem de verdade. O custo é mais um serviço rodando, que será medido com `docker stats`.
