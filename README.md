# kb-chat

Standalone LibreChat deployment for KnowledgeBase-S.

This repo runs LibreChat, MongoDB, Meilisearch, nginx, and a small `kb-mcp`
bridge that exposes KnowledgeBase-S API calls to LibreChat through MCP.

## Services

- `librechat`: chat UI and provider integration.
- `mongodb`: LibreChat application state.
- `meilisearch`: LibreChat search backend.
- `kb-mcp`: MCP bridge to the remote KnowledgeBase-S API.
- `nginx`: HTTP entrypoint for `chat.laughtale.co.uk`.
- `watchtower`: optional image auto-updater.

## Configuration

Copy `.env.example` to `.env` and fill in real values.

Important variables:

- `KB_API_BASE`: public KnowledgeBase-S API origin, for example `https://swanny.laughtale.co.uk`.
- `KB_SERVICE_TOKEN`: service token sent by `kb-mcp` as both `Authorization: Bearer ...` and `X-KB-Service-Token`.
- `LIBRECHAT_DOMAIN_CLIENT` / `LIBRECHAT_DOMAIN_SERVER`: public LibreChat URL.
- `CLAUDE_API_KEY` / `OPENAI_API_KEY`: model provider keys.

`KB_SERVICE_TOKEN` is prepared in this repo, but KnowledgeBase-S must also be
updated to validate it before this becomes an enforced authentication boundary.

## Local Run

```bash
make dev
```

Detached:

```bash
make dev-d
```

## VPS Deploy

On every push to `main`, GitHub Actions builds:

- `ghcr.io/<owner>/kb-chat-kb-mcp:latest`

```bash
make deploy
```

This runs:

```bash
docker compose pull
docker compose up -d --remove-orphans
```

## Data

Persistent runtime data is stored under:

- `data/mongo`
- `data/meili`
- `data/librechat/images`
- `data/librechat/logs`

If migrating from the old KnowledgeBase-S VPS, copy the corresponding old
directories before switching DNS.
