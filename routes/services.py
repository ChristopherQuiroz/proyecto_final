from database import dbConnection
from entities.product import Product
from entities.category import Category, category_manager
from entities.stock import Stock
from entities.user import User
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash

db = dbConnection()

# ============================
#        CATEGORÍAS
# ============================

def get_all_categories(with_count=False):
    categories_collection = db['categories']
    products_collection = db['products']
    categorias = list(categories_collection.find())
    if with_count:
        for cat in categorias:
            cat['cantidad_productos'] = products_collection.count_documents({'category': cat['name']})
    return categorias

def get_category_by_name(name):
    return db['categories'].find_one({'name': name})

def create_category(name, icono="default.png", descripcion=""):
    if not name:
        return False, "El nombre es obligatorio"
    if get_category_by_name(name):
        return False, "La categoría ya existe"
    categoria = Category(name, icono, descripcion)
    db['categories'].insert_one(categoria.toDBCollection())
    category_manager.add_category(categoria)
    return True, "Categoría creada correctamente"

def update_category(old_name, new_name, icono=None, descripcion=None):
    update_data = {}
    if new_name:
        update_data['name'] = new_name
    if icono:
        update_data['icono'] = icono
    if descripcion:
        update_data['descripcion'] = descripcion
    if not update_data:
        return False, "Nada que actualizar"
    result = db['categories'].update_one({"name": old_name}, {"$set": update_data})
    if result.matched_count > 0:
        return True, "Categoría actualizada"
    return False, "No se encontró la categoría"

def delete_category(name):
    products_collection = db['products']
    if products_collection.count_documents({'category': name}) > 0:
        return False, "No se puede eliminar: hay productos en esta categoría"
    result = db['categories'].delete_one({'name': name})
    if result.deleted_count > 0:
        return True, "Categoría eliminada"
    return False, "No se encontró la categoría"

# ============================
#         PRODUCTOS
# ============================

def get_all_products(category=None, low_stock=False, top_n=None):
    query = {}
    if category:
        query['category'] = category
    if low_stock:
        query['quantity'] = {'$lt': 5}
    cursor = db['products'].find(query)
    if top_n:
        cursor = cursor.sort('price', -1).limit(top_n)
    return list(cursor)

def get_product_by_id(product_id):
    try:
        return db['products'].find_one({'_id': ObjectId(product_id)})
    except:
        return None

def create_product(name, description, category, price, status, quantity, image_filename=None):
    if not name or not category:
        return False, "Nombre y categoría son obligatorios"
    if not get_category_by_name(category):
        return False, "La categoría no existe"
    try:
        product = Product(name, description, category, price, status, quantity, image_filename)
        db['products'].insert_one(product.toDBCollection())
        category_manager.add_product(product)
        return True, "Producto creado"
    except Exception as e:
        return False, f"Error al crear producto: {str(e)}"

def update_product(product_id, data):
    try:
        result = db['products'].update_one({'_id': ObjectId(product_id)}, {'$set': data})
        if result.matched_count > 0:
            return True, "Producto actualizado"
        return False, "Producto no encontrado"
    except Exception as e:
        return False, f"Error al actualizar producto: {str(e)}"

def delete_product(product_id):
    try:
        result = db['products'].delete_one({'_id': ObjectId(product_id)})
        if result.deleted_count > 0:
            return True, "Producto eliminado"
        return False, "Producto no encontrado"
    except Exception as e:
        return False, f"Error al eliminar producto: {str(e)}"


# ============================
#           STOCK
# ============================

def get_all_stock():
    return list(db['stock'].find())

def get_stock_by_product(product_name):
    return db['stock'].find_one({'product_name': product_name})

def create_stock(product_name, minimun_quantity):
    if not product_name:
        return False, "Nombre del producto obligatorio"
    stock = Stock(product_name, minimun_quantity)
    db['stock'].insert_one(stock.toDBCollection())
    return True, "Stock creado"

def update_stock(product_name, minimun_quantity):
    result = db['stock'].update_one({'product_name': product_name}, {'$set': {'Minimun_Quantity': minimun_quantity}})
    if result.matched_count > 0:
        return True, "Stock actualizado"
    return False, "Stock no encontrado"

def delete_stock(product_name):
    result = db['stock'].delete_one({'product_name': product_name})
    if result.deleted_count > 0:
        return True, "Stock eliminado"
    return False, "Stock no encontrado"

# ============================
#           USUARIOS
# ============================

def get_all_users():
    return list(db['users'].find())

def get_user_by_email(email):
    return db['users'].find_one({'email': email})

def create_user(username, email, password, role="cliente"):
    if not username or not email or not password:
        return False, "Todos los campos son obligatorios"
    if get_user_by_email(email):
        return False, "Usuario ya existe"
    user = User(username, email, password, role)
    db['users'].insert_one(user.toDBCollection())
    return True, "Usuario creado"

def update_user(user_id, data):
    if 'password' in data:
        data['password_hash'] = generate_password_hash(data.pop('password'))
    result = db['users'].update_one({'_id': ObjectId(user_id)}, {'$set': data})
    if result.matched_count > 0:
        return True, "Usuario actualizado"
    return False, "Usuario no encontrado"

def delete_user(user_id):
    result = db['users'].delete_one({'_id': ObjectId(user_id)})
    if result.deleted_count > 0:
        return True, "Usuario eliminado"
    return False, "Usuario no encontrado"
