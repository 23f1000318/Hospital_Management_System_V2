from models import db, Doctor, User, Department, Role, UserRoles
from services.service_errors import ServiceError
from flask_security.utils import hash_password
import uuid


class DoctorService:
    @staticmethod
    def get_all():
        return Doctor.query.all()
    
    @staticmethod
    def get_by_id(id):
        item = Doctor.query.get(id)
        if not item:
            raise ServiceError("Doctor not found")
        return item
    
    @staticmethod
    def get_by_user_id(user_id):
        item = Doctor.query.filter_by(user_id=user_id).first()
        if not item:
            raise ServiceError("Doctor profile not found")
        return item
    
    @staticmethod
    def get_by_department(department_id):
        return Doctor.query.filter_by(department_id=department_id).all()
    
    @staticmethod
    def search(query=None, department_id=None):
        """Search doctors by name or specialization"""
        result = Doctor.query.join(User).join(Department, isouter=True)
        
        if query:
            search_term = f"%{query}%"
            result = result.filter(
                db.or_(
                    User.name.ilike(search_term),
                    Department.name.ilike(search_term),
                    Doctor.qualification.ilike(search_term)
                )
            )
        
        if department_id:
            result = result.filter(Doctor.department_id == department_id)
        
        return result.all()
    
    @staticmethod
    def create(data):
        item = Doctor(**data)
        db.session.add(item)
        db.session.commit()
        return item
    
    @staticmethod
    def create_with_user(data):
        """Admin creates doctor with user account"""
        # Check if user with email already exists
        if User.query.filter_by(email=data.get('email')).first():
            raise ServiceError("A user with this email already exists")
        
        # Create user
        user = User(
            name=data.get('name'),
            email=data.get('email'),
            password=hash_password(data.get('password')),
            fs_uniquifier=str(uuid.uuid4()),
            active=True
        )
        db.session.add(user)
        db.session.flush()  # Get user.id without committing
        
        # Assign doctor role
        doctor_role = Role.query.filter_by(name='doctor').first()
        if doctor_role:
            user.roles.append(doctor_role)
        
        # Create doctor profile
        doctor = Doctor(
            user_id=user.id,
            department_id=data.get('department_id'),
            qualification=data.get('qualification', ''),
            experience_years=data.get('experience_years', 0),
            consultation_fee=data.get('consultation_fee', 0),
            availability=data.get('availability', ''),
            phone=data.get('phone', '')
        )
        db.session.add(doctor)
        db.session.commit()
        return doctor

    @staticmethod
    def delete(id):
        item = Doctor.query.get(id)
        if not item:
            raise ServiceError("Doctor not found")
        
        # Get the associated user before deleting doctor
        user_id = item.user_id
        user = User.query.get(user_id) if user_id else None
        
        # Delete doctor profile first
        db.session.delete(item)
        
        # Delete user_roles entries for this user
        if user_id:
            UserRoles.query.filter_by(user_id=user_id).delete()
        
        # Also delete the associated user account
        if user:
            db.session.delete(user)
        
        db.session.commit()
        return {"message": f"Doctor {id} deleted successfully"}
    
    @staticmethod
    def update(data):
        item = Doctor.query.get(data["id"])
        if not item:
            raise ServiceError("Doctor not found")
        # Filter out auto-managed timestamp fields and id
        excluded_keys = {'id', 'created_at', 'updated_at'}
        for key in data:
            if key not in excluded_keys:
                setattr(item, key, data[key])
        db.session.commit()
        return item
