# StudsUp.com — LEGO Community Platform

> Version 6.0 · Full-stack prototype

LEGO community platform with marketplace, parts catalogue (12,658 parts), LUG club governance, live streams, blog, collection tracker, LUGBULK order history, and full-text search.

## Project structure

```
studsup_platform/
├── index.html                  ← Landing page / project index
├── render.yaml                 ← Render.com deploy config
├── frontend/
│   ├── css/shared.css          ← Global design system
│   ├── js/shared.js            ← Shared utilities
│   └── pages/                  ← All HTML pages
│       ├── home.html           Marketplace homepage
│       ├── search.html         Global search (8 categories)
│       ├── lugbulk.html        Parts catalogue — 12,658 parts
│       ├── part-detail.html    Part page + price chart
│       ├── collection.html     My Collection + LUGBULK history
│       ├── lug.html            LUG governance + voting
│       ├── stream.html         Live streams + chat
│       ├── profile-blog.html   User profile + blog editor
│       ├── instructions.html   Instructions + build checker
│       ├── login.html          Sign in / Register
│       ├── profile-setup.html  Onboarding wizard
│       └── changelog.html      Version history
└── backend/
    ├── main.py                 FastAPI — 15 REST endpoints
    ├── requirements.txt
    └── db/
        ├── studsup.db          SQLite — 4.3 MB, 12,658 parts
        └── init_db.py          Re-seed DB from LUGBULK xlsx
```

## Run locally

```bash
# Frontend only (no install needed)
# Just open index.html in your browser

# Backend (for live search)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Demo login: `georgs@studsup.com` / `demo1234`

## Deploy to Render.com

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render reads `render.yaml` and deploys both services automatically

Or manually:
- **Backend**: New → Web Service → root dir `backend` → start command `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Frontend**: New → Static Site → root dir `frontend` → publish dir `.`

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/health` | Status + DB stats |
| `GET /api/search?q=castle` | Search all 8 categories |
| `GET /api/parts?per_page=48` | Parts list, paginated |
| `GET /api/parts/colors` | Color filter options |
| `GET /api/parts/{element_id}` | Single part |
| `GET /api/stores` | Stores |
| `GET /api/discounts` | Active discounts |
| `GET /api/sets` | LEGO sets |
| `GET /api/users` | Users |
| `GET /api/lugs` | LUG clubs |
| `GET /api/lugs/{slug}` | Single LUG with members |
| `GET /api/streams` | Streams + VODs |
| `GET /api/posts` | Blog posts |

## Tech stack

- **Frontend**: Pure HTML, CSS, JavaScript — no framework, no build step
- **Backend**: Python, FastAPI, SQLite, FTS5 full-text search
- **Charts**: Chart.js (CDN)
- **Deploy**: Render.com (free tier)
