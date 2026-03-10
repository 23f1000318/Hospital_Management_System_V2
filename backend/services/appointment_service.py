from models import db, Appointment
from services.service_errors import ServiceError


# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    'booked': ['completed', 'cancelled'],
    'completed': [],  # Cannot change once completed
    'cancelled': [],  # Cannot change once cancelled
}


class AppointmentService:
    @staticmethod
    def get_all():
        return Appointment.query.all()
    
    @staticmethod
    def get_by_id(id):
        item = Appointment.query.get(id)
        if not item:
            raise ServiceError("Appointment not found")
        return item
    
    @staticmethod
    def get_by_patient(patient_id):
        return Appointment.query.filter_by(patient_id=patient_id).all()
    
    @staticmethod
    def get_by_doctor(doctor_id):
        return Appointment.query.filter_by(doctor_id=doctor_id).all()
    
    @staticmethod
    def get_patient_history(patient_id):
        """Get all completed appointments with treatments for a patient"""
        return Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.status == 'completed'
        ).order_by(Appointment.date.desc()).all()
    
    @staticmethod
    def check_conflict(doctor_id, date, time, exclude_id=None):
        """Check if there's already a booked appointment at this slot"""
        query = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date == date,
            Appointment.time == time,
            Appointment.status == 'booked'
        )
        if exclude_id:
            query = query.filter(Appointment.id != exclude_id)
        return query.first() is not None
    
    @staticmethod
    def validate_status_transition(current_status, new_status):
        """Validate if status transition is allowed"""
        allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
        return new_status in allowed
    
    @staticmethod
    def create(data):
        # Check for conflicts before creating
        if AppointmentService.check_conflict(data['doctor_id'], data['date'], data['time']):
            raise ServiceError("This time slot is already booked")
        item = Appointment(**data)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def delete(id):
        item = Appointment.query.get(id)
        if not item:
            raise ServiceError("Appointment not found")
        db.session.delete(item)
        db.session.commit()
        return {"message": f"Appointment {id} deleted successfully"}
    
    @staticmethod
    def update(data):
        item = Appointment.query.get(data["id"])
        if not item:
            raise ServiceError("Appointment not found")
        
        # Validate status transition if status is being changed
        if 'status' in data and data['status'] != item.status:
            if not AppointmentService.validate_status_transition(item.status, data['status']):
                raise ServiceError(f"Cannot change status from '{item.status}' to '{data['status']}'")
        
        # Check for conflicts if date/time is being changed
        if ('date' in data or 'time' in data) and item.status == 'booked':
            new_date = data.get('date', item.date)
            new_time = data.get('time', item.time)
            if AppointmentService.check_conflict(item.doctor_id, new_date, new_time, exclude_id=item.id):
                raise ServiceError("This time slot is already booked")
        
        # Filter out auto-managed timestamp fields and id
        excluded_keys = {'id', 'created_at', 'updated_at'}
        for key in data:
            if key not in excluded_keys:
                setattr(item, key, data[key])
        db.session.commit()
        return item
