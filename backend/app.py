import sys
import os

# Ensure backend directory is in Python path for Celery workers
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Flask, jsonify
from config import LocalDevelopmentConfig
from dotenv import load_dotenv
from resources import auth_bp, api, api_bp
from flask_cors import CORS
from extensions import cache
from celery_factory import celery_init_app
from celery.schedules import crontab


def create_app():
    app = Flask(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Config
    app.config.from_object(LocalDevelopmentConfig)
    
    # Database connection
    from models import db, User, Role
    db.init_app(app)
    
    # Enable CORS - allow any localhost port for development
    CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*"], 
         resources={r"/api/*": {"origins": "*"}})
    
    # Flask-Security setup
    from flask_security.datastore import SQLAlchemyUserDatastore
    from extensions import security
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, datastore=datastore)
    app.datastore = datastore
    
    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    
    # Cache
    cache.init_app(app)
    
    # Celery config with beat schedule
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost:6379/0",
            result_backend="redis://localhost:6379/1",
            timezone='Asia/Kolkata',
            include=['tasks.reminder_tasks', 'tasks.report_tasks', 'tasks.export_tasks'],
            beat_schedule={
                # Daily appointment reminders - runs at 8:00 AM every day
                'daily-appointment-reminders': {
                    'task': 'tasks.reminder_tasks.send_daily_appointment_reminders',
                    'schedule': crontab(hour=13, minute=4),
                },
                # Monthly doctor activity reports - runs at 9:00 AM on 1st of every month
                'monthly-doctor-reports': {
                    'task': 'tasks.report_tasks.send_monthly_doctor_reports',
                    'schedule': crontab(hour=22, minute=36, day_of_month=11),
                },
            },
            # Removed task_routes - all tasks go to default queue
        ),
    )
    celery_app = celery_init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Global error handlers - return JSON so CORS headers are preserved
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"message": "Internal server error", "error": str(e)}), 500

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"message": "Not found"}), 404
    
    return app, celery_app


def find_available_port(start_port=5000, max_attempts=100):
    """Find an available port starting from start_port"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_attempts}")


app, celery = create_app()


if __name__ == "__main__":
    port = find_available_port(5000)
    print(f"Starting server on http://localhost:{port}")
    app.run(port=port)
