from flask_restful import fields


# Custom field for time formatting (HH:MM)
class TimeField(fields.Raw):
    def format(self, value):
        if value is None:
            return None
        return value.strftime("%H:%M")


# User fields
user_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "email": fields.String,
    "active": fields.Boolean,
    "created_at": fields.DateTime,
}

# Department fields
department_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "description": fields.String,
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime,
}

# Doctor fields
doctor_fields = {
    "id": fields.Integer,
    "user_id": fields.Integer,
    "user": fields.Nested(user_fields),
    "department_id": fields.Integer,
    "department": fields.Nested(department_fields),
    "qualification": fields.String,
    "experience_years": fields.Integer,
    "consultation_fee": fields.Float,
    "availability": fields.String,
    "phone": fields.String,
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime,
}

# Patient fields
patient_fields = {
    "id": fields.Integer,
    "user_id": fields.Integer,
    "user": fields.Nested(user_fields),
    "date_of_birth": fields.String,
    "gender": fields.String,
    "blood_group": fields.String,
    "phone": fields.String,
    "address": fields.String,
    "emergency_contact": fields.String,
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime,
}

# Treatment fields (basic, for nesting)
treatment_fields_basic = {
    "id": fields.Integer,
    "diagnosis": fields.String,
    "prescription": fields.String,
    "notes": fields.String,
    "follow_up_date": fields.String,
    "created_at": fields.DateTime,
}

# Appointment fields
appointment_fields = {
    "id": fields.Integer,
    "patient_id": fields.Integer,
    "doctor_id": fields.Integer,
    "date": fields.String,
    "time": TimeField(),
    "status": fields.String,
    "reason": fields.String,
    "patient": fields.Nested(patient_fields),
    "doctor": fields.Nested(doctor_fields),
    "treatment": fields.Nested(treatment_fields_basic),
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime,
}

# Treatment fields (full)
treatment_fields = {
    "id": fields.Integer,
    "appointment_id": fields.Integer,
    "diagnosis": fields.String,
    "prescription": fields.String,
    "notes": fields.String,
    "follow_up_date": fields.String,
    "appointment": fields.Nested({
        "id": fields.Integer,
        "date": fields.String,
        "time": TimeField(),
        "status": fields.String,
    }),
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime,
}
