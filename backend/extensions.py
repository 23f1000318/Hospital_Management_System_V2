from flask_sqlalchemy import SQLAlchemy
from flask_security.core import Security
from flask_caching import Cache

db = SQLAlchemy()
security = Security()

# Cache is initialized with app config in app.py
# Default to SimpleCache for fallback, Redis in production
cache = Cache()
