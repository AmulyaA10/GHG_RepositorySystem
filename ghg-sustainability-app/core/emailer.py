"""
Email Notification System
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from pathlib import Path
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class Emailer:
    """Email notification manager"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_address = settings.SMTP_FROM

    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: bool = True
    ) -> bool:
        """
        Send an email

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body
            html: Whether body is HTML

        Returns:
            bool: True if sent successfully
        """
        if not self.username or not self.password:
            logger.warning("SMTP credentials not configured, skipping email")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_address
            msg['To'] = ', '.join(to)

            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')

            msg.attach(part)

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {', '.join(to)}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def load_template(self, template_name: str, **kwargs) -> str:
        """
        Load and render email template

        Args:
            template_name: Template filename (without .html)
            **kwargs: Template variables

        Returns:
            str: Rendered template
        """
        template_path = settings.EMAIL_TEMPLATES_DIR / f"{template_name}.html"

        try:
            with open(template_path, 'r') as f:
                template = f.read()

            # Simple template rendering
            for key, value in kwargs.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))

            return template

        except FileNotFoundError:
            logger.warning(f"Template not found: {template_path}")
            return self._get_default_template(**kwargs)

    def _get_default_template(self, **kwargs) -> str:
        """Generate a default email template"""
        content = "<br>".join([f"<strong>{k}:</strong> {v}" for k, v in kwargs.items()])
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2E7D32;">GHG Sustainability Reporting System</h2>
            <p>{content}</p>
            <hr>
            <p style="color: #666; font-size: 0.9em;">
                This is an automated notification. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

# Global instance
emailer = Emailer()

def send_workflow_email(
    project,
    transition: str,
    comments: Optional[str] = None,
    reason_code: Optional[str] = None
):
    """
    Send workflow transition notification email

    Args:
        project: Project object
        transition: Transition identifier
        comments: Optional comments
        reason_code: Optional reason code
    """
    # Email configuration based on transition
    email_config = {
        "DRAFT_to_SUBMITTED": {
            "template": "submission",
            "subject": f"Project {project.id} Submitted for Calculation",
            "recipients": ["l2@example.com"]  # L2 users
        },
        "UNDER_CALCULATION_to_PENDING_REVIEW": {
            "template": "review_request",
            "subject": f"Project {project.id} Ready for Review",
            "recipients": ["l3@example.com"]  # L3 users
        },
        "PENDING_REVIEW_to_REJECTED": {
            "template": "rejection",
            "subject": f"Project {project.id} Rejected - Action Required",
            "recipients": [project.created_by_email] if hasattr(project, 'created_by_email') else []
        },
        "APPROVED_to_LOCKED": {
            "template": "approval",
            "subject": f"Project {project.id} Approved and Locked",
            "recipients": [project.created_by_email] if hasattr(project, 'created_by_email') else []
        }
    }

    config = email_config.get(transition)

    if not config:
        logger.debug(f"No email configuration for transition: {transition}")
        return

    template_data = {
        "project_id": project.id,
        "project_name": project.project_name,
        "organization": project.organization_name,
        "status": project.status,
        "comments": comments or "N/A",
        "reason_code": reason_code or "N/A"
    }

    body = emailer.load_template(config["template"], **template_data)
    emailer.send_email(
        to=config["recipients"],
        subject=config["subject"],
        body=body,
        html=True
    )
