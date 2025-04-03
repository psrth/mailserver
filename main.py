import time
import logging
from utils.email_client import EmailClient

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info("Logging initialized")

def main():
    # Setup logging
    setup_logging()
    logging.info("Starting email processing service")
    
    # Initialize email client
    logging.info("Initializing email client")
    email_client = EmailClient()
    logging.info("Email client initialized successfully")
    
    while True:
        try:
            # A. Check for new emails
            logging.info("Checking for new emails")
            email_data = email_client.fetch_latest_email()

            # B. Process any new emails
            if email_data:
                logging.info("New email found - starting processing pipeline")
                
                # 1. Extract the data from the email
                logging.info("Step 1: Extracting data from email")
                original_msg, email_body, attachments = email_client.extract_email_data(email_data)
                logging.info(f"Email data extracted.")
                
                # 2. Do some processing with the email
                logging.info("Step 2: Analyzing email content")
                # ----
                # response_text = process_email(original_msg, email_body, attachments)
                # ----
                response_text = "some response text"

                # 3. Send reply email
                logging.info("Step 3: Sending reply")
                email_client.send_reply(original_msg, response_text)
                logging.info("Reply sent successfully")
            else:
                logging.info("No new emails found")

            # C. Sleep for 60 seconds
            logging.info("Sleeping for 60 seconds before next check")
            time.sleep(60)
            
        except Exception as e:
            logging.error(f"Error in main processing loop: {e}", exc_info=True)
            logging.info("Continuing to next iteration after error")
            time.sleep(60)


if __name__ == "__main__":
    main()
