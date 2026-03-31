import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict
from datetime import datetime
from typing import List

from crawler.parser_base import CrawlSiteResult, JobPosting

logger = logging.getLogger(__name__)


class EmailNotifier:
    def __init__(self, config: dict):
        email_cfg = config.get("email", {})
        self.smtp_server = email_cfg.get("smtp_server", "")
        self.smtp_port = email_cfg.get("smtp_port", 587)
        self.sender_email = email_cfg.get("sender_email", "")
        self.sender_password = email_cfg.get("sender_password", "")
        self.recipient_email = email_cfg.get("recipient_email", "")

    @property
    def is_configured(self) -> bool:
        return all([
            self.smtp_server,
            self.sender_email,
            self.sender_password,
            self.recipient_email,
            self.sender_email != "your_email@gmail.com",
        ])

    def notify(self, new_jobs: List[JobPosting]):
        """Send notification about new jobs. Falls back to console if email not configured."""
        if not new_jobs:
            return

        if not self.is_configured:
            logger.info("Email not configured. Logging new jobs to console:")
            for job in new_jobs:
                logger.info(f"  - {job.title} at {job.company} ({job.location}) | {job.url}")
            return

        self._send_email(new_jobs)

    def _send_email(self, jobs: List[JobPosting]):
        """Send an HTML email with a table of new job postings."""
        subject = f"Job Crawler: {len(jobs)} New Job(s) Found"

        rows = ""
        for job in jobs:
            rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{job.title}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{job.company}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{job.location}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{job.job_id}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    <a href="{job.url}">Apply</a>
                </td>
            </tr>"""

        html = f"""
        <html>
        <body>
            <h2>New Job Postings Found</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; border: 1px solid #ddd;">Title</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Company</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Location</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Job ID</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Apply</th>
                </tr>
                {rows}
            </table>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            logger.info(f"Email sent to {self.recipient_email} with {len(jobs)} jobs")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def send_health_report(self, results: List[CrawlSiteResult], jobs_added_today: int, cycle_count: int):
        """Send a health report email. Falls back to console if email not configured."""
        ok_count = sum(1 for r in results if r.success)
        fail_count = len(results) - ok_count
        new_this_cycle = sum(r.new_jobs_added for r in results)

        if not self.is_configured:
            self._log_health_report(results, jobs_added_today, cycle_count, ok_count, fail_count, new_this_cycle)
            return

        self._send_health_email(results, jobs_added_today, cycle_count, ok_count, fail_count, new_this_cycle)

    def _log_health_report(self, results, jobs_added_today, cycle_count, ok_count, fail_count, new_this_cycle):
        """Log health report to console."""
        logger.info(f"=== Health Report (Cycle {cycle_count}) ===")
        logger.info(f"Jobs added today: {jobs_added_today} | Sites: {ok_count} OK, {fail_count} failed | New this cycle: {new_this_cycle}")
        for r in results:
            status = "OK" if r.success else "FAILED"
            msg = f"  [{status}] {r.label} ({r.parser_name}) — {r.jobs_found} found, {r.new_jobs_added} new"
            if r.error_message:
                msg += f" | Error: {r.error_message}"
            logger.info(msg)

    def _send_health_email(self, results, jobs_added_today, cycle_count, ok_count, fail_count, new_this_cycle):
        """Send an HTML health report email."""
        now = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        subject = f"Crawler Health Report — Cycle {cycle_count} ({ok_count} OK / {fail_count} Failed)"

        # Per-site rows
        site_rows = ""
        for r in results:
            status_color = "#28a745" if r.success else "#dc3545"
            status_text = "OK" if r.success else "FAILED"
            error = r.error_message if r.error_message else "—"
            site_rows += f"""
            <tr>
                <td style="padding: 6px; border: 1px solid #ddd;">{r.site_name}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">{r.search_text or '—'}</td>
                <td style="padding: 6px; border: 1px solid #ddd; color: {status_color}; font-weight: bold;">{status_text}</td>
                <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">{r.jobs_found}</td>
                <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">{r.new_jobs_added}</td>
                <td style="padding: 6px; border: 1px solid #ddd; font-size: 12px;">{error}</td>
            </tr>"""

        # Parser health aggregation
        parser_stats = defaultdict(lambda: {"total": 0, "ok": 0, "failed": 0})
        for r in results:
            parser_stats[r.parser_name]["total"] += 1
            if r.success:
                parser_stats[r.parser_name]["ok"] += 1
            else:
                parser_stats[r.parser_name]["failed"] += 1

        parser_rows = ""
        for name, stats in sorted(parser_stats.items()):
            pct = int(stats["ok"] / stats["total"] * 100) if stats["total"] else 0
            bar_color = "#28a745" if pct >= 80 else "#ffc107" if pct >= 50 else "#dc3545"
            parser_rows += f"""
            <tr>
                <td style="padding: 6px; border: 1px solid #ddd;">{name}</td>
                <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">{stats['total']}</td>
                <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">{stats['ok']}</td>
                <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">{stats['failed']}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">
                    <div style="background: #e9ecef; border-radius: 4px; overflow: hidden; width: 100px; height: 16px;">
                        <div style="background: {bar_color}; width: {pct}%; height: 100%;"></div>
                    </div>
                    <span style="font-size: 11px;">{pct}%</span>
                </td>
            </tr>"""

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Crawler Health Report</h2>
            <p style="color: #666;">Cycle {cycle_count} &middot; {now}</p>

            <h3>Summary</h3>
            <table style="border-collapse: collapse; margin-bottom: 20px;">
                <tr><td style="padding: 4px 12px; font-weight: bold;">Jobs added today</td><td>{jobs_added_today}</td></tr>
                <tr><td style="padding: 4px 12px; font-weight: bold;">Sites crawled</td><td>{ok_count} OK / {fail_count} failed</td></tr>
                <tr><td style="padding: 4px 12px; font-weight: bold;">New jobs this cycle</td><td>{new_this_cycle}</td></tr>
            </table>

            <h3>Per-Site Results</h3>
            <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 6px; border: 1px solid #ddd;">Company</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Search Term</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Status</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Found</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">New</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Error</th>
                </tr>
                {site_rows}
            </table>

            <h3>Parser Health</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 6px; border: 1px solid #ddd;">Parser</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Total Sites</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">OK</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Failed</th>
                    <th style="padding: 6px; border: 1px solid #ddd;">Health</th>
                </tr>
                {parser_rows}
            </table>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            logger.info(f"Health report email sent to {self.recipient_email}")
        except Exception as e:
            logger.error(f"Failed to send health report email: {e}")
            self._log_health_report(results, jobs_added_today, 0, sum(1 for r in results if r.success),
                                    sum(1 for r in results if not r.success),
                                    sum(r.new_jobs_added for r in results))
