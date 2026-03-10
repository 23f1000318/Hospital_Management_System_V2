"""
Report Generation Tasks for Hospital Management System
Celery tasks for generating and sending activity reports
"""
import sys
import os

# Ensure backend directory is in Python path for Celery workers
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from celery import shared_task
from datetime import date, datetime, timedelta
from calendar import monthrange
from flask import current_app


@shared_task(ignore_result=False)
def send_monthly_doctor_reports():
    """
    Scheduled task to send monthly activity reports to all doctors.
    
    Runs on the first day of every month and generates a report
    for the previous month's activities.
    
    Returns:
        dict: Summary of reports sent
    """
    # Ensure path is set inside task for forked workers
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    from models import db, Doctor, Appointment, Treatment
    from utils.email_utils import send_email
    
    # For testing/demo: Include current month data
    # In production, change include_current_month to False
    include_current_month = True
    
    today = date.today()
    first_day_current_month = today.replace(day=1)
    
    if include_current_month:
        # Include current month data for testing
        start_date = first_day_current_month
        end_date = today
        month_name = today.strftime('%B %Y')
    else:
        # Previous month only (production behavior)
        last_day_prev_month = first_day_current_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)
        start_date = first_day_prev_month
        end_date = last_day_prev_month
        month_name = last_day_prev_month.strftime('%B %Y')
    
    # Get all active doctors
    doctors = Doctor.query.filter(Doctor.user.has(active=True)).all()
    
    sent_count = 0
    failed_count = 0
    results = []
    
    for doctor in doctors:
        try:
            if not doctor.user or not doctor.user.email:
                results.append({
                    'doctor_id': doctor.id,
                    'status': 'skipped',
                    'reason': 'No email found'
                })
                continue
            
            # Get doctor's appointments for the month (use date objects, not strings)
            appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.date >= start_date,
                Appointment.date <= end_date
            ).all()
            
            # Calculate statistics
            total_appointments = len(appointments)
            completed = [a for a in appointments if a.status == 'completed']
            cancelled = [a for a in appointments if a.status == 'cancelled']
            booked = [a for a in appointments if a.status == 'booked']
            unique_patients = len(set(a.patient_id for a in appointments))
            
            # Get treatments for completed appointments
            treatments_data = []
            diagnosis_count = {}
            
            for apt in completed:
                if apt.treatment:
                    treatment_info = {
                        'date': str(apt.date) if apt.date else 'N/A',
                        'patient_name': apt.patient.user.name if apt.patient and apt.patient.user else 'Unknown',
                        'diagnosis': apt.treatment.diagnosis or 'N/A',
                        'prescription': apt.treatment.prescription or 'N/A',
                        'follow_up': str(apt.treatment.follow_up_date) if apt.treatment.follow_up_date else None
                    }
                    treatments_data.append(treatment_info)
                    
                    # Count diagnoses
                    diag = apt.treatment.diagnosis or 'Unspecified'
                    diagnosis_count[diag] = diagnosis_count.get(diag, 0) + 1
            
            # Generate HTML report
            html_report = generate_doctor_monthly_report_html(
                doctor_name=doctor.user.name,
                department=doctor.department.name if doctor.department else 'General',
                month_name=month_name,
                total_appointments=total_appointments,
                completed_count=len(completed),
                cancelled_count=len(cancelled),
                booked_count=len(booked),
                unique_patients_count=unique_patients,
                treatments_data=treatments_data,
                diagnosis_count=diagnosis_count
            )

            # Plain text summary
            plain_text = f"""
Monthly Activity Report - {month_name}

Dear Dr. {doctor.user.name},

Here is your activity summary for {month_name}:

Total Appointments: {total_appointments}
- Completed: {len(completed)}
- Booked (Pending): {len(booked)}
- Cancelled: {len(cancelled)}
- Unique Patients: {unique_patients}

Treatments Provided: {len(treatments_data)}

Please see the attached HTML report for detailed information.

Best regards,
Hospital Management System
"""
            
            # Send email
            subject = f"Monthly Activity Report - {month_name}"
            success = send_email(
                to_email=doctor.user.email,
                subject=subject,
                body=plain_text,
                html_body=html_report
            )
            
            if success:
                sent_count += 1
                results.append({
                    'doctor_id': doctor.id,
                    'doctor_name': doctor.user.name,
                    'status': 'sent',
                    'appointments': total_appointments
                })
            else:
                failed_count += 1
                results.append({
                    'doctor_id': doctor.id,
                    'status': 'failed'
                })
                
        except Exception as e:
            failed_count += 1
            results.append({
                'doctor_id': doctor.id,
                'status': 'error',
                'error': str(e)
            })
    
    summary = {
        'report_month': month_name,
        'total_doctors': len(doctors),
        'reports_sent': sent_count,
        'reports_failed': failed_count,
        'details': results
    }
    
    current_app.logger.info(f"Monthly report task completed: {summary}")
    
    return summary


def generate_doctor_monthly_report_html(doctor_name, department, month_name,
                                         total_appointments, completed_count,
                                         cancelled_count, booked_count, unique_patients_count,
                                         treatments_data, diagnosis_count):
    """
    Generate HTML content for doctor's monthly activity report.
    """
    
    # Generate diagnosis summary rows
    diagnosis_rows = ""
    for diag, count in sorted(diagnosis_count.items(), key=lambda x: -x[1])[:10]:
        diagnosis_rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{diag}</td>
            <td style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: center;">{count}</td>
        </tr>
        """
    
    if not diagnosis_rows:
        diagnosis_rows = '<tr><td colspan="2" style="padding: 8px; text-align: center; color: #6c757d;">No diagnosis data for this period</td></tr>'
    
    # Generate treatment details rows
    treatment_rows = ""
    for t in treatments_data[:20]:  # Limit to 20 entries
        follow_up_badge = f'<span style="background: #17a2b8; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">Follow-up: {t["follow_up"]}</span>' if t['follow_up'] else ''
        treatment_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{t['date']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{t['patient_name']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{t['diagnosis']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{t['prescription'][:50]}{'...' if len(t['prescription']) > 50 else ''}</td>
            <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{follow_up_badge}</td>
        </tr>
        """
    
    if not treatment_rows:
        treatment_rows = '<tr><td colspan="5" style="padding: 15px; text-align: center; color: #6c757d;">No treatments recorded for this period</td></tr>'
    
    # Calculate completion rate
    completion_rate = round((completed_count / total_appointments * 100), 1) if total_appointments > 0 else 0
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Monthly Activity Report - {month_name}</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #0d6efd 0%, #0056b3 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 28px;">🏥 Monthly Activity Report</h1>
        <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">{month_name}</p>
    </div>
    
    <!-- Doctor Info -->
    <div style="background: white; padding: 25px; border-bottom: 1px solid #dee2e6;">
        <h2 style="margin: 0 0 5px 0; color: #0d6efd;">Dr. {doctor_name}</h2>
        <p style="margin: 0; color: #6c757d; font-size: 16px;">📋 Department: {department}</p>
        <p style="margin: 5px 0 0 0; color: #6c757d; font-size: 14px;">Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    
    <!-- Statistics Cards -->
    <div style="background: white; padding: 25px;">
        <h3 style="margin: 0 0 20px 0; color: #333; border-bottom: 2px solid #0d6efd; padding-bottom: 10px;">📊 Appointment Statistics</h3>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 20%; padding: 15px; text-align: center; background: #e7f1ff; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #0d6efd;">{total_appointments}</div>
                    <div style="color: #6c757d; font-size: 13px;">Total</div>
                </td>
                <td style="width: 20%; padding: 15px; text-align: center; background: #d4edda; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #28a745;">{completed_count}</div>
                    <div style="color: #6c757d; font-size: 13px;">Completed</div>
                </td>
                <td style="width: 20%; padding: 15px; text-align: center; background: #cce5ff; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #004085;">{booked_count}</div>
                    <div style="color: #6c757d; font-size: 13px;">Booked</div>
                </td>
                <td style="width: 20%; padding: 15px; text-align: center; background: #fff3cd; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #856404;">{cancelled_count}</div>
                    <div style="color: #6c757d; font-size: 13px;">Cancelled</div>
                </td>
                <td style="width: 20%; padding: 15px; text-align: center; background: #e2d9f3; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: bold; color: #6f42c1;">{unique_patients_count}</div>
                    <div style="color: #6c757d; font-size: 13px;">Unique Patients</div>
                </td>
            </tr>
        </table>
        
        <!-- Completion Rate Bar -->
        <div style="margin-top: 20px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-weight: 500;">Completion Rate</span>
                <span style="font-weight: bold; color: #28a745;">{completion_rate}%</span>
            </div>
            <div style="background: #e9ecef; border-radius: 10px; height: 20px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #28a745, #20c997); height: 100%; width: {completion_rate}%; border-radius: 10px;"></div>
            </div>
        </div>
    </div>
    
    <!-- Diagnosis Summary -->
    <div style="background: white; padding: 25px; margin-top: 2px;">
        <h3 style="margin: 0 0 20px 0; color: #333; border-bottom: 2px solid #17a2b8; padding-bottom: 10px;">🩺 Diagnosis Summary</h3>
        
        <table style="width: 100%; border-collapse: collapse; background: #f8f9fa; border-radius: 8px; overflow: hidden;">
            <thead>
                <tr style="background: #17a2b8; color: white;">
                    <th style="padding: 12px; text-align: left;">Diagnosis</th>
                    <th style="padding: 12px; text-align: center; width: 100px;">Count</th>
                </tr>
            </thead>
            <tbody>
                {diagnosis_rows}
            </tbody>
        </table>
    </div>
    
    <!-- Treatment Details -->
    <div style="background: white; padding: 25px; margin-top: 2px;">
        <h3 style="margin: 0 0 20px 0; color: #333; border-bottom: 2px solid #28a745; padding-bottom: 10px;">💊 Treatment Details</h3>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; background: #f8f9fa; border-radius: 8px; overflow: hidden; min-width: 700px;">
                <thead>
                    <tr style="background: #28a745; color: white;">
                        <th style="padding: 12px; text-align: left;">Date</th>
                        <th style="padding: 12px; text-align: left;">Patient</th>
                        <th style="padding: 12px; text-align: left;">Diagnosis</th>
                        <th style="padding: 12px; text-align: left;">Prescription</th>
                        <th style="padding: 12px; text-align: left;">Follow-up</th>
                    </tr>
                </thead>
                <tbody>
                    {treatment_rows}
                </tbody>
            </table>
        </div>
        
        {'<p style="color: #6c757d; font-size: 12px; margin-top: 10px;">* Showing first 20 treatments. Total treatments: ' + str(len(treatments_data)) + '</p>' if len(treatments_data) > 20 else ''}
    </div>
    
    <!-- Footer -->
    <div style="background: #343a40; color: white; padding: 20px; border-radius: 0 0 10px 10px; text-align: center;">
        <p style="margin: 0; font-size: 14px;">Thank you for your dedication to patient care.</p>
        <p style="margin: 10px 0 0 0; font-size: 12px; opacity: 0.7;">Hospital Management System | Automated Monthly Report</p>
        <p style="margin: 5px 0 0 0; font-size: 11px; opacity: 0.5;">This is an automated email. Please do not reply.</p>
    </div>
    
</body>
</html>
"""
    
    return html


@shared_task(ignore_result=False)
def send_single_doctor_report(doctor_id, month=None, year=None):
    """
    Generate and send a monthly report for a specific doctor.
    Useful for manual triggers or re-sending reports.
    
    Args:
        doctor_id: ID of the doctor
        month: Month number (1-12), defaults to previous month
        year: Year, defaults to current/previous year
    
    Returns:
        dict: Result of the report generation
    """
    # Ensure path is set inside task for forked workers
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    from models import Doctor, Appointment
    from utils.email_utils import send_email
    
    doctor = Doctor.query.get(doctor_id)
    
    if not doctor:
        return {'status': 'error', 'message': 'Doctor not found'}
    
    if not doctor.user or not doctor.user.email:
        return {'status': 'error', 'message': 'No email found for doctor'}
    
    # Calculate date range
    today = date.today()
    
    if month is None or year is None:
        # Default to previous month
        first_day_current = today.replace(day=1)
        last_day_prev = first_day_current - timedelta(days=1)
        target_month = last_day_prev.month
        target_year = last_day_prev.year
    else:
        target_month = month
        target_year = year
    
    # Get first and last day of target month
    first_day = date(target_year, target_month, 1)
    last_day = date(target_year, target_month, monthrange(target_year, target_month)[1])
    
    month_name = first_day.strftime('%B %Y')
    # Use date objects directly for comparison
    start_date = first_day
    end_date = last_day
    
    # Get appointments
    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date >= start_date,
        Appointment.date <= end_date
    ).all()
    
    total_appointments = len(appointments)
    completed = [a for a in appointments if a.status == 'completed']
    cancelled = [a for a in appointments if a.status == 'cancelled']
    booked = [a for a in appointments if a.status == 'booked']
    unique_patients = len(set(a.patient_id for a in appointments))
    
    treatments_data = []
    diagnosis_count = {}
    
    for apt in completed:
        if apt.treatment:
            treatment_info = {
                'date': str(apt.date) if apt.date else 'N/A',
                'patient_name': apt.patient.user.name if apt.patient and apt.patient.user else 'Unknown',
                'diagnosis': apt.treatment.diagnosis or 'N/A',
                'prescription': apt.treatment.prescription or 'N/A',
                'follow_up': str(apt.treatment.follow_up_date) if apt.treatment.follow_up_date else None
            }
            treatments_data.append(treatment_info)
            
            diag = apt.treatment.diagnosis or 'Unspecified'
            diagnosis_count[diag] = diagnosis_count.get(diag, 0) + 1
    
    html_report = generate_doctor_monthly_report_html(
        doctor_name=doctor.user.name,
        department=doctor.department.name if doctor.department else 'General',
        month_name=month_name,
        total_appointments=total_appointments,
        completed_count=len(completed),
        cancelled_count=len(cancelled),
        booked_count=len(booked),
        unique_patients_count=unique_patients,
        treatments_data=treatments_data,
        diagnosis_count=diagnosis_count
    )
    
    plain_text = f"Monthly Activity Report for {month_name} - Dr. {doctor.user.name}"
    
    success = send_email(
        to_email=doctor.user.email,
        subject=f"Monthly Activity Report - {month_name}",
        body=plain_text,
        html_body=html_report
    )
    
    return {
        'status': 'sent' if success else 'failed',
        'doctor_id': doctor_id,
        'doctor_email': doctor.user.email,
        'month': month_name,
        'appointments': total_appointments
    }
