from flask import request, jsonify
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64
from typing import Dict, List
import jwt
from datetime import datetime, timedelta
from functools import wraps
from config import app, ROLE_PERMISSIONS, Roles, ENCRYPTION_KEY
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.WARNING)

class AuthenticationSystem:
    def __init__(self):
        # Use the simple key from config
        self.key = ENCRYPTION_KEY
            
        self.users = {
            "admin@example.com": {
                "password": self.encrypt_password("admin123"),
                "role": "admin",
                "permissions": [
                    "adminRead",
                    "adminWrite",
                    "vendorRead",
                    "vendorWrite",
                ]
            },
            "vendor@example.com": {
                "password": self.encrypt_password("vendor123"),
                "role": "vendor",
                "permissions": [
                    "vendorRead",
                    "vendorWrite",
                ]
            },
            "suspiciousVendor@example.com": {
                "password": self.encrypt_password("suspiciousVendor123"),
                "role": "vendor",
                "permissions": [
                    "vendorRead",
                    "vendorWrite",
                    "adminRead"
                ]
            }
        }

    def encrypt_password(self, password: str) -> str:
        try:
            cipher = AES.new(self.key, AES.MODE_CBC)
            ct_bytes = cipher.encrypt(pad(password.encode(), AES.block_size))
            iv = base64.b64encode(cipher.iv).decode('utf-8')
            ct = base64.b64encode(ct_bytes).decode('utf-8')
            return f"{iv}:{ct}"
        except Exception as e:
            logger.error(f"Error encrypting password: {str(e)}")
            raise

    def decrypt_password(self, encrypted_password: str) -> str:
        try:
            iv, ct = encrypted_password.split(':')
            iv = base64.b64decode(iv)
            ct = base64.b64decode(ct)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting password: {str(e)}")
            raise

    def get_permissions_for_role(self, role: str) -> List[str]:
        return ROLE_PERMISSIONS.get(role, [])

    def is_valid_role(self, role: str) -> bool:
        return role in [r.value for r in Roles]

    def add_user(self, email: str, password: str, role: str) -> Dict:
        """
        Add a new user with role-based permissions
        Returns tuple (success, message, data)
        """
        try:
            if email in self.users:
                return {
                    'success': False,
                    'message': 'Email already exists',
                    'status_code': 400
                }

            if not self.is_valid_role(role):
                return {
                    'success': False,
                    'message': f'Invalid role. Allowed roles: {[r.value for r in Roles]}',
                    'status_code': 400
                }

            permissions = self.get_permissions_for_role(role)
            
            self.users[email] = {
                "password": self.encrypt_password(password),
                "role": role,
                "permissions": permissions
            }

            return {
                'success': True,
                'message': 'User created successfully',
                'data': {
                    'email': email,
                    'role': role,
                    'permissions': permissions
                },
                'status_code': 201
            }
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}")
            return {
                'success': False,
                'message': 'Error adding user',
                'status_code': 500
            }

    def authenticate(self, email: str, password: str) -> bool:
        try:
            if email not in self.users:
                return False
            stored_password = self.decrypt_password(self.users[email]["password"])
            return stored_password == password
        except Exception as e:
            logger.error(f"Error in authentication: {str(e)}")
            return False

    def get_user_data(self, email: str) -> Dict:
        try:
            if email in self.users:
                return {
                    "email": email,
                    "role": self.users[email]["role"],
                    "permissions": self.users[email]["permissions"]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return None

# Initialize the authentication system
auth_system = AuthenticationSystem()

def generate_token(user_data: Dict) -> str:
    try:
        token = jwt.encode(
            {
                'email': user_data['email'],
                'role': user_data['role'],
                'permissions': user_data['permissions'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return token
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        if not all([email, password, role]):
            return jsonify({
                'message': 'Missing required fields: email, password, role'
            }), 400

        result = auth_system.add_user(email, password, role)
        
        if not result['success']:
            return jsonify({'message': result['message']}), result['status_code']

        token = generate_token(result['data'])
        
        return jsonify({
            'message': result['message'],
            'token': token,
            'user': result['data']
        }), result['status_code']

    except Exception as e:
        logger.error(f"Error in register endpoint: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Missing email or password'}), 400

        if auth_system.authenticate(email, password):
            user_data = auth_system.get_user_data(email)
            token = generate_token(user_data)
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user_data
            }), 200
        else:
            return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
