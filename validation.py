from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime
from config import app, ROLE_PERMISSIONS
from authentication import auth_system
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


validation_bp = Blueprint('validation', __name__)

def is_valid_permission(permission: str) -> bool:
    """Check if permission exists in any role"""
    all_permissions = set()
    for permissions in ROLE_PERMISSIONS.values():
        all_permissions.update(permissions)
    return permission in all_permissions

def log_suspicious_activity(email: str, permission: str, role: str):
    """Log suspicious permission usage to CloudWatch"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User: {email}, Permission: {permission}, Mismatched Role: {role}"
    logger.warning(log_entry)

@validation_bp.route('/api/validation/token', methods=['POST'])
def verify_permission():
    try:
        data = request.get_json()
        token = data.get('token')
        permission = data.get('permission')

        if not token or not permission:
            return jsonify({'message': 'Missing token or permission'}), 400

        # Check if permission is valid
        if not is_valid_permission(permission):
            return jsonify({'message': 'Invalid permission'}), 400

        try:
            # Decode token
            token_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        email = token_data.get('email')
        token_permissions = token_data.get('permissions', [])
        
        # Check if user exists in database
        user_data = auth_system.get_user_data(email)
        if not user_data:
            return jsonify({'message': 'User not found'}), 401

        # Check if permission is in token
        if permission not in token_permissions:
            return jsonify({'message': 'Unauthorized - Permission not in token'}), 401

        # Get role's allowed permissions
        role_permissions = auth_system.get_permissions_for_role(user_data['role'])

        # Check if permission is in user's permissions but not in role's permissions
        if permission in user_data['permissions'] and permission not in role_permissions:
            log_suspicious_activity(email, permission, user_data['role'])
            return jsonify({'message': 'Permission verified successfully (logged for review)'}), 200

        # Check if permission is in user's permissions and role's permissions
        if permission in user_data['permissions'] and permission in role_permissions:
            return jsonify({'message': 'Permission verified successfully'}), 200

        return jsonify({'message': 'Unauthorized'}), 401

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500 