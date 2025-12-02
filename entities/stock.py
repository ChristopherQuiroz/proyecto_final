class Stock:
    def __init__(self, product_name, Minimun_Quantity):
        self.product_name = product_name
        self.Minimun_Quantity = Minimun_Quantity

    def toDBCollection(self):
        return {
            'product_name': self.product_name,
            'Minimun_Quantity': self.Minimun_Quantity
        }