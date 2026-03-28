import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

from crawler.parser_base import JobPosting

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
