from datetime import datetime
class Category:
    def __init__(self, name, icon="default.jpg", description="", is_active=True, created_at=None):
        self.name = name
        self.icon = icon
        self.description = description
        self.is_active = is_active
        self.created_at = created_at if created_at else datetime.utcnow()

    def to_dict(self):
        return {
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
        
    @staticmethod
    def from_dict(data):
        return Category(
            name=data.get("name"),
            icon=data.get("icon"),
            description=data.get("description"),
            is_active=data.get("is_active"),
            created_at=data.get("created_at")
        )