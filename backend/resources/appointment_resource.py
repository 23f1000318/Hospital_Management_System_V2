from flask import request
from flask_restful import Resource, marshal, reqparse
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from services import AppointmentService
from .marshal_fields import appointment_fields
from .resource_utils import validate_date, validate_time


parser = reqparse.RequestParser()
parser.add_argument("patient_id", type=int, required=True)
parser.add_argument("doctor_id", type=int, required=True)
parser.add_argument("date", type=validate_date, required=True)
parser.add_argument("time", type=validate_time, required=True)
parser.add_argument("reason", type=str)
parser.add_argument("status", type=str)

service = AppointmentService


class AppointmentResource(Resource):
    @auth_required("token")
    def get(self, id):
        item = service.get_by_id(id)
        
        # Check authorization
        if current_user.has_role("patient"):
            if not hasattr(current_user, 'patient_profile') or current_user.patient_profile.id != item.patient_id:
                return {"message": "Not authorized"}, 401
        elif current_user.has_role("doctor"):
            if not hasattr(current_user, 'doctor_profile') or current_user.doctor_profile.id != item.doctor_id:
                return {"message": "Not authorized"}, 401
        
        return marshal(item, appointment_fields), 200
    
    @auth_required("token")
    def put(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Appointment not found"}, 404
        
        args = parser.parse_args()
        args["id"] = id
        item = service.update(args)
        return marshal(item, appointment_fields), 200
    
    @auth_required("token")
    def patch(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Appointment not found"}, 404
        
        data = request.get_json()
        data["id"] = id
        item = service.update(data)
        return marshal(item, appointment_fields), 200
    
    @auth_required("token")
    def delete(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Appointment not found"}, 404
        
        # Only admin or the patient who booked can delete
        if not current_user.has_role("admin"):
            if current_user.has_role("patient"):
                if not hasattr(current_user, 'patient_profile') or current_user.patient_profile.id != item.patient_id:
                    return {"message": "Not authorized"}, 401
            else:
                return {"message": "Not authorized"}, 401
        
        result = service.delete(id)
        return result, 200


class AppointmentListResource(Resource):
    @auth_required("token")
    def get(self):
        # Admin sees all, doctors see their appointments, patients see their appointments
        if current_user.has_role("admin"):
            items = service.get_all()
        elif current_user.has_role("doctor"):
            if hasattr(current_user, 'doctor_profile') and current_user.doctor_profile:
                items = service.get_by_doctor(current_user.doctor_profile.id)
            else:
                items = []
        elif current_user.has_role("patient"):
            if hasattr(current_user, 'patient_profile') and current_user.patient_profile:
                items = service.get_by_patient(current_user.patient_profile.id)
            else:
                items = []
        else:
            items = []
        
        return marshal(items, appointment_fields), 200
    
    @auth_required("token")
    def post(self):
        args = parser.parse_args()
        
        # Patients can only book appointments for themselves
        if current_user.has_role("patient"):
            if hasattr(current_user, 'patient_profile') and current_user.patient_profile:
                args["patient_id"] = current_user.patient_profile.id
            else:
                return {"message": "Patient profile not found"}, 400
        
        args["status"] = "booked"
        item = service.create(args)
        return marshal(item, appointment_fields), 201
