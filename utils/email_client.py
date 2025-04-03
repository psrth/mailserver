import imaplib
import email
import smtplib
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import getaddresses
from utils.config import IMAP_SERVER, SMTP_SERVER, EMAIL_ADDRESS, EMAIL_PASSWORD

logger = logging.getLogger(__name__)

class EmailClient:
    def __init__(self):
        self.mail = None
        self.connect()

    def connect(self):
        """Establish IMAP connection with retries."""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                if self.mail:
                    try:
                        self.mail.close()
                        self.mail.logout()
                    except:
                        pass
                
                self.mail = imaplib.IMAP4_SSL(IMAP_SERVER)
                self.mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                logger.info("Successfully initialized IMAP connection")
                return
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

    def ensure_connection(self):
        """Ensure IMAP connection is alive, reconnect if needed."""
        try:
            # Try to check connection status with a simple NOOP command
            self.mail.noop()
        except Exception as e:
            logger.warning(f"Connection check failed: {e}. Attempting to reconnect...")
            self.connect()

    def _parse_email_addresses(self, addr_string: str) -> list:
        """Safely parse and validate email addresses."""
        if not addr_string:
            return []
        try:
            # getaddresses handles multiple addresses and various formats
            addresses = getaddresses([addr_string])
            # Filter out invalid addresses and extract email part
            valid_addresses = [email for name, email in addresses if '@' in email]
            logger.debug(f"Parsed {len(valid_addresses)} valid email addresses from: {addr_string}")
            return valid_addresses
        except Exception as e:
            logger.warning(f"Error parsing email addresses from '{addr_string}': {e}")
            return []

    def fetch_latest_email(self):
        """Fetch latest unread email with connection retry logic."""
        try:
            self.ensure_connection()
            
            self.mail.select("inbox")
            status, messages = self.mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            if not email_ids:
                logger.debug("No unread emails found")
                return None
                
            latest_email_id = email_ids[-1]
            status, data = self.mail.fetch(latest_email_id, "(RFC822)")
            
            if status != 'OK':
                raise Exception(f"Failed to fetch email: {status}")
                
            msg = email.message_from_bytes(data[0][1])

            # Mark as read
            self.mail.store(latest_email_id, '+FLAGS', '\\Seen')
            
            # Safely get sender
            from_addr = self._parse_email_addresses(msg['From'])
            if from_addr:
                logger.info(f"Processing email from: {from_addr[0]}")
            else:
                logger.warning("Could not determine sender address")

            body = ""
            attachments = []
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                content_disposition = str(part.get('Content-Disposition') or '')
                if 'attachment' in content_disposition:
                    attachments.append(part)
                else:
                    if part.get_content_type() == 'text/plain':
                        try:
                            payload = part.get_payload(decode=True)
                            charset = part.get_content_charset() or 'utf-8'
                            body += payload.decode(charset, errors='replace')
                        except Exception as e:
                            logger.error(f"Error decoding email body: {e}")
                            body += "[Error: Could not decode part of the message]"

            logger.info(f"Email processed with {len(attachments)} attachments")
            return msg, body, attachments
            
        except Exception as e:
            logger.error(f"Error fetching email: {e}", exc_info=True)
            # Try to reconnect on next iteration
            self.connect()
            return None

    def extract_email_data(self, email_data):
        """Extract and log data from the email."""
        try:
            logger.info("Extracting email data")
            if not email_data:
                logger.warning("No email data provided to extract_email_data")
                return None, "", []
                
            original_msg, email_body, attachments = email_data
            logger.info(f"Processing email from: {original_msg.get('From', 'Unknown sender')}")
            logger.info(f"Email subject: {original_msg.get('Subject', 'No subject')}")
            logger.info(f"Email body length: {len(email_body)} characters")
            logger.info(f"Number of attachments: {len(attachments)}")
            
            return original_msg, email_body, attachments
        except Exception as e:
            logger.error(f"Error extracting email data: {e}", exc_info=True)
            # Return empty data in case of error to prevent downstream failures
            return {}, "", []

    def send_reply(self, original_msg, response_text):
        """Send a reply with connection retry logic."""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                msg = MIMEMultipart('alternative')
                msg["From"] = EMAIL_ADDRESS
                
                # Safely handle To field
                to_addrs = self._parse_email_addresses(original_msg["From"])
                if not to_addrs:
                    raise ValueError("No valid 'To' address found")
                msg["To"] = ", ".join(to_addrs)
                
                # Safely handle Subject
                subject = original_msg.get("Subject", "").strip() or "No Subject"
                msg["Subject"] = f"Re: {subject}"
                
                # Handle threading headers if available
                message_id = original_msg.get("Message-ID")
                if message_id:
                    msg["In-Reply-To"] = message_id
                    msg["References"] = message_id
                
                # Safely handle CC recipients
                cc_addrs = self._parse_email_addresses(original_msg.get("Cc", ""))
                if cc_addrs:
                    msg["Cc"] = ", ".join(cc_addrs)
                    
                # Create both plain text and HTML versions
                text_part = MIMEText("This is an HTML email. Please use an email client that supports HTML to view this message.", "plain", "utf-8")
                html_part = MIMEText(response_text, "html", "utf-8")

                # Add both parts to the message
                msg.attach(text_part)
                msg.attach(html_part)

                # Collect all recipients
                recipients = to_addrs + cc_addrs
                if not recipients:
                    raise ValueError("No valid recipients found")
                
                logger.info(f"Sending reply to {len(recipients)} recipients")
                
                with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
                    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                    server.sendmail(EMAIL_ADDRESS, recipients, msg.as_string())
                    logger.info("Reply sent successfully")
                    return
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to send email: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
