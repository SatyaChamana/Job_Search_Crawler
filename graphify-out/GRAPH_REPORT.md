# Graph Report - /Users/satyachamana/My Projects/Job_Search_Crawler  (2026-05-03)

## Corpus Check
- 95 files · ~158,734 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 461 nodes · 684 edges · 26 communities detected
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 151 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Parser Framework & Registry|Parser Framework & Registry]]
- [[_COMMUNITY_Crawler Pipeline & Orchestration|Crawler Pipeline & Orchestration]]
- [[_COMMUNITY_PDF Document Formatting|PDF Document Formatting]]
- [[_COMMUNITY_Frontend UI Components|Frontend UI Components]]
- [[_COMMUNITY_Backend API & Models|Backend API & Models]]
- [[_COMMUNITY_HTTP Fetching & Simple Parsers|HTTP Fetching & Simple Parsers]]
- [[_COMMUNITY_Project Architecture Docs|Project Architecture Docs]]
- [[_COMMUNITY_AI Document Generation|AI Document Generation]]
- [[_COMMUNITY_Browser-Rendered Parsers|Browser-Rendered Parsers]]
- [[_COMMUNITY_Generic HTML Parser|Generic HTML Parser]]
- [[_COMMUNITY_Job Description Scraper|Job Description Scraper]]
- [[_COMMUNITY_MetaFacebook Parser|Meta/Facebook Parser]]
- [[_COMMUNITY_Radancy Parser|Radancy Parser]]
- [[_COMMUNITY_Databricks Parser|Databricks Parser]]
- [[_COMMUNITY_Supabase File Storage|Supabase File Storage]]
- [[_COMMUNITY_Frontend Icon Assets|Frontend Icon Assets]]
- [[_COMMUNITY_Phenom Parser|Phenom Parser]]
- [[_COMMUNITY_Frontend App Shell|Frontend App Shell]]
- [[_COMMUNITY_Location Analysis Script|Location Analysis Script]]
- [[_COMMUNITY_Backend Configuration|Backend Configuration]]
- [[_COMMUNITY_Favicon Assets|Favicon Assets]]
- [[_COMMUNITY_Vite Build Assets|Vite Build Assets]]
- [[_COMMUNITY_Job Scraper Service|Job Scraper Service]]
- [[_COMMUNITY_Python Dependencies|Python Dependencies]]
- [[_COMMUNITY_Phenom Rationale|Phenom Rationale]]
- [[_COMMUNITY_Frontend Index|Frontend Index]]

## God Nodes (most connected - your core abstractions)
1. `JobPosting` - 64 edges
2. `ParserBase` - 31 edges
3. `GenericHTMLParser` - 13 edges
4. `_safe()` - 13 edges
5. `format_resume_pdf()` - 12 edges
6. `EmailNotifier` - 11 edges
7. `DatabricksParser` - 11 edges
8. `MetaParser` - 11 edges
9. `generate_document()` - 11 edges
10. `RadancyParser` - 10 edges

## Surprising Connections (you probably didn't know these)
- `CLAUDE.md Project Instructions` --semantically_similar_to--> `Job Search Crawler Project Overview (README)`  [INFERRED] [semantically similar]
  CLAUDE.md → README.md
- `Crawler Python Dependencies` --semantically_similar_to--> `Backend Python Dependencies`  [INFERRED] [semantically similar]
  crawler/requirements.txt → backend/requirements.txt
- `_get_description()` --calls--> `scrape_job_description()`  [INFERRED]
  backend/services/document_generator.py → crawler/scraper.py
- `Location Format Analysis (location_analysis.xlsx)` --references--> `Parser Registry (25 parsers)`  [INFERRED]
  graphify-out/converted/location_analysis_a606c56f.md → CLAUDE.md
- `fetch_job_description()` --calls--> `scrape_job_description()`  [INFERRED]
  backend/routers/generate.py → crawler/scraper.py

## Hyperedges (group relationships)
- **AI Document Generation Pipeline** — concept_ai_document_generation, resume_txt_system_prompt, cover_letter_txt_system_prompt, master_resume_satya_chamana, concept_nvidia_cloud_llm, concept_supabase_backend [EXTRACTED 0.95]
- **Crawler Data Pipeline (config -> parse -> filter -> store)** — config_yaml_site_definitions, concept_parser_registry, concept_pipeline_flow, concept_dual_storage, jobs_57a65867_job_postings_data, concept_supabase_backend [EXTRACTED 0.95]
- **Docker Compose Service Orchestration (backend + frontend + crawler + n8n)** — docker_compose_orchestration, concept_n8n_workflow_automation, concept_supabase_backend, frontend_index_html [EXTRACTED 0.90]

## Communities

### Community 0 - "Parser Framework & Registry"
Cohesion: 0.04
Nodes (37): ABC, JobPosting, ParserBase, Filter jobs by case-insensitive substring match against target_titles,         t, ParserBase, AirbnbParser, Parser for Airbnb's careers site using HTML parsing., AmazonParser (+29 more)

