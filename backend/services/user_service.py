from models import db, User
from services.service_errors import ServiceError


class UserService:
    @staticmethod
    def get_all():
        return User.query.all()
    
    @staticmethod
    def get_pending():
        """Get users awaiting approval (inactive users)"""
        return User.query.filter_by(active=False).all()
    
    @staticmethod
    def get_by_id(id):
        item = User.query.get(id)
        if not item:
            raise ServiceError("User not found")
        return item
    
    @staticmethod
    def create(data):
        item = User(**data)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def delete(id):
        item = User.query.get(id)
        if not item:
            raise ServiceError("User not found")
        db.session.delete(item)
        db.session.commit()
        return {"message": f"User {id} deleted successfully"}
    
    @staticmethod
    def update(data):
        item = User.query.get(data["id"])
        if not item:
            raise ServiceError("User not found")
        # Filter out auto-managed timestamp fields and id
        excluded_keys = {'id', 'created_at', 'updated_at'}
        for key in data:
            if key not in excluded_keys:
                setattr(item, key, data[key])
        db.session.commit()
        return item
