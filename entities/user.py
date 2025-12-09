from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User:
    def __init__(self, username, email, password, role="cliente", phone=None,address=None,position=None):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.role = role
        self.phone = phone
        self.address = address
        self.position = position
        self.created_at = datetime.utcnow()
        self.is_active = True
    
    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "phone": self.phone,
            "address": self.address,
            "position": self.position,
            "created_at": self.created_at,
            "is_active": self.is_active
        }
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def from_dict(data):
        user = User.__new__(User)
        user.username = data.get("username")
        user.email = data.get("email")
        user.password_hash = data.get("password_hash")
        user.role = data.get("role", "customer")
        user.phone = data.get("phone")
        user.address = data.get("address")
        user.position = data.get("position")
        user.created_at = data.get("created_at", datetime.utcnow())
        user.is_active = data.get("is_active", True)
        return user