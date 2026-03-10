from flask import request
from flask_restful import Resource, marshal, reqparse
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from services import TreatmentService, AppointmentService
from .marshal_fields import treatment_fields
from .resource_utils import validate_date


parser = reqparse.RequestParser()
parser.add_argument("appointment_id", type=int, required=True)
parser.add_argument("diagnosis", type=str)
parser.add_argument("prescription", type=str)
parser.add_argument("notes", type=str)
parser.add_argument("follow_up_date", type=validate_date)

service = TreatmentService


class TreatmentResource(Resource):
    @auth_required("token")
    def get(self, id):
        item = service.get_by_id(id)
        return marshal(item, treatment_fields), 200
    
    @auth_required("token")
    @roles_required("doctor")
    def put(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Treatment not found"}, 404
        
        # Only the doctor assigned to the appointment can update
        appointment = AppointmentService.get_by_id(item.appointment_id)
        if current_user.doctor_profile.id != appointment.doctor_id:
            return {"message": "Not authorized"}, 401
        
        args = parser.parse_args()
        args["id"] = id
        item = service.update(args)
        return marshal(item, treatment_fields), 200
    
    @auth_required("token")
    @roles_required("doctor")
    def patch(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Treatment not found"}, 404
        
        # Only the doctor assigned to the appointment can update
        appointment = AppointmentService.get_by_id(item.appointment_id)
        if current_user.doctor_profile.id != appointment.doctor_id:
            return {"message": "Not authorized"}, 401
        
        data = request.get_json()
        data["id"] = id
        item = service.update(data)
        return marshal(item, treatment_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def delete(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Treatment not found"}, 404
        result = service.delete(id)
        return result, 200


class TreatmentListResource(Resource):
    @auth_required("token")
    def get(self):
        items = service.get_all()
        return marshal(items, treatment_fields), 200
    
    @auth_required("token")
    @roles_required("doctor")
    def post(self):
        args = parser.parse_args()
        
        # Verify the doctor is assigned to this appointment
        appointment = AppointmentService.get_by_id(args["appointment_id"])
        if not appointment:
            return {"message": "Appointment not found"}, 404
        
        if current_user.doctor_profile.id != appointment.doctor_id:
            return {"message": "Not authorized to add treatment for this appointment"}, 401
        
        # Mark appointment as completed when treatment is added
        AppointmentService.update({"id": appointment.id, "status": "completed"})
        
        item = service.create(args)
        return marshal(item, treatment_fields), 201
