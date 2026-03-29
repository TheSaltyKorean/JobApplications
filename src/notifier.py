"""
Desktop and email notifications.
Sends Windows toast notifications and emails to randy.walker@live.com.
"""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

_settings = {}

def load_settings(settings: dict):
    global _settings
    _settings = settings


# ─────────────────────────────────────────────────────────
# DESKTOP NOTIFICATION (Windows toast)
# ─────────────────────────────────────────────────────────

def notify_desktop(title: str, message: str, app_id: str = 'JobApplicationBot'):
    """Send a Windows 10/11 toast notification."""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title,
            message[:200],
            icon_path=None,
            duration=8,
            threaded=True
        )
        return True
    except ImportError:
        pass

    # Fallback: plyer
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message[:200],
            app_name=app_id,
            timeout=8,
        )
        return True
    except Exception as e:
        logger.debug(f"Desktop notification failed: {e}")

    # Fallback: Windows PowerShell balloon
    try:
        import subprocess
        # Sanitize inputs to prevent PowerShell injection
        safe_title = title.replace('"', "'").replace('`', '').replace('$', '')[:100]
        safe_message = message.replace('"', "'").replace('`', '').replace('$', '')[:150]
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.Visible = $true
        $notify.ShowBalloonTip(8000, "{safe_title}", "{safe_message}", [System.Windows.Forms.ToolTipIcon]::Info)
        Start-Sleep -Seconds 9
        $notify.Dispose()
        '''
        subprocess.Popen(
            ['powershell', '-WindowStyle', 'Hidden', '-Command', ps_script],
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
        return True
    except Exception as e:
        logger.debug(f"PowerShell notification failed: {e}")

    return False


# ─────────────────────────────────────────────────────────
# EMAIL NOTIFICATION
# ─────────────────────────────────────────────────────────

def send_email(subject: str, body: str, to_email: str = None):
    """Send email notification to Randy."""
    smtp_host = _settings.get('smtp_host', '')
    smtp_port = int(_settings.get('smtp_port', 587))
    smtp_user = _settings.get('smtp_user', '')
    smtp_pass = _settings.get('smtp_pass', '')
    from_email = smtp_user or 'randy.walker@live.com'
    to = to_email or 'randy.walker@live.com'

    if not smtp_host or not smtp_user or not smtp_pass:
        logger.info("Email not configured – skipping email notification")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[JobBot] {subject}'
        msg['From'] = from_email
        msg['To'] = to

        html_body = f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #2c5282;">🤖 Job Application Bot</h2>
        <p>{body.replace(chr(10), '<br>')}</p>
        <hr>
        <p style="color: #718096; font-size: 12px;">
            <a href="http://localhost:5000">Open Dashboard</a>
        </p>
        </body></html>
        """
        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to, msg.as_string())

        logger.info(f"Email sent: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


# ─────────────────────────────────────────────────────────
# COMBINED NOTIFY
# ─────────────────────────────────────────────────────────

def notify(title: str, message: str, send_mail: bool = True):
    """Send both desktop and email notifications."""
    notify_desktop(title, message)
    if send_mail and _settings.get('email_notifications', 'true').lower() == 'true':
        send_email(title, message)


# ─────────────────────────────────────────────────────────
# SPECIFIC NOTIFICATIONS
# ─────────────────────────────────────────────────────────

def notify_jobs_found(count: int, platform: str):
    notify(
        f"New Jobs Found",
        f"Found {count} new management job(s) on {platform.title()}.\n"
        f"Open the dashboard to review and queue applications.\n"
        f"http://localhost:5000/jobs?status=new"
    )


def notify_applied(title: str, company: str):
    notify(
        f"Application Submitted ✓",
        f"Successfully applied to: {title}\nCompany: {company}"
    )


def notify_failed(title: str, company: str, reason: str):
    notify(
        f"Application Failed ✗",
        f"Could not apply to: {title}\nCompany: {company}\nReason: {reason}"
    )


def notify_needs_input(question: str, job_title: str):
    """Called when Claude needs input via clipboard method."""
    notify(
        "Action Required – Answer Needed",
        f"Job: {job_title}\n\nQuestion: {question[:150]}\n\n"
        f"1. Claude.ai is opening in your browser\n"
        f"2. Paste (Ctrl+V) – the prompt is in your clipboard\n"
        f"3. Copy Claude's answer\n"
        f"4. Paste it at: http://localhost:5000/answer"
    )


def notify_question_ready(job_title: str):
    """Notify that a pending question is ready for clipboard method."""
    notify_desktop(
        "Paste Prompt into Claude.ai",
        f"Application for: {job_title}\n"
        f"Prompt copied to clipboard!\n"
        f"Paste into Claude.ai, copy answer, go to http://localhost:5000/answer"
    )
