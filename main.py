import argparse
import logging
import time

import yaml
import schedule

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
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def crawl_once(config: dict):
    """Run a single crawl cycle across all enabled sites."""
    storage_cfg = config.get("storage", {})
    excel_file = storage_cfg.get("excel_file", "jobs.xlsx")
    storage = ExcelStorage(filepath=excel_file)
    notifier = EmailNotifier(config)

    sites = config.get("sites", [])
    all_new_jobs = []

    for site in sites:
        if not site.get("enabled", True):
            logger.info(f"Skipping disabled site: {site.get('name', 'Unknown')}")
            continue

        parser_name = site.get("parser", "")
        parser_cls = PARSER_REGISTRY.get(parser_name)
        if not parser_cls:
            logger.warning(f"No parser registered for '{parser_name}', skipping site '{site.get('name')}'")
            continue

        logger.info(f"Crawling site: {site.get('name')}")
        parser = parser_cls(site)

        try:
            jobs = parser.fetch_and_parse()
            logger.info(f"Found {len(jobs)} matching jobs from {site.get('name')}")
        except Exception as e:
            logger.error(f"Error crawling {site.get('name')}: {e}")
            continue

        # Phase 2 pass-through filter
        jobs = filter_by_keywords(jobs)

        new_jobs = storage.add_jobs(jobs)
        all_new_jobs.extend(new_jobs)

    if all_new_jobs:
        logger.info(f"Total new jobs found: {len(all_new_jobs)}")
        notifier.notify(all_new_jobs)
    else:
        logger.info("No new jobs found in this cycle.")


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

    interval = config.get("scheduler", {}).get("interval_minutes", 10)
    logger.info(f"Starting scheduled crawler (every {interval} minutes)")

    # Run immediately on start
    crawl_once(config)

    schedule.every(interval).minutes.do(crawl_once, config)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
