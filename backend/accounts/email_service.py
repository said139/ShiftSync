import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)


def _build_html_wrapper(title: str, content_html: str, action_url: str = None, action_label: str = None) -> str:
    """Renders a responsive, Kenya Airways branded email template."""
    action_button_html = ""
    if action_url and action_label:
        action_button_html = f"""
        <div style="margin: 28px 0 16px 0; text-align: center;">
            <a href="{action_url}" style="background-color: #c8102e; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: 700; font-size: 14px; display: inline-block; letter-spacing: 0.02em;">
                {action_label} &rarr;
            </a>
        </div>
        <p style="font-size: 11px; color: #64748b; text-align: center; margin-top: 10px;">
            If the button doesn't work, copy and paste this link into your browser:<br/>
            <a href="{action_url}" style="color: #c8102e; word-break: break-all;">{action_url}</a>
        </p>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; color: #1e293b;">
    <div style="max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
        <!-- Kenya Airways Top Livery Banner -->
        <div style="display: flex; height: 5px;">
            <div style="flex: 5; background-color: #c8102e;"></div>
            <div style="flex: 2; background-color: #e5a823;"></div>
            <div style="flex: 2; background-color: #007a3d;"></div>
        </div>
        
        <!-- Header -->
        <div style="padding: 24px 28px; background-color: #0f172a; color: #ffffff; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span style="background: rgba(200, 16, 46, 0.25); color: #fca5a5; font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.06em; text-transform: uppercase;">
                    Kenya Airways &bull; JKIA Hub
                </span>
                <h1 style="margin: 6px 0 0 0; font-size: 18px; font-weight: 800; letter-spacing: -0.01em;">
                    ShiftSync Operational Portal
                </h1>
            </div>
            <div style="font-size: 12px; color: #e5a823; font-weight: 700; text-align: right;">
                FLIGHT OPS &amp; LINE MAINT
            </div>
        </div>

        <!-- Body Content -->
        <div style="padding: 28px 28px 20px 28px; font-size: 14px; line-height: 1.6; color: #334155;">
            {content_html}
            {action_button_html}
        </div>

        <!-- Footer -->
        <div style="padding: 16px 28px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center;">
            <p style="margin: 0 0 4px 0;">This is an automated operational notification from ShiftSync Handover System.</p>
            <p style="margin: 0;">Kenya Airways Flight Operations &amp; Line Maintenance &bull; Jomo Kenyatta International Airport, Nairobi</p>
        </div>
    </div>
</body>
</html>"""


