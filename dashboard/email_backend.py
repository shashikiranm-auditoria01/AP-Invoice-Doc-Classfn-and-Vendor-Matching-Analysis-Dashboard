"""
Email Sender Backend — adapted from the annotation & insights tool's working Gmail-SMTP
sender, made SMTP-configurable so it can be tested end-to-end against a local SMTP server
(no real Gmail credentials needed for testing).

Run:
    pip3 install flask flask-cors
    python3 email_backend.py            # Gmail (prod): smtp.gmail.com:587 + STARTTLS
Test locally (no Gmail):
    MAIL_SMTP_HOST=localhost MAIL_SMTP_PORT=8025 MAIL_STARTTLS=false python3 email_backend.py

Endpoints (same shapes as the source tool):
    GET  /api/health
    POST /api/send_email          { recipient_email, sender_email, sender_password,
                                     email_subject, email_body, file:{name, data(base64)} }
    POST /api/email/send-simple   { sender_email, app_password, recipient, subject, body,
                                     attachments:[{name, base64Data, mimeType}] }   (HelpDesk bulk)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib, os, base64, traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)
CORS(app)

SMTP_HOST = os.environ.get('MAIL_SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('MAIL_SMTP_PORT', '587'))
USE_STARTTLS = os.environ.get('MAIL_STARTTLS', 'true').lower() != 'false'
SKIP_LOGIN = os.environ.get('MAIL_SKIP_LOGIN', 'false').lower() == 'true'  # for testing vs a no-auth local SMTP
BACKEND_PORT = int(os.environ.get('MAIL_BACKEND_PORT', '5001'))


def _smtp_send(sender, password, recipient, msg):
    """Open the (configurable) SMTP server, optionally STARTTLS + login, send, close.
    Login is skipped when no password is given — so a local test SMTP works without auth."""
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    try:
        if USE_STARTTLS:
            server.starttls()
        if password and not SKIP_LOGIN:
            server.login(sender, password)
        server.sendmail(sender, [r.strip() for r in recipient.split(',') if r.strip()], msg.as_string())
    finally:
        try: server.quit()
        except Exception: pass


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'smtp_host': SMTP_HOST, 'smtp_port': SMTP_PORT, 'starttls': USE_STARTTLS})


@app.route('/api/send_email', methods=['POST'])
def send_single_email():
    """Single email with one PDF attachment (AP Invoice mode)."""
    try:
        data = request.get_json(force=True) or {}
        recipient_email = data.get('recipient_email', '').strip()
        sender_email = data.get('sender_email', '').strip()
        sender_password = data.get('sender_password', '')
        email_subject = data.get('email_subject', 'Document Delivery')
        email_body = data.get('email_body', 'Please find the attached document.')
        file_info = data.get('file', {}) or {}

        if not recipient_email or not sender_email:
            return jsonify({'success': False, 'error': 'Missing sender or recipient'}), 400

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = email_subject
        msg.attach(MIMEText(email_body, 'plain'))

        filename = file_info.get('name')
        file_b64 = file_info.get('data', '')
        if file_b64:
            try:
                file_bytes = base64.b64decode(file_b64)
            except Exception:
                return jsonify({'success': False, 'error': f'Invalid base64 for {filename}'}), 400
            part = MIMEBase('application', 'pdf')
            part.set_payload(file_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename or "document.pdf"}"')
            msg.attach(part)

        try:
            _smtp_send(sender_email, sender_password, recipient_email, msg)
        except smtplib.SMTPAuthenticationError:
            return jsonify({'success': False, 'error': 'Authentication failed. Use a Gmail App Password.'}), 401
        except Exception as e:
            return jsonify({'success': False, 'file': filename, 'status': 'failed', 'error': str(e)}), 500

        return jsonify({'success': True, 'file': filename, 'status': 'sent', 'message': 'Email sent successfully'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route('/api/email/send-simple', methods=['POST'])
def send_simple_email():
    """Email with any number of attachments (HelpDesk bulk mode)."""
    try:
        data = request.get_json(force=True) or {}
        sender = data.get('sender_email', '').strip()
        password = data.get('app_password', '').strip()
        recipient = data.get('recipient', '').strip()
        subject = data.get('subject', 'No Subject')
        body = data.get('body', '')
        attachments = data.get('attachments', []) or []

        if not sender or not recipient:
            return jsonify({'success': False, 'error': 'Missing sender or recipient'}), 200

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        for att in attachments:
            name = att.get('name', 'document.pdf')
            b64 = att.get('base64Data', '')
            if not b64:
                continue
            try:
                file_bytes = base64.b64decode(b64)
                mime = att.get('mimeType') or 'application/pdf'
                main, _, sub = mime.partition('/')
                part = MIMEBase(main, sub or 'octet-stream')
                part.set_payload(file_bytes)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{name}"')
                msg.attach(part)
            except Exception as att_err:
                print(f'  Failed to attach {name}: {att_err}')

        try:
            _smtp_send(sender, password, recipient, msg)
        except smtplib.SMTPAuthenticationError:
            return jsonify({'success': False, 'error': 'Gmail authentication failed. Use an App Password.'}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 200

        return jsonify({'success': True, 'attachments_sent': len(attachments)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 200


if __name__ == '__main__':
    print(f'Email backend on http://localhost:{BACKEND_PORT}  (SMTP {SMTP_HOST}:{SMTP_PORT}, STARTTLS={USE_STARTTLS})')
    app.run(host='0.0.0.0', port=BACKEND_PORT, debug=False)
