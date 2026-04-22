# Job Search Crawler

Automated job search crawler that scrapes career pages from 30+ companies, deduplicates listings, saves them to Excel, sends email notifications for new jobs, and provides periodic health reports.

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/SatyaChamana/Job_Search_Crawler.git
cd Job_Search_Crawler
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Run once (test it out)

```bash
python main.py --once
```

### 3. Run on a schedule

The crawler runs on a randomized interval (default 18-23 minutes) during active hours (7am-11pm). Edit `config.yaml` to customize:

```yaml
scheduler:
  interval_min_minutes: 18
  interval_max_minutes: 23
  start_hour: 7
  stop_hour: 23
```

Then run:

```bash
python main.py
```

### 4. Run in the background (persistent)

```bash
# Using nohup
nohup python main.py > crawler.log 2>&1 &

# Or using screen
screen -S crawler
python main.py
# Press Ctrl+A, then D to detach

# Or using launchd (macOS) - create ~/Library/LaunchAgents/com.jobcrawler.plist
```

## Project Structure

```
Job_Search_Crawler/
├── main.py                      # Entry point - parser registry, scheduler, parallel execution
├── config.yaml                  # All configuration (sites, email, schedule)
├── requirements.txt             # Python dependencies
├── Career Links.xlsx            # Master list of career URLs with status tracking
├── jobs.xlsx                    # Output - scraped job listings (auto-created)
│
├── crawler/
│   ├── __init__.py
│   ├── parser_base.py           # JobPosting + CrawlSiteResult dataclasses, ParserBase ABC
│   ├── storage.py               # Excel storage with deduplication + daily job counts
│   ├── notifier.py              # Email notifications (job alerts + health reports)
│   ├── browser.py               # Playwright browser rendering for JS-heavy sites
│   ├── fetcher.py               # HTTP fetch utilities (static HTML + JSON)
│   ├── filter.py                # Keyword filter (post-processing)
│   │
│   └── parsers/                 # One parser per site/platform
│       ├── workday.py           # Workday platform (Adobe, Netflix, Autodesk, Zillow, Intel, T-Mobile, CrowdStrike)
│       ├── phenom.py            # Phenom platform (Abbott, Qualtrics, Lowes, HPE)
│       ├── eightfold.py         # Eightfold.ai platform (Amex)
│       ├── jibe.py              # Google Jibe platform (DocuSign)
│       ├── radancy.py           # Radancy/TMP platform (Wells Fargo, Chime)
│       ├── greenhouse.py        # Greenhouse browser-rendered (Waymo, Zoom)
│       ├── greenhouse_api.py    # Greenhouse public boards API (Cloudflare)
│       ├── oracle_hcm.py        # Oracle HCM Cloud (JPMC, Oracle)
│       ├── generic.py           # Generic parser with HTML + browser fallback
│       ├── salesforce.py        # Salesforce
│       ├── airbnb.py            # Airbnb
│       ├── apple.py             # Apple
│       ├── caterpillar.py       # Caterpillar
│       ├── spotify.py           # Spotify
│       ├── stripe.py            # Stripe
│       ├── uber.py              # Uber
│       ├── databricks.py        # Databricks
│       ├── walmart.py           # Walmart (GraphQL API)
│       ├── microsoft.py         # Microsoft
│       ├── meta.py              # Meta
│       ├── visa.py              # Visa
│       ├── paypal.py            # PayPal
│       └── ford.py              # Ford
│
├── CLAUDE.md                    # Instructions for Claude Code AI assistant
└── .gitignore
```

## How It Works

```
main.py
  ├── Reads config.yaml
  ├── For each enabled site (in parallel via ThreadPoolExecutor):
  │     ├── Picks parser from PARSER_REGISTRY (23 parsers)
  │     ├── Parser fetches jobs (API / HTML / Browser — depends on platform)
  │     ├── Filters by target_titles (case-insensitive substring match)
  │     ├── Filters by target_locations (optional, case-insensitive substring)
  │     ├── Deduplicates against existing jobs.xlsx
  │     └── Appends new jobs to Excel
  ├── Sends email notification for new jobs (or logs to console)
  ├── If any site exceeds 2-min timeout, sends interim email for jobs found so far
  └── Every N cycles (default 10), sends health report email
```

