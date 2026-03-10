from flask_restful import Resource, marshal
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from models import Doctor, Patient, Appointment, Department, User, Treatment
from extensions import cache
from .marshal_fields import patient_fields, doctor_fields, appointment_fields, treatment_fields_basic


class DashboardResource(Resource):
    @auth_required("token")
    @roles_required("admin")
    @cache.cached(timeout=60, key_prefix="admin_dashboard")
    def get(self):
        """Get dashboard statistics for admin"""
        total_doctors = Doctor.query.count()
        total_patients = Patient.query.count()
        total_appointments = Appointment.query.count()
        total_departments = Department.query.count()
        
        # Appointments by status
        booked_appointments = Appointment.query.filter_by(status="booked").count()
        completed_appointments = Appointment.query.filter_by(status="completed").count()
        cancelled_appointments = Appointment.query.filter_by(status="cancelled").count()
        
        # Pending doctor approvals
        pending_approvals = User.query.filter_by(active=False).count()
        
        return {
            "total_doctors": total_doctors,
            "total_patients": total_patients,
            "total_appointments": total_appointments,
            "total_departments": total_departments,
            "booked_appointments": booked_appointments,
            "completed_appointments": completed_appointments,
            "cancelled_appointments": cancelled_appointments,
            "pending_approvals": pending_approvals,
        }, 200


class AdminPatientProfileResource(Resource):
    @auth_required("token")
    @roles_required("admin")
    def get(self, id):
        """Get detailed patient profile with treatment history for admin"""
        patient = Patient.query.get(id)
        if not patient:
            return {"message": "Patient not found"}, 404
        
        # Get all appointments for this patient
        appointments = Appointment.query.filter_by(patient_id=id).order_by(Appointment.date.desc()).all()
        
        # Stats
        total_appointments = len(appointments)
        completed = sum(1 for a in appointments if a.status == "completed")
        cancelled = sum(1 for a in appointments if a.status == "cancelled")
        booked = sum(1 for a in appointments if a.status == "booked")
        
        # Get treatment history
        treatments = []
        for apt in appointments:
            if apt.treatment:
                treatments.append({
                    "appointment_id": apt.id,
                    "date": apt.date.isoformat() if apt.date else None,
                    "doctor_name": apt.doctor.user.name if apt.doctor and apt.doctor.user else "N/A",
                    "diagnosis": apt.treatment.diagnosis,
                    "prescription": apt.treatment.prescription,
                    "notes": apt.treatment.notes,
                    "follow_up_date": apt.treatment.follow_up_date.isoformat() if apt.treatment.follow_up_date else None,
                })
        
        return {
            "patient": marshal(patient, patient_fields),
            "stats": {
                "total_appointments": total_appointments,
                "completed": completed,
                "cancelled": cancelled,
                "booked": booked,
            },
            "treatments": treatments,
        }, 200


class AdminDoctorProfileResource(Resource):
    @auth_required("token")
    @roles_required("admin")
    def get(self, id):
        """Get detailed doctor profile with appointment statistics for admin"""
        doctor = Doctor.query.get(id)
        if not doctor:
            return {"message": "Doctor not found"}, 404
        
        # Get all appointments for this doctor
        appointments = Appointment.query.filter_by(doctor_id=id).all()
        
        # Stats
        total_appointments = len(appointments)
        completed = sum(1 for a in appointments if a.status == "completed")
        cancelled = sum(1 for a in appointments if a.status == "cancelled")
        booked = sum(1 for a in appointments if a.status == "booked")
        
        # Unique active patients (booked or completed appointments)
        unique_patients = len(
            set(a.patient_id for a in appointments if a.status in ["booked", "completed"])
        )
        
        return {
            "doctor": marshal(doctor, doctor_fields),
            "stats": {
                "total_appointments": total_appointments,
                "completed_appointments": completed,
                "cancelled_appointments": cancelled,
                "booked_appointments": booked,
                "completed": completed,
                "cancelled": cancelled,
                "booked": booked,
                "unique_patients": unique_patients,
            },
        }, 200


def invalidate_admin_dashboard_cache():
    """Helper function to invalidate admin dashboard cache"""
    cache.delete("admin_dashboard")
