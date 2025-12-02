class Product:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
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