class product_category:
    def __init__(self):
        self.categories = {}
        self.products = []

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
        if category_name in self.categories:
            return [product for product in self.products if product.category == category_name]
        else:
            print("Category does not exist")
            return []
        
    def get_products_by_name(self, product_name):
        for product in self.products:
            if product.name.lower() == product_name.lower():
                return product
        return None