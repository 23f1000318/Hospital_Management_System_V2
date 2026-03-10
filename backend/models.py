from extensions import db
from datetime import datetime, timezone
from flask_security.core import UserMixin, RoleMixin

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# ==================== Authentication Models ====================

class User(BaseModel, UserMixin):
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    
    # Flask-Security-Too required fields
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    roles = db.relationship('Role', backref='bearers', secondary='user_roles')


class Role(BaseModel, RoleMixin):
    name = db.Column(db.String(50), unique=True, nullable=False)  # admin, doctor, patient
    description = db.Column(db.String(255), nullable=False)


class UserRoles(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete='CASCADE'))


# ==================== Department Model ====================

class Department(BaseModel):
    """Medical department/specialization"""
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Relationships
    doctors = db.relationship('Doctor', back_populates='department')


# ==================== Doctor Model ====================

class Doctor(BaseModel):
    """Doctor profile linked to a user"""
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer)
    consultation_fee = db.Column(db.Numeric(10, 2))
    availability = db.Column(db.String(500))  # JSON string for availability slots
    phone = db.Column(db.String(20))
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('doctor_profile', uselist=False))
    department = db.relationship('Department', back_populates='doctors')
    appointments = db.relationship('Appointment', back_populates='doctor')


# ==================== Patient Model ====================

class Patient(BaseModel):
    """Patient profile linked to a user"""
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  # Male, Female, Other
    blood_group = db.Column(db.String(5))  # A+, B-, O+, etc.
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(20))
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('patient_profile', uselist=False))
    appointments = db.relationship('Appointment', back_populates='patient')


# ==================== Appointment Model ====================

class Appointment(BaseModel):
    """Scheduled appointment between patient and doctor"""
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='booked')  # booked, completed, cancelled
    reason = db.Column(db.Text)  # Reason for visit
    
    # Foreign Keys
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    treatment = db.relationship('Treatment', back_populates='appointment', uselist=False)


# ==================== Treatment Model ====================

class Treatment(BaseModel):
    """Medical treatment record for an appointment"""
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    
    # Foreign Keys
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), unique=True)
    
    # Relationships
    appointment = db.relationship('Appointment', back_populates='treatment')
