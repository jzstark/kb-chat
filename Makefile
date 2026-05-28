.PHONY: dev dev-d deploy down build logs ps config

COMPOSE=docker compose

dev:
	$(COMPOSE) up --remove-orphans

dev-d:
	$(COMPOSE) up -d --remove-orphans

deploy:
	./deploy.sh

down:
	$(COMPOSE) down --remove-orphans

build:
	$(COMPOSE) build kb-mcp search-mcp

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

config:
	$(COMPOSE) config