### Community 1 - "Crawler Pipeline & Orchestration"
Cohesion: 0.05
Nodes (31): filter_by_keywords(), Phase 2 placeholder: pass-through that returns all jobs unchanged.      In Phase, _build_storage(), crawl_once(), _crawl_site(), _fetch_descriptions(), load_config(), main() (+23 more)

### Community 2 - "PDF Document Formatting"
Cohesion: 0.09
Nodes (38): format_cover_letter_pdf(), format_resume_pdf(), _is_section_header(), _new_pdf(), _normalize_section_name(), _parse_resume_sections(), Professional PDF formatter for resumes and cover letters.  Parses LLM markdown o, Check if a line is a section header (## Header or ALL CAPS HEADER). (+30 more)

### Community 3 - "Frontend UI Components"
Cohesion: 0.08
Nodes (23): handleBulkGenerate(), handleFetch(), handleSave(), handleGenerate(), handleRegenerate(), handleSave(), PreviewModal(), SearchBar() (+15 more)

### Community 4 - "Backend API & Models"
Cohesion: 0.09
Nodes (28): JobListResponse, JobResponse, StatsResponse, BaseModel, bulk_generate(), BulkGenerateRequest, BulkGenerateResponse, BulkJobResult (+20 more)

### Community 5 - "HTTP Fetching & Simple Parsers"
Cohesion: 0.09
Nodes (14): fetch_json(), fetch_page(), Fetch JSON data from a URL., Fetch a web page with browser-like User-Agent headers., CaterpillarParser, Parser for Caterpillar's careers site using HTML parsing., Try API first, fall back to HTML parsing., Fetch jobs from the Salesforce careers API. (+6 more)

### Community 6 - "Project Architecture Docs"
Cohesion: 0.14
Nodes (22): Career Links Registry (Career Links.xlsx), CLAUDE.md Project Instructions, AI Document Generation Pipeline, Dual Storage Pattern (Excel + Supabase), Greenhouse API Platform, Health Report System, n8n Workflow Automation, NVIDIA Cloud LLM (meta/llama-3.1-70b-instruct) (+14 more)

### Community 7 - "AI Document Generation"
Cohesion: 0.12
Nodes (19): generate_cover_letter(), generate_resume(), Generate a tailored resume and return the PDF directly., Generate a tailored cover letter and return the PDF directly., generate_document(), _get_description(), _get_job(), _load_master_resume() (+11 more)

### Community 8 - "Browser-Rendered Parsers"
Cohesion: 0.13
Nodes (8): fetch_rendered_html(), Fetch a page using a headless browser and return the fully rendered HTML.      A, GreenhouseParser, Parser for Greenhouse-powered career sites (Waymo, Zoom, etc.).      Requires br, OracleHCMParser, Parser for career sites powered by Oracle HCM Cloud (JPMC, Oracle, etc.).      T, Parser for Visa's careers site. Requires browser rendering., VisaParser

### Community 9 - "Generic HTML Parser"
Cohesion: 0.18
Nodes (7): GenericHTMLParser, Convert a dictionary to a JobPosting if it has enough fields., Find job listings from HTML links., Try to extract location from an element's parent card., Generic parser that tries static HTML first, then falls back to     Playwright b, Extract jobs from Next.js __NEXT_DATA__., Recursively search for job-like data in nested dicts.

### Community 10 - "Job Description Scraper"
Cohesion: 0.21
Nodes (11): _clean_text(), _extract_description(), _is_quality_description(), Scrape and clean job descriptions from career page URLs., Extract the job description text from HTML., Clean extracted text: collapse whitespace, limit length., Check if scraped text looks like a real job description, not meta tag dump., Scrape a job posting URL and return the cleaned description text.      Tries a f (+3 more)

### Community 11 - "Meta/Facebook Parser"
Cohesion: 0.26
Nodes (5): MetaParser, Parse Meta's data-sjs embedded JSON scripts., Fallback: extract from role='link' elements., Parser for Meta careers. Uses browser rendering and extracts     job data from e, Recursively search API response for job listings.

### Community 12 - "Radancy Parser"
Cohesion: 0.25
Nodes (5): RadancyParser, Parse section29 layout (Palo Alto Networks)., Parse generic a[data-job-id] layout (Disney, NetApp)., Parser for Radancy/TMP-powered career sites (Wells Fargo, Chime, etc.).      Sta, Parse classic .card.card-job layout (Wells Fargo, Chime).

### Community 13 - "Databricks Parser"
Cohesion: 0.36
Nodes (2): DatabricksParser, Parser for Databricks careers using Gatsby static page-data.json (Greenhouse).

### Community 14 - "Supabase File Storage"
Cohesion: 0.29
Nodes (7): ensure_bucket(), get_signed_url(), Supabase Storage helpers for uploading and downloading generated documents., Create the storage bucket if it doesn't exist., Upload a file to Supabase Storage. Returns the storage path., Get a signed download URL for a stored file., upload_file()

### Community 15 - "Frontend Icon Assets"
Cohesion: 0.36
Nodes (8): Frontend Public Assets Directory, Bluesky Social Icon, Discord Icon, Documentation Icon (Code Brackets), GitHub Icon, Social/User-Star Icon, SVG Icon Sprite Sheet, X (Twitter) Icon

### Community 16 - "Phenom Parser"
Cohesion: 0.47
Nodes (3): _extract_phenom_data(), PhenomParser, Parser for Phenom-powered career sites (Abbott, Qualtrics, etc.).      Phenom em

### Community 17 - "Frontend App Shell"
Cohesion: 0.4
Nodes (6): App.tsx - Main React Layout, Frontend Static Assets Directory, Hero Image - Isometric Platform Icon, 3D Isometric Perspective with Dashed Connection Lines, Purple Gradient Solid Layer (bottom rounded square), Wireframe Outline Layer (top rounded square)

### Community 18 - "Location Analysis Script"
Cohesion: 0.4
Nodes (3): fetch_locations(), One-time script to capture raw location strings from every enabled company. Save, Fetch jobs from a site and return (company, parser, list_of_locations).

### Community 19 - "Backend Configuration"
Cohesion: 0.67
Nodes (2): Settings, BaseSettings

### Community 20 - "Favicon Assets"
Cohesion: 1.0
Nodes (3): Frontend Application, Vite Lightning Bolt Favicon, Vite

### Community 21 - "Vite Build Assets"
Cohesion: 1.0
Nodes (3): Frontend Application, Vite, Vite Logo (SVG)

### Community 25 - "Job Scraper Service"
Cohesion: 1.0
Nodes (1): Re-export scraper from crawler package.

### Community 27 - "Python Dependencies"
Cohesion: 1.0
Nodes (2): Backend Python Dependencies, Crawler Python Dependencies

### Community 33 - "Phenom Rationale"
Cohesion: 1.0
Nodes (1): Extract eagerLoadRefineSearch JSON from static HTML.

### Community 39 - "Frontend Index"
Cohesion: 1.0
Nodes (1): Frontend Entry Point (index.html)

## Knowledge Gaps
- **128 isolated node(s):** `Scrape and clean job descriptions from career page URLs.`, `Extract the job description text from HTML.`, `Clean extracted text: collapse whitespace, limit length.`, `Check if scraped text looks like a real job description, not meta tag dump.`, `Scrape a job posting URL and return the cleaned description text.      Tries a f` (+123 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Databricks Parser`** (9 nodes): `databricks.py`, `DatabricksParser`, `.fetch_and_parse()`, `._matches_department()`, `._matches_location()`, `._parse_departments()`, `._parse_location()`, `._resolve_city_keywords()`, `Parser for Databricks careers using Gatsby static page-data.json (Greenhouse).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Backend Configuration`** (3 nodes): `config.py`, `Settings`, `BaseSettings`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Job Scraper Service`** (2 nodes): `job_scraper.py`, `Re-export scraper from crawler package.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Python Dependencies`** (2 nodes): `Backend Python Dependencies`, `Crawler Python Dependencies`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Phenom Rationale`** (1 nodes): `Extract eagerLoadRefineSearch JSON from static HTML.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Frontend Index`** (1 nodes): `Frontend Entry Point (index.html)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `JobPosting` connect `Parser Framework & Registry` to `Crawler Pipeline & Orchestration`, `HTTP Fetching & Simple Parsers`, `Browser-Rendered Parsers`, `Generic HTML Parser`, `Meta/Facebook Parser`, `Radancy Parser`, `Databricks Parser`, `Phenom Parser`?**
  _High betweenness centrality (0.309) - this node is a cross-community bridge._
- **Why does `scrape_job_description()` connect `Job Description Scraper` to `Browser-Rendered Parsers`, `Crawler Pipeline & Orchestration`, `HTTP Fetching & Simple Parsers`, `AI Document Generation`?**
  _High betweenness centrality (0.243) - this node is a cross-community bridge._
- **Why does `fetch_rendered_html()` connect `Browser-Rendered Parsers` to `Parser Framework & Registry`, `Generic HTML Parser`, `Job Description Scraper`?**
  _High betweenness centrality (0.158) - this node is a cross-community bridge._
- **Are the 63 inferred relationships involving `JobPosting` (e.g. with `EmailNotifier` and `ExcelStorage`) actually correct?**
  _`JobPosting` has 63 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `ParserBase` (e.g. with `MicrosoftParser` and `PayPalParser`) actually correct?**
  _`ParserBase` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `GenericHTMLParser` (e.g. with `ParserBase` and `JobPosting`) actually correct?**
  _`GenericHTMLParser` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Scrape and clean job descriptions from career page URLs.`, `Extract the job description text from HTML.`, `Clean extracted text: collapse whitespace, limit length.` to the rest of the system?**
  _128 weakly-connected nodes found - possible documentation gaps or missing edges._