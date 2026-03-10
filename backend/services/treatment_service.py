from models import db, Treatment
from services.service_errors import ServiceError


class TreatmentService:
    @staticmethod
    def get_all():
        return Treatment.query.all()
    
    @staticmethod
    def get_by_id(id):
        item = Treatment.query.get(id)
        if not item:
            raise ServiceError("Treatment not found")
        return item
    
    @staticmethod
    def get_by_appointment(appointment_id):
        item = Treatment.query.filter_by(appointment_id=appointment_id).first()
        return item
    
    @staticmethod
    def create(data):
        item = Treatment(**data)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def delete(id):
        item = Treatment.query.get(id)
        if not item:
            raise ServiceError("Treatment not found")
        db.session.delete(item)
        db.session.commit()
        return {"message": f"Treatment {id} deleted successfully"}
    
    @staticmethod
    def update(data):
        item = Treatment.query.get(data["id"])
        if not item:
            raise ServiceError("Treatment not found")
        # Filter out auto-managed timestamp fields and id
        excluded_keys = {'id', 'created_at', 'updated_at'}
        for key in data:
            if key not in excluded_keys:
                setattr(item, key, data[key])
        db.session.commit()
        return item
