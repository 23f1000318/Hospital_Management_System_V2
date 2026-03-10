from flask import request
from flask_restful import Resource, marshal, reqparse
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from services import UserService, DoctorService
from models import db, Doctor
from .marshal_fields import user_fields
from extensions import cache


parser = reqparse.RequestParser()
parser.add_argument("name", type=str)
parser.add_argument("email", type=str)

service = UserService


class UserResource(Resource):
    @auth_required("token")
    def get(self, id):
        # Users can only view their own profile, admin can view any
        if not current_user.has_role("admin") and current_user.id != id:
            return {"message": "Not authorized"}, 401
        
        item = service.get_by_id(id)
        return marshal(item, user_fields), 200
    
    @auth_required("token")
    def put(self, id):
        if not current_user.has_role("admin") and current_user.id != id:
            return {"message": "Not authorized"}, 401
        
        item = service.get_by_id(id)
        if not item:
            return {"message": "User not found"}, 404
        
        args = parser.parse_args()
        args["id"] = id
        item = service.update(args)
        return marshal(item, user_fields), 200
    
    @auth_required("token")
    def patch(self, id):
        if not current_user.has_role("admin") and current_user.id != id:
            return {"message": "Not authorized"}, 401
        
        item = service.get_by_id(id)
        if not item:
            return {"message": "User not found"}, 404
        
        data = request.get_json()
        data["id"] = id
        item = service.update(data)
        return marshal(item, user_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def delete(self, id):
        item = service.get_by_id(id)
        if not item:
            return {"message": "User not found"}, 404
        result = service.delete(id)
        return result, 200


class UserListResource(Resource):
    @auth_required("token")
    @roles_required("admin")
    def get(self):
        items = service.get_all()
        return marshal(items, user_fields), 200

class PendingUsersResource(Resource):
    @auth_required("token")
    @roles_required("admin")
    def get(self):
        """Get users pending approval"""
        items = service.get_pending()
        return marshal(items, user_fields)

@auth_required("token")
@roles_required("admin")
def approve_user(id):
    """Admin endpoint to activate a user (approve doctor registration)"""
    user = service.get_by_id(id)
    if not user:
        return {"message": "User not found"}, 404
    
    # Activate the user
    user = service.update({"id": id, "active": True})
    
    # If user is a doctor, create doctor profile
    if user.has_role("doctor"):
        existing_doctor = Doctor.query.filter_by(user_id=user.id).first()
        if not existing_doctor:
            doctor = Doctor(user_id=user.id)
            db.session.add(doctor)
            db.session.commit()
    
    return marshal(user, user_fields)


@auth_required("token")
@roles_required("admin")
def toggle_user_active(id):
    """Admin endpoint to toggle user active status (blacklist/activate)"""
    user = service.get_by_id(id)
    if not user:
        return {"message": "User not found"}, 404
    
    # Toggle active status
    new_status = not user.active
    user = service.update({"id": id, "active": new_status})
    
    # Invalidate caches since user status affects display
    cache.delete("doctors_all")
    cache.delete("patients_all")
    
    action = "activated" if new_status else "blacklisted"
    return {"message": f"User {action} successfully", "user": marshal(user, user_fields)}
