from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from functools import wraps
import database as dbase

from entities.products import Product
from entities.category import Category
from entities.stock import Stock
from entities.product_category import product_category

db = dbase.dbConnection()
app = Flask(__name__)
app.secret_key = "clave_super_segura"

# Inicializar el manager de categorías
category_manager = product_category()


# ============================================================
#                LOGIN (CON BASE DE DATOS REAL)
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    # Si ya está logueado, redirigir según su rol
    if 'user_id' in session:
        return redirect(get_redirect_url(session.get('role', 'cliente')))
    
    if request.method == "POST":
        username = request.form["usuario"]
        password = request.form["password"]
        
        # Buscar usuario en la base de datos
        users_collection = db['users']
        user_data = users_collection.find_one({'username': username})
        
        if not user_data:
            return render_template("auth/login.html", error="Usuario no encontrado")
        
        # Verificar contraseña
        if not check_password_hash(user_data['password_hash'], password):
            return render_template("auth/login.html", error="Contraseña incorrecta")
        
        # Verificar si el usuario está activo
        if not user_data.get('is_active', True):
            return render_template("auth/login.html", error="Cuenta desactivada")
        
        # Guardar sesión
        session['user_id'] = str(user_data['_id'])
        session['usuario'] = user_data['username']
        session['role'] = user_data['role']
        session['email'] = user_data.get('email', '')
        
        # Redireccionar según rol
        return redirect(get_redirect_url(user_data['role']))
    
    return render_template("auth/login.html")

# ============================================================
#                FUNCIONES AUXILIARES DE AUTENTICACIÓN
# ============================================================

