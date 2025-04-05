from flask import Flask
import os
from enum import Enum
from typing import Dict, List

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

class Roles(Enum):
    ADMIN = "admin"
    VENDOR = "vendor"

class Permissions(Enum):
    ADMIN_READ = "adminRead"
    ADMIN_WRITE = "adminWrite"
    ADMIN_DELETE = "adminDelete"
    VENDOR_READ = "vendorRead"
    VENDOR_WRITE = "vendorWrite"
    VENDOR_DELETE = "vendorDelete"

ROLE_PERMISSIONS = {
    Roles.ADMIN.value: [
        Permissions.ADMIN_READ.value,
        Permissions.ADMIN_WRITE.value,
        Permissions.ADMIN_DELETE.value,
        Permissions.VENDOR_READ.value,
        Permissions.VENDOR_WRITE.value,
        Permissions.VENDOR_DELETE.value
    ],
    Roles.VENDOR.value: [
        Permissions.VENDOR_READ.value,
        Permissions.VENDOR_WRITE.value,
        Permissions.VENDOR_DELETE.value
    ]
} 