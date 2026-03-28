# Job Search Crawler - Claude Code Instructions

## Project Overview

This is a Python job search crawler that scrapes career pages from multiple companies. Jobs are saved to `jobs.xlsx` with deduplication. Configuration is in `config.yaml`.

## Key Files

- `main.py` - Entry point. Contains `PARSER_REGISTRY` dict mapping parser names to classes.
- `config.yaml` - All site configurations, email settings, scheduler interval.
- `crawler/parser_base.py` - `JobPosting` dataclass and `ParserBase` ABC.
- `crawler/browser.py` - `fetch_rendered_html()` using Playwright for JS-heavy sites.
- `crawler/fetcher.py` - `fetch_page()` and `fetch_json()` for static fetching.
- `crawler/storage.py` - `ExcelStorage` class with dedup via `title|job_id` keys.
- `Career Links.xlsx` - Master list of career URLs. Column A = company, Column B = URL, Column C = status.

## Parser Types Available

| Parser | Use When | Config Keys |
|--------|----------|-------------|
| `generic` | Unknown site, try HTML then browser fallback | `wait_ms` |
| `workday` | Workday-powered sites (wd5.myworkdayjobs.com) | `workday_url`, `search_text`, `limit` |
| `eightfold` | Eightfold.ai-powered sites | `eightfold_domain`, `eightfold_company_domain`, `search_text`, `search_location` |
| `oracle_hcm` | Oracle HCM Cloud sites (fa.oraclecloud.com) | `wait_ms` |
| `spotify` | Spotify only (custom API) | `categories`, `search_location` |
| `salesforce` | Salesforce only | - |
| `airbnb` | Airbnb only | - |
| `apple` | Apple only | - |
| `caterpillar` | Caterpillar only | - |
| `visa` | Visa only | `wait_ms` |
| `microsoft` | Microsoft only | `search_text` |
| `meta` | Meta only | - |

## How to Add a New Website Parser

When the user adds a new career link to `Career Links.xlsx`, follow these steps:

### Step 1: Investigate the site

```python
# Try static HTML first
from crawler.fetcher import fetch_page
r = fetch_page("https://example.com/careers?search=Software")
# Check if job listings are in the HTML

# If not, try browser rendering
from crawler.browser import fetch_rendered_html
html = fetch_rendered_html("https://example.com/careers", wait_ms=8000)
# Parse with BeautifulSoup to find job elements
```

### Step 2: Identify the platform

Check if the site uses a known platform:
- **Workday**: URL contains `wd5.myworkdayjobs.com` or similar. Use `workday` parser.
- **Eightfold**: URL contains `eightfold.ai`. Use `eightfold` parser.
- **Oracle HCM**: URL contains `fa.oraclecloud.com`. Use `oracle_hcm` parser.
- **Greenhouse**: URL contains `boards.greenhouse.io`. Create parser or use `generic`.
- **Lever**: URL contains `jobs.lever.co`. Create parser or use `generic`.
- **Other**: Start with `generic` parser. If it fails, create a custom parser.

### Step 3: Try the generic parser first

Add to `config.yaml`:

```yaml
  - name: CompanyName
    enabled: true
    parser: generic
    url: "the career page URL"
    wait_ms: 8000
    target_titles:
      - "Software Engineer"
```

Run `python main.py --once` and check if it finds jobs. If it does, you're done.

### Step 4: Create a custom parser (if generic fails)

Create `crawler/parsers/companyname.py`:

```python
import re
import logging
from typing import List
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

class CompanyNameParser(ParserBase):
    def fetch_and_parse(self) -> List[JobPosting]:
        # Implement fetching and parsing logic
        # Return self.filter_by_title(jobs) at the end
        pass
```

Then register it in `main.py`:

```python
from crawler.parsers.companyname import CompanyNameParser

PARSER_REGISTRY = {
    # ... existing parsers ...
    "companyname": CompanyNameParser,
}
```

### Step 5: Update Career Links.xlsx

Set column C (Status) for the new site:
- `Working` - parser returns jobs successfully
- `Not Working` - parser exists but site blocks scraping
- `Not Configured` - no parser set up yet

### Step 6: Update config.yaml

Add the site entry with appropriate parser, URL, and target_titles.

## API Investigation Patterns

When probing a new site for APIs:

```python
# 1. Check for Workday API
requests.post("https://company.wd5.myworkdayjobs.com/wday/cxs/company/external/jobs",
    json={"searchText": "Software", "limit": 5, "offset": 0})

# 2. Check for Eightfold API
requests.get("https://company.eightfold.ai/api/apply/v2/jobs",
    params={"domain": "company.com", "query": "Software", "num": 5})

# 3. Check for __NEXT_DATA__ (Next.js sites)
# Look for <script id="__NEXT_DATA__"> in page source

# 4. Intercept API calls with Playwright
def handle_response(response):
    if "api" in response.url and response.status == 200:
        print(response.url, response.json())
page.on("response", handle_response)

# 5. Check for embedded JSON in scripts
# Look for patterns like phApp.ddo, window.__DATA__, data-sjs attributes
```

## Common Fixes

- **0 jobs found**: Site may need browser rendering. Add `wait_ms: 8000` to config.
- **403 errors**: Site has bot protection. Try browser rendering via `generic` parser.
- **Wrong titles filtered**: Check `target_titles` in config. The filter is case-insensitive substring match.
- **Duplicate jobs**: Dedup is based on `title|job_id` key. If titles change slightly, duplicates may appear.

## Testing

```bash
# Run single site
python3 -c "
import yaml
from crawler.parsers.generic import GenericHTMLParser
with open('config.yaml') as f:
    config = yaml.safe_load(f)
site = [s for s in config['sites'] if s['name'] == 'CompanyName'][0]
parser = GenericHTMLParser(site)
jobs = parser.fetch_and_parse()
for j in jobs[:5]:
    print(f'{j.title} | {j.location} | {j.url}')
"
```
