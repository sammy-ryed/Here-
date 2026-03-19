"""
Email service for sending registration tokens and notifications.
Uses SMTP to send emails to student emails.
"""

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with registration tokens."""

    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.sender_email = os.environ.get('SENDER_EMAIL', 'se6334@srmist.edu.in')
        self.sender_password = os.environ.get('EMAIL_PASSWORD', '')
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.app_name = 'Face Recognition Attendance System'
        
        # Log configuration status (but not password)
        logger.info(f"📧 EmailService initialized: {self.sender_email} via {self.smtp_server}:{self.smtp_port}")
        
        if not self.sender_password:
            logger.warning("⚠️ EMAIL_PASSWORD not set in .env - emails will fail to send")

    def test_connection(self) -> bool:
        """Test if email configuration is valid."""
        try:
            logger.info(f"Testing SMTP connection to {self.smtp_server}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            logger.info("✅ SMTP connection test successful!")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ SMTP Authentication failed - check EMAIL_PASSWORD and ensure it's an App Password for Gmail")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    def send_registration_token(self, student_email: str, student_name: str, token: str, deployment_url: str = None) -> bool:
        """
        Send a registration token to a student via email.
        
        Args:
            student_email: Email address of the student
            student_name: Name of the student
            token: Registration token (unique identifier)
            deployment_url: Base URL of the deployed application (e.g., from Vercel)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not deployment_url:
            deployment_url = os.environ.get('DEPLOYMENT_URL', 'http://localhost:3000')

        # Create the registration link
        registration_link = f"{deployment_url}/self-register/{token}"

        # Create email content
        subject = f"Registration Link - {self.app_name}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #2563eb;">Welcome to {self.app_name}!</h2>
                    
                    <p>Hello <strong>{student_name}</strong>,</p>
                    
                    <p>Your registration link is ready. Click the button below to complete your profile and submit your photos for face recognition.</p>
                    
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="{registration_link}" style="display: inline-block; padding: 12px 30px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">
                            Complete Your Registration
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px;">
                        <a href="{registration_link}" style="color: #2563eb; text-decoration: none;">
                            {registration_link}
                        </a>
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        <strong>Important:</strong> This link will expire in 7 days. Please complete your registration before the expiration date.
                    </p>
                    
                    <p style="font-size: 12px; color: #666;">
                        If you did not request this registration link or have any questions, please contact your administrator.
                    </p>
                </div>
            </body>
        </html>
        """

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = student_email

            # Attach HTML content
            message.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                logger.debug(f"Logging in as {self.sender_email}...")
                server.login(self.sender_email, self.sender_password)
                logger.debug(f"Sending email to {student_email}...")
                server.send_message(message)

            logger.info(f"✅ Registration email sent to {student_email} ({student_name})")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed to {student_email}: {str(e)}")
            logger.error("   Double-check EMAIL_PASSWORD is a Gmail App Password, not your regular password")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error sending to {student_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email to {student_email}: {type(e).__name__}: {str(e)}", exc_info=True)
            return False

    def send_bulk_registration_emails(self, students: list, deployment_url: str = None) -> dict:
        """
        Send registration emails to multiple students.
        
        Args:
            students: List of dicts with 'email', 'name', and 'token' keys
            deployment_url: Base URL of the deployed application
        
        Returns:
            Dict with 'sent', 'failed', and 'failed_emails' counts
        """
        sent = 0
        failed = 0
        failed_list = []

        for student in students:
            email = student.get('email')
            name = student.get('name')
            token = student.get('token')

            if not email or not token:
                logger.warning(f"Skipping student: missing email or token")
                failed += 1
                failed_list.append({'name': name, 'reason': 'Missing email or token'})
                continue

            if self.send_registration_token(email, name, token, deployment_url):
                sent += 1
            else:
                failed += 1
                failed_list.append({'email': email, 'name': name, 'reason': 'SMTP error'})

        logger.info(f"Bulk email summary: {sent} sent, {failed} failed")
        return {
            'sent': sent,
            'failed': failed,
            'failed_emails': failed_list
        }
