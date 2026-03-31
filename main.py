import argparse
import logging
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import yaml

from crawler.parsers.salesforce import SalesforceParser
from crawler.parsers.airbnb import AirbnbParser
from crawler.parsers.apple import AppleParser
from crawler.parsers.caterpillar import CaterpillarParser
from crawler.parsers.eightfold import EightfoldParser
from crawler.parsers.workday import WorkdayParser
from crawler.parsers.generic import GenericHTMLParser
from crawler.parsers.spotify import SpotifyParser
from crawler.parsers.oracle_hcm import OracleHCMParser
from crawler.parsers.visa import VisaParser
from crawler.parsers.microsoft import MicrosoftParser
from crawler.parsers.meta import MetaParser
from crawler.parsers.stripe import StripeParser
from crawler.parsers.uber import UberParser
from crawler.parsers.databricks import DatabricksParser
from crawler.parsers.paypal import PayPalParser
from crawler.parsers.ford import FordParser
from crawler.parsers.phenom import PhenomParser
from crawler.parsers.walmart import WalmartParser
from crawler.parsers.jibe import JibeParser
from crawler.parsers.radancy import RadancyParser
from crawler.parsers.greenhouse import GreenhouseParser
from crawler.parsers.greenhouse_api import GreenhouseAPIParser
from crawler.parser_base import CrawlSiteResult
from crawler.storage import ExcelStorage
from crawler.notifier import EmailNotifier
from crawler.filter import filter_by_keywords

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PARSER_REGISTRY = {
    "salesforce": SalesforceParser,
    "airbnb": AirbnbParser,
    "apple": AppleParser,
    "caterpillar": CaterpillarParser,
    "eightfold": EightfoldParser,
    "workday": WorkdayParser,
    "generic": GenericHTMLParser,
    "spotify": SpotifyParser,
    "oracle_hcm": OracleHCMParser,
    "visa": VisaParser,
    "microsoft": MicrosoftParser,
    "meta": MetaParser,
    "stripe": StripeParser,
    "uber": UberParser,
    "databricks": DatabricksParser,
    "paypal": PayPalParser,
    "ford": FordParser,
    "phenom": PhenomParser,
    "walmart": WalmartParser,
    "jibe": JibeParser,
    "radancy": RadancyParser,
    "greenhouse": GreenhouseParser,
    "greenhouse_api": GreenhouseAPIParser,
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


SITE_TIMEOUT = 120  # 2 minutes


def _crawl_site(parser, site_name, storage, site_config):
    """Crawl a single site, filter, store to Excel. Returns (CrawlSiteResult, new_jobs)."""
    search_text = site_config.get("search_text", "")
    parser_name = site_config.get("parser", "")
    try:
        jobs = parser.fetch_and_parse()
        logger.info(f"Found {len(jobs)} matching jobs from {site_name}")
        jobs = filter_by_keywords(jobs)
        target_locations = site_config.get("target_locations", [])
        if target_locations:
            jobs = [j for j in jobs if any(loc.lower() in j.location.lower() for loc in target_locations)]
        new_jobs = storage.add_jobs(jobs)
        result = CrawlSiteResult(
            label=site_name,
            site_name=site_config.get("name", "Unknown"),
            search_text=search_text,
            parser_name=parser_name,
            success=True,
            jobs_found=len(jobs),
            new_jobs_added=len(new_jobs),
        )
        return result, new_jobs
    except Exception as e:
        logger.error(f"Error crawling {site_name}: {e}")
        result = CrawlSiteResult(
            label=site_name,
            site_name=site_config.get("name", "Unknown"),
            search_text=search_text,
            parser_name=parser_name,
            success=False,
            error_message=str(e),
        )
        return result, []


def crawl_once(config: dict) -> list:
    """Run a single crawl cycle across all enabled sites in parallel. Returns list of CrawlSiteResult."""
    storage_cfg = config.get("storage", {})
    excel_file = storage_cfg.get("excel_file", "jobs.xlsx")
    storage = ExcelStorage(filepath=excel_file)
    notifier = EmailNotifier(config)

    sites = config.get("sites", [])
    all_new_jobs = []
    all_results = []
    notified_keys = set()

    # Build list of (site_name, parser, site_config) for enabled sites
    tasks = []
    for site in sites:
        if not site.get("enabled", True) or site.get("skip", False):
            logger.info(f"Skipping site: {site.get('name', 'Unknown')}")
            continue

        parser_name = site.get("parser", "")
        parser_cls = PARSER_REGISTRY.get(parser_name)
        if not parser_cls:
            logger.warning(f"No parser registered for '{parser_name}', skipping site '{site.get('name')}'")
            continue

        site_name = site.get("name", "Unknown")
        search = site.get("search_text", "")
        label = f"{site_name} ({search})" if search else site_name
        parser = parser_cls(site)
        tasks.append((label, parser, site))

    if not tasks:
        logger.info("No sites to crawl.")
        return []

    logger.info(f"Crawling {len(tasks)} sites in parallel...")

    # Run all parsers in parallel
    max_workers = min(len(tasks), 10)
    future_to_label = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for label, parser, site_config in tasks:
            future = executor.submit(_crawl_site, parser, label, storage, site_config)
            future_to_label[future] = label

        # Collect results as they complete, flush email after 2-min mark
        done_before_timeout = set()
        try:
            for future in as_completed(future_to_label, timeout=SITE_TIMEOUT):
                label = future_to_label[future]
                try:
                    crawl_result, new_jobs = future.result()
                    all_results.append(crawl_result)
                    all_new_jobs.extend(new_jobs)
                    done_before_timeout.add(future)
                    logger.info(f"[{label}] done — {len(new_jobs)} new jobs")
                except Exception as e:
                    done_before_timeout.add(future)
                    logger.error(f"[{label}] raised: {e}")
        except TimeoutError:
            pass

        # Check if any sites are still running past the 2-min mark
        pending = [f for f in future_to_label if f not in done_before_timeout]
        if pending:
            pending_labels = [future_to_label[f] for f in pending]
            logger.warning(f"Sites still running after {SITE_TIMEOUT}s: {', '.join(pending_labels)}")

            # Flush interim email for jobs collected so far
            if all_new_jobs:
                unsent = [j for j in all_new_jobs if j.dedup_key not in notified_keys]
                if unsent:
                    logger.info(f"Sending interim email with {len(unsent)} jobs while slow sites finish")
                    notifier.notify(unsent)
                    for j in unsent:
                        notified_keys.add(j.dedup_key)

            # Wait for remaining sites to finish (no hard kill)
            for future in pending:
                label = future_to_label[future]
                try:
                    crawl_result, new_jobs = future.result()  # blocks until done
                    all_results.append(crawl_result)
                    all_new_jobs.extend(new_jobs)
                    logger.info(f"[{label}] finished late — {len(new_jobs)} new jobs")
                except Exception as e:
                    logger.error(f"[{label}] raised: {e}")

    # Send final email for any remaining jobs not yet notified
    unsent = [j for j in all_new_jobs if j.dedup_key not in notified_keys]
    if unsent:
        logger.info(f"Total new jobs found: {len(unsent)}")
        notifier.notify(unsent)
    elif not all_new_jobs:
        logger.info("No new jobs found in this cycle.")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Job Search Crawler")
    parser.add_argument("--once", action="store_true", help="Run a single crawl cycle and exit")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()
    config = load_config(args.config)

    if args.once:
        logger.info("Running single crawl cycle...")
        crawl_once(config)
        return

    sched_cfg = config.get("scheduler", {})
    interval_min = sched_cfg.get("interval_min_minutes", 18)
    interval_max = sched_cfg.get("interval_max_minutes", 24)
    start_hour = sched_cfg.get("start_hour", 7)
    stop_hour = sched_cfg.get("stop_hour", 23)
    report_interval = config.get("health_report_interval", 10)
    logger.info(f"Starting scheduled crawler (every {interval_min}–{interval_max} min, active {start_hour}:00–{stop_hour}:00)")

    notifier = EmailNotifier(config)
    storage_cfg = config.get("storage", {})
    excel_file = storage_cfg.get("excel_file", "jobs.xlsx")
    storage = ExcelStorage(filepath=excel_file)
    cycle_count = 0

    while True:
        now = datetime.now()
        logger.info(f"Current time: {now.strftime('%I:%M %p')}")
        if now.hour >= stop_hour or now.hour < start_hour:
            # Outside active hours — sleep until start_hour
            wake = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            if now.hour >= stop_hour:
                wake += timedelta(days=1)

            sleep_secs = int((wake - now).total_seconds())
            logger.info(f"Outside active hours. Sleeping until {wake.strftime('%I:%M %p')}...")

            for remaining in range(sleep_secs, 0, -1):
                h, rem = divmod(remaining, 3600)
                m, s = divmod(rem, 60)
                sys.stdout.write(f"\r  Resumes in {h:02d}:{m:02d}:{s:02d} ")
                sys.stdout.flush()
                time.sleep(1)

            sys.stdout.write("\r" + " " * 30 + "\r")
            sys.stdout.flush()
            continue

        results = crawl_once(config)
        cycle_count += 1

        if results and cycle_count % report_interval == 0:
            jobs_added_today = storage.get_jobs_added_today_count()
            notifier.send_health_report(results, jobs_added_today, cycle_count)

        # Check if next crawl would land outside active hours
        wait_seconds = int(random.uniform(interval_min, interval_max) * 60)
        next_time = datetime.now() + timedelta(seconds=wait_seconds)

        if next_time.hour >= stop_hour:
            logger.info(f"Next crawl would be at {next_time.strftime('%I:%M %p')}, past {stop_hour}:00. Stopping for the night.")
            continue  # Loop back to the sleep-until-morning check

        logger.info(f"Next crawl in {wait_seconds // 60}m {wait_seconds % 60}s")

        for remaining in range(wait_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            sys.stdout.write(f"\r  Next crawl in {mins:02d}:{secs:02d} ")
            sys.stdout.flush()
            time.sleep(1)

        sys.stdout.write("\r" + " " * 30 + "\r")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
