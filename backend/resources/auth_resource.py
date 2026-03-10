from flask import Blueprint, jsonify, request, current_app
from flask_security.utils import verify_password, hash_password
from models import User, Patient, db


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=['POST'])
def login():
    data = request.get_json()
    
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    if not verify_password(password, user.password):
        return jsonify({"message": "Wrong password"}), 400
    
    if not user.active:
        return jsonify({"message": "Account not active. Contact admin."}), 403
    
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "token": user.get_auth_token(),
        "role": user.roles[0].name if user.roles else None,
    }), 200


@auth_bp.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    
    # Only patients can self-register. Doctors are added by admin.
    if role != "patient":
        return jsonify({"message": "Only patients can self-register. Doctors must be added by admin."}), 400
    
    # Validate inputs
    if not name or not email or not password:
        return jsonify({"message": "Name, email, and password are required"}), 400
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User already exists"}), 400
    
    datastore = current_app.datastore
    
    # Create user (patients are auto-activated)
    datastore.create_user(
        name=name,
        email=email,
        password=hash_password(password),
        active=True
    )
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating user"}), 400
    
    # Assign patient role
    role_obj = datastore.find_role("patient")
    user = datastore.find_user(email=email)
    datastore.add_role_to_user(user, role_obj)
    
    # Create patient profile
    patient = Patient(user_id=user.id)
    db.session.add(patient)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating patient profile"}), 400
    
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": "patient",
        "message": "Registration successful"
    }), 201
