from flask_restful import Api
from flask import Blueprint

from resources.auth_resource import auth_bp
from .department_resource import DepartmentListResource, DepartmentResource
from .doctor_resource import DoctorListResource, DoctorResource, DoctorSearchResource
from .patient_resource import PatientListResource, PatientResource, PatientSearchResource, AdminPatientHistoryResource
from .appointment_resource import AppointmentListResource, AppointmentResource
from .treatment_resource import TreatmentListResource, TreatmentResource
from .user_resource import UserListResource, UserResource, PendingUsersResource, approve_user, toggle_user_active
from .dashboard_resource import DashboardResource, AdminPatientProfileResource, AdminDoctorProfileResource
from .doctor_dashboard_resource import (
    DoctorDashboardResource, 
    DoctorAvailabilityResource, 
    DoctorAppointmentStatusResource,
    DoctorTreatmentResource,
    DoctorPatientHistoryResource
)
from .patient_dashboard_resource import (
    PatientDashboardResource,
    PatientProfileResource,
    DoctorAvailabilityPublicResource,
    PatientBookAppointmentResource,
    PatientCancelAppointmentResource,
    PatientRescheduleAppointmentResource,
    PatientTreatmentHistoryResource
)
from .export_resource import (
    PatientExportResource,
    ExportStatusResource,
    ExportDownloadResource,
    PatientExportHistoryResource
)

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

# Dashboard route (admin)
api.add_resource(DashboardResource, "/dashboard")
api.add_resource(AdminPatientProfileResource, "/admin/patients/<int:id>/profile")
api.add_resource(AdminDoctorProfileResource, "/admin/doctors/<int:id>/profile")

# Doctor Dashboard (doctor role)
api.add_resource(DoctorDashboardResource, "/doctor/dashboard")
api.add_resource(DoctorAvailabilityResource, "/doctor/availability")
api.add_resource(DoctorAppointmentStatusResource, "/doctor/appointments/<int:appointment_id>/status")
api.add_resource(DoctorTreatmentResource, "/doctor/appointments/<int:appointment_id>/treatment")
api.add_resource(DoctorPatientHistoryResource, "/doctor/patients/<int:patient_id>/history")

# Patient Dashboard (patient role)
api.add_resource(PatientDashboardResource, "/patient/dashboard")
api.add_resource(PatientProfileResource, "/patient/profile")
api.add_resource(PatientTreatmentHistoryResource, "/patient/history")
api.add_resource(DoctorAvailabilityPublicResource, "/doctors/<int:doctor_id>/availability")
api.add_resource(PatientBookAppointmentResource, "/patient/book-appointment")
api.add_resource(PatientCancelAppointmentResource, "/patient/appointments/<int:appointment_id>/cancel")
api.add_resource(PatientRescheduleAppointmentResource, "/patient/appointments/<int:appointment_id>/reschedule")

# Department routes
api.add_resource(DepartmentListResource, "/departments")
api.add_resource(DepartmentResource, "/departments/<int:id>")

# Doctor routes
api.add_resource(DoctorListResource, "/doctors")
api.add_resource(DoctorResource, "/doctors/<int:id>")
api.add_resource(DoctorSearchResource, "/doctors/search")

# Patient routes
api.add_resource(PatientListResource, "/patients")
api.add_resource(PatientResource, "/patients/<int:id>")
api.add_resource(PatientSearchResource, "/patients/search")
api.add_resource(AdminPatientHistoryResource, "/admin/patients/<int:patient_id>/history")

# Appointment routes
api.add_resource(AppointmentListResource, "/appointments")
api.add_resource(AppointmentResource, "/appointments/<int:id>")

# Treatment routes
api.add_resource(TreatmentListResource, "/treatments")
api.add_resource(TreatmentResource, "/treatments/<int:id>")

# User routes
api.add_resource(UserListResource, "/users")
api.add_resource(UserResource, "/users/<int:id>")
api.add_resource(PendingUsersResource, "/users/pending")

# User approval route (admin only)
api_bp.add_url_rule("/users/<int:id>/approve", view_func=approve_user, methods=["PATCH"])

# User blacklist/activate toggle route (admin only)
api_bp.add_url_rule("/users/<int:id>/toggle-active", view_func=toggle_user_active, methods=["PATCH"])

# Export routes (patient)
api.add_resource(PatientExportResource, "/patient/export")
api.add_resource(PatientExportHistoryResource, "/patient/exports")
api.add_resource(ExportStatusResource, "/exports/status/<string:task_id>")
api.add_resource(ExportDownloadResource, "/exports/download/<string:filename>")
