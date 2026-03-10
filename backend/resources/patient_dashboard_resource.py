from flask import request
from flask_restful import Resource, marshal
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from models import db, Patient, Department, Doctor, Appointment
from .marshal_fields import department_fields, doctor_fields, appointment_fields, patient_fields
from extensions import cache
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_
import json

# IST timezone offset (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def make_patient_dashboard_key():
    """Generate cache key specific to current patient"""
    if hasattr(current_user, 'patient_profile') and current_user.patient_profile:
        return f"patient_dashboard_{current_user.patient_profile.id}"
    return "patient_dashboard_unknown"


class PatientDashboardResource(Resource):
    @auth_required("token")
    @roles_required("patient")
    @cache.cached(timeout=60, key_prefix=make_patient_dashboard_key)
    def get(self):
        """Get patient's dashboard data: departments, available doctors, appointments"""
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        patient_id = current_user.patient_profile.id
        today = datetime.now().date()
        week_end = today + timedelta(days=7)
        
        # Get all departments
        departments = Department.query.all()
        
        # Get all active doctors with their availability
        doctors = Doctor.query.join(Doctor.user).filter(
            Doctor.user.has(active=True)
        ).all()
        
        # Parse doctor availability
        doctors_with_availability = []
        for doc in doctors:
            doc_data = marshal(doc, doctor_fields)
            try:
                availability = json.loads(doc.availability or "{}")
            except:
                availability = {}
            doc_data["parsed_availability"] = availability
            doctors_with_availability.append(doc_data)
        
        # Get patient's appointments
        all_appointments = Appointment.query.filter_by(patient_id=patient_id).all()
        
        # Upcoming appointments (booked, future dates)
        upcoming = [apt for apt in all_appointments 
                   if apt.status == "booked" and apt.date >= today]
        upcoming.sort(key=lambda x: (x.date, x.time))
        
        # Past/completed appointments
        past = [apt for apt in all_appointments 
               if apt.status == "completed" or apt.date < today]
        past.sort(key=lambda x: (x.date, x.time), reverse=True)
        
        # Stats
        stats = {
            "total_appointments": len(all_appointments),
            "upcoming_count": len(upcoming),
            "completed": len([a for a in all_appointments if a.status == "completed"]),
            "cancelled": len([a for a in all_appointments if a.status == "cancelled"]),
        }
        
        return {
            "stats": stats,
            "departments": marshal(departments, department_fields),
            "doctors": doctors_with_availability,
            "upcoming_appointments": marshal(upcoming[:5], appointment_fields),  # Show first 5
            "past_appointments": marshal(past[:5], appointment_fields),  # Show first 5
        }


class PatientProfileResource(Resource):
    @auth_required("token")
    @roles_required("patient")
    def get(self):
        """Get current patient's profile"""
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        patient = current_user.patient_profile
        return marshal(patient, patient_fields)
    
    @auth_required("token")
    @roles_required("patient")
    def put(self):
        """Update current patient's profile"""
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        try:
            data = request.get_json()
            patient = current_user.patient_profile
            
            # Update patient fields
            if "phone" in data:
                patient.phone = data["phone"] or None
            if "address" in data:
                patient.address = data["address"] or None
            if "gender" in data:
                patient.gender = data["gender"] or None
            if "blood_group" in data:
                patient.blood_group = data["blood_group"] or None
            if "date_of_birth" in data and data["date_of_birth"]:
                # Parse date string to date object
                from datetime import datetime
                if isinstance(data["date_of_birth"], str):
                    patient.date_of_birth = datetime.strptime(data["date_of_birth"], "%Y-%m-%d").date()
                else:
                    patient.date_of_birth = data["date_of_birth"]
            if "emergency_contact" in data:
                patient.emergency_contact = data["emergency_contact"] or None
            
            # Update user name if provided
            if "name" in data and data["name"]:
                current_user.name = data["name"]
            
            db.session.commit()
            
            # Invalidate cache
            cache.delete(f"patient_dashboard_{patient.id}")
            
            return {
                "message": "Profile updated successfully",
                "patient": marshal(patient, patient_fields)
            }
        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to update profile: {str(e)}"}, 400


