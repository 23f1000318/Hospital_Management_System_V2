from app import app
from models import db, Department
from flask_security.datastore import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
import os
import shutil

# Run from backend folder: python3 -m scripts.init_db

with app.app_context():
    exports_dir = os.path.join(app.instance_path, "exports")
    if os.path.exists(exports_dir):
        shutil.rmtree(exports_dir)

    db.drop_all()
    db.create_all()
    
    datastore: SQLAlchemyUserDatastore = app.datastore
    
    # Create roles
    admin_role = datastore.find_or_create_role("admin", description="Hospital administrator with full access")
    doctor_role = datastore.find_or_create_role("doctor", description="Medical professional")
    patient_role = datastore.find_or_create_role("patient", description="Patient user")
    
    # Create admin user
    if not datastore.find_user(email="admin@hospital.com"):
        datastore.create_user(
            email="admin@hospital.com",
            name="Admin",
            password=hash_password('admin123'),
            active=True
        )
    
    try:
        db.session.commit()
        print("✅ Roles and admin user created")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
    
    # Assign admin role
    admin_user = datastore.find_user(email="admin@hospital.com")
    datastore.add_role_to_user(admin_user, admin_role)
    
    # Create sample departments
    departments = [
        Department(name="General Medicine", description="General health checkups and treatments"),
        Department(name="Cardiology", description="Heart and cardiovascular system"),
        Department(name="Orthopedics", description="Bones, joints, and muscles"),
        Department(name="Pediatrics", description="Child healthcare"),
        Department(name="Dermatology", description="Skin conditions and treatments"),
        Department(name="Neurology", description="Brain and nervous system"),
        Department(name="Gynecology", description="Women's health"),
        Department(name="ENT", description="Ear, Nose, and Throat"),
    ]
    
    for dept in departments:
        db.session.add(dept)
    
    try:
        db.session.commit()
        print("✅ Departments created")
        print("✅ Database initialized successfully!")
        print("\n📋 Admin Login:")
        print("   Email: admin@hospital.com")
        print("   Password: admin123")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating departments: {e}")
