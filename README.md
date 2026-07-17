# CFP & Conference Schedule Agent

An agent that automatically discovers and curates **Calls for Papers (CFPs)**
and **conference schedules** relevant to:

- Speech processing & speech applications (ASR, TTS, speaker recognition, prosody, dysarthria, etc.)
- Natural Language Processing (LLMs, dialogue systems, computational linguistics, etc.)
- Healthcare / clinical & biomedical NLP, health informatics, digital health

It polls [WikiCFP](http://www.wikicfp.com) category RSS feeds on a schedule,
filters entries against a configurable keyword list, stores relevant results
in a database, and serves them through a REST API, a browsable dashboard, and
a downloadable `.ics` calendar feed you can subscribe to from Google
Calendar / Outlook.

## Features

- **Automatic refresh** — a background job (APScheduler) re-pulls all
  configured WikiCFP categories every `REFRESH_INTERVAL_HOURS` (default 24h).
- **Keyword filtering** — only entries matching your research-area keywords
  (see `app/config.py`) are kept; extend via `EXTRA_KEYWORDS` env var.
- **REST API** — `/api/cfps`, `/api/categories`, `/api/refresh`,
  `/api/calendar.ics`.
- **Dashboard** — simple filterable HTML table at `/`.
- **Calendar export** — `/api/calendar.ics` for calendar-app subscriptions.
- **Render-ready** — `render.yaml` + `Procfile` included.

## Project layout

```
cfp-agent/
├── app/
│   ├── main.py            FastAPI app & routes
│   ├── config.py          Keywords, categories, env settings
│   ├── db.py               SQLAlchemy models & session
│   ├── models.py           Pydantic response schemas
│   ├── scheduler.py         APScheduler wiring
│   ├── services/
│   │   ├── fetcher.py       WikiCFP RSS fetch + parse + upsert
│   │   ├── filters.py        Keyword matching
│   │   └── ics_export.py      .ics calendar builder
│   ├── templates/index.html
│   └── static/style.css
├── requirements.txt
├── render.yaml
├── Procfile
└── .env.example
```

## Run locally

```bash
cd cfp-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` for the dashboard, or
`http://localhost:8000/docs` for interactive API docs (Swagger UI).

On startup the app triggers an initial fetch in the background — give it a
few seconds and refresh the dashboard.

To force a refresh at any time:

```bash
curl -X POST http://localhost:8000/api/refresh
```

## Deploy to Render

### Option A — one-click via `render.yaml` (Blueprint)

1. Push this folder to a GitHub repo.
2. In Render: **New → Blueprint**, point it at your repo. Render will read
   `render.yaml` and provision the web service automatically (free tier,
   no persistent disk).
3. Deploy. Your dashboard will be live at the assigned `*.onrender.com` URL.

### Option B — manual Web Service

1. **New → Web Service**, connect your repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set env var `DATABASE_URL=sqlite:///./data/cfp_agent.db` (or leave the
   default in `.env.example`), and `REFRESH_INTERVAL_HOURS` as desired.

> **About storage on the free tier:** Render's free web services don't
> support persistent disks, so the SQLite file lives on the service's local,
> ephemeral filesystem — it resets whenever the service redeploys or spins
> down from inactivity. This is fine for this agent since it re-fetches all
> CFPs from WikiCFP automatically on every startup, so the data rebuilds
> itself within seconds. If you want the database to persist across
> restarts (e.g. to keep a long history or manual edits), either:
> - upgrade to a paid instance type and add a **Disk** (mount path of your
>   choice, then point `DATABASE_URL` at a file under it), or
> - switch to a managed database instead of SQLite — Render offers a free
>   Postgres tier; just change `DATABASE_URL` to a `postgresql://...` URL
>   and add `psycopg2-binary` to `requirements.txt`.

> **Note on the scheduler:** free web services also spin down after
> inactivity, which pauses the background refresh job along with everything
> else. If you need guaranteed periodic refreshes even with no traffic,
> either upgrade to a paid instance type, or call `POST /api/refresh` from
> an external cron service (e.g. Render Cron Jobs, GitHub Actions on a
> schedule, or cron-job.org) hitting your deployed URL.

## Customizing your research areas

All filtering logic lives in `app/config.py`:

- `BASE_KEYWORDS` — the master keyword list driving relevance filtering.
- `EXTRA_KEYWORDS` — add more via the `EXTRA_KEYWORDS` env var
  (comma-separated), without touching code.
- `WIKICFP_CATEGORIES` — which WikiCFP RSS category feeds get polled.

## Extending

Good next additions if you want to grow this into a fuller agent:

- Add more sources (e.g. ACL Anthology, arXiv new-submission feeds, ACM/IEEE
  conference listings) as additional functions in `app/services/fetcher.py`
  that produce the same normalized dict shape consumed by `refresh_all`.
- Add email/Slack notifications for new high-relevance CFPs (hook into
  `refresh_all`'s `inserted` count).
- Swap SQLite for Postgres (Render offers managed Postgres) if you outgrow
  a single disk-backed file — just change `DATABASE_URL`.
- Add an LLM summarization step (e.g. call the Anthropic API) to generate
  short natural-language summaries of each CFP's scope/topics for the
  dashboard.
