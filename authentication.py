from flask import request, jsonify
from cryptography.fernet import Fernet
from typing import Dict, List
import jwt
from datetime import datetime, timedelta
from functools import wraps
from config import app, ROLE_PERMISSIONS, Roles

class AuthenticationSystem:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self.users = {
            "admin@example.com": {
                "password": self.encrypt_password("admin123"),
                "role": "admin",
                "permissions": [
                    "adminRead",
                    "adminWrite",
                    "adminDelete",
                    "vendorRead",
                    "vendorWrite",
                    "vendorDelete"
                ]
            },
            "vendor@example.com": {
                "password": self.encrypt_password("vendor123"),
                "role": "vendor",
                "permissions": [
                    "vendorRead",
                    "vendorWrite",
                    "vendorDelete"
                ]
            },
            "suspiciousVendor@example.com": {
                "password": self.encrypt_password("suspiciousVendor123"),
                "role": "vendor",
                "permissions": [
                    "vendorRead",
                    "vendorWrite",
                    "vendorDelete",
                    "adminRead"
                ]
            }
        }

    def encrypt_password(self, password: str) -> bytes:
        return self.cipher_suite.encrypt(password.encode())

    def decrypt_password(self, encrypted_password: bytes) -> str:
        return self.cipher_suite.decrypt(encrypted_password).decode()

    def get_permissions_for_role(self, role: str) -> List[str]:
        return ROLE_PERMISSIONS.get(role, [])

    def is_valid_role(self, role: str) -> bool:
        return role in [r.value for r in Roles]

    def add_user(self, email: str, password: str, role: str) -> Dict:
        """
        Add a new user with role-based permissions
        Returns tuple (success, message, data)
        """
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

    def authenticate(self, email: str, password: str) -> bool:
        if email not in self.users:
            return False
        stored_password = self.decrypt_password(self.users[email]["password"])
        return stored_password == password

    def get_user_data(self, email: str) -> Dict:
        if email in self.users:
            return {
                "email": email,
                "role": self.users[email]["role"],
                "permissions": self.users[email]["permissions"]
            }
        return None

# Initialize the authentication system
auth_system = AuthenticationSystem()

def generate_token(user_data: Dict) -> str:
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
        return jsonify({'message': f'Error: {str(e)}'}), 500

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
        return jsonify({'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
