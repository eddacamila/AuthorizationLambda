from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime
from config import app, ROLE_PERMISSIONS
from authentication import auth_system
import os
import logging
import traceback
import boto3

validation_bp = Blueprint('validation', __name__)
logger = logging.getLogger()
logger.setLevel(logging.WARNING)

def is_valid_permission(permission: str) -> bool:
    """Check if permission exists in any role"""
    all_permissions = set()
    for permissions in ROLE_PERMISSIONS.values():
        all_permissions.update(permissions)
    return permission in all_permissions

def upload_to_s3(log_entry: str, bucket_name: str):
    """Upload log entry to S3 bucket"""
    try:
        s3_client = boto3.client('s3')
        # Create a timestamp-based key for the log entry
        timestamp = datetime.utcnow().strftime("%Y/%m/%d/suspicious_permissions.log")
        
        # Try to get existing log content
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=timestamp)
            existing_content = response['Body'].read().decode('utf-8')
            log_content = existing_content + log_entry
        except e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                log_content = log_entry
            else:
                logger.error(f"Error retrieving existing log: {str(e)}")
                return False

        # Upload the log content
        s3_client.put_object(
            Bucket=bucket_name,
            Key=timestamp,
            Body=log_content.encode('utf-8'),
            ContentType='text/plain'
        )
        return True
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        return False

def log_suspicious_activity(email: str, permission: str, role: str):
    """Log suspicious permission usage"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User: {email}, Permission: {permission}, Mismatched Role: {role}\n"
    
    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        logger.warning(log_entry)
        
        # Upload to S3
        bucket_name = os.environ.get('LOG_BUCKET_NAME')
        if bucket_name:
            upload_success = upload_to_s3(log_entry, bucket_name)
            if not upload_success:
                logger.error("Failed to upload log to S3")
    else:
        # Local file logging
        log_directory = "logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        
        log_file_path = os.path.join(log_directory, "suspicious_permissions.log")
        with open(log_file_path, "a") as log_file:
            log_file.write(log_entry)

@validation_bp.route('/api/validation/token', methods=['POST'])
def verify_permission():
    try:
        data = request.get_json()
        token = data.get('token')
        permission = data.get('permission')

        if not token or not permission:
            return jsonify({'message': 'Missing token or permission'}), 400

        if not is_valid_permission(permission):
            return jsonify({'message': 'Invalid permission'}), 400

        try:
            token_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        email = token_data.get('email')
        token_permissions = token_data.get('permissions', [])
        
        user_data = auth_system.get_user_data(email)
        if not user_data:
            return jsonify({'message': 'User not found'}), 401

        # Check if permission is in token
        if permission not in token_permissions:
            return jsonify({'message': 'Unauthorized - Permission not in token'}), 401

        role_permissions = auth_system.get_permissions_for_role(user_data['role'])

        if permission in user_data['permissions'] and permission not in role_permissions:
            log_suspicious_activity(email, permission, user_data['role'])
            return jsonify({'message': 'Permission verified successfully (logged for review)'}), 200

        if permission in user_data['permissions'] and permission in role_permissions:
            return jsonify({'message': 'Permission verified successfully'}), 200

        return jsonify({'message': 'Unauthorized'}), 401

    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in verify_permission: {error_details}")
        return jsonify({
            'message': 'Internal server error',
            'error': str(e)
        }), 500 