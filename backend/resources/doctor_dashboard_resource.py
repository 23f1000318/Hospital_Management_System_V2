from flask import request
from flask_restful import Resource, marshal
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from models import db, Doctor, Appointment, Patient, Treatment
from .marshal_fields import appointment_fields, patient_fields
from extensions import cache
from datetime import datetime, timedelta
from sqlalchemy import and_, or_


# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    'booked': ['completed', 'cancelled'],
    'completed': [],  # Cannot change once completed
    'cancelled': [],  # Cannot change once cancelled
}


def make_doctor_dashboard_key():
    """Generate cache key specific to current doctor"""
    if hasattr(current_user, 'doctor_profile') and current_user.doctor_profile:
        return f"doctor_dashboard_{current_user.doctor_profile.id}"
    return "doctor_dashboard_unknown"


class DoctorDashboardResource(Resource):
    @auth_required("token")
    @roles_required("doctor")
    @cache.cached(timeout=60, key_prefix=make_doctor_dashboard_key)
    def get(self):
        """Get doctor's dashboard data: today's appointments, week's appointments, assigned patients"""
        if not hasattr(current_user, 'doctor_profile') or not current_user.doctor_profile:
            return {"message": "Doctor profile not found"}, 404
        
        doctor_id = current_user.doctor_profile.id
        today = datetime.now().date()
        week_end = today + timedelta(days=7)
        
        # Today's appointments
        todays_appointments = Appointment.query.filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.date == today
            )
        ).order_by(Appointment.time).all()
        
        # This week's appointments (next 7 days)
        weeks_appointments = Appointment.query.filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.date >= today,
                Appointment.date <= week_end
            )
        ).order_by(Appointment.date, Appointment.time).all()
        
        # All appointments for stats
        all_appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()
        
        # Unique patients assigned to this doctor (from all appointments)
        patient_ids = list(set([apt.patient_id for apt in all_appointments]))
        assigned_patients = Patient.query.filter(Patient.id.in_(patient_ids)).all() if patient_ids else []
        
        # Stats
        stats = {
            "total_appointments": len(all_appointments),
            "completed": len([a for a in all_appointments if a.status == "completed"]),
            "pending": len([a for a in all_appointments if a.status == "booked"]),
            "cancelled": len([a for a in all_appointments if a.status == "cancelled"]),
            "today_count": len(todays_appointments),
            "week_count": len(weeks_appointments),
            "total_patients": len(assigned_patients),
        }
        
        return {
            "stats": stats,
            "today_appointments": marshal(todays_appointments, appointment_fields),
            "week_appointments": marshal(weeks_appointments, appointment_fields),
            "assigned_patients": marshal(assigned_patients, patient_fields),
        }


class DoctorAvailabilityResource(Resource):
    @auth_required("token")
    @roles_required("doctor")
    def get(self):
        """Get doctor's availability"""
        if not hasattr(current_user, 'doctor_profile') or not current_user.doctor_profile:
            return {"message": "Doctor profile not found"}, 404
        
        doctor = current_user.doctor_profile
        return {"availability": doctor.availability or "{}"}
    
    @auth_required("token")
    @roles_required("doctor")
    def put(self):
        """Update doctor's availability for next 7 days"""
        if not hasattr(current_user, 'doctor_profile') or not current_user.doctor_profile:
            return {"message": "Doctor profile not found"}, 404
        
        data = request.get_json()
        doctor = current_user.doctor_profile
        
        # Availability is stored as JSON string
        # Format: {"2026-03-05": ["09:00", "10:00", "11:00"], ...}
        try:
            doctor.availability = data.get("availability", "{}")
            db.session.commit()
            
            # Invalidate doctor dashboard cache
            cache.delete(f"doctor_dashboard_{doctor.id}")
            
            return {"message": "Availability updated", "availability": doctor.availability}
        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to update availability: {str(e)}"}, 400


class DoctorAppointmentStatusResource(Resource):
    @auth_required("token")
    @roles_required("doctor")
    def patch(self, appointment_id):
        """Mark appointment as completed or cancelled"""
        if not hasattr(current_user, 'doctor_profile') or not current_user.doctor_profile:
            return {"message": "Doctor profile not found"}, 404
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return {"message": "Appointment not found"}, 404
        
        # Verify this appointment belongs to this doctor
        if appointment.doctor_id != current_user.doctor_profile.id:
            return {"message": "Not authorized"}, 401
        
        data = request.get_json()
        new_status = data.get("status")
        
        if new_status not in ["completed", "cancelled"]:
            return {"message": "Invalid status. Must be 'completed' or 'cancelled'"}, 400
        
        # Validate status transition
        allowed_transitions = VALID_STATUS_TRANSITIONS.get(appointment.status, [])
        if new_status not in allowed_transitions:
            return {"message": f"Cannot change status from '{appointment.status}' to '{new_status}'"}, 400
        
        appointment.status = new_status
        db.session.commit()
        
        # Invalidate caches
        cache.delete(f"patient_dashboard_{appointment.patient_id}")
        cache.delete(f"doctor_dashboard_{current_user.doctor_profile.id}")
        cache.delete("admin_dashboard")
        
        return marshal(appointment, appointment_fields)


class DoctorTreatmentResource(Resource):
    @auth_required("token")
    @roles_required("doctor")
    def post(self, appointment_id):
        """Add/update treatment record for an appointment"""
        if not hasattr(current_user, 'doctor_profile') or not current_user.doctor_profile:
            return {"message": "Doctor profile not found"}, 404
        
        try:
            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                return {"message": "Appointment not found"}, 404
            
            # Verify this appointment belongs to this doctor
            if appointment.doctor_id != current_user.doctor_profile.id:
                return {"message": "Not authorized"}, 401
            
            data = request.get_json()
            
            # Parse follow_up_date if provided
            follow_up_date = None
            if data.get("follow_up_date"):
                follow_up_date = datetime.strptime(data["follow_up_date"], "%Y-%m-%d").date()
            
            # Check if treatment already exists
            if appointment.treatment:
                # Update existing treatment
                treatment = appointment.treatment
                if "diagnosis" in data:
                    treatment.diagnosis = data["diagnosis"] or None
                if "prescription" in data:
                    treatment.prescription = data["prescription"] or None
                if "notes" in data:
                    treatment.notes = data["notes"] or None
                if "follow_up_date" in data:
                    treatment.follow_up_date = follow_up_date
            else:
                # Create new treatment
                treatment = Treatment(
                    appointment_id=appointment_id,
                    diagnosis=data.get("diagnosis") or None,
                    prescription=data.get("prescription") or None,
                    notes=data.get("notes") or None,
                    follow_up_date=follow_up_date,
                )
                db.session.add(treatment)
            
            # Mark appointment as completed when treatment is added
            appointment.status = "completed"
            db.session.commit()
            
            # Invalidate relevant caches
            cache.delete(f"doctor_dashboard_{current_user.doctor_profile.id}")
            cache.delete(f"patient_dashboard_{appointment.patient_id}")
            cache.delete("admin_dashboard")
            
            return {
                "message": "Treatment saved successfully",
                "appointment": marshal(appointment, appointment_fields)
            }
        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to save treatment: {str(e)}"}, 400


class DoctorPatientHistoryResource(Resource):
    """View full treatment history of a patient (for informed consultation)"""
    
    @auth_required("token")
    @roles_required("doctor")
    def get(self, patient_id):
        """Get full treatment history for a patient"""
        if not hasattr(current_user, 'doctor_profile') or not current_user.doctor_profile:
            return {"message": "Doctor profile not found"}, 404
        
        doctor_id = current_user.doctor_profile.id
        
        # Get patient
        patient = Patient.query.get(patient_id)
        if not patient:
            return {"message": "Patient not found"}, 404
        
        # Verify doctor has treated this patient before (has appointments with them)
        has_relation = Appointment.query.filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.patient_id == patient_id
            )
        ).first()
        
        if not has_relation:
            return {"message": "Not authorized to view this patient's history"}, 401
        
        # Get all completed appointments with treatments (from any doctor)
        history = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.status == 'completed'
        ).order_by(Appointment.date.desc()).all()
        
        # Build detailed history
        treatment_history = []
        for apt in history:
            entry = {
                "appointment_id": apt.id,
                "date": apt.date,
                "time": apt.time,
                "doctor_name": apt.doctor.user.name if apt.doctor and apt.doctor.user else "Unknown",
                "department": apt.doctor.department.name if apt.doctor and apt.doctor.department else "General",
                "reason": apt.reason,
                "is_own_appointment": apt.doctor_id == doctor_id
            }
            
            if apt.treatment:
                entry["treatment"] = {
                    "diagnosis": apt.treatment.diagnosis,
                    "prescription": apt.treatment.prescription,
                    "notes": apt.treatment.notes,
                    "follow_up_date": apt.treatment.follow_up_date
                }
            else:
                entry["treatment"] = None
            
            treatment_history.append(entry)
        
        return {
            "patient": marshal(patient, patient_fields),
            "total_visits": len(history),
            "history": treatment_history
        }