class DoctorAvailabilityPublicResource(Resource):
    def get(self, doctor_id):
        """Get a doctor's availability for next 7 days (public)"""
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return {"message": "Doctor not found"}, 404
        
        try:
            availability = json.loads(doctor.availability or "{}")
        except:
            availability = {}
        
        # Use IST timezone for current date/time
        now_ist = datetime.now(IST)
        today = now_ist.date()
        current_time = now_ist.time()
        today_str = today.isoformat()
        
        week_dates = [(today + timedelta(days=i)).isoformat() for i in range(7)]
        
        # Get already booked or completed appointments for this doctor in next 7 days
        # (completed slots must stay unavailable — doctor already treated a patient then)
        occupied_appointments = Appointment.query.filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.date >= today,
                Appointment.date <= today + timedelta(days=6),
                Appointment.status.in_(["booked", "completed"])
            )
        ).all()
        
        # Create a set of occupied slots: {(date_str, time_str), ...}
        booked_slots = set()
        for apt in occupied_appointments:
            date_str = apt.date.isoformat()
            time_str = apt.time.strftime("%H:%M")
            booked_slots.add((date_str, time_str))
        
        # Filter availability: remove occupied slots and past time slots for today
        filtered_availability = {}
        for date, slots in availability.items():
            if date in week_dates:
                available_slots = []
                for slot in slots:
                    # Skip if slot is booked
                    if (date, slot) in booked_slots:
                        continue
                    # For today, skip past time slots
                    if date == today_str:
                        slot_time = datetime.strptime(slot, "%H:%M").time()
                        if slot_time <= current_time:
                            continue
                    available_slots.append(slot)
                if available_slots:
                    filtered_availability[date] = available_slots
        
        return {
            "doctor_id": doctor_id,
            "doctor_name": doctor.user.name if doctor.user else "Unknown",
            "availability": filtered_availability
        }


class PatientBookAppointmentResource(Resource):
    @auth_required("token")
    @roles_required("patient")
    def post(self):
        """Book an appointment"""
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get("doctor_id"):
                return {"message": "Doctor ID is required"}, 400
            if not data.get("date"):
                return {"message": "Date is required"}, 400
            if not data.get("time"):
                return {"message": "Time is required"}, 400
            
            # Check doctor exists
            doctor = Doctor.query.get(data["doctor_id"])
            if not doctor:
                return {"message": "Doctor not found"}, 404
            
            # Parse date and time
            appointment_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            appointment_time = datetime.strptime(data["time"], "%H:%M").time()
            
            patient_id = current_user.patient_profile.id
            
            # Rule 1: Same patient + same doctor + same date = Not allowed (any time)
            existing_with_same_doctor = Appointment.query.filter(
                and_(
                    Appointment.patient_id == patient_id,
                    Appointment.doctor_id == data["doctor_id"],
                    Appointment.date == appointment_date,
                    Appointment.status.in_(["booked", "completed"])
                )
            ).first()
            
            if existing_with_same_doctor:
                return {"message": "You already have an appointment with this doctor on this date"}, 400
            
            # Rule 2: Same patient + same date + same time = Not allowed (any doctor)
            existing_at_same_time = Appointment.query.filter(
                and_(
                    Appointment.patient_id == patient_id,
                    Appointment.date == appointment_date,
                    Appointment.time == appointment_time,
                    Appointment.status.in_(["booked", "completed"])
                )
            ).first()
            
            if existing_at_same_time:
                return {"message": "You already have an appointment with a doctor at this time on this date"}, 400
            
            # Rule 3: Check if slot is already taken by another patient (booked or completed)
            existing = Appointment.query.filter(
                and_(
                    Appointment.doctor_id == data["doctor_id"],
                    Appointment.date == appointment_date,
                    Appointment.time == appointment_time,
                    Appointment.status.in_(["booked", "completed"])
                )
            ).first()
            
            if existing:
                return {"message": "This time slot is already taken"}, 400
            
            # Create appointment
            appointment = Appointment(
                patient_id=current_user.patient_profile.id,
                doctor_id=data["doctor_id"],
                date=appointment_date,
                time=appointment_time,
                reason=data.get("reason", ""),
                status="booked"
            )
            db.session.add(appointment)
            db.session.commit()
            
            # Invalidate caches
            cache.delete(f"patient_dashboard_{current_user.patient_profile.id}")
            cache.delete(f"doctor_dashboard_{data['doctor_id']}")
            cache.delete("admin_dashboard")
            
            return {
                "message": "Appointment booked successfully",
                "appointment": marshal(appointment, appointment_fields)
            }, 201
        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to book appointment: {str(e)}"}, 400


