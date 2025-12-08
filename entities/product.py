class Product:
    def __init__(self, name, description, category, price, status, quantity):
        self.name = name
        self.description = description
        self.category = category
        self.price = price
        self.status = status
        self.quantity = quantity

    def toDBCollection(self):
        return{
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'status': self.status,
            'quantity': self.quantity
        }