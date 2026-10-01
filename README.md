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

The model picker includes `Claude Sonnet 5`, `Claude Sonnet 4.6`, and
`Claude Opus 4.7`. New chats continue to default to the `Claude Sonnet 4.6`
model spec, configured in `config/librechat.yaml`.

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

## Upgrade LibreChat from v0.8.7 to v0.8.8

This repository uses `ghcr.io/librechat-ai/librechat:latest`, which pointed to
v0.8.8 on 2026-10-01. The image moved from the `danny-avila` package namespace.
Once these repository changes are available on the VPS, run the commands below
from its repo directory.
The server's existing `.env` values, especially `LIBRECHAT_CREDS_KEY`,
`LIBRECHAT_CREDS_IV`, and the JWT secrets, must stay the same.

First download the new image while the current site is still running:

```bash
git pull --ff-only
docker compose pull librechat
```

Stop LibreChat writers and back up the database and mounted files. MongoDB
stays running for the backup and migration. Keep this backup outside the repo.

```bash
docker compose stop librechat
umask 077
backup_dir="../kb-chat-backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"
docker compose exec -T mongodb mongodump --db LibreChat --archive > "$backup_dir/mongo.archive"
tar -czf "$backup_dir/files.tgz" .env config data/librechat/images
```

Confirm both backup commands succeeded and the archive files are nonempty
before continuing. Stop if any command fails.

LibreChat v0.8.8 needs an explicit MongoDB tenant-index migration for
databases created by v0.8.7 or earlier, including single-tenant installs.
Check the dry-run output, then apply it while LibreChat remains stopped:

```bash
docker compose run --rm --no-deps -w /app librechat npm run migrate:tenant-indexes:dry-run
docker compose run --rm --no-deps -w /app librechat npm run migrate:tenant-indexes
docker compose up -d --no-deps librechat
docker compose ps
docker compose logs --tail=100 librechat
```

Check that the site loads, sign in, open an old conversation, send a new
message, and try the KnowledgeBase and web-search MCP tools. If startup reports
an index error, leave LibreChat stopped and follow the
[tenant-index migration guide](https://www.librechat.ai/docs/configuration/mongodb/tenant_index_migration)
before retrying. Do not drop MongoDB indexes or volumes to clear the error.

For later releases, `make deploy` pulls the current `latest` image without a
version edit. Check LibreChat's release and configuration notes first: a future
release may require another migration or a `config/librechat.yaml` update.
The LibreChat service is excluded from Watchtower updates, so `latest` does
not change the running site until you deploy it.

For rollback, stop LibreChat, restore the saved MongoDB archive and files,
then run the previous `ghcr.io/danny-avila/librechat:v0.8.7` image and the
previous `config/librechat.yaml`. Keep the backup until the upgraded site has
been checked.

## Data

Persistent runtime data is stored under:

- `data/mongo`
- `data/meili`
- `data/librechat/images`
- `data/librechat/logs`

If migrating from the old KnowledgeBase-S VPS, copy the corresponding old
directories before switching DNS.
