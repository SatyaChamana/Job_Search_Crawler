# Job Search Crawler

Full-stack job search platform: Python crawler scrapes career pages from 47 companies, FastAPI backend serves data from Supabase, React frontend with resume/cover letter generation via NVIDIA Cloud LLM. Uses `.venv/bin/python3`.

## Architecture

```
config/
  config.yaml               # Sites, email, scheduler, health_report_interval
  config_intern.yaml         # Alternate config for intern positions
crawler/
  main.py                   # Entry point, PARSER_REGISTRY, _crawl_site(), crawl_once(), main()
  __main__.py               # python -m crawler entry point
  requirements.txt          # Crawler Python dependencies
  Dockerfile                # Crawler container
  parser_base.py            # JobPosting, CrawlSiteResult dataclasses, ParserBase ABC
  storage.py                # ExcelStorage, SupabaseStorage, DualStorage
  notifier.py               # EmailNotifier (job alerts + send_health_report with HTML email)
  fetcher.py                # fetch_page(), fetch_json() for static HTTP
  browser.py                # fetch_rendered_html() via Playwright
  filter.py                 # filter_by_keywords() post-filter
  parsers/                  # One file per parser (see registry below)
backend/
  main.py                   # FastAPI app, CORS, router registration
  config.py                 # Pydantic Settings (Supabase, NVIDIA API)
  database.py               # Supabase client init
  models.py                 # Pydantic response models
  Dockerfile                # Backend container
  requirements.txt          # Backend Python dependencies
  .env.example              # Template for credentials
  routers/
    jobs.py                 # GET /api/jobs, /api/stats
    generate.py             # POST /api/generate/*, /api/bulk-generate, master resume CRUD
  services/
    llm_client.py           # NVIDIA Cloud LLM (OpenAI-compatible)
    job_scraper.py           # Scrape job descriptions (reuses crawler/fetcher + browser)
    document_generator.py    # Orchestrator: scrape -> LLM -> PDF -> Supabase Storage
    supabase_storage.py      # Upload/download from Supabase Storage
  prompts/
    resume.txt              # System prompt for resume tailoring
    cover_letter.txt        # System prompt for cover letter generation
frontend/
  Dockerfile                # Node build -> nginx serve
  nginx.conf                # Reverse proxy /api -> backend:8000
  vite.config.ts            # Dev proxy + Tailwind
  src/
    App.tsx                 # Main layout with modals and toast system
    api.ts                  # Centralized API client
    types.ts                # TypeScript interfaces
    components/             # JobTable, JobRow, SearchBar, Pagination, StatsBar,
                            # Modal, Toast, Spinner, BulkActionBar,
                            # PreviewModal, DescriptionModal, MasterResumeModal
    hooks/useJobs.ts        # Data-fetching hook with search/filter/sort/pagination
scripts/
  schema.sql                # Supabase table definitions
  migrate_excel_to_supabase.py  # One-time migration from Excel to Supabase
  capture_locations.py      # Utility to analyze location formats across companies
n8n/workflows/              # n8n workflow templates (bulk generate, daily auto-generate)
docker-compose.yml          # Orchestrates backend, frontend, crawler, n8n
Career Links.xlsx           # Master list: Col A=company, B=URL, C=status
jobs.xlsx                   # Output: deduplicated job postings (gitignored)
```

## Parser Registry (25 parsers)

