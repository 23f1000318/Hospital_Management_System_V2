from flask import request
from flask_restful import Resource, marshal, reqparse
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from services import PatientService
from models import Patient, Appointment
from .marshal_fields import patient_fields
from .resource_utils import validate_date


parser = reqparse.RequestParser()
parser.add_argument("user_id", type=int)
parser.add_argument("date_of_birth", type=validate_date)
parser.add_argument("gender", type=str)
parser.add_argument("blood_group", type=str)
parser.add_argument("phone", type=str)
parser.add_argument("address", type=str)
parser.add_argument("emergency_contact", type=str)

service = PatientService


class PatientResource(Resource):
    @auth_required("token")
    def get(self, id):
        item = service.get_by_id(id)
        
        # Patients can only view their own profile, admin/doctor can view any
        if current_user.has_role("patient"):
            if not hasattr(current_user, 'patient_profile') or current_user.patient_profile.id != id:
                return {"message": "Not authorized"}, 401
        
        return marshal(item, patient_fields), 200
    
    @auth_required("token")
    def put(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Patient not found"}, 404
        
        # Patients can only update their own profile
        if current_user.has_role("patient"):
            if not hasattr(current_user, 'patient_profile') or current_user.patient_profile.id != id:
                return {"message": "Not authorized"}, 401
        
        args = parser.parse_args()
        args["id"] = id
        item = service.update(args)
        return marshal(item, patient_fields), 200
    
    @auth_required("token")
    def patch(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Patient not found"}, 404
        
        if current_user.has_role("patient"):
            if not hasattr(current_user, 'patient_profile') or current_user.patient_profile.id != id:
                return {"message": "Not authorized"}, 401
        
        data = request.get_json()
        data["id"] = id
        item = service.update(data)
        return marshal(item, patient_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def delete(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Patient not found"}, 404
        result = service.delete(id)
        return result, 200


class PatientListResource(Resource):
    @auth_required("token")
    def get(self):
        # Admin and doctors can view all patients
        if not (current_user.has_role("admin") or current_user.has_role("doctor")):
            return {"message": "Not authorized"}, 401
        items = service.get_all()
        return marshal(items, patient_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def post(self):
        args = parser.parse_args()
        item = service.create(args)
        return marshal(item, patient_fields), 201


class PatientSearchResource(Resource):
    @auth_required("token")
    def get(self):
        """Search patients by name, email, or phone (admin/doctor only)"""
        if not (current_user.has_role("admin") or current_user.has_role("doctor")):
            return {"message": "Not authorized"}, 401
        
        query = request.args.get("q", "")
        items = service.search(query=query)
        return marshal(items, patient_fields), 200


class AdminPatientHistoryResource(Resource):
    """Admin endpoint to view full treatment history of a patient"""
    
    @auth_required("token")
    @roles_required("admin")
    def get(self, patient_id):
        """Get full treatment history for a patient"""
        patient = Patient.query.get(patient_id)
        if not patient:
            return {"message": "Patient not found"}, 404
        
        # Get all completed appointments with treatments
        history = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.status == 'completed'
        ).order_by(Appointment.date.desc()).all()
        
        # Build detailed history
        treatments = []
        for apt in history:
            if apt.treatment:
                entry = {
                    "id": apt.treatment.id,
                    "date": str(apt.date) if apt.date else None,
                    "doctor": {
                        "user": {
                            "name": apt.doctor.user.name if apt.doctor and apt.doctor.user else "Unknown"
                        }
                    },
                    "diagnosis": apt.treatment.diagnosis,
                    "prescription": apt.treatment.prescription,
                    "notes": apt.treatment.notes,
                    "follow_up_date": str(apt.treatment.follow_up_date) if apt.treatment.follow_up_date else None
                }
                treatments.append(entry)
        
        return {
            "patient": marshal(patient, patient_fields),
            "total_visits": len(treatments),
            "treatments": treatments
        }
