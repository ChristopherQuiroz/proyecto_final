class Category:
    def __init__(self, name, icono="default.jpg", descripcion=""):
        self.name = name
        self.icono = icono
        self.descripcion = descripcion

    def toDBCollection(self):
        return {
            "name": self.name,
            "icono": self.icono,
            "descripcion": self.descripcion
        }

class ProductCategoryManager:
    def __init__(self):
        self.categories = {}  # {nombre_categoria: Category}
        self.products = []    # Lista de Product

    def add_category(self, category):
        if category.name not in self.categories:
            self.categories[category.name] = category
            return True
        else:
            print("Category already exists")
            return False

    def add_product(self, product):
        if product.category in self.categories:
            self.products.append(product)
            return True
        else:
            print("Category does not exist")
            return False

    def get_products_by_category(self, category_name):
        return [p for p in self.products if p.category == category_name]

    def get_products_by_name(self, product_name):
        for product in self.products:
            if product.name.lower() == product_name.lower():
                return product
        return None

# Instancia global
category_manager = ProductCategoryManager()
