# Job Search Crawler

Full-stack job search platform: Python crawler scrapes career pages from 47+ companies, FastAPI backend serves data from Supabase, React frontend displays jobs with AI-powered resume and cover letter generation via NVIDIA Cloud LLM.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup](#setup)
  - [Prerequisites](#prerequisites)
  - [1. Clone and Install](#1-clone-and-install)
  - [2. Supabase Setup](#2-supabase-setup)
  - [3. NVIDIA Cloud API Setup](#3-nvidia-cloud-api-setup)
  - [4. Email Notifications (Optional)](#4-email-notifications-optional)
  - [5. Environment Variables](#5-environment-variables)
- [Running Locally](#running-locally)
  - [Crawler Only](#crawler-only)
  - [Full Stack (Backend + Frontend)](#full-stack-backend--frontend)
- [Running with Docker](#running-with-docker)
- [n8n Workflow Automation](#n8n-workflow-automation)
- [API Reference](#api-reference)
- [Configuration](#configuration)
  - [Target Job Roles](#target-job-roles)
  - [Location Filtering](#location-filtering)
  - [Scheduler](#scheduler)
  - [Health Reports](#health-reports)
- [Adding a New Company](#adding-a-new-company)
- [Supported Platforms & Companies](#supported-platforms--companies)

---

## Features

- **Automated Crawling** -- Scrapes career pages from 47+ companies across 25 parser types (Workday, Greenhouse, Phenom, Radancy, and more)
- **Deduplication** -- Same job is never added twice (matched by title + job ID)
- **Dual Storage** -- Writes to both Excel (`jobs.xlsx`) and Supabase, with graceful fallback if Supabase is not configured
- **React Dashboard** -- Browse, search, filter, and sort jobs with a modern UI
- **AI Resume/Cover Letter Generation** -- Generates tailored resumes and cover letters using NVIDIA Cloud LLM (meta/llama-3.1-70b-instruct)
- **Bulk Generation** -- Select multiple jobs and generate documents in batch
- **PDF Download & Preview** -- View generated documents inline or download as PDF
- **Job Description Scraping** -- Automatically scrapes full job descriptions; supports manual paste as fallback
- **Email Notifications** -- Sends alerts for new jobs and periodic health reports
- **Docker Compose** -- One-command deployment of all services
- **n8n Integration** -- Workflow automation for scheduled bulk generation

---

## Architecture

```
                    :3000                    :8000
React (Vite) ──────────────> FastAPI Backend ──────────> Supabase (Postgres + Storage)
                                  │
                                  ├──────────> NVIDIA Cloud API (LLM)
                                  │
                                  └──────────> crawler/ (job description scraping)

Crawler (Python) ──> Excel (jobs.xlsx) + Supabase (dual-write)

n8n (:5678) ──> FastAPI (bulk generation webhooks)

Docker Compose orchestrates: backend, frontend, crawler, n8n
```

---

## Project Structure

```
Job_Search_Crawler/
├── config/
│   ├── config.yaml              # Sites, email, scheduler, storage settings
│   └── config_intern.yaml       # Alternate config for intern positions
│
├── crawler/
│   ├── main.py                  # Entry point, parser registry, scheduler, parallel execution
│   ├── __main__.py              # python -m crawler entry point
│   ├── __init__.py
│   ├── parser_base.py           # JobPosting + CrawlSiteResult dataclasses, ParserBase ABC
│   ├── storage.py               # ExcelStorage, SupabaseStorage, DualStorage
│   ├── notifier.py              # Email notifications + health reports
│   ├── fetcher.py               # Static HTTP fetch (HTML + JSON)
│   ├── browser.py               # Playwright browser rendering for JS-heavy sites
│   ├── filter.py                # Keyword post-filter
│   ├── requirements.txt         # Crawler Python dependencies
│   ├── Dockerfile               # Crawler container
│   └── parsers/                 # One parser per platform/company (25 parsers)
│
├── backend/
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── config.py                # Pydantic Settings (Supabase, NVIDIA)
│   ├── database.py              # Supabase client init
│   ├── models.py                # Pydantic response models
│   ├── requirements.txt         # Backend Python dependencies
│   ├── Dockerfile               # Backend container
│   ├── .env.example             # Template for credentials
│   ├── routers/
│   │   ├── jobs.py              # GET /api/jobs, /api/stats
│   │   └── generate.py          # Document generation + bulk + master resume
│   ├── services/
│   │   ├── llm_client.py        # NVIDIA Cloud LLM (OpenAI-compatible)
│   │   ├── job_scraper.py       # Scrape job descriptions
│   │   ├── document_generator.py # Orchestrator: scrape -> LLM -> PDF -> upload
│   │   └── supabase_storage.py  # Supabase Storage upload/download
│   └── prompts/
│       ├── resume.txt           # System prompt for resume generation
│       └── cover_letter.txt     # System prompt for cover letter generation
│
├── frontend/
│   ├── package.json             # React 19, Vite 8, Tailwind CSS v4
│   ├── vite.config.ts           # Dev proxy /api -> localhost:8000
│   ├── Dockerfile               # Node build -> nginx serve
│   ├── nginx.conf               # Production reverse proxy
│   └── src/
│       ├── App.tsx              # Main layout with modals and toast system
│       ├── api.ts               # Centralized API client
│       ├── types.ts             # TypeScript interfaces
│       ├── components/          # JobTable, JobRow, SearchBar, Pagination, StatsBar,
│       │                        # Modal, Toast, Spinner, BulkActionBar,
│       │                        # PreviewModal, DescriptionModal, MasterResumeModal
│       └── hooks/useJobs.ts     # Data-fetching hook with search/filter/sort/pagination
│
├── scripts/
│   ├── schema.sql               # Supabase table definitions
│   ├── migrate_excel_to_supabase.py  # One-time migration from Excel
│   └── capture_locations.py     # Location format analysis utility
│
├── n8n/workflows/               # n8n workflow JSON templates
│   ├── bulk_generate.json       # Webhook-triggered bulk generation
│   └── daily_auto_generate.json # Daily cron: new jobs -> auto-generate docs
│
├── docker-compose.yml           # Orchestrates backend, frontend, crawler, n8n
├── Career Links.xlsx            # Master list of career URLs with status
├── jobs.xlsx                    # Output: deduplicated job postings (auto-created)
└── README.md
```

---

## Setup

### Prerequisites

- **Python 3.12+**
- **Node.js 22+** and npm (for the frontend)
- **Docker** and **Docker Compose** (optional, for containerized deployment)
- A **Supabase** account (free tier works)
- An **NVIDIA Cloud** API key (free tier at [build.nvidia.com](https://build.nvidia.com))

### 1. Clone and Install

```bash
git clone https://github.com/SatyaChamana/Job_Search_Crawler.git
cd Job_Search_Crawler
```

**Crawler dependencies:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r crawler/requirements.txt
playwright install chromium
```

**Backend dependencies:**

```bash
pip install -r backend/requirements.txt
playwright install chromium   # if not already installed above
```

**Frontend dependencies:**

```bash
cd frontend
npm install
cd ..
```

### 2. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the contents of `scripts/schema.sql` to create the tables:
   - `jobs` -- stores crawled job listings
   - `generated_documents` -- tracks generated resumes/cover letters
   - `master_resume` -- stores your master resume for AI tailoring
3. Go to **Storage** and create a bucket named `generated-docs` (set to private)
4. Copy your project URL and anon key from **Settings > API**

**Migrate existing jobs (if you have a `jobs.xlsx`):**

```bash
source .venv/bin/activate
python scripts/migrate_excel_to_supabase.py
```

### 3. NVIDIA Cloud API Setup

The AI document generation uses NVIDIA Cloud's free-tier LLM API (OpenAI-compatible):

1. Sign up at [build.nvidia.com](https://build.nvidia.com)
2. Go to any model page (e.g., meta/llama-3.1-70b-instruct) and click **Get API Key**
3. Copy your API key

### 4. Email Notifications (Optional)

Edit `config/config.yaml` to configure Gmail SMTP:

```yaml
email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender_email: your_email@gmail.com
  sender_password: your_app_password
  recipient_email: recipient@example.com
```

To generate a Gmail App Password:
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and your device
3. Copy the 16-character password

If email is not configured, notifications are logged to the console instead.

### 5. Environment Variables

Create `backend/.env` from the template:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
NVIDIA_API_KEY=your-nvidia-api-key-here
```

Also update the Supabase section in `config/config.yaml` (used by the crawler for dual-write):

```yaml
supabase:
  url: "https://your-project.supabase.co"
  key: "your-anon-key-here"
```

---

## Running Locally

### Crawler Only

The crawler works standalone -- no Supabase or backend required. Jobs are saved to `jobs.xlsx`.

```bash
source .venv/bin/activate

# Single run
python -m crawler --once

# Continuous (scheduled every 18-23 minutes)
python -m crawler

# Custom config
python -m crawler --config config/config_intern.yaml

# Background
nohup python -m crawler > crawler.log 2>&1 &
```

### Full Stack (Backend + Frontend)

Start the backend and frontend in separate terminals:

**Terminal 1 -- Backend:**

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 -- Frontend:**

```bash
cd frontend
npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies `/api` requests to the backend at `localhost:8000`.

**Using the dashboard:**

1. Open `http://localhost:5173`
2. Browse, search, and filter jobs
3. Click **Apply** to open the job posting in a new tab
4. Click **Resume** or **Cover Letter** to generate AI-tailored documents
5. Use the **Master Resume** button (top right) to upload your resume -- the LLM uses it to tailor generated documents
6. Select multiple jobs with checkboxes and use **Generate All Selected** for bulk generation

---

## Running with Docker

Docker Compose runs the backend, frontend, and n8n together:

```bash
# Start backend + frontend + n8n
docker compose up -d

# Run the crawler (one-shot, separate profile)
docker compose --profile crawl run --rm crawler
```

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | `http://localhost:3000` | React dashboard |
| Backend | `http://localhost:8000` | FastAPI API |
| n8n | `http://localhost:5678` | Workflow automation |
| Health check | `http://localhost:8000/health` | Backend health endpoint |

**n8n default credentials:** `admin` / `changeme` (change in `docker-compose.yml`)

To rebuild after code changes:

```bash
docker compose up -d --build
```

---

## n8n Workflow Automation

Two workflow templates are included in `n8n/workflows/`:

1. **Bulk Generate** (`bulk_generate.json`) -- Webhook-triggered. Send a POST to n8n with a list of job IDs, and it calls the backend's bulk-generate endpoint.

2. **Daily Auto-Generate** (`daily_auto_generate.json`) -- Runs daily at 8am. Fetches jobs added in the last 24 hours, then triggers bulk generation for all of them.

**To import:** Open n8n at `http://localhost:5678`, go to **Workflows > Import from File**, and select the JSON file.

---

## API Reference

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs?page=1&per_page=50&company=&search=&sort_by=added_on&sort_dir=desc` | List jobs (paginated, filterable, sortable) |
| `GET` | `/api/jobs/{id}` | Get a single job |
| `GET` | `/api/stats` | Dashboard stats (total jobs, companies, added today) |

### Document Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/generate/resume/{job_id}` | Generate a tailored resume |
| `POST` | `/api/generate/cover-letter/{job_id}` | Generate a tailored cover letter |
| `GET` | `/api/generate/status/{job_id}` | Check generation status for a job |
| `POST` | `/api/bulk-generate` | Bulk generate documents for multiple jobs |

### Master Resume

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/master-resume` | Get current master resume |
| `PUT` | `/api/master-resume` | Update master resume |

### Job Descriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs/{id}/description` | Get cached job description |
| `PUT` | `/api/jobs/{id}/description` | Manually set a job description |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Backend health check |

---

## Configuration

All configuration lives in `config/config.yaml`.

### Target Job Roles

Each site has a `target_titles` list. The filter does **case-insensitive substring matching** -- if any target title appears anywhere in the job title, it's included.

```yaml
sites:
  - name: Adobe
    target_titles:
      - "Software Engineer"    # matches "Senior Software Engineer", "Staff Software Engineer"
      - "Data Engineer"        # matches "Senior Data Engineer"
      - "ML Engineer"          # matches "Staff ML Engineer"
```

| Target Title | What It Matches |
|---|---|
| `"Software Engineer"` | Software Engineer, Senior Software Engineer, Staff Software Engineer |
| `"Data Scientist"` | Data Scientist, Senior Data Scientist |
| `"SDE"` | SDE, SDE II, SDE III |
| `"Software"` | Broad match -- catches non-standard titles |

### Location Filtering

For sites returning global results, add `target_locations`:

```yaml
  - name: MongoDB
    parser: greenhouse_api
    greenhouse_board: "mongodb"
    target_locations:
      - "United States of America"
```

### Scheduler

```yaml
scheduler:
  interval_min_minutes: 18    # Min minutes between crawls
  interval_max_minutes: 23    # Max minutes between crawls
  start_hour: 7               # Only crawl after this hour
  stop_hour: 23               # Stop crawling after this hour
```

### Health Reports

The crawler sends an HTML health report email every N cycles:

```yaml
health_report_interval: 10
```

The report includes:
- Jobs added today, sites crawled (OK/failed), new jobs this cycle
- Per-site table with status, job counts, and errors
- Parser health bars (OK/failed percentages)

---

## Adding a New Company

1. **Identify the platform** -- visit the careers page and look for:
   - URL has `wd{N}.myworkdayjobs.com` -> `workday` parser
   - Page source has `phApp` / `phenom` -> `phenom` parser
   - `tbcdn.talentbrew.com` in source -> `radancy` parser
   - Test `GET https://boards-api.greenhouse.io/v1/boards/{company}/jobs` -> `greenhouse_api` parser
   - Page source has `eightfold` -> `eightfold` parser
   - `data-jibe` attributes -> `jibe` parser

2. **Add to `config/config.yaml`** (follow the dual-entry pattern for software + data searches):

```yaml
  - name: NewCompany
    enabled: true
    parser: greenhouse_api
    url: "https://newcompany.com/careers"
    greenhouse_board: "newcompany"
    search_text: "software"
    target_titles:
      - "Software Engineer"
      - "Software Developer"

  - name: NewCompany
    enabled: true
    parser: greenhouse_api
    url: "https://newcompany.com/careers"
    greenhouse_board: "newcompany"
    search_text: "data"
    target_titles:
      - "Data Engineer"
      - "Data Scientist"
      - "Data Analyst"
      - "ML Engineer"
```

3. **Test:**

```bash
source .venv/bin/activate
python -m crawler --once
```

4. Update `Career Links.xlsx` with the company name, URL, and status

---

## Supported Platforms & Companies

| Platform | Parser | Companies |
|----------|--------|-----------|
| Workday | `workday` | Adobe, Autodesk, Zillow, Intel, T-Mobile, CrowdStrike, NVIDIA, Capital One, General Motors, Boeing, Nordstrom, Expedia |
| Phenom | `phenom` | Abbott, Qualtrics, Lowes, HPE, Snowflake |
| Greenhouse (API) | `greenhouse_api` | Cloudflare, Discord, Figma, Reddit, Roblox, Coinbase, Box, MongoDB, Brex, Datadog, New York Times |
| Greenhouse (browser) | `greenhouse` | Waymo, Zoom, Etsy |
| Radancy/TMP | `radancy` | Wells Fargo, Chime, Palo Alto Networks, Disney, NetApp, Synopsys |
| Oracle HCM | `oracle_hcm` | JPMC, Oracle |
| Avature | `avature` | Two Sigma, Bloomberg |
| Eightfold | `eightfold` | Amex |
| Google Jibe | `jibe` | DocuSign |
| Generic | `generic` | Cisco, Goldman Sachs, DoorDash |
| Custom | Various | Salesforce, Airbnb, Apple, Caterpillar, Spotify, Stripe, Uber, Databricks, Walmart, Microsoft, Meta, Visa, PayPal, Ford, Amazon |

---

## CLI Options

```bash
python -m crawler                              # Run continuously on schedule
python -m crawler --once                       # Single run, then exit
python -m crawler --config config/custom.yaml  # Use a different config file
```

---

## Output

Jobs are saved to `jobs.xlsx` with these columns:

| Column | Description |
|--------|-------------|
| Job ID | Unique identifier from the career site |
| Requisition ID | Internal req ID (if available) |
| Title | Job title |
| Company | Company name |
| Location | Job location |
| Date Posted | When the job was posted |
| URL | Direct link to the job posting |
| Added On | When the crawler found this job |

Duplicates (same title + job ID) are automatically skipped.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Crawler | Python 3.12, Playwright, BeautifulSoup, Requests |
| Backend | FastAPI, Uvicorn, Supabase Python SDK, OpenAI SDK |
| Frontend | React 19, Vite 8, TypeScript 6, Tailwind CSS v4 |
| Database | Supabase (PostgreSQL) |
| File Storage | Supabase Storage |
| LLM | NVIDIA Cloud API (meta/llama-3.1-70b-instruct) |
| PDF Generation | fpdf2 |
| Containers | Docker, Docker Compose |
| Automation | n8n |
