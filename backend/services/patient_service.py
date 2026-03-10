from models import db, Patient, User
from services.service_errors import ServiceError


class PatientService:
    @staticmethod
    def get_all():
        return Patient.query.all()
    
    @staticmethod
    def get_by_id(id):
        item = Patient.query.get(id)
        if not item:
            raise ServiceError("Patient not found")
        return item
    
    @staticmethod
    def get_by_user_id(user_id):
        item = Patient.query.filter_by(user_id=user_id).first()
        if not item:
            raise ServiceError("Patient profile not found")
        return item
    
    @staticmethod
    def search(query=None):
        """Search patients by name, email, phone, or ID"""
        result = Patient.query.join(User)
        
        if query:
            # Check if query is a numeric ID
            if query.isdigit():
                patient_by_id = Patient.query.get(int(query))
                if patient_by_id:
                    return [patient_by_id]
            
            search_term = f"%{query}%"
            result = result.filter(
                db.or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term),
                    Patient.phone.ilike(search_term),
                    Patient.emergency_contact.ilike(search_term)
                )
            )
        
        return result.all()
    
    @staticmethod
    def create(data):
        item = Patient(**data)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def delete(id):
        item = Patient.query.get(id)
        if not item:
            raise ServiceError("Patient not found")
        db.session.delete(item)
        db.session.commit()
        return {"message": f"Patient {id} deleted successfully"}
    
    @staticmethod
    def update(data):
        item = Patient.query.get(data["id"])
        if not item:
            raise ServiceError("Patient not found")
        
        # Only update fields that are actually provided (not None)
        # Skip 'id' and 'user_id' to avoid accidentally breaking relationships
        allowed_fields = ['date_of_birth', 'gender', 'blood_group', 'phone', 'address', 'emergency_contact']
        for key in data:
            if key in allowed_fields and data[key] is not None:
                setattr(item, key, data[key])
        
        db.session.commit()
        return item
