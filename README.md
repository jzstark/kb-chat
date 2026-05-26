# kb-chat

Standalone LibreChat deployment for KnowledgeBase-S.

This repo runs LibreChat, MongoDB, Meilisearch, nginx, and a small `kb-mcp`
bridge that exposes KnowledgeBase-S API calls to LibreChat through MCP. It also
runs `search-mcp`, a Brave Search MCP bridge for current web/news search.

## Services

- `librechat`: chat UI and provider integration.
- `mongodb`: LibreChat application state.
- `meilisearch`: LibreChat search backend.
- `kb-mcp`: MCP bridge to the remote KnowledgeBase-S API.
- `search-mcp`: MCP bridge to Brave Search API.
- `nginx`: HTTP entrypoint for `chat.laughtale.co.uk`.
- `watchtower`: optional image auto-updater.

## Configuration

Copy `.env.example` to `.env` and fill in real values.

Important variables:

- `KB_API_BASE`: public KnowledgeBase-S API origin, for example `https://swanny.laughtale.co.uk`.
- `KB_SERVICE_TOKEN`: service token sent by `kb-mcp` as both `Authorization: Bearer ...` and `X-KB-Service-Token`.
- `LIBRECHAT_DOMAIN_CLIENT` / `LIBRECHAT_DOMAIN_SERVER`: public LibreChat URL.
- `CLAUDE_API_KEY` / `OPENAI_API_KEY`: model provider keys.
- `BRAVE_SEARCH_API_KEY`: Brave Search API key used by `search-mcp`.
- `ALLOW_REGISTRATION`: set to `true` only while creating the first account, then set it back to `false`.

New chats default to the `Claude Sonnet 4.6` model spec, configured in
`config/librechat.yaml`.

`KB_SERVICE_TOKEN` must match the value configured in the KnowledgeBase-S `.env`.

The `web-search` MCP exposes Brave LLM Context, Web Search, News Search, and a
basic URL fetcher. Use Brave LLM Context for grounded current-information
answers; use News Search when the user specifically asks for recent news.

## Local Run

```bash
make dev
```

Detached:

```bash
make dev-d
```

## First Account

Temporarily enable registration:

```env
ALLOW_REGISTRATION=true
```

Apply the change:

```bash
make deploy
```

Create your account in the web UI, then disable registration again:

```env
ALLOW_REGISTRATION=false
```

Apply the change again:

```bash
make deploy
```

## VPS Deploy

On every push to `main`, GitHub Actions builds:

- `ghcr.io/<owner>/kb-chat-kb-mcp:latest`
- `ghcr.io/<owner>/kb-chat-search-mcp:latest`

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