def send_password_reset_email(user, reset_token: str) -> bool:
    """Sends a password recovery link to the user via configured SMTP backend."""
    frontend_url = getattr(settings, "FRONTEND_URL", "http://127.0.0.1:5173")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    subject = "[ShiftSync] Password Reset Verification Request"

    plain_content = f"""Hello {user.full_name},

A password reset request was received for your ShiftSync account ({user.email}).

Please open the following link in your browser to choose a new password:
{reset_url}

This link is valid for 1 hour. If you did not request this reset, you can safely ignore this email.

— Kenya Airways ShiftSync Operations Hub
"""

    html_body = f"""
    <h2 style="font-size: 17px; font-weight: 700; color: #0f172a; margin-top: 0;">Password Recovery Request</h2>
    <p>Hello <strong>{user.full_name}</strong>,</p>
    <p>A password reset request was submitted for your ShiftSync account (<strong>{user.email}</strong>, Staff ID: <code>{user.employee_id or 'N/A'}</code>).</p>
    <p>Click the button below to verify your identity and set a new secure password. This verification token is time-limited and expires in <strong>1 hour</strong>.</p>
    """

    html_content = _build_html_wrapper(
        title=subject,
        content_html=html_body,
        action_url=reset_url,
        action_label="Reset Your Password",
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Password reset email dispatched to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch password reset email to {user.email}: {e}")
        return False


def send_handover_submitted_email(handover) -> bool:
    """Dispatches an email alert to the designated incoming worker when a handover report is submitted."""
    incoming_worker = handover.designated_incoming_worker
    if not incoming_worker or not incoming_worker.email:
        return False

    frontend_url = getattr(settings, "FRONTEND_URL", "http://127.0.0.1:5173")
    review_url = f"{frontend_url}/handovers/{handover.id}/acknowledge"
    shift = handover.shift
    submitting_worker = handover.submitting_worker

    subject = f"[Action Required] Shift Handover Submitted: {handover.report_code} ({getattr(shift, 'name', 'Shift')})"

    task_count = handover.tasks.count()
    unresolved_count = handover.tasks.exclude(status="COMPLETED").count()
    has_incident_str = "YES (Requires Immediate Attention)" if handover.has_safety_incident else "None reported"

    plain_content = f"""Hello {incoming_worker.full_name},

{submitting_worker.full_name} has formally submitted the shift handover report {handover.report_code} for:
Shift: {getattr(shift, 'name', 'Shift')} ({shift.shift_date})
Department: {shift.department}

Summary of Custody Transfer:
- Total Tasks Logged: {task_count}
- Unresolved / In-Progress Tasks: {unresolved_count}
- Safety Issues / Incidents: {has_incident_str}

Please review and formally acknowledge receipt of operational responsibility:
{review_url}

— Kenya Airways ShiftSync Operations Hub
"""

    html_body = f"""
    <div style="background-color: #fee2e2; border-left: 4px solid #c8102e; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px;">
        <strong style="color: #991b1b; font-size: 13px;">ACTION REQUIRED: Shift Handover Awaiting Your Acknowledgment</strong>
    </div>
    <p>Hello <strong>{incoming_worker.full_name}</strong>,</p>
    <p>Outgoing worker <strong>{submitting_worker.full_name}</strong> has formally submitted the operational handover report for your upcoming shift.</p>
    
    <table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px;">
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Report Code:</td>
            <td style="padding: 8px 0; font-weight: 700; color: #0f172a;">{handover.report_code}</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Shift &amp; Window:</td>
            <td style="padding: 8px 0; color: #0f172a;">{getattr(shift, 'name', 'Shift')} ({shift.shift_date} &bull; {shift.start_time.strftime('%H:%M')} – {shift.end_time.strftime('%H:%M')})</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Total Tasks:</td>
            <td style="padding: 8px 0; color: #0f172a;">{task_count} recorded ({unresolved_count} carried forward)</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Safety Incident:</td>
            <td style="padding: 8px 0; color: {'#c8102e' if handover.has_safety_incident else '#007a3d'}; font-weight: 700;">{has_incident_str}</td>
        </tr>
    </table>

    <p>Please review all tasks, equipment statuses, and contextual logs, and submit your explicit custody sign-off.</p>
    """

    html_content = _build_html_wrapper(
        title=subject,
        content_html=html_body,
        action_url=review_url,
        action_label="Review & Acknowledge Handover",
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[incoming_worker.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Handover submission email dispatched to {incoming_worker.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch handover submission email to {incoming_worker.email}: {e}")
        return False


def send_handover_acknowledged_email(handover) -> bool:
    """Dispatches an email alert to the outgoing worker when their handover is formally signed off."""
    submitting_worker = handover.submitting_worker
    acknowledging_worker = handover.designated_incoming_worker
    if not submitting_worker or not submitting_worker.email:
        return False

    frontend_url = getattr(settings, "FRONTEND_URL", "http://127.0.0.1:5173")
    detail_url = f"{frontend_url}/handovers/{handover.id}"
    shift = handover.shift
    shift_name = getattr(shift, "name", "Shift")

    subject = f"[Confirmed] Handover Acknowledged: {handover.report_code} ({shift_name})"

    plain_content = f"""Hello {submitting_worker.full_name},

Your handover report {handover.report_code} has been formally acknowledged by {acknowledging_worker.full_name} on {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}.

Operational custody for shift '{shift_name}' has been successfully transferred.

View Handover Record:
{detail_url}

— Kenya Airways ShiftSync Operations Hub
"""

    html_body = f"""
    <div style="background-color: #dcfce7; border-left: 4px solid #007a3d; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px;">
        <strong style="color: #166534; font-size: 13px;">CONFIRMED: Handover Formally Acknowledged</strong>
    </div>
    <p>Hello <strong>{submitting_worker.full_name}</strong>,</p>
    <p>Incoming worker <strong>{acknowledging_worker.full_name}</strong> has formally reviewed and signed off on handover report <strong>{handover.report_code}</strong>.</p>
    <p>Operational custody has been officially recorded in the audit trail at <strong>{timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</strong>.</p>
    """

    html_content = _build_html_wrapper(
        title=subject,
        content_html=html_body,
        action_url=detail_url,
        action_label="View Handover Record",
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[submitting_worker.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Handover acknowledgment email dispatched to {submitting_worker.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch handover acknowledgment email to {submitting_worker.email}: {e}")
        return False


def send_smtp_diagnostic_test(recipient_email: str, actor_name: str = "Administrator") -> dict:
    """Tests the configured SMTP server connection and sends a diagnostic verification email."""
    subject = "[ShiftSync] SMTP Delivery Diagnostics Test"
    frontend_url = getattr(settings, "FRONTEND_URL", "http://127.0.0.1:5173")

    html_body = f"""
    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 14px 18px; border-radius: 6px; margin-bottom: 18px;">
        <strong style="color: #15803d; font-size: 14px;">&check; SMTP Channel Active &amp; Verified</strong>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #166534;">
            This test email confirms that ShiftSync's real SMTP delivery pipeline is operational.
        </p>
    </div>
    <p>Triggered by: <strong>{actor_name}</strong> at <code>{timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</code></p>
    <p><strong>Configured Backend:</strong> <code>{settings.EMAIL_BACKEND}</code></p>
    <p><strong>SMTP Host:</strong> <code>{getattr(settings, 'EMAIL_HOST', 'N/A')}:{getattr(settings, 'EMAIL_PORT', 'N/A')}</code></p>
    <p><strong>TLS Active:</strong> <code>{getattr(settings, 'EMAIL_USE_TLS', False)}</code> &bull; <strong>SSL Active:</strong> <code>{getattr(settings, 'EMAIL_USE_SSL', False)}</code></p>
    """

    html_content = _build_html_wrapper(
        title=subject,
        content_html=html_body,
        action_url=frontend_url,
        action_label="Return to ShiftSync Portal",
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=f"SMTP Diagnostic Test from ShiftSync. Sent at {timezone.now()}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return {
            "success": True,
            "recipient": recipient_email,
            "backend": settings.EMAIL_BACKEND,
            "host": getattr(settings, "EMAIL_HOST", "localhost"),
            "port": getattr(settings, "EMAIL_PORT", 587),
            "detail": f"Diagnostic test email successfully dispatched to {recipient_email}.",
        }
    except Exception as e:
        logger.error(f"SMTP Diagnostic Test failed to {recipient_email}: {e}")
        return {
            "success": False,
            "recipient": recipient_email,
            "error": str(e),
            "detail": f"Failed to send email: {e}",
        }
