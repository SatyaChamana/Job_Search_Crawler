# Job Search Crawler

Python crawler that scrapes career pages, saves to `jobs.xlsx` with dedup, sends email alerts for new jobs, and periodic health reports. Config in `config.yaml`. Uses `.venv/bin/python3`.

## Architecture

```
main.py                     # Entry point, PARSER_REGISTRY, _crawl_site(), crawl_once(), main()
config.yaml                 # Sites, email, scheduler, health_report_interval
crawler/
  parser_base.py            # JobPosting, CrawlSiteResult dataclasses, ParserBase ABC
  storage.py                # ExcelStorage (dedup via title|job_id, get_jobs_added_today_count)
  notifier.py               # EmailNotifier (job alerts + send_health_report with HTML email)
  fetcher.py                # fetch_page(), fetch_json() for static HTTP
  browser.py                # fetch_rendered_html() via Playwright
  filter.py                 # filter_by_keywords() post-filter
  parsers/                  # One file per parser (see registry below)
Career Links.xlsx           # Master list: Col A=company, B=URL, C=status (Working/Not Working/Not Configured)
jobs.xlsx                   # Output: deduplicated job postings
```

## Parser Registry (21 parsers)

| Parser | Platform | Config Keys | Companies Using It |
|--------|----------|-------------|-------------------|
| `workday` | Workday API (`*.wd{N}.myworkdayjobs.com`) | `workday_url`, `search_text`, `limit`, `applied_facets` | Adobe, Netflix, Autodesk, Zillow, Intel, T-Mobile, + others |
| `phenom` | Phenom (`phApp.ddo`) via Playwright | `wait_ms` | Abbott, Qualtrics, Lowes, HPE |
| `jibe` | Google Jibe (`/api/jobs` JSON) | `jibe_base_url`, `search_text`, `location` | DocuSign |
| `eightfold` | Eightfold.ai API | `eightfold_domain`, `eightfold_company_domain`, `search_text`, `search_location` | Various |
| `walmart` | Walmart GraphQL API | `search_text`, `populations` | Walmart |
| `generic` | HTML + browser fallback | `wait_ms` | Fallback for unknown sites |
| `oracle_hcm` | Oracle HCM Cloud | `wait_ms` | Oracle |
| `salesforce` | Custom | - | Salesforce |
| `spotify` | Custom API | `categories`, `search_location` | Spotify |
| `stripe` | Custom (HTML table) | - | Stripe |
| `uber` | Custom API | - | Uber |
| `databricks` | Custom | - | Databricks |
| `microsoft` | Custom | `search_text` | Microsoft |
| `meta` | Custom | - | Meta |
| `airbnb` | Custom | - | Airbnb |
| `apple` | Custom | - | Apple |
| `caterpillar` | Custom | - | Caterpillar |
| `visa` | Custom | `wait_ms` | Visa |
| `paypal` | Custom | - | PayPal |
| `ford` | Custom | - | Ford |

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
  wait_ms: 8000            # Playwright wait (phenom, generic, oracle_hcm, visa)
  jibe_base_url: "..."     # Jibe base URL
  location: "United States" # Jibe location filter
```

## Pipeline Flow

1. `_crawl_site()` → parser.fetch_and_parse() → filter_by_keywords() → target_locations filter → storage.add_jobs()
2. Returns `(CrawlSiteResult, new_jobs)` tuple
3. `crawl_once()` runs all sites in parallel via ThreadPoolExecutor, sends email for new jobs, returns `List[CrawlSiteResult]`
4. `main()` runs scheduled loop with cycle counter; sends health report every N cycles (default 10)

## Adding a New Site

1. **Fetch the page** — check for platform indicators: `phApp`/`phenom`, `*.wd{N}.myworkdayjobs.com`, `eightfold`, `jibe`/`data-jibe`, `__NEXT_DATA__`
2. **Match to existing parser** — Workday API, Phenom browser, Jibe /api/jobs, etc.
3. **Test the API** before configuring:
   - Workday: `POST https://{co}.wd{N}.myworkdayjobs.com/wday/cxs/{co}/{site}/jobs` with `{"searchText":"...","limit":20,"offset":0,"appliedFacets":{}}`
   - Jibe: `GET https://{domain}/api/jobs?keywords=...&page=1`
   - Phenom: Browser render, extract `window.phApp.ddo.eagerLoadRefineSearch`
4. **Add to config.yaml**, **register in main.py** (if new parser), **update Career Links.xlsx**
5. **Test**: `.venv/bin/python3 -c "..."` with parser class directly

## Workday URL Pattern

- Public URL: `https://{co}.wd{N}.myworkdayjobs.com/{SiteID}/job/...`
- API URL: `https://{co}.wd{N}.myworkdayjobs.com/wday/cxs/{co}/{SiteID}/jobs`
- Parser auto-converts API paths to public URLs (strips `/wday/cxs/{co}`)
- `applied_facets` supports `locationCountry`, `locations`, etc.

## Health Report System

- `CrawlSiteResult` tracks per-site success/failure, jobs found, new jobs added
- `crawl_once()` returns results list; `main()` triggers report every N cycles
- `send_health_report()` sends HTML email (summary + per-site table + parser health bars) or falls back to console logging
- `get_jobs_added_today_count()` reads "Added On" column from jobs.xlsx

## Common Issues

- **0 jobs**: Try `wait_ms: 8000` or browser rendering; check if API endpoint changed
- **403**: Bot protection — use browser rendering via `generic` or Playwright-based parser
- **Wrong titles**: `target_titles` is case-insensitive substring; use broad terms like "Software" for sites with non-standard titles (e.g. Intel)
- **Global results**: Add `target_locations: ["United States of America"]` to filter by location
- **Workday facets ignored**: Use `applied_facets` in config (passed to Workday API body)
