from bson import ObjectId

class OrderDetail:
    def __init__(self, product_id, quantity, subtotal):
        self.product_id = ObjectId(product_id)  
        self.quantity = quantity
        self.subtotal = subtotal

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "quantity": self.quantity,
            "subtotal": self.subtotal
        }

    @staticmethod
    def from_dict(data):
        return OrderDetail(
            product_id=data.get("product_id"),
            quantity=data.get("quantity"),
            subtotal=data.get("subtotal")
        )