### Reusable Platform Parsers
| Parser | Platform | Config Keys | Companies Using It |
|--------|----------|-------------|-------------------|
| `workday` | Workday API (`*.wd{N}.myworkdayjobs.com`) | `workday_url`, `search_text`, `limit`, `applied_facets` | Adobe, Autodesk, Zillow, Intel, T-Mobile, CrowdStrike, NVIDIA (`wd5`, site `NVIDIAExternalCareerSite`), Capital One (`wd12`, site `Capital_One`), General Motors (`wd5`, site `Careers_GM`), Boeing (`wd1`, site `EXTERNAL_CAREERS`), Nordstrom (`wd501`, site `nordstrom_careers`), Expedia (`wd108`, site `search`) |
| `phenom` | Phenom (`phApp.ddo`) via Playwright | `wait_ms` | Abbott, Qualtrics, Lowes, HPE, Snowflake |
| `eightfold` | Eightfold.ai API | `eightfold_domain`, `eightfold_company_domain`, `search_text`, `search_location` | Amex |
| `jibe` | Google Jibe (`/api/jobs` JSON) | `jibe_base_url`, `search_text`, `location` | DocuSign |
| `radancy` | Radancy/TMP (static HTML) | - | Wells Fargo, Chime (`.card.card-job` layout, `?page=`), Palo Alto Networks (`section29` layout, `&p=`), Disney, NetApp, Synopsys (`a[data-job-id]` layout, `&p=`) |
| `greenhouse` | Greenhouse (browser-rendered, `.job-search-results-card-body`) | `wait_ms` | Waymo, Zoom, Etsy (Clinch Talent, same CSS class) |
| `greenhouse_api` | Greenhouse public boards API | `greenhouse_board` | Cloudflare, Discord, Figma, Reddit, Roblox, Coinbase, Box (`boxinc`), MongoDB, Brex, Datadog, New York Times |
| `oracle_hcm` | Oracle HCM Cloud | `wait_ms` | JPMC, Oracle |
| `avature` | Avature ATS (static HTML) | - | Two Sigma, Bloomberg |
| `generic` | HTML + browser fallback | `wait_ms` | Cisco, Goldman Sachs, DoorDash |

### Company-Specific Parsers
| Parser | Company | Notes |
|--------|---------|-------|
| `salesforce` | Salesforce | HTML parsing |
| `airbnb` | Airbnb | HTML parsing |
| `apple` | Apple | HTML parsing |
| `caterpillar` | Caterpillar | HTML parsing |
| `spotify` | Spotify | REST API (`categories`, `search_location`) |
| `stripe` | Stripe | HTML table parsing |
| `uber` | Uber | Custom API |
| `databricks` | Databricks | Custom API |
| `walmart` | Walmart | GraphQL API (`search_text`, `populations`) |
| `microsoft` | Microsoft | PCSX API (`search_text`, `search_location`, `limit`) |
| `meta` | Meta | Browser + data-sjs parsing |
| `visa` | Visa | Browser rendering (`wait_ms`) |
| `paypal` | PayPal | Eightfold-based custom |
| `ford` | Ford | Custom |
| `amazon` | Amazon | JSON API (`search.json`, `search_text`, `search_location`, `limit`) |

## Config Keys Reference

```yaml
- name: CompanyName        # Display name
  enabled: true            # Skip if false
  parser: workday          # Parser from registry
  url: "..."               # Career page URL (for reference)
  search_text: "software"  # Search query (parser-specific)
  target_titles:           # Case-insensitive substring match on job title
    - "Software Engineer"
  target_locations:        # Case-insensitive substring match on job location (optional)
    - "United States of America"
  # Parser-specific:
  workday_url: "..."       # Workday API endpoint
  limit: 20                # Workday page size
  applied_facets:          # Workday facets (locationCountry, locations, etc.)
    locationCountry: ["id"]
  wait_ms: 8000            # Playwright wait (phenom, generic, oracle_hcm, visa, greenhouse)
  jibe_base_url: "..."     # Jibe base URL
  location: "United States" # Jibe location filter
  greenhouse_board: "name" # Greenhouse boards API board name
```

## Pipeline Flow

1. `_crawl_site()` -> parser.fetch_and_parse() -> filter_by_keywords() -> target_locations filter -> storage.add_jobs()
2. Returns `(CrawlSiteResult, new_jobs)` tuple
3. `crawl_once()` runs all sites in parallel via ThreadPoolExecutor, sends email for new jobs, returns `List[CrawlSiteResult]`
4. `main()` runs scheduled loop with cycle counter; sends health report every N cycles (default 10)
5. Interim email sent if any sites exceed 2-min timeout while others have already found new jobs

## Adding a New Site

### Step 1: Identify the platform
Use `WebFetch` on the career URL and look for these indicators:
- **Phenom**: `phApp`, `phenom`, `cdn.phenompeople.com` in page source
- **Workday**: URL contains `wd{N}.myworkdayjobs.com`, or page links to a Workday login
- **Greenhouse**: `greenhouse.io` references, or try `GET https://boards-api.greenhouse.io/v1/boards/{company}/jobs`
- **Radancy**: `tbcdn.talentbrew.com`, `.card.card-job` or `section29__search-results-li` elements
- **Eightfold**: `eightfold.ai` in URL or source, `vscdn.net` CDN
- **Jibe**: `data-jibe` attributes, `/api/jobs` endpoint
- **Oracle HCM**: `*.fa.oraclecloud.com` URL

### Step 2: Test the API before configuring
- **Workday**: `POST https://{co}.wd{N}.myworkdayjobs.com/wday/cxs/{co}/{site}/jobs` with `{"searchText":"...","limit":20,"offset":0,"appliedFacets":{}}`. Finding the site ID is the hard part — check the career page source for `myworkdayjobs.com/{SiteID}` patterns, or look for Workday login links. Note: `applied_facets` IDs are site-specific; use `target_locations` if the standard US country ID (`bc33aa3152ec42d4995f4791a106ed09`) doesn't work.
- **Greenhouse API**: `GET https://boards-api.greenhouse.io/v1/boards/{board}/jobs` — try company name, `{company}inc`, etc.
- **Jibe**: `GET https://{domain}/api/jobs?keywords=...&page=1`
- **Phenom**: Uses Playwright browser rendering. Just set `parser: phenom`, `wait_ms: 8000`, and test.
- **Radancy**: Static HTML fetch. Supports two layouts: `.card.card-job` (pagination via `?page=`) and `section29__search-results-li` (pagination via `&p=`).

### Step 3: Add to config/config.yaml
Follow the existing dual-entry pattern (software search + data search) for each company. Use `target_locations` for companies returning global results.

### Step 4: Test with the actual parser
```bash
.venv/bin/python3 -c "
from crawler.parsers.{parser} import {ParserClass}
p = {ParserClass}({...config dict...})
jobs = p.fetch_and_parse()
print(f'{len(jobs)} jobs')
for j in jobs[:5]: print(f'  - {j.title} @ {j.location}')
"
```

### Step 5: Update Career Links.xlsx (if available)

## Workday URL Pattern

- Public URL: `https://{co}.wd{N}.myworkdayjobs.com/{SiteID}/job/...`
- API URL: `https://{co}.wd{N}.myworkdayjobs.com/wday/cxs/{co}/{SiteID}/jobs`
- Parser auto-converts API paths to public URLs (strips `/wday/cxs/{co}`)
- `applied_facets` supports `locationCountry`, `locations`, etc.
- **Finding the site ID is the hardest part.** The wd number and site ID vary per company and cannot be guessed easily. Best approach: use `WebFetch` on the company's careers page and look for `myworkdayjobs.com/{SiteID}` links or Workday login URLs (which reveal both wd number and site ID). Alternatively, brute-force common site IDs: `en-US`, `External`, `ExternalSite`, `Careers`, `{CompanyName}`, `{CompanyName}ExternalCareerSite`, `{CompanyName}_Careers`, `ExternalCareerSite`.
- **Applied facets are site-specific.** The US location country ID `bc33aa3152ec42d4995f4791a106ed09` works for some sites (Autodesk, CrowdStrike, Intel) but causes 400 errors on others (NVIDIA). When facets fail, omit `applied_facets` and use `target_locations` instead.

### Known Working Workday Configurations
| Company | Host | Site ID | Notes |
|---------|------|---------|-------|
| Adobe | `adobe.wd5` | `external_experienced` | |
| Autodesk | `autodesk.wd1` | `Ext` | US facet works |
| Zillow | `zillow.wd5` | `Zillow_Group_External` | |
| Intel | `intel.wd1` | `External` | Uses `locations` facets |
| T-Mobile | `tmobile.wd1` | `External` | |
| CrowdStrike | `crowdstrike.wd5` | `crowdstrikecareers` | US facet works |
| NVIDIA | `nvidia.wd5` | `NVIDIAExternalCareerSite` | No facets, use `target_locations` |
| Capital One | `capitalone.wd12` | `Capital_One` | Note: wd12 (unusual) |
| General Motors | `generalmotors.wd5` | `Careers_GM` | Phenom frontend, Workday backend |
| Boeing | `boeing.wd1` | `EXTERNAL_CAREERS` | Radancy/TMP frontend, Workday backend |
| Nordstrom | `nordstrom.wd501` | `nordstrom_careers` | Note: wd501 (very unusual) |
| Expedia | `expedia.wd108` | `search` | US facet works, uses "Software Development Engineer" titles |

