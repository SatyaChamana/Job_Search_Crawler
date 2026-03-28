# Job Search Crawler

Automated job search crawler that scrapes career pages from 17+ companies, deduplicates listings, saves them to Excel, and optionally sends email notifications.

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

### 3. Run every 15 minutes

Edit `config.yaml` and set the interval:

```yaml
scheduler:
  interval_minutes: 15
```

Then run:

```bash
python main.py
```

The crawler runs immediately on start, then repeats every 15 minutes. Keep the terminal open or use a process manager (see below).

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
├── main.py                      # Entry point - parser registry, scheduler, CLI
├── config.yaml                  # All configuration (sites, email, schedule)
├── requirements.txt             # Python dependencies
├── Career Links.xlsx            # Master list of career URLs with status
├── jobs.xlsx                    # Output - scraped job listings (auto-created)
│
├── crawler/
│   ├── __init__.py
│   ├── browser.py               # Playwright browser rendering for SPA sites
│   ├── fetcher.py               # HTTP fetch utilities (static HTML + JSON)
│   ├── filter.py                # Phase 2 keyword filter (pass-through for now)
│   ├── notifier.py              # Email notifications via Gmail SMTP
│   ├── parser_base.py           # JobPosting dataclass + ParserBase ABC
│   ├── storage.py               # Excel storage with deduplication
│   │
│   └── parsers/                 # One parser per site/platform
│       ├── __init__.py
│       ├── salesforce.py        # Salesforce (API + HTML fallback)
│       ├── airbnb.py            # Airbnb (HTML parsing)
│       ├── apple.py             # Apple (HTML parsing)
│       ├── caterpillar.py       # Caterpillar (HTML parsing)
│       ├── eightfold.py         # Eightfold platform (Amex, PayPal API)
│       ├── workday.py           # Workday platform (Adobe API)
│       ├── spotify.py           # Spotify (REST API)
│       ├── oracle_hcm.py        # Oracle HCM (JPMC, Oracle - browser)
│       ├── visa.py              # Visa (browser rendering)
│       ├── microsoft.py         # Microsoft (browser + API interception)
│       ├── meta.py              # Meta (browser + data-sjs parsing)
│       └── generic.py           # Generic parser (HTML + browser fallback)
│
├── CLAUDE.md                    # Instructions for Claude Code AI assistant
└── .gitignore
```

## How It Works

```
main.py
  ├── Reads config.yaml
  ├── For each enabled site:
  │     ├── Picks parser from PARSER_REGISTRY
  │     ├── Parser fetches jobs (API → HTML → Browser fallback)
  │     ├── Filters by target_titles (case-insensitive substring match)
  │     ├── Deduplicates against existing jobs.xlsx
  │     └── Appends new jobs to Excel
  └── Sends email notification (or logs to console)
```

## Where to Configure Target Job Roles

Open `config.yaml` and edit the `target_titles` list under each site. The filter does **case-insensitive substring matching** - if any target title appears anywhere in the job title, it's a match.

```yaml
sites:
  - name: Adobe
    # ...
    target_titles:
      - "Software Engineer"      # matches "Senior Software Engineer", "Staff Software Engineer"
      - "Data Engineer"          # matches "Senior Data Engineer"
      - "ML Engineer"            # matches "Staff ML Engineer"
```

**To apply the same roles across ALL sites**, edit the `target_titles` under every site entry. Common patterns:

| Target Title | What It Matches |
|---|---|
| `"Software Engineer"` | Software Engineer, Senior Software Engineer, Staff Software Engineer, etc. |
| `"Software Developer"` | Software Developer 3, Senior Software Developer, etc. |
| `"Data Engineer"` | Data Engineer, Senior Data Engineer, etc. |
| `"Backend Engineer"` | Backend Engineer, Senior Backend Engineer, etc. |
| `"ML Engineer"` | ML Engineer, Staff ML Engineer, etc. |
| `"SDE"` | SDE, SDE II, SDE III, etc. |

**Tip:** Some companies use non-standard titles. Check the crawler log output to see what titles each site returns, then adjust accordingly.

## Email Notifications (Optional)

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

## Adding a New Company

1. Add a new entry to `config.yaml` under `sites:`
2. For most sites, start with the `generic` parser:

```yaml
  - name: NewCompany
    enabled: true
    parser: generic
    url: "https://newcompany.com/careers?search=Software"
    wait_ms: 8000          # Browser wait time (ms) for JS-rendered sites
    target_titles:
      - "Software Engineer"
```

3. Run `python main.py --once` to test
4. If the generic parser finds 0 jobs, a custom parser may be needed

## Current Site Status

| Company | Parser | Status | Method |
|---------|--------|--------|--------|
| Salesforce | salesforce | Working | HTML parsing |
| Airbnb | airbnb | Working | HTML parsing |
| Adobe | workday | Working | Workday REST API |
| Amex | eightfold | Working | Eightfold REST API |
| Apple | apple | Working | HTML parsing |
| Cisco | generic | Working | Browser rendering |
| Caterpillar | caterpillar | Working | HTML parsing |
| Ford | generic | Working | Browser rendering |
| PayPal | generic | Working | Browser rendering |
| JPMC | oracle_hcm | Working | Browser + job-tile parsing |
| Goldman Sachs | generic | Working | Browser rendering |
| DoorDash | generic | Working | Browser rendering |
| Visa | visa | Working | Browser rendering |
| Spotify | spotify | Working | REST API |
| Oracle | oracle_hcm | Working | Browser + job-tile parsing |
| Meta | meta | Not Working | Bot protection |
| Microsoft | microsoft | Not Working | SPA + bot protection |
| Tesla | generic | Not Working | Bot protection |

## CLI Options

```bash
python main.py              # Run continuously on schedule
python main.py --once       # Single run, then exit
python main.py --config custom.yaml  # Use a different config file
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
