# News Extractor

A service that extracts the main content of a news article from a URL and
returns consistent JSON. Ships with an **Apache Airflow** pipeline that
automatically crawls Indonesian news sources, extracts articles, and ingests
them into a **SQLite** database.

## Project structure

```
├── app/
│   ├── main.py                  # Public async API
│   ├── clients/http_client.py   # httpx client with retry & backoff
│   ├── config/
│   │   ├── constants.py         # Source homepages, link patterns, parsers map
│   │   └── settings.py          # pydantic-settings (.env support)
│   ├── extractors/              # trafilatura (primary) + BS4 (fallback)
│   ├── models/                  # Article & Metadata pydantic models
│   ├── parsers/                 # Site-specific parsers (detik, kompas, …)
│   ├── services/
│   │   ├── extractor_service.py # Full extraction workflow
│   │   ├── metadata_service.py  # OpenGraph / meta / site parser extraction
│   │   └── discovery_service.py # Homepage URL discovery (single fetch)
│   ├── storage/
│   │   └── database.py          # SQLite manager (create, upsert, query)
│   └── utils/                   # URL, date, HTML, logging helpers
├── dags/
│   └── news_crawler_dag.py      # Airflow DAG: discover → extract → ingest
├── scripts/
│   └── extract.py               # CLI wrapper
├── Dockerfile                   # Custom Airflow image
├── docker-compose.yml           # Airflow + PostgreSQL + SQLite
├── requirements.txt             # pip deps (for Docker build)
└── pyproject.toml               # uv project metadata & dev deps
```

## Quick start (local CLI)

```bash
uv sync
uv run scripts/extract.py https://news.detik.com/berita/d-xxxx
uv run scripts/extract.py detik kompas tempo --limit 5
```

```python
import asyncio
from app.main import extract_article, extract_many

article = asyncio.run(extract_article("https://news.detik.com/berita/d-xxxx"))
print(article.model_dump_json(indent=2))

articles = asyncio.run(extract_many(["detik", "kompas"], limit_per_source=5))
```

## Airflow pipeline

The DAG `news_crawler_pipeline` runs every 2 hours and has three tasks:

```
discover_urls(cnn) ──┐
discover_urls(detik) ─┤
discover_urls(kompas) ─┼──► extract_articles ──► ingest_to_sqlite
discover_urls(liputan6)┘      (one batch,          (upsert into
                        async connection pool)   articles.db)
```

### Docker setup

```bash
# One-time prep
mkdir -p data && chmod 777 data

# Build the custom Airflow image
docker compose build

# Initialize Airflow (DB migration + admin user)
docker compose up airflow-init

# Start all services
docker compose up -d

# Open http://localhost:8080  (admin / admin)
# Unpause the "news_crawler_pipeline" DAG
```

### Configuration

| Env var | Default | Description |
|---|---|---|
| `CRAWLER_DB_PATH` | `/opt/airflow/data/articles.db` | SQLite DB path |
| `CRAWLER_LIMIT_PER_SOURCE` | `3` | Max articles per source per run |
| `AIRFLOW_UID` | `50000` | Container user UID (set in `.env` if needed) |
| `TEMPO_SESSION_COOKIE` | — | Required for full tempo.co content |

### Checking the data

```bash
# Direct query from the container
docker compose exec airflow-scheduler sqlite3 /opt/airflow/data/articles.db \
  "SELECT source, COUNT(*) FROM articles GROUP BY source;"

# The database is also available on the host at ./data/articles.db
# (bind mount, DELETE journal mode — works with DBeaver, VSCode SQLite, etc.)
sqlite3 -column -header data/articles.db \
  "SELECT id, title, source, status, scrapped_at FROM articles LIMIT 10;"
```

## Supported sources

| Source | Domain | Site-specific parser |
|---|---|---|
| CNN Indonesia | `cnnindonesia.com` | ✅ |
| Detik | `news.detik.com` | ✅ |
| Kompas | `www.kompas.com` | ✅ |
| Tempo | `www.tempo.co` | ✅ |
| Liputan6 | `www.liputan6.com` | ✅ |

> Other URLs fall back to the **generic parser** (JSON-LD / OpenGraph / meta tags)
> automatically.

## Article output

```json
{
  "url": "https://www.cnnindonesia.com/...",
  "title": "Sample Article Title",
  "author": "Author Name",
  "published_date": "2026-07-31T10:00:00+00:00",
  "language": "id",
  "source": "cnn",
  "category": "Nasional",
  "tags": ["politik", "pemerintahan"],
  "image": "https://.../image.jpg",
  "summary": "First paragraph or excerpt",
  "content": "Full article body text...",
  "text_length": 1234,
  "word_count": 200,
  "extraction_method": "trafilatura",
  "scrapped_at": "2026-07-31T12:00:00+00:00",
  "status": "success",
  "error": null
}
```

- `source` is always the canonical source key (`cnn`, `detik`, …) derived from the
  domain, never from page metadata.
- `status` is `"success"` or `"failed"`. Failed articles include an `error` message.

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```
