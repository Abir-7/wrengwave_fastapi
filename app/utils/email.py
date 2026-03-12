import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings

# ─── Core sender ───────────────────────────────────────────
async def _send_email(to: str, subject: str, html: str):
    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.APP_NAME} <{settings.EMAIL_USER}>"
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))
    print(settings.EMAIL_USER, settings.EMAIL_PASS)
    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_SERVER,
        port=settings.SMTP_PORT,
        start_tls=True,
        username=settings.EMAIL_USER,
        password=settings.EMAIL_PASS,
    )

# ─── Template ──────────────────────────────────────────────
def _build_template(app_name: str, title: str, message: str, code: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 32px; border: 1px solid #eee; border-radius: 8px;">
        <h2 style="color: #333;">{app_name}</h2>
        <h3 style="color: #555;">{title}</h3>
        <p style="color: #666;">{message}</p>
        <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px; text-align: center;
                    padding: 24px; background: #f5f5f5; border-radius: 8px; margin: 24px 0;">
            {code}
        </div>
        <p style="color: #999; font-size: 12px;">This code expires in 10 minutes. If you didn't request this, ignore this email.</p>
    </div>
    """

# ─── Public functions ───────────────────────────────────────
async def send_verification_email(to: str, code: str):
    html = _build_template(
        app_name=settings.APP_NAME,
        title="Verify your email",
        message="Use the code below to verify your email address.",
        code=code,
    )
    await _send_email(to, subject=f"{settings.APP_NAME} - Email Verification", html=html)


async def send_password_reset_email(to: str, code: str):
    html = _build_template(
        app_name=settings.APP_NAME,
        title="Reset your password",
        message="Use the code below to reset your password.",
        code=code,
    )
    await _send_email(to, subject=f"{settings.APP_NAME} - Password Reset", html=html)

async def resend_code_email(to: str, code: str):
    html = _build_template(
        app_name=settings.APP_NAME,
        title="New Verification Code",
        message="Use the code below to verify.",
        code=code,
    )
    await _send_email(to, subject=f"{settings.APP_NAME} - New Verification Code", html=html)