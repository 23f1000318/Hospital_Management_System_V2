"""
Export Resource for Hospital Management System
API endpoints for triggering and downloading CSV exports
"""
from flask import request, send_file, current_app
from flask_restful import Resource
from flask_security import current_user
from flask_security.decorators import auth_required, roles_required
from celery.result import AsyncResult
import os
import csv


def get_current_db_path():
    return os.path.join(current_app.instance_path, 'database.sqlite3')


def is_current_export_file(filepath):
    """Return True only for exports generated against the current database."""
    db_path = get_current_db_path()
    if not os.path.exists(filepath) or not os.path.exists(db_path):
        return False
    return os.path.getmtime(filepath) >= os.path.getmtime(db_path)


def is_export_owned_by_current_patient(filepath):
    """Validate CSV content belongs to currently logged-in patient."""
    if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
        return False

    try:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # header
            first_row = next(reader, None)

        # Empty export (no completed appointments) is still valid for current patient
        if first_row is None:
            return True

        row_patient_id = int(first_row[0]) if len(first_row) > 0 else None
        row_patient_name = first_row[1].strip() if len(first_row) > 1 and first_row[1] else ""
        current_name = (current_user.name or "").strip()

        return (
            row_patient_id == current_user.patient_profile.id
            and row_patient_name.lower() == current_name.lower()
        )
    except Exception:
        return False


class PatientExportResource(Resource):
    """Trigger treatment history CSV export for patient"""
    
    @auth_required("token")
    @roles_required("patient")
    def post(self):
        """Trigger async export of patient's treatment history"""
        from tasks.export_tasks import export_patient_treatments_csv
        
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        patient_id = current_user.patient_profile.id
        user_email = current_user.email
        user_name = current_user.name
        
        # Trigger async task
        task = export_patient_treatments_csv.delay(
            patient_id=patient_id,
            user_email=user_email,
            user_name=user_name,
            requester_user_id=current_user.id
        )
        
        return {
            "message": "Export started. You will receive an email when it's ready.",
            "task_id": task.id,
            "status": "processing"
        }, 202


class ExportStatusResource(Resource):
    """Check status of an export task"""
    
    @auth_required("token")
    def get(self, task_id):
        """Get status of an export task"""
        result = AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready()
        }
        
        if result.ready():
            if result.successful():
                task_result = result.result
                response["result"] = task_result
                if task_result.get("status") == "completed":
                    response["download_url"] = f"/api/exports/download/{task_result.get('filename')}"
            else:
                response["error"] = str(result.result)
        elif result.status == 'PROCESSING':
            response["meta"] = result.info
        
        return response


class ExportDownloadResource(Resource):
    """Download exported CSV file"""
    
    @auth_required("token")
    def get(self, filename):
        """Download an exported file"""
        # Security check: ensure filename matches expected pattern
        if not filename.startswith("treatment_history_"):
            return {"message": "Invalid file"}, 400
        
        # Additional security: check if this file belongs to the current user
        # Extract patient_id from filename (format: treatment_history_{patient_id}_{timestamp}.csv)
        try:
            parts = filename.replace(".csv", "").split("_")
            file_patient_id = int(parts[2])
        except (IndexError, ValueError):
            return {"message": "Invalid filename format"}, 400
        
        # Verify ownership (patients can only download their own exports)
        if hasattr(current_user, 'patient_profile') and current_user.patient_profile:
            if current_user.patient_profile.id != file_patient_id:
                # Allow admin to download any file
                if 'admin' not in [r.name for r in current_user.roles]:
                    return {"message": "Access denied"}, 403
        elif 'admin' not in [r.name for r in current_user.roles]:
            return {"message": "Access denied"}, 403
        
        # Build file path
        exports_dir = os.path.join(current_app.instance_path, 'exports')
        filepath = os.path.join(exports_dir, filename)
        
        if not os.path.exists(filepath):
            return {"message": "File not found. It may have expired."}, 404

        if not is_current_export_file(filepath):
            return {"message": "File not found. It belongs to an older database snapshot."}, 404

        if hasattr(current_user, 'patient_profile') and current_user.patient_profile:
            if not is_export_owned_by_current_patient(filepath):
                return {"message": "File not found. It does not belong to current patient."}, 404
        
        return send_file(
            filepath,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )


class PatientExportHistoryResource(Resource):
    """Get list of available exports for patient"""
    
    @auth_required("token")
    @roles_required("patient")
    def get(self):
        """Get list of available exports for current patient"""
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        patient_id = current_user.patient_profile.id
        exports_dir = os.path.join(current_app.instance_path, 'exports')
        
        if not os.path.exists(exports_dir):
            return {"exports": []}
        
        # Find files matching this patient
        prefix = f"treatment_history_{patient_id}_"
        exports = []
        
        for filename in os.listdir(exports_dir):
            if filename.startswith(prefix) and filename.endswith('.csv'):
                filepath = os.path.join(exports_dir, filename)
                if not is_current_export_file(filepath):
                    continue
                if not is_export_owned_by_current_patient(filepath):
                    continue
                stat = os.stat(filepath)
                
                # Extract timestamp from filename
                try:
                    timestamp_str = filename.replace(prefix, "").replace(".csv", "")
                    created = f"{timestamp_str[:4]}-{timestamp_str[4:6]}-{timestamp_str[6:8]} {timestamp_str[9:11]}:{timestamp_str[11:13]}:{timestamp_str[13:15]}"
                except:
                    created = "Unknown"
                
                exports.append({
                    "filename": filename,
                    "created": created,
                    "size_bytes": stat.st_size,
                    "download_url": f"/api/exports/download/{filename}"
                })
        
        # Sort by newest first
        exports.sort(key=lambda x: x["created"], reverse=True)
        
        return {"exports": exports}
