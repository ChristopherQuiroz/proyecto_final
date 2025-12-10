from database import dbConnection
from entities.product import Product
from entities.category import Category
from entities.stock import Stock
from entities.user import User
from entities.order import Order
from entities.orderDetail import OrderDetail
from entities.stock import Stock
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash
db = dbConnection()
def normalize_product(producto):
    """
    Convierte un producto que puede tener atributos en español o inglés
    a un diccionario consistente con claves en español.
    """
    return {
        "nombre": producto.get("nombre") or producto.get("name") or "Sin nombre",
        "descripcion": producto.get("descripcion") or producto.get("description") or "",
        "precio": producto.get("precio") or producto.get("price") or 0,
        "cantidad": producto.get("cantidad") or producto.get("quantity") or 0,
        "categoria": producto.get("categoria") or producto.get("category_id") or "Sin categoría",
        "estado": producto.get("estado") or producto.get("status") or "desconocido",
        "imagen": producto.get("imagen") or producto.get("image") or "cupcake.jpg"
    }

# ================= CATEGORÍAS =================
def get_all_categories(with_count=False):
    cats = list(db['categories'].find())
    for c in cats:
        c['_id'] = str(c['_id'])
        if with_count:
            c['cantidad_productos'] = db['products'].count_documents({'category_id': ObjectId(c['_id'])})
    return cats


def get_category_by_name(name):
    return db['categories'].find_one({'name': name})

def create_category(name, icon="default.png", description=""):
    if not name:
        return False, "Nombre obligatorio"
    if get_category_by_name(name):
        return False, "Categoría ya existe"
    cat = Category(name, icon, description)
    db['categories'].insert_one(cat.to_dict())
    return True, "Categoría creada"

def update_category(category_id, data):
    result = db['categories'].update_one({'_id': ObjectId(category_id)}, {'$set': data})
    if result.matched_count:
        return True, "Categoría actualizada"
    return False, "Categoría no encontrada"

def delete_category(category_id):
    result = db['categories'].delete_one({'_id': ObjectId(category_id)})
    if result.deleted_count:
        return True, "Categoría eliminada"
    return False, "Categoría no encontrada"

# ================= PRODUCTOS =================
def get_all_products(category=None):
    query = {}
    if category:
        query['category_id'] = category
    return list(db['products'].find(query))

def get_product_by_id(product_id):
    try:
        return db['products'].find_one({'_id': ObjectId(product_id)})
    except:
        return None

def create_product(name, description, category_id, price, status="available", quantity=0, image=None):
    if not name or not category_id:
        return False, "Nombre y categoría obligatorios"
    if not db['categories'].find_one({'_id': ObjectId(category_id)}):
        return False, "Categoría no existe"
    prod = Product(name, description, category_id, price, status, quantity, image)
    db['products'].insert_one(prod.to_dict())
    return True, "Producto creado"

def update_product(product_id, data):
    result = db['products'].update_one({'_id': ObjectId(product_id)}, {'$set': data})
    if result.matched_count:
        return True, "Producto actualizado"
    return False, "Producto no encontrado"

def delete_product(product_id):
    result = db['products'].delete_one({'_id': ObjectId(product_id)})
    if result.deleted_count:
        return True, "Producto eliminado"
    return False, "Producto no encontrado"

# ================= STOCK =================
def get_all_stock():
    # Devuelve los productos con su stock actual
    products = list(db['products'].find())
    for p in products:
        p['quantity'] = p.get('inventory', {}).get('current_quantity', 0)
    return products

def get_stock_by_product(product_id):
    product = db['products'].find_one({'_id': ObjectId(product_id)})
    if not product:
        return None
    return product.get('inventory', {}).get('current_quantity', 0)

def create_stock(product_id, initial_quantity=0):
    # Inicializa el stock de un producto
    db['products'].update_one(
        {'_id': ObjectId(product_id)},
        {'$set': {'inventory.current_quantity': initial_quantity}}
    )
    return True, "Stock inicializado"

def update_stock(product_id, new_quantity):
    result = db['products'].update_one(
        {'_id': ObjectId(product_id)},
        {'$set': {'inventory.current_quantity': new_quantity}}
    )
    if result.matched_count:
        return True, "Stock actualizado"
    return False, "Producto no encontrado"

def delete_stock(product_id):
    result = db['products'].update_one(
        {'_id': ObjectId(product_id)},
        {'$unset': {'inventory.current_quantity': ""}}
    )
    if result.matched_count:
        return True, "Stock eliminado"
    return False, "Producto no encontrado"

def verificar_y_ajustar_stock(product_id, cantidad):
    """
    Ajusta el stock de un producto.
    - cantidad < 0: venta/resta
    - cantidad > 0: reabastecer/sumar
    """
    product = db["products"].find_one({"_id": ObjectId(product_id)})
    if not product:
        return False, "Producto no encontrado"

    stock_actual = product.get("inventory", {}).get("current_quantity", 0)

    if cantidad < 0:
        if stock_actual + cantidad < 0:
            return False, f"Stock insuficiente: solo quedan {stock_actual}"

    # Ajustar stock
    db["products"].update_one(
        {"_id": ObjectId(product_id)},
        {"$inc": {"inventory.current_quantity": cantidad}}
    )
    return True, "Stock ajustado correctamente"

