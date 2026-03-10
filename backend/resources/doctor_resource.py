from flask import request
from flask_restful import Resource, marshal, reqparse
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from services import DoctorService
from services.service_errors import ServiceError
from .marshal_fields import doctor_fields
from extensions import cache


parser = reqparse.RequestParser()
parser.add_argument("name", type=str)
parser.add_argument("email", type=str)
parser.add_argument("password", type=str)
parser.add_argument("user_id", type=int)
parser.add_argument("department_id", type=int)
parser.add_argument("qualification", type=str)
parser.add_argument("experience_years", type=int)
parser.add_argument("consultation_fee", type=float)
parser.add_argument("availability", type=str)
parser.add_argument("phone", type=str)

service = DoctorService


class DoctorResource(Resource):
    @cache.memoize(timeout=300)  # 5 minutes cache
    def get(self, id):
        item = service.get_by_id(id)
        return marshal(item, doctor_fields), 200
    
    @auth_required("token")
    def put(self, id):
        # Admin can update any doctor, doctor can update own profile
        item = service.get_by_id(id)
        if not item:
            return {"message": "Doctor not found"}, 404
        
        if not current_user.has_role("admin"):
            if not hasattr(current_user, 'doctor_profile') or current_user.doctor_profile.id != id:
                return {"message": "Not authorized"}, 401
        
        args = parser.parse_args()
        args["id"] = id
        item = service.update(args)
        # Invalidate both individual and list cache
        cache.delete_memoized(DoctorResource.get, DoctorResource, id)
        cache.delete("doctors_all")
        return marshal(item, doctor_fields), 200
    
    @auth_required("token")
    def patch(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Doctor not found"}, 404
        
        if not current_user.has_role("admin"):
            if not hasattr(current_user, 'doctor_profile') or current_user.doctor_profile.id != id:
                return {"message": "Not authorized"}, 401
        
        data = request.get_json()
        data["id"] = id
        item = service.update(data)
        # Invalidate both individual and list cache
        cache.delete_memoized(DoctorResource.get, DoctorResource, id)
        cache.delete("doctors_all")
        return marshal(item, doctor_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def delete(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "Doctor not found"}, 404
        result = service.delete(id)
        # Invalidate both individual and list cache
        cache.delete_memoized(DoctorResource.get, DoctorResource, id)
        cache.delete("doctors_all")
        return result, 200


class DoctorListResource(Resource):
    @cache.cached(timeout=300, key_prefix="doctors_all")  # 5 minutes cache
    def get(self):
        items = service.get_all()
        return marshal(items, doctor_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def post(self):
        """Admin creates a new doctor with user account"""
        data = request.get_json() or {}
        
        # Validate required fields
        if not data.get('name') or not data.get('email'):
            return {"message": "Name and email are required"}, 400
        if not data.get('password'):
            return {"message": "Password is required"}, 400
        
        try:
            item = service.create_with_user({
                'name': data.get('name'),
                'email': data.get('email'),
                'password': data.get('password'),
                'department_id': data.get('department_id'),
                'qualification': data.get('qualification'),
                'experience_years': data.get('experience_years'),
                'consultation_fee': data.get('consultation_fee'),
                'availability': data.get('availability'),
                'phone': data.get('phone')
            })
        except ServiceError as e:
            return {"message": str(e)}, 400
        
        cache.delete("doctors_all")
        return marshal(item, doctor_fields), 201


class DoctorSearchResource(Resource):
    def get(self):
        """Search doctors by name, specialization, or department"""
        query = request.args.get("q", "")
        department_id = request.args.get("department_id", type=int)
        
        items = service.search(query=query, department_id=department_id)
        return marshal(items, doctor_fields), 200