### Known Working Greenhouse Board Names
| Company | Board Name | Notes |
|---------|-----------|-------|
| Cloudflare | `cloudflare` | |
| Discord | `discord` | |
| Figma | `figma` | |
| Reddit | `reddit` | |
| Roblox | `roblox` | |
| Coinbase | `coinbase` | |
| Box | `boxinc` | Note: not `box` |
| MongoDB | `mongodb` | Global results, use `target_locations` |
| Brex | `brex` | Global results, use `target_locations` |
| Datadog | `datadog` | Global results, use `target_locations` (locations use "USA" not "United States") |
| New York Times | `thenewyorktimes` | Note: not `nytimes` or `nyt` |

### Radancy Layouts
The radancy parser supports three HTML layouts:
1. **Card layout** (Wells Fargo, Chime): `.card.card-job` elements, `?page=` pagination, location via SVG icon detection
2. **Section29 layout** (Palo Alto Networks): `li.section29__search-results-li` elements, `&p=` pagination, `a[data-job-id]` for job IDs
3. **Job-link layout** (Disney, NetApp): `#search-results-list a[data-job-id]` elements, `&p=` pagination, `.job-location` and `.job-date-posted` spans. Title in `h2` (Disney) or `h3` (NetApp).

## Health Report System

- `CrawlSiteResult` tracks per-site success/failure, jobs found, new jobs added
- `crawl_once()` returns results list; `main()` triggers report every N cycles
- `send_health_report()` sends HTML email (summary + per-site table + parser health bars) or falls back to console logging
- `get_jobs_added_today_count()` reads "Added On" column from jobs.xlsx

## Companies Investigated but Not Yet Added (as of 2026-04-22)

These companies were tested but couldn't be configured with existing parsers:
| Company | Platform | Issue |
|---------|----------|-------|
| Tesla | Custom (`tesla.com/cua-api/apps/careers/state`) | Akamai Bot Manager blocks all automated access (curl, Playwright, curl_cffi, undetected-chromedriver). API exists and accepts `query`/`offset`/`count` but requires solved JS challenge cookie (`_abck`). Currently disabled. |
| Netflix | Custom (`jobs.netflix.com`) | 403 on API, needs custom parser |
| Amazon | Custom (`amazon.jobs/en/search.json`) | **Added** — custom `amazon` parser with JSON API |
| EA | Avature (`avature.net`) | Can try with `avature` parser (untested) |
| Google | Custom (`careers.google.com`) | Needs custom parser |
| EA | Avature (`avature.net`) | Unsupported ATS, needs new parser |
| ServiceNow | Unknown | 403 on careers page |
| Qualcomm | Eightfold | Different API pattern than standard eightfold, returns 0 results |
| Samsung | Unknown | Career page unreachable via fetch |
| Intuit | Unknown | 429 rate limiting |
| Palantir | Unknown | Workday site IDs not found |
| Broadcom | Unknown | Workday 404s, may have moved platforms |
| Notion | Greenhouse | Board returns 0 jobs (may not use public boards API) |
| Plaid | Greenhouse | Board returns 0 jobs |
| HashiCorp | Greenhouse | Board returns 0 jobs |

## Common Issues

- **0 jobs**: Try `wait_ms: 8000` or browser rendering; check if API endpoint changed
- **403**: Bot protection — use browser rendering via `generic` or Playwright-based parser
- **202 empty response**: Site needs browser rendering (e.g. Greenhouse sites)
- **Wrong titles**: `target_titles` is case-insensitive substring; use broad terms like "Software" for sites with non-standard titles (e.g. Intel)
- **Global results**: Add `target_locations: ["United States of America"]` to filter by location
- **Workday facets ignored**: Use `applied_facets` in config (passed to Workday API body)
- **Radancy location wrong**: Parser uses SVG icon detection (`#map-marker`) to distinguish location from department
