class Product:
    def __init__(self, name, description, category, price, status, quantity, image=None):
        self.name = name
        self.description = description
        self.category = category
        self.price = price
        self.status = status
        self.quantity = quantity
        self.image = image  # nombre de la imagen, ej: "cupcake.jpg"

    def toDBCollection(self):
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'status': self.status,
            'quantity': self.quantity,
            'image': self.image  # guardamos en la base de datos
        }
