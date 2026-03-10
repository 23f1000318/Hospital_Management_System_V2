from flask import request
from flask_restful import Resource, marshal, reqparse
from flask_security import current_user
from flask_security.decorators import roles_required, auth_required
from services import DepartmentService
from services.service_errors import ServiceError
from .marshal_fields import department_fields
from extensions import cache


parser = reqparse.RequestParser()
parser.add_argument("name", type=str, required=True)
parser.add_argument("description", type=str)

service = DepartmentService


class DepartmentResource(Resource):
    @cache.memoize(timeout=3600)  # 1 hour cache for individual departments
    def get(self, id):
        item = service.get_by_id(id)
        return marshal(item, department_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def put(self, id):
        try:
            item = service.get_by_id(id)
        except ServiceError as e:
            return {"message": str(e)}, 404
        args = parser.parse_args()
        args["id"] = id
        item = service.update(args)
        cache.delete_memoized(DepartmentResource.get, DepartmentResource, id)
        cache.delete("departments_all")
        return marshal(item, department_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def patch(self, id):
        try:
            item = service.get_by_id(id)
        except ServiceError as e:
            return {"message": str(e)}, 404
        data = request.get_json()
        data["id"] = id
        item = service.update(data)
        cache.delete_memoized(DepartmentResource.get, DepartmentResource, id)
        cache.delete("departments_all")
        return marshal(item, department_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def delete(self, id):
        try:
            item = service.get_by_id(id)
        except ServiceError as e:
            return {"message": str(e)}, 404
        
        try:
            result = service.delete(id)
        except Exception as e:
            return {"message": f"Cannot delete department: {str(e)}"}, 400
        
        # Invalidate both individual and list cache
        cache.delete_memoized(DepartmentResource.get, DepartmentResource, id)
        cache.delete("departments_all")
        return result, 200


class DepartmentListResource(Resource):
    @cache.cached(timeout=3600, key_prefix="departments_all")  # 1 hour cache
    def get(self):
        items = service.get_all()
        return marshal(items, department_fields), 200
    
    @auth_required("token")
    @roles_required("admin")
    def post(self):
        args = parser.parse_args()
        item = service.create(args)
        cache.delete("departments_all")
        return marshal(item, department_fields), 201
