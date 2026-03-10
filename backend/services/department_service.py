from models import db, Department
from services.service_errors import ServiceError


class DepartmentService:
    @staticmethod
    def get_all():
        return Department.query.all()
    
    @staticmethod
    def get_by_id(id):
        item = Department.query.get(id)
        if not item:
            raise ServiceError("Department not found")
        return item
    
    @staticmethod
    def create(data):
        item = Department(**data)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def delete(id):
        item = Department.query.get(id)
        if not item:
            raise ServiceError("Department not found")
        db.session.delete(item)
        db.session.commit()
        return {"message": f"Department {id} deleted successfully"}
    
    @staticmethod
    def update(data):
        item = Department.query.get(data["id"])
        if not item:
            raise ServiceError("Department not found")
        # Filter out auto-managed timestamp fields and id
        excluded_keys = {'id', 'created_at', 'updated_at'}
        for key in data:
            if key not in excluded_keys:
                setattr(item, key, data[key])
        db.session.commit()
        return item
