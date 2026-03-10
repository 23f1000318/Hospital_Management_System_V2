"""
Daily Reminder Tasks for Hospital Management System
Celery tasks for sending appointment reminders via email
"""
import sys
import os

# Ensure backend directory is in Python path for Celery workers
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from celery import shared_task
from datetime import date


@shared_task(ignore_result=False)
def send_daily_appointment_reminders():
    """
    Scheduled task to send daily appointment reminders.
    
    Runs every morning and sends email reminders to all patients
    who have appointments scheduled for that day.
    """
    # Ensure path is set inside task for forked workers
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    from models import Appointment
    from utils.email_utils import send_appointment_reminder
    
    today = date.today().isoformat()
    
    # Get all booked appointments for today
    appointments = Appointment.query.filter(
        Appointment.date == today,
        Appointment.status == 'booked'
    ).all()
    
    sent_count = 0
    failed_count = 0
    results = []
    
    for apt in appointments:
        patient = apt.patient
        doctor = apt.doctor
        
        if not patient or not patient.user or not patient.user.email:
            results.append({
                'appointment_id': apt.id,
                'status': 'skipped',
                'reason': 'No patient email'
            })
            continue
        
        patient_name = patient.user.name
        patient_email = patient.user.email
        doctor_name = doctor.user.name if doctor and doctor.user else 'Unknown'
        department = doctor.department.name if doctor and doctor.department else 'General'
        
        # Send reminder email
        success = send_appointment_reminder(
            patient_name=patient_name,
            patient_email=patient_email,
            doctor_name=doctor_name,
            department=department,
            appointment_date=apt.date,
            appointment_time=apt.time
        )
        
        if success:
            sent_count += 1
            results.append({
                'appointment_id': apt.id,
                'patient_email': patient_email,
                'status': 'sent'
            })
        else:
            failed_count += 1
            results.append({
                'appointment_id': apt.id,
                'patient_email': patient_email,
                'status': 'failed'
            })
    
    summary = {
        'date': today,
        'total_appointments': len(appointments),
        'reminders_sent': sent_count,
        'reminders_failed': failed_count,
        'details': results
    }
    
    print(f"[DAILY REMINDER] Date: {today}, Sent: {sent_count}, Failed: {failed_count}")
    
    return summary


@shared_task(ignore_result=False)
def send_single_appointment_reminder(appointment_id):
    """
    Send a reminder for a specific appointment.
    Useful for manual triggers or testing.
    """
    # Ensure path is set inside task for forked workers
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    from models import Appointment
    from utils.email_utils import send_appointment_reminder
    
    apt = Appointment.query.get(appointment_id)
    
    if not apt:
        return {'status': 'error', 'message': 'Appointment not found'}
    
    if apt.status != 'scheduled':
        return {'status': 'skipped', 'message': f'Appointment status is {apt.status}'}
    
    patient = apt.patient
    doctor = apt.doctor
    
    if not patient or not patient.user or not patient.user.email:
        return {'status': 'error', 'message': 'No patient email found'}
    
    success = send_appointment_reminder(
        patient_name=patient.user.name,
        patient_email=patient.user.email,
        doctor_name=doctor.user.name if doctor and doctor.user else 'Unknown',
        department=doctor.department.name if doctor and doctor.department else 'General',
        appointment_date=apt.date,
        appointment_time=apt.time
    )
    
    return {
        'status': 'sent' if success else 'failed',
        'appointment_id': appointment_id,
        'patient_email': patient.user.email
    }
