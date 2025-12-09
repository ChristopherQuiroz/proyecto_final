from datetime import datetime
class Product:
    def __init__(self, name, description, category_id, price, status="available", quantity=0, image=None, is_active=True, created_at=None):
        self.name = name
        self.description = description
        self.category_id = category_id     # referencia a Category._id
        self.price = price
        self.status = status               # available / unavailable
        self.quantity = quantity
        self.image = image
        self.is_active = is_active
        self.created_at = created_at if created_at else datetime.utcnow()

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id,
            "price": self.price,
            "status": self.status,
            "quantity": self.quantity,
            "image": self.image,
            "is_active": self.is_active,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data):
        return Product(
            name=data.get("name"),
            description=data.get("description"),
            category_id=data.get("category_id"),
            price=data.get("price"),
            status=data.get("status", "available"),
            quantity=data.get("quantity", 0),
            image=data.get("image"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at")
        )