# ================= USUARIOS =================
def get_all_users():
    return list(db['users'].find())

def get_user_by_email(email):
    return db['users'].find_one({'email': email})

def create_user(username, email, password, role="cliente"):
    if not username or not email or not password:
        return False, "Campos obligatorios"
    if get_user_by_email(email):
        return False, "Usuario ya existe"
    user = User(username, email, password, role)
    db['users'].insert_one(user.to_dict())
    return True, "Usuario creado"

def update_user(user_id, data):
    if 'password' in data:
        data['password_hash'] = generate_password_hash(data.pop('password'))
    result = db['users'].update_one({'_id': ObjectId(user_id)}, {'$set': data})
    if result.matched_count:
        return True, "Usuario actualizado"
    return False, "Usuario no encontrado"

def delete_user(user_id):
    result = db['users'].delete_one({'_id': ObjectId(user_id)})
    if result.deleted_count:
        return True, "Usuario eliminado"
    return False, "Usuario no encontrado"

# ================= PEDIDOS =================
def get_all_orders():
    """Listar todos los pedidos"""
    orders = db['orders'].find()
    return [Order.from_dict(o) for o in orders]

def get_order_by_id(order_id):
    """Obtener un pedido por ID"""
    try:
        data = db['orders'].find_one({'_id': ObjectId(order_id)})
        return Order.from_dict(data) if data else None
    except:
        return None

def get_orders_for_user(user_id, role):
    """
    Devuelve los pedidos según el rol:
    - admin: todos los pedidos
    - empleado: todos los pedidos
    - cliente: solo los suyos
    """
    query = {}
    if role == "cliente":
        query['customer_id'] = ObjectId(user_id)
    orders = db['orders'].find(query)
    return [Order.from_dict(o) for o in orders]

def create_order(customer_data, details, employee_id=None, status="pendiente", created_in_person=False):
    """
    customer_data: si es cliente registrado, enviar {'customer_id': id}
                   si es cliente presencial, enviar {'name': ..., 'nit': ..., 'email': ...}
    details: lista de diccionarios [{product_id, quantity, subtotal}, ...]
    """
    if not details or not isinstance(details, list):
        return None, "Detalles del pedido son obligatorios"

    # Crear objetos OrderDetail
    order_details = []
    for d in details:
        if not all(k in d for k in ('product_id', 'quantity', 'subtotal')):
            return None, "Cada detalle debe tener product_id, quantity y subtotal"
        order_details.append(OrderDetail(d['product_id'], d['quantity'], d['subtotal']))

    total = sum(d.subtotal for d in order_details)

    # Cliente registrado o venta presencial
    customer_id = customer_data.get('customer_id')
    if customer_id:
        customer_id = ObjectId(customer_id)
    else:
        temp_customer = {
            "username": customer_data.get("name", "Cliente Presencial"),
            "email": customer_data.get("email", None),
            "role": "cliente",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "nit": customer_data.get("nit", None)
        }
        result = db['users'].insert_one(temp_customer)
        customer_id = result.inserted_id

    order = Order(customer_id, employee_id, status=status, total=total, details=order_details, created_in_person=created_in_person)
    result = db['orders'].insert_one(order.to_dict())
    return str(result.inserted_id), "Pedido creado" if result.inserted_id else None, "Error al crear pedido"

def update_order(order_id, user_role=None, user_id=None, data=None):
    """
    Actualiza un pedido
    - El cliente solo puede actualizar su pedido si aún no está aceptado
    - El empleado o admin puede actualizar cualquier pedido
    """
    order = get_order_by_id(order_id)
    if not order:
        return False, "Pedido no encontrado"

    # Validación de roles
    if user_role == "cliente":
        if order.status != "pendiente":
            return False, "No se puede modificar un pedido ya procesado"
        if str(order.customer_id) != str(user_id):
            return False, "No puedes modificar pedidos de otros clientes"

    # Actualizar detalles
    if 'details' in data:
        new_details = []
        for d in data['details']:
            if not all(k in d for k in ('product_id', 'quantity', 'subtotal')):
                return False, "Cada detalle debe tener product_id, quantity y subtotal"
            new_details.append(OrderDetail(d['product_id'], d['quantity'], d['subtotal']).to_dict())
        data['details'] = new_details
        data['total'] = sum(d['subtotal'] for d in new_details)

    # Actualizar pedido
    result = db['orders'].update_one({'_id': ObjectId(order_id)}, {'$set': data})
    if result.matched_count:
        return True, "Pedido actualizado"
    return False, "Error al actualizar pedido"

def delete_order(order_id):
    result = db['orders'].delete_one({'_id': ObjectId(order_id)})
    if result.deleted_count > 0:
        return True, "Pedido eliminado"
    return False, "Pedido no encontrado"