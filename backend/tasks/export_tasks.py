"""
Export Tasks for Hospital Management System
Celery tasks for generating CSV exports and sending email notifications
"""
import sys
import os

# Ensure backend directory is in Python path for Celery workers
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from celery import shared_task
from datetime import datetime
import csv
import os


@shared_task(bind=True, ignore_result=False)
def export_patient_treatments_csv(self, patient_id, user_email, user_name, requester_user_id=None):
    """
    Async task to export patient treatment history as CSV.
    
    Generates a CSV file and sends email notification when complete.
    """
    # Ensure path is set inside task for forked workers
    import sys
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    from flask import current_app
    from models import Patient, Appointment
    from utils.email_utils import send_export_notification
    
    try:
        # Update task state
        self.update_state(state='PROCESSING', meta={'status': 'Fetching data...'})
        
        # Get patient
        patient = Patient.query.get(patient_id)
        if not patient:
            return {'status': 'error', 'message': 'Patient not found'}

        # Safety guard: ensure task context matches the requesting authenticated user.
        # Prevents cross-user exports when IDs are reused or worker context is stale.
        if requester_user_id is not None and patient.user_id != requester_user_id:
            return {
                'status': 'error',
                'message': 'Export blocked: patient ownership mismatch for current user'
            }

        patient_email = patient.user.email if patient.user else None
        if user_email and patient_email and patient_email.lower() != user_email.lower():
            return {
                'status': 'error',
                'message': 'Export blocked: patient email mismatch for current user'
            }

        patient_name = patient.user.name if patient.user else None
        if user_name and patient_name and patient_name.strip().lower() != user_name.strip().lower():
            return {
                'status': 'error',
                'message': 'Export blocked: patient name mismatch for current user'
            }
        
        # Get all completed appointments with treatments
        appointments = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.status == 'completed'
        ).order_by(Appointment.date.desc()).all()
        
        self.update_state(state='PROCESSING', meta={'status': 'Generating CSV...'})
        
        # Create exports directory if not exists
        exports_dir = os.path.join(current_app.instance_path, 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"treatment_history_{patient_id}_{timestamp}.csv"
        filepath = os.path.join(exports_dir, filename)
        
        # CSV Headers
        headers = [
            'Patient ID',
            'Patient Name',
            'Appointment Date',
            'Appointment Time',
            'Consulting Doctor',
            'Department',
            'Doctor Qualification',
            'Diagnosis',
            'Prescription',
            'Doctor Notes',
            'Follow-up Date',
            'Export Generated'
        ]
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            patient_name = patient.user.name if patient.user else 'Unknown'
            
            for apt in appointments:
                doctor_name = apt.doctor.user.name if apt.doctor and apt.doctor.user else 'Unknown'
                department = apt.doctor.department.name if apt.doctor and apt.doctor.department else 'General'
                qualification = apt.doctor.qualification if apt.doctor else 'N/A'
                
                # Treatment details
                if apt.treatment:
                    diagnosis = apt.treatment.diagnosis or 'N/A'
                    prescription = apt.treatment.prescription or 'N/A'
                    notes = apt.treatment.notes or 'N/A'
                    follow_up = apt.treatment.follow_up_date or 'N/A'
                else:
                    diagnosis = 'No treatment recorded'
                    prescription = 'N/A'
                    notes = 'N/A'
                    follow_up = 'N/A'
                
                row = [
                    patient_id,
                    patient_name,
                    apt.date,
                    apt.time,
                    f"Dr. {doctor_name}",
                    department,
                    qualification,
                    diagnosis,
                    prescription,
                    notes,
                    follow_up,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                writer.writerow(row)
        
        self.update_state(state='PROCESSING', meta={'status': 'Sending notification...'})
        
        # Send email notification
        send_export_notification(
            user_name=user_name,
            user_email=user_email,
            filename=filename,
            record_count=len(appointments)
        )
        
        print(f"[EXPORT COMPLETE] Patient: {patient_id}, File: {filename}, Records: {len(appointments)}")
        
        return {
            'status': 'completed',
            'filename': filename,
            'filepath': filepath,
            'record_count': len(appointments),
            'patient_id': patient_id
        }
        
    except Exception as e:
        print(f"[EXPORT ERROR] Patient {patient_id}: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(ignore_result=False)
def check_export_status(task_id):
    """
    Check the status of an export task.
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    return {
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready(),
        'result': result.result if result.ready() else None
    }
