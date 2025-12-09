class Stock:
    def __init__(self, product_name, minimum_quantity):
        self.product_name = product_name
        self.minimum_quantity = minimum_quantity

    def to_dict(self):
        return {
            "product_name": self.product_name,
            "minimum_quantity": self.minimum_quantity
        }
    
    @staticmethod
    def from_dict(data):
        return Stock(
            product_name=data.get("product_name"),
            minimum_quantity=data.get("minimum_quantity")
        )
