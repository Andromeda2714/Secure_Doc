from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.verifier import verifier_bp
from routes.user import user_bp

__all__ = ['auth_bp', 'admin_bp', 'verifier_bp', 'user_bp']