# Función para crear admin inicial
def create_initial_admin():
    """Crear usuario admin si no existe ninguno"""
    users_collection = db['users']
    
    # Verificar si ya existe un admin
    admin_exists = users_collection.find_one({'role': 'admin'})
    
    if not admin_exists:
        admin_user = {
            'username': 'admin',
            'email': 'admin@pasteleria.com',
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        users_collection.insert_one(admin_user)
        print("✅ Usuario admin creado:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("   Email: admin@pasteleria.com")

# Middleware para verificar sesión
@app.before_request
def before_request():
    # Rutas públicas que no requieren autenticación
    public_routes = ['login', 'register', 'cliente_home', 'cliente_productos', 
                     'cliente_categorias', 'static', 'not_found']
    
    if request.endpoint in public_routes:
        return
    
    # Verificar si el usuario está logueado
    if 'user_id' not in session:
        return redirect('/login')
    
    # Verificar si el usuario existe y está activo
    try:
        user_data = db['users'].find_one({'_id': ObjectId(session['user_id'])})
        if not user_data or not user_data.get('is_active', True):
            session.clear()
            return redirect('/login')
    except:
        session.clear()
        return redirect('/login')

# Función para obtener URL de redirección
def get_redirect_url(role):
    """Obtener la URL de redirección según el rol"""
    if role == "admin":
        return "/admin"
    elif role == "empleado":
        return "/empleado"
    else:
        return "/"

# Decoradores para verificar roles
def require_role(role):
    """Decorador para verificar rol del usuario"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                return redirect('/login')
            if session['role'] != role:
                flash('No tienes permisos para acceder a esta página', 'error')
                return redirect(get_redirect_url(session['role']))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_employee_or_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect('/login')
        if session['role'] not in ['empleado', 'admin']:
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# Crear admin al inicio
with app.app_context():
    if 'users' in db.list_collection_names():
        create_initial_admin()

# ============================================================
#                REGISTRO (GUARDA EN BASE DE DATOS)
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["usuario"]
        email = request.form["correo"]
        password = request.form["password"]
        role = request.form.get("rol", "cliente")
        
        # Validaciones básicas
        if not username or not email or not password:
            return render_template("auth/register.html", error="Todos los campos son obligatorios")
        
        users_collection = db['users']
        
        # Verificar si el usuario ya existe
        existing_user = users_collection.find_one({
            '$or': [
                {'username': username},
                {'email': email}
            ]
        })
        
        if existing_user:
            return render_template("auth/register.html", 
                                 error="El usuario o email ya están registrados")
        
        # Validar que solo un admin pueda crear otros admins
        if role == 'admin' and ('role' not in session or session.get('role') != 'admin'):
            role = 'cliente'  # Degradar a cliente si no es admin quien crea
        
        # Crear nuevo usuario
        new_user = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': role,
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        
        # Insertar en la base de datos
        result = users_collection.insert_one(new_user)
        
        # Si el registro fue exitoso, iniciar sesión automáticamente
        if result.inserted_id:
            session['user_id'] = str(result.inserted_id)
            session['usuario'] = username
            session['role'] = role
            session['email'] = email
            
            return redirect(get_redirect_url(role))
        else:
            return render_template("auth/register.html", error="Error al crear usuario")
    
    return render_template("auth/register.html")

# ============================================================
#                LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ============================================================
#                   ROL: CLIENTE
# ============================================================

def format_product_for_template(product):
    """Convertir producto de BD (inglés) a template (español)"""
    return {
        'id': str(product.get('_id', '')),
        'nombre': product.get('name', 'Sin nombre'),
        'descripcion': product.get('description', ''),
        'precio': product.get('price', 0),
        'cantidad': product.get('quantity', 0),
        'categoria': product.get('category', 'General'),
        'estado': product.get('status', 'Desconocido'),
        'imagen': product.get('image', 'cupcake.png')
    }

def format_category_for_template(category):
    """Convertir categoría de BD a template"""
    return {
        'id': str(category.get('_id', '')),
        'nombre': category.get('name', 'Sin nombre'),
        'icono': category.get('icono', 'cupcake.png'),
        'descripcion': category.get('descripcion', '')
    }

@app.route("/")
def cliente_home():
    # Obtener productos y categorías de la BD
    products_collection = db['products']
    categories_collection = db['categories']
    
    # Productos disponibles (limitar a 8 para home)
    productos_db = list(products_collection.find({'status': 'Disponible'}).limit(8))
    productos = [format_product_for_template(p) for p in productos_db]
    
    # Categorías
    categorias_db = list(categories_collection.find().limit(6))
    categorias = [format_category_for_template(c) for c in categorias_db]
    
    rol_actual = session.get('role', 'cliente')
    return render_template("cliente/index.html", 
                         productos=productos, 
                         categorias=categorias,
                         rol=rol_actual)

@app.route("/cliente/productos")
def cliente_productos():
    # Obtener productos de la BD
    products_collection = db['products']
    
    # Manejar búsqueda si existe
    buscar = request.args.get('buscar', '').strip()
    if buscar:
        # Búsqueda por nombre o descripción (case-insensitive)
        productos_db = list(products_collection.find({
            'status': 'Disponible',
            '$or': [
                {'name': {'$regex': buscar, '$options': 'i'}},
                {'description': {'$regex': buscar, '$options': 'i'}},
                {'category': {'$regex': buscar, '$options': 'i'}}
            ]
        }))
    else:
        # Todos los productos disponibles
        productos_db = list(products_collection.find({'status': 'Disponible'}))
    
    productos = [format_product_for_template(p) for p in productos_db]
    
    rol_actual = session.get('role', 'cliente')
    return render_template("cliente/productos.html", 
                         productos=productos, 
                         rol=rol_actual)

@app.route("/cliente/categorias")
def cliente_categorias():
    # Obtener categorías de la BD
    categories_collection = db['categories']
    categorias_db = list(categories_collection.find())
    categorias = [format_category_for_template(c) for c in categorias_db]
    
    # Obtener productos de ejemplo (esto se podría cambiar a productos por categoría)
    products_collection = db['products']
    productos_db = list(products_collection.find({'status': 'Disponible'}).limit(12))
    productos = [format_product_for_template(p) for p in productos_db]
    
    rol_actual = session.get('role', 'cliente')
    return render_template("cliente/categorias.html", 
                         categorias=categorias, 
                         productos=productos, 
                         rol=rol_actual)

@app.route("/cliente/carrito")
def cliente_carrito():
    # Verificar que esté logueado
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver el carrito', 'error')
        return redirect('/login')
    
    productos_carrito = []
    total = 0
    
    if 'carrito' in session and session['carrito']:
        carrito_items = session['carrito']
        products_collection = db['products']
        
        for product_id, cantidad in carrito_items.items():
            try:
                producto_db = products_collection.find_one({'_id': ObjectId(product_id)})
                if producto_db and producto_db.get('status') == 'Disponible':
                    # Formatear producto para el template
                    producto = format_product_for_template(producto_db)
                    producto['cantidad'] = cantidad
                    producto['subtotal'] = producto['precio'] * cantidad
                    productos_carrito.append(producto)
                    total += producto['subtotal']
            except:
                continue
    
    rol_actual = session.get('role', 'cliente')
    return render_template("cliente/carrito.html", 
                         productos=productos_carrito, 
                         total=total,
                         rol=rol_actual)

@app.route("/cliente/mis_pedidos")
def cliente_mis_pedidos():
    # Verificar que esté logueado
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tus pedidos', 'error')
        return redirect('/login')
    
    # Obtener pedidos del usuario
    if 'orders' in db.list_collection_names():
        orders_collection = db['orders']
        pedidos_db = list(orders_collection.find({'user_id': session['user_id']}))
        
        # Formatear pedidos
        pedidos = []
        for pedido in pedidos_db:
            pedidos.append({
                'id': str(pedido.get('_id', '')),
                'total': pedido.get('total', 0),
                'estado': pedido.get('estado', 'Pendiente'),
                'fecha': pedido.get('fecha', '')
            })
    else:
        pedidos = []
    
    rol_actual = session.get('role', 'cliente')
    return render_template("cliente/mis_pedidos.html", 
                         pedidos=pedidos, 
                         rol=rol_actual)

@app.route("/cliente/producto/<product_id>")
def cliente_detalle_producto(product_id):
    try:
        products_collection = db['products']
        producto_db = products_collection.find_one({'_id': ObjectId(product_id)})
        
        if not producto_db:
            flash('Producto no encontrado', 'error')
            return redirect('/cliente/productos')
        
        producto = format_product_for_template(producto_db)
        
        rol_actual = session.get('role', 'cliente')
        return render_template("cliente/detalle_producto.html", 
                             producto=producto, 
                             rol=rol_actual)
    except:
        flash('ID de producto inválido', 'error')
        return redirect('/cliente/productos')


# ============================================================
#                   ROL: EMPLEADO
# ============================================================

@app.route("/empleado")
@require_employee_or_admin
def empleado_panel():
    productos = [
        {"nombre": f"Producto {i}", "precio": 3*i, "descripcion": f"Descripción {i}", "imagen": "/static/img/cupcake.png"}
        for i in range(1, 11)
    ]
    return render_template("empleado/panel_empleado.html", productos=productos, rol="empleado")


@app.route("/empleado/clientes")
@require_employee_or_admin
def empleado_clientes():
    clientes = [
        {"id": i, "nombre": f"Cliente {i}", "telefono": f"7000000{i}", "correo": f"cliente{i}@gmail.com"}
        for i in range(1, 11)
    ]
    return render_template("empleado/empleado_clientes.html", clientes=clientes, rol="empleado")


@app.route("/empleado/crear_pedido")
@require_employee_or_admin
def empleado_crear_pedido():
    return render_template("empleado/crear_pedido.html", rol="empleado")


@app.route("/empleado/productos")
@require_employee_or_admin
def empleado_productos():
    return render_template("empleado/productos.html", rol="empleado")


@app.route("/empleado/inventario")
@require_employee_or_admin
def empleado_inventario():
    return render_template("empleado/inventario.html", rol="empleado")

# ============================================================
#                   ROL: ADMIN
# ============================================================

@app.route("/admin")
@require_role('admin')
def admin_dashboard():
    
    # Obtener datos REALES de la base de datos
    products_collection = db['products']
    categories_collection = db['categories']
    
    # Estadísticas reales
    total_productos = products_collection.count_documents({})
    total_categorias = categories_collection.count_documents({})
    
    # Contar usuarios (simulado por ahora)
    total_usuarios = db['users'].count_documents({}) if 'users' in db.list_collection_names() else 45
    
    # Pedidos pendientes (simulado)
    pedidos_pendientes = 3
    
    # Productos con stock bajo (REAL)
    stock_bajo = []
    for product in products_collection.find({'quantity': {'$lt': 5}}):
        stock_bajo.append(product['name'])
    
    # Últimos pedidos (simulado)
    ultimos_pedidos = [
        {"id": 101, "cliente": "Ana", "fecha": "2025-12-01", "estado": "Pendiente"},
        {"id": 102, "cliente": "Pedro", "fecha": "2025-12-01", "estado": "Enviado"},
    ]
    
    # Productos más vendidos (simulado por ahora)
    productos_populares = []
    for i, product in enumerate(products_collection.find().limit(3), 1):
        productos_populares.append({
            "nombre": product['name'],
            "cantidad": 50 - (i * 10)  # Simulado
        })
    
    # Clientes top (simulado)
    clientes_top = [
        {"nombre": "Juan Pérez", "total": 16},
        {"nombre": "María López", "total": 12},
        {"nombre": "Carlos Ruiz", "total": 10},
    ]
    
    return render_template(
        "admin/dashboard.html",
        rol="admin",
        total_productos=total_productos,
        total_categorias=total_categorias,
        total_usuarios=total_usuarios,
        pedidos_pendientes=pedidos_pendientes,
        stock_bajo=stock_bajo,
        ultimos_pedidos=ultimos_pedidos,
        productos_populares=productos_populares,
        clientes_top=clientes_top
    )

@app.route("/admin/categorias", methods=['GET', 'POST'])
@require_role('admin')
def admin_categorias():
    
    categories_collection = db['categories']
    
    if request.method == 'POST':
        # Agregar nueva categoría
        name = request.form.get('name')
        
        if not name:
            flash('El nombre de la categoría es requerido', 'error')
            return redirect('/admin/categorias')
        
        # Verificar si ya existe
        existing = categories_collection.find_one({'name': name})
        if existing:
            flash('La categoría ya existe', 'error')
            return redirect('/admin/categorias')
        
        # Crear categoría usando tu entidad
        category = Category(name)
        categories_collection.insert_one(category.toDBCollection())
        
        # Actualizar el manager en memoria
        category_manager.add_category(category)
        
        flash('Categoría agregada exitosamente', 'success')
        return redirect('/admin/categorias')
    
    # GET: Mostrar todas las categorías
    categorias = list(categories_collection.find())
    return render_template("admin/categorias.html", 
                         categorias=categorias, 
                         rol="admin")

@app.route("/edit_category/<string:category_name>", methods=['POST'])
@require_role('admin')
def edit_category(category_name):
    
    categories_collection = db['categories']
    new_name = request.form.get('name')
    
    if not new_name:
        flash('El nombre es requerido', 'error')
        return redirect('/admin/categorias')
    
    # Actualizar en MongoDB
    result = categories_collection.update_one(
        {'name': category_name},
        {'$set': {'name': new_name}}
    )
    
    if result.modified_count > 0:
        flash('Categoría actualizada exitosamente', 'success')
    else:
        flash('No se encontró la categoría', 'error')
    
    return redirect('/admin/categorias')

@app.route("/delete_category/<string:category_name>")
@require_role('admin')
def delete_category(category_name):
    
    categories_collection = db['categories']
    products_collection = db['products']
    
    # Verificar si hay productos en esta categoría
    products_in_category = products_collection.count_documents({'category': category_name})
    
    if products_in_category > 0:
        flash(f'No se puede eliminar: Hay {products_in_category} productos en esta categoría', 'error')
        return redirect('/admin/categorias')
    
    # Eliminar la categoría
    result = categories_collection.delete_one({'name': category_name})
    
    if result.deleted_count > 0:
        flash('Categoría eliminada exitosamente', 'success')
    else:
        flash('No se encontró la categoría', 'error')
    
    return redirect('/admin/categorias')

# ============================================================
#                        PRODUCTOS
# ============================================================
@app.route("/admin/productos", methods=['GET', 'POST'])
def admin_productos():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect('/login')
    
    products_collection = db['products']
    categories_collection = db['categories']
    
    if request.method == 'POST':
        # Agregar nuevo producto
        name = request.form.get('name')
        description = request.form.get('description', '')
        category = request.form.get('category')
        price = float(request.form.get('price', 0))
        status = request.form.get('status', 'Disponible')
        quantity = int(request.form.get('quantity', 0))
        
        # Validaciones
        if not name or not category:
            flash('Nombre y categoría son requeridos', 'error')
            return redirect('/admin/productos')
        
        # Verificar si la categoría existe
        category_exists = categories_collection.find_one({'name': category})
        if not category_exists:
            flash('La categoría seleccionada no existe', 'error')
            return redirect('/admin/productos')
        
        # Crear producto usando tu entidad
        product = Product(name, description, category, price, status, quantity)
        
        # Insertar en MongoDB
        products_collection.insert_one(product.toDBCollection())
        
        # Actualizar manager en memoria
        category_manager.add_product(product)
        
        flash('Producto agregado exitosamente', 'success')
        return redirect('/admin/productos')
    
    # GET: Mostrar todos los productos
    productos = list(products_collection.find())
    categorias = list(categories_collection.find())
    
    return render_template("admin/productos.html", 
                         productos=productos, 
                         categorias=categorias,
                         rol="admin")

@app.route("/admin/productos/editar", methods=['POST'])
def editar_producto():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect('/login')
    
    products_collection = db['products']
    
    product_id = request.form.get('product_id')
    name = request.form.get('name')
    description = request.form.get('description', '')
    category = request.form.get('category')
    price = float(request.form.get('price', 0))
    status = request.form.get('status', 'Disponible')
    quantity = int(request.form.get('quantity', 0))
    
    # Actualizar en MongoDB
    result = products_collection.update_one(
        {'_id': product_id} if '_id' in request.form else {'name': name},
        {'$set': {
            'name': name,
            'description': description,
            'category': category,
            'price': price,
            'status': status,
            'quantity': quantity
        }}
    )
    
    if result.modified_count > 0:
        flash('Producto actualizado exitosamente', 'success')
    else:
        flash('No se pudo actualizar el producto', 'error')
    
    return redirect('/admin/productos')

@app.route("/admin/productos/eliminar/<string:product_name>")
def eliminar_producto(product_name):
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect('/login')
    
    products_collection = db['products']
    
    result = products_collection.delete_one({'name': product_name})
    
    if result.deleted_count > 0:
        flash('Producto eliminado exitosamente', 'success')
    else:
        flash('No se encontró el producto', 'error')
    
    return redirect('/admin/productos')

# ============================================================
#                      STOCK Y REPORTES
# ============================================================
@app.route("/admin/inventario")
def admin_inventario():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect('/login')
    
    products_collection = db['products']
    productos = list(products_collection.find())
    
    return render_template("admin/inventario.html", 
                         productos=productos, 
                         rol="admin")

@app.route("/admin/actualizar_stock", methods=['POST'])
def actualizar_stock():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect('/login')
    
    products_collection = db['products']
    
    product_name = request.form.get('product_name')
    nueva_cantidad = int(request.form.get('cantidad', 0))
    
    result = products_collection.update_one(
        {'name': product_name},
        {'$set': {'quantity': nueva_cantidad}}
    )
    
    if result.modified_count > 0:
        flash(f'Stock de {product_name} actualizado a {nueva_cantidad}', 'success')
    else:
        flash('No se pudo actualizar el stock', 'error')
    
    return redirect('/admin/inventario')

@app.route("/admin/reportes")
def admin_reportes():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect('/login')
    
    products_collection = db['products']
    
    # Calcular ventas totales (simulado por ahora)
    total_products = products_collection.count_documents({})
    ventas_hoy = total_products * 125  # Simulación
    ventas_mes = ventas_hoy * 30
    ventas_anio = ventas_mes * 12
    
    # Productos con poco stock
    productos_bajo_stock = list(products_collection.find({'quantity': {'$lt': 5}}))
    
    # Productos más caros (top 5)
    productos_top = list(products_collection.find().sort('price', -1).limit(5))
    
    # Productos por categoría
    categorias_collection = db['categories']
    categorias = list(categorias_collection.find())
    productos_por_categoria = []
    
    for cat in categorias:
        count = products_collection.count_documents({'category': cat['name']})
        productos_por_categoria.append({
            'categoria': cat['name'],
            'cantidad': count
        })
    
    return render_template(
        "admin/reportes.html",
        rol="admin",
        ventas_hoy=ventas_hoy,
        ventas_mes=ventas_mes,
        ventas_anio=ventas_anio,
        pedidos_completados=87,  # Simulado
        promedio_pedido=175,     # Simulado
        ventas_por_mes=[         # Simulado
            {"mes": "Enero", "total": 12000},
            {"mes": "Febrero", "total": 9800},
            {"mes": "Marzo", "total": 15200},
            {"mes": "Abril", "total": 14300},
        ],
        productos_top=productos_top,
        productos_bajo_stock=productos_bajo_stock,
        productos_por_categoria=productos_por_categoria,
        clientes_top=[           # Simulado
            {"nombre": "Juan Pérez", "compras": 12},
            {"nombre": "Ana López", "compras": 9},
        ]
    )

# ============================================================
#                        ERROR 404
# ============================================================

@app.errorhandler(404)
def not_found(error=None):
    message = {
        'message': 'No encontrado: ' + request.url,
        'status': 404
    }
    return jsonify(message), 404

# ============================================================
#                        MAIN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, port=4000)
