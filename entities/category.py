class Category:
    def __init__(self, name):
        self.name = name

    def toDBCollection(self):
        return {
            'name': self.name
        }