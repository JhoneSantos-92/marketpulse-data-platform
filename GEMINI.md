# Project Instructions & Workflow Conventions

## Git Development Lifecycle & Git Flow
O projeto segue estritamente o padrão de mercado para controle de versão e entrega contínua:
1. **Ambiente Local:** Todos os ajustes e implementações são realizados e testados localmente (`pytest`, `ruff check`, `ruff format`).
2. **Branch de Desenvolvimento (`dev` / `develop`):** Após validação local, os commits são enviados para a branch de desenvolvimento (`dev` ou `develop`).
3. **Quality Gate & CI/CD:** A pipeline de CI/CD no GitHub Actions deve executar todos os testes unitários, de integração, análises de segurança (Bandit) e linters (Ruff) obrigatoriamente.
4. **Pull Request & Code Review:** Nenhuma alteração é mergeada diretamente na branch `main`. Deve-se abrir uma Pull Request (PR) de `dev`/`develop` para `main`.
5. **Critério de Merge:** O merge para a branch **`main`** só é permitido após:
   - Todos os testes passarem sem erros.
   - O bot de CI/CD do GitHub certificar que o status está 100% verde (`✓`).
   - Revisão de código limpa.
