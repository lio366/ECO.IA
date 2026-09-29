"""Reporter - generates automated reports and sends email alerts."""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class Reporter:
    """Generates and distributes automated system reports."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        to_emails: Optional[List[str]] = None,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.to_emails = to_emails or []
        self._reports: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_daily_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured daily report from *data*."""
        report = {
            "type": "daily",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": self._build_summary(data),
            "data": data,
        }
        self._reports.append(report)
        logger.info("Daily report generated.")
        return report

    def generate_alert_report(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an alert report for a critical event."""
        report = {
            "type": "alert",
            "generated_at": datetime.utcnow().isoformat(),
            "alert": alert,
        }
        self._reports.append(report)
        logger.warning("Alert report generated: %s", alert.get("message"))
        return report

    def _build_summary(self, data: Dict[str, Any]) -> str:
        lines = ["ECO-IA Daily Report", "=" * 40]
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Email delivery
    # ------------------------------------------------------------------

    def send_email(self, subject: str, body: str, to: Optional[List[str]] = None) -> bool:
        """Send an email report. Returns True on success."""
        recipients = to or self.to_emails
        if not recipients or not self.smtp_host:
            logger.warning("Email not configured; skipping send.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email or ""
            msg["To"] = ", ".join(recipients)
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email or "", recipients, msg.as_string())

            logger.info("Email sent to %s.", recipients)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send email: %s", exc)
            return False

    def send_daily_report_email(self, data: Dict[str, Any]) -> bool:
        report = self.generate_daily_report(data)
        subject = f"ECO-IA Daily Report – {datetime.utcnow().strftime('%Y-%m-%d')}"
        return self.send_email(subject, report["summary"])

    def get_reports(self, report_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        reports = self._reports
        if report_type:
            reports = [r for r in reports if r.get("type") == report_type]
        return reports[-limit:]
