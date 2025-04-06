from flask import Flask
from flask_cors import CORS
import os
from enum import Enum

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173"],  # Your Vue.js frontend URL
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

app.config['SECRET_KEY'] = os.urandom(24)

class Roles(Enum):
    ADMIN = "admin"
    VENDOR = "vendor"

class Permissions(Enum):
    ADMIN_READ = "adminRead"
    ADMIN_WRITE = "adminWrite"
    VENDOR_READ = "vendorRead"
    VENDOR_WRITE = "vendorWrite"

ROLE_PERMISSIONS = {
    Roles.ADMIN.value: [
        Permissions.ADMIN_READ.value,
        Permissions.ADMIN_WRITE.value,
        Permissions.VENDOR_READ.value,
        Permissions.VENDOR_WRITE.value,
    ],
    Roles.VENDOR.value: [
        Permissions.VENDOR_READ.value,
        Permissions.VENDOR_WRITE.value,
    ]
} 