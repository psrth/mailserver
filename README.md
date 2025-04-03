# mailserver

a python-based email processing server that connects to an inbox via IMAP/SMTP, extracts the email contents, does some processing and then sends a reply.

## Setup

### Pre-Configuration

1. **Clone the repository**

```bash
git clone https://github.com/psrth/mailserver
cd mailserver
```

2. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:

```
<!-- email config -->
EMAIL_ADDRESS=your-email@email.com
EMAIL_PASSWORD=email-app-password (this is not the email password!)

<!-- llm provider keys -->
OPENAI_API_KEY=your-openai-key (arguably smarter; better for analysis / content)
GEMINI_API_KEY=your-gemini-key (long context window; better for attachments)

<!-- langfuse tracing -->
LANGFUSE_PUBLIC_KEY=your-langfuse-key
LANGFUSE_SECRET_KEY=your-langfuse-secret
LANGFUSE_HOST=your-langfuse-host
```

### Running the server locally

1. **Create and activate virtual environment**

```bash
python3 -m venv env
source env/bin/activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Run the server**

```bash
python main.py
```

The server will start checking for new emails every 60 seconds. Use Ctrl+C to stop the server.

### Running the server on AWS

1. **SSH into EC2 Instance**

```bash
ssh -i path/to/your-key.pem ec2-user@your-ec2-instance
```

2. **Setup on EC2**

```bash
git clone <repository-url>
cd <repository_name>

python3 -m venv env
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure systemd service**
   First, update the variables in the systemd service in `devops/email_processor.service`. Then,

```bash
# Copy service file
sudo cp devops/email_processor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable email_processor
sudo systemctl start email_processor
```

4. **Service Management Commands**

```bash
# Check service status
sudo systemctl status email_processor

# View logs
sudo journalctl -u email_processor -f

# Stop service
sudo systemctl stop email_processor

# Restart service
sudo systemctl restart email_processor
```

## Agents

You should be able to add agents to the `agents` directory. You can expose these as single functions or build an orchestration pipeline. These should be abstracted into a:

```python
def process_email(original_msg, email_body, attachments):
   # some processing
   return response_text
```

## Notes

- The server checks for new emails every 60 seconds by default. You can change this in `main.py`.
- Email passwords are actually _[app passwords](https://support.google.com/mail/answer/185833?hl=en)_.
- A pretty easy oversight is running the server locally while leaving it up on AWS as well. Emails get marked as read by whoever processes it first, so this starts to become a lot less deterministic.
- By default, all originally CC'ed users are copied on the reply. You can change this in `utils/email_client`
