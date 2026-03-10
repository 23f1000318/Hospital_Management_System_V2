"""
Email Utility Module for Hospital Management System
Handles sending emails via SMTP (configured for MailHog testing)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def send_email(to_email, subject, body, html_body=None):
    """
    Send an email using SMTP configuration from Flask app config.
    Configured for MailHog by default (localhost:1025).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get SMTP configuration from app config
        smtp_host = current_app.config.get('SMTP_HOST', 'localhost')
        smtp_port = current_app.config.get('SMTP_PORT', 1025)
        smtp_user = current_app.config.get('SMTP_USER')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        sender_email = current_app.config.get('SENDER_EMAIL', 'noreply@hospital.com')
        use_tls = current_app.config.get('SMTP_USE_TLS', False)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_email
        
        # Attach plain text body
        part1 = MIMEText(body, 'plain')
        msg.attach(part1)
        
        # Attach HTML body if provided
        if html_body:
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
        
        # Connect and send
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        
        print(f"[EMAIL SENT] To: {to_email}, Subject: {subject}")
        return True
        
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {to_email}: {str(e)}")
        return False


def send_appointment_reminder(patient_name, patient_email, doctor_name, department, 
                               appointment_date, appointment_time):
    """
    Send appointment reminder email to a patient.
    """
    subject = f"Appointment Reminder - {appointment_date}"
    
    # Plain text body
    body = f"""
Dear {patient_name},

This is a friendly reminder about your upcoming appointment at our hospital.

APPOINTMENT DETAILS:
--------------------
Date: {appointment_date}
Time: {appointment_time}
Doctor: Dr. {doctor_name}
Department: {department}

Please arrive 15 minutes before your scheduled time.
Don't forget to bring your ID and any relevant medical records.

If you need to reschedule or cancel, please do so through our portal.

Best regards,
Hospital Management System
"""

    # HTML body
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #0d6efd; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
        .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #0d6efd; }}
        .detail-row {{ margin: 10px 0; }}
        .label {{ color: #6c757d; font-size: 14px; }}
        .value {{ font-weight: bold; font-size: 16px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">Appointment Reminder</h1>
        </div>
        <div class="content">
            <p>Dear <strong>{patient_name}</strong>,</p>
            <p>This is a friendly reminder about your upcoming appointment.</p>
            
            <div class="details">
                <h3 style="margin-top: 0; color: #0d6efd;">Appointment Details</h3>
                <div class="detail-row">
                    <span class="label">Date:</span><br>
                    <span class="value">{appointment_date}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span><br>
                    <span class="value">{appointment_time}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Doctor:</span><br>
                    <span class="value">Dr. {doctor_name}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Department:</span><br>
                    <span class="value">{department}</span>
                </div>
            </div>
            
            <p><strong>Please remember to:</strong></p>
            <ul>
                <li>Arrive 15 minutes before your scheduled time</li>
                <li>Bring your ID and any relevant medical records</li>
            </ul>
            
            <p>Best regards,<br><strong>Hospital Management System</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(patient_email, subject, body, html_body)


def send_monthly_report_email(doctor_name, doctor_email, month_name, report_html):
    """
    Send monthly activity report to a doctor.
    """
    subject = f"Monthly Activity Report - {month_name}"
    
    plain_text = f"""
Monthly Activity Report - {month_name}

Dear Dr. {doctor_name},

Please find your monthly activity report attached.

Best regards,
Hospital Management System
"""

    return send_email(doctor_email, subject, plain_text, report_html)


def send_export_notification(user_name, user_email, filename, record_count):
    """
    Send notification when CSV export is complete.
    """
    subject = "Your Treatment History Export is Ready"
    
    plain_text = f"""
Dear {user_name},

Your treatment history export has been completed!

Export Details:
- File: {filename}
- Records: {record_count}

You can download the file from your Patient Dashboard.

Best regards,
Hospital Management System
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
        .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745; }}
        .footer {{ text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">Export Complete!</h1>
        </div>
        <div class="content">
            <p>Dear <strong>{user_name}</strong>,</p>
            <p>Your treatment history export has been completed!</p>
            
            <div class="details">
                <h3 style="margin-top: 0; color: #28a745;">Export Details</h3>
                <p><strong>File:</strong> {filename}</p>
                <p><strong>Records Exported:</strong> {record_count}</p>
            </div>
            
            <p>You can download your file from the Patient Dashboard.</p>
            
            <p>Best regards,<br><strong>Hospital Management System</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(user_email, subject, plain_text, html_body)