## Supported Platforms & Companies

| Platform | Parser | Companies |
|----------|--------|-----------|
| Workday | `workday` | Adobe, Netflix, Autodesk, Zillow, Intel, T-Mobile, CrowdStrike |
| Phenom | `phenom` | Abbott, Qualtrics, Lowes, HPE |
| Eightfold | `eightfold` | Amex |
| Google Jibe | `jibe` | DocuSign |
| Radancy/TMP | `radancy` | Wells Fargo, Chime |
| Greenhouse (browser) | `greenhouse` | Waymo, Zoom |
| Greenhouse (API) | `greenhouse_api` | Cloudflare |
| Oracle HCM | `oracle_hcm` | JPMC, Oracle |
| Generic (HTML/browser) | `generic` | Cisco, Goldman Sachs, DoorDash |
| Custom | Various | Salesforce, Airbnb, Apple, Caterpillar, Spotify, Stripe, Uber, Databricks, Walmart, Microsoft, Meta, Visa, PayPal, Ford |

## Configuration

### Target Job Roles

Edit the `target_titles` list under each site in `config.yaml`. The filter does **case-insensitive substring matching** — if any target title appears anywhere in the job title, it's a match.

```yaml
sites:
  - name: Adobe
    # ...
    target_titles:
      - "Software Engineer"      # matches "Senior Software Engineer", "Staff Software Engineer"
      - "Data Engineer"          # matches "Senior Data Engineer"
      - "ML Engineer"            # matches "Staff ML Engineer"
```

| Target Title | What It Matches |
|---|---|
| `"Software Engineer"` | Software Engineer, Senior Software Engineer, Staff Software Engineer |
| `"Software Developer"` | Software Developer 3, Senior Software Developer |
| `"Data Engineer"` | Data Engineer, Senior Data Engineer |
| `"Data Scientist"` | Data Scientist, Senior Data Scientist |
| `"ML Engineer"` | ML Engineer, Staff ML Engineer |
| `"SDE"` | SDE, SDE II, SDE III |
| `"Software"` | Broad match — catches non-standard titles like "Software DevOps Engineer" |

### Location Filtering

For sites returning global results, add `target_locations` to filter by location:

```yaml
  - name: HPE
    parser: phenom
    # ...
    target_locations:
      - "United States of America"
```

### Email Notifications

Edit `config.yaml` with your Gmail credentials:

```yaml
email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender_email: your_email@gmail.com
  sender_password: your_app_password       # Use a Gmail App Password, not your real password
  recipient_email: recipient@example.com
```

To generate a Gmail App Password:
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the 16-character password

If email is not configured, new jobs are logged to the console instead.

### Health Reports

The crawler sends a health report email every N crawl cycles (default 10). The report includes:
- **Summary**: jobs added today, sites crawled (OK/failed), new jobs this cycle
- **Per-Site Table**: company, search term, status (color-coded), jobs found, new jobs, errors
- **Parser Health**: parser name, total sites, OK/failed counts, health percentage bar

Configure the interval:
```yaml
health_report_interval: 10
```

## Adding a New Company

1. Add a new entry to `config.yaml` under `sites:`
2. For most sites, start with the `generic` parser:

```yaml
  - name: NewCompany
    enabled: true
    parser: generic
    url: "https://newcompany.com/careers?search=Software"
    wait_ms: 8000
    target_titles:
      - "Software Engineer"
```

3. Run `python main.py --once` to test
4. If the generic parser finds 0 jobs, check if the site uses a known platform (Workday, Phenom, Greenhouse, etc.) and switch to the appropriate parser
5. Update `Career Links.xlsx` with the company name, URL, and status

## CLI Options

```bash
python main.py                         # Run continuously on schedule
python main.py --once                  # Single run, then exit
python main.py --config custom.yaml    # Use a different config file
```

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

Duplicate jobs (same title + job ID) are automatically skipped.
