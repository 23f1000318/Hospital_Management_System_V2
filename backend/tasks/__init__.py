import sys
import os

# Ensure backend directory is in Python path for Celery workers
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from celery import shared_task

# Import all tasks so Celery can discover them
from tasks.reminder_tasks import (
    send_daily_appointment_reminders,
    send_single_appointment_reminder
)
from tasks.report_tasks import (
    send_monthly_doctor_reports,
    send_single_doctor_report
)
from tasks.export_tasks import (
    export_patient_treatments_csv,
    check_export_status
)


@shared_task
def sample_task(x, y):
    """Sample Celery task"""
    return x + y