class PatientCancelAppointmentResource(Resource):
    @auth_required("token")
    @roles_required("patient")
    def patch(self, appointment_id):
        """Cancel an appointment"""
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return {"message": "Appointment not found"}, 404
        
        # Verify this appointment belongs to this patient
        if appointment.patient_id != current_user.patient_profile.id:
            return {"message": "Not authorized"}, 401
        
        if appointment.status != "booked":
            return {"message": "Can only cancel booked appointments"}, 400
        
        doctor_id = appointment.doctor_id
        appointment.status = "cancelled"
        db.session.commit()
        
        # Invalidate caches
        cache.delete(f"patient_dashboard_{current_user.patient_profile.id}")
        cache.delete(f"doctor_dashboard_{doctor_id}")
        cache.delete("admin_dashboard")
        
        return {
            "message": "Appointment cancelled successfully",
            "appointment": marshal(appointment, appointment_fields)
        }


class PatientRescheduleAppointmentResource(Resource):
    @auth_required("token")
    @roles_required("patient")
    def patch(self, appointment_id):
        """Reschedule an appointment to a new date/time"""
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return {"message": "Appointment not found"}, 404
        
        # Verify this appointment belongs to this patient
        if appointment.patient_id != current_user.patient_profile.id:
            return {"message": "Not authorized"}, 401
        
        if appointment.status != "booked":
            return {"message": "Can only reschedule booked appointments"}, 400
        
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get("date"):
                return {"message": "New date is required"}, 400
            if not data.get("time"):
                return {"message": "New time is required"}, 400
            
            # Parse new date and time
            new_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            new_time = datetime.strptime(data["time"], "%H:%M").time()
            
            # Check for conflicting appointment at new slot
            existing = Appointment.query.filter(
                and_(
                    Appointment.doctor_id == appointment.doctor_id,
                    Appointment.date == new_date,
                    Appointment.time == new_time,
                    Appointment.status == "booked",
                    Appointment.id != appointment_id  # Exclude current appointment
                )
            ).first()
            
            if existing:
                return {"message": "This time slot is already booked"}, 400
            
            # Update appointment
            old_doctor_id = appointment.doctor_id
            appointment.date = new_date
            appointment.time = new_time
            if data.get("reason"):
                appointment.reason = data["reason"]
            
            db.session.commit()
            
            # Invalidate caches
            cache.delete(f"patient_dashboard_{current_user.patient_profile.id}")
            cache.delete(f"doctor_dashboard_{old_doctor_id}")
            cache.delete("admin_dashboard")
            
            return {
                "message": "Appointment rescheduled successfully",
                "appointment": marshal(appointment, appointment_fields)
            }
        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to reschedule appointment: {str(e)}"}, 400


class PatientTreatmentHistoryResource(Resource):
    """View complete treatment history for the patient"""
    
    @auth_required("token")
    @roles_required("patient")
    def get(self):
        """Get full treatment history for current patient"""
        if not hasattr(current_user, 'patient_profile') or not current_user.patient_profile:
            return {"message": "Patient profile not found"}, 404
        
        patient_id = current_user.patient_profile.id
        
        # Get all completed appointments with treatments
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
                "doctor_qualification": apt.doctor.qualification if apt.doctor else "N/A",
                "department": apt.doctor.department.name if apt.doctor and apt.doctor.department else "General",
                "reason": apt.reason,
                "status": apt.status
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
            "total_visits": len(history),
            "history": treatment_history
        }
