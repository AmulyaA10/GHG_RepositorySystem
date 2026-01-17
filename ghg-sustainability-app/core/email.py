"""
Email Service
Handles sending emails for password reset and notifications
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails via SMTP"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.smtp_use_tls = settings.SMTP_USE_TLS

    def _get_smtp_connection(self):
        """Create and return SMTP connection"""
        try:
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            return server
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to_email

            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)

            # Attach text part
            text_part = MIMEText(body_text, 'plain')
            msg.attach(text_part)

            # Attach HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, 'html')
                msg.attach(html_part)

            # Send email
            with self._get_smtp_connection() as server:
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)

                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_password_reset_email(
        self,
        to_email: str,
        username: str,
        reset_link: str
    ) -> bool:
        """
        Send password reset email

        Args:
            to_email: User's email address
            username: User's username
            reset_link: Password reset link with token

        Returns:
            bool: True if email sent successfully
        """
        subject = f"{settings.APP_NAME} - Password Reset Request"

        # Plain text version
        body_text = f"""
Hello {username},

You have requested to reset your password for {settings.APP_NAME}.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email or contact support if you have concerns.

Best regards,
{settings.APP_NAME} Team
"""

        # HTML version
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background: #f9fafb;
            padding: 30px;
            border: 1px solid #e5e7eb;
        }}
        .button {{
            display: inline-block;
            background: #2563eb;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 14px;
        }}
        .warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 12px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>

            <p>You have requested to reset your password for <strong>{settings.APP_NAME}</strong>.</p>

            <p>Click the button below to reset your password:</p>

            <center>
                <a href="{reset_link}" class="button">Reset Password</a>
            </center>

            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background: white; padding: 10px; border: 1px solid #ddd;">
                {reset_link}
            </p>

            <div class="warning">
                <strong>⏰ Important:</strong> This link will expire in 24 hours.
            </div>

            <p>If you did not request this password reset, please ignore this email or contact support if you have concerns.</p>

            <p>Best regards,<br>
            <strong>{settings.APP_NAME} Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply.</p>
            <p>&copy; 2026 {settings.APP_NAME}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(to_email, subject, body_text, body_html)

    def send_password_changed_notification(
        self,
        to_email: str,
        username: str
    ) -> bool:
        """
        Send notification that password was changed

        Args:
            to_email: User's email address
            username: User's username

        Returns:
            bool: True if email sent successfully
        """
        subject = f"{settings.APP_NAME} - Password Changed"

        body_text = f"""
Hello {username},

Your password for {settings.APP_NAME} has been successfully changed.

If you did not make this change, please contact support immediately.

Best regards,
{settings.APP_NAME} Team
"""

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background: #f9fafb;
            padding: 30px;
            border: 1px solid #e5e7eb;
        }}
        .alert {{
            background: #fee2e2;
            border-left: 4px solid #ef4444;
            padding: 12px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Password Changed</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>

            <p>Your password for <strong>{settings.APP_NAME}</strong> has been successfully changed.</p>

            <div class="alert">
                <strong>⚠️ Security Notice:</strong> If you did not make this change, please contact support immediately.
            </div>

            <p>Best regards,<br>
            <strong>{settings.APP_NAME} Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply.</p>
            <p>&copy; 2026 {settings.APP_NAME}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(to_email, subject, body_text, body_html)

    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(
            self.smtp_host and
            self.smtp_port and
            self.smtp_from
        )


# Singleton instance
email_service = EmailService()
