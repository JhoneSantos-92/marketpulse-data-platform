COMPOSE = docker compose -f infra/docker-compose.yml --env-file .env

.PHONY: up down ps logs stats test lint

up:      ## Sobe todos os serviços
	$(COMPOSE) up -d

down:    ## Derruba todos os serviços
	$(COMPOSE) down

ps:      ## Lista os serviços e o status
	$(COMPOSE) ps

logs:    ## Acompanha os logs
	$(COMPOSE) logs -f --tail=100

stats:   ## Mostra consumo de CPU e RAM por container
	docker stats --no-stream

test:    ## Roda os testes
	pytest

lint:    ## Verifica estilo e erros comuns
	ruff check .
