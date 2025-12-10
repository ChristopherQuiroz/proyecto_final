import os
from flask import Blueprint, render_template, request, session, flash, redirect, current_app
from bson.objectid import ObjectId
from database import dbConnection
from routes.auth import require_role  
from datetime import datetime

bp_cliente = Blueprint("cliente", __name__, url_prefix="/cliente")
db = dbConnection()
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
    """Convertir categoría de BD (inglés) a template (español)"""
    return {
        'id': str(category.get('_id', '')),
        'nombre': category.get('name', 'Sin nombre'),
        'icono': category.get('icon', 'cupcake.png'),   # campo correcto de BD
        'descripcion': category.get('description', '')  # campo correcto de BD
    }

    
@bp_cliente.route("/")
def cliente_dashboard():
    # Obtener productos y categorías de la BD
    products_collection = db['products']
    categories_collection = db['categories']
    
    # Productos disponibles (limitar a 8 para home)
    productos_db = list(products_collection.find({'status': 'Disponible'}).limit(8))
    productos = [format_product_for_template(p) for p in productos_db]
    
    # Categorías
    categorias_db = list(categories_collection.find().limit(6))
    categorias = [format_category_for_template(c) for c in categorias_db]

    # ==== CARGAR AUTOMÁTICAMENTE LOS BANNERS DEL HERO ====
    hero_dir= os.path.join(current_app.static_folder, "img/hero")
    
    # lista solo archivos válidos (jpg, png, jpeg)
    banners = [
        f"img/hero/{f}"
          for f in os.listdir(hero_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    banners.sort()  # opcional: banner1, banner2, etc.

    # Rol actual
    rol_actual = session.get('role', 'invitado')

    return render_template(
        "cliente/dashboard.html",
        productos=productos,
        categorias=categorias,
        banners=banners,   
        rol=rol_actual
    )

@bp_cliente.route("/productos")
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
    
    rol_actual = session.get('role', 'invitado')
    return render_template("cliente/productos.html", 
                         productos=productos, 
                         rol=rol_actual)

@bp_cliente.route("/categorias")
def cliente_categorias():
    categories_collection = db['categories']
    products_collection = db['products']

    # Todas las categorías
    categorias_db = list(categories_collection.find())
    categorias = [format_category_for_template(c) for c in categorias_db]

    # Todos los productos disponibles
    productos_db = list(products_collection.find({'status': 'Disponible'}))
    productos = [format_product_for_template(p) for p in productos_db]

    # ==========================
    # CALCULAR CONTEO DE PRODUCTOS POR CATEGORÍA
    # ==========================
    conteo = {}
    for cat in categorias:
        nombre_categoria = cat['nombre']
        conteo[nombre_categoria] = sum(
            1 for p in productos if p['categoria'] == nombre_categoria
        )

    # ==========================
    # ENVÍO DE VARIABLES AL HTML
    # ==========================
    return render_template(
        "cliente/categorias.html",
        categorias=categorias,
        productos=productos,
        conteo=conteo, 
        rol=session.get("role", "invitado")
    )

@bp_cliente.route("/carrito")
@require_role('cliente')
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

@bp_cliente.route("/mis_pedidos")
@require_role('cliente')
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
            'fecha': pedido.get('fecha', ''),
            'productos': pedido.get('productos', [])
})

    else:
        pedidos = []
    
    rol_actual = session.get('role', 'cliente')
    return render_template("cliente/mis_pedidos.html", 
                         pedidos=pedidos, 
                         rol=rol_actual)

@bp_cliente.route("/carrito/agregar/<product_id>", methods=["POST"])
@require_role('cliente')
def agregar_al_carrito(product_id):

    cantidad = int(request.form.get("cantidad", 1))

    # Crear el carrito si no existe
    if "carrito" not in session:
        session["carrito"] = {}

    # Convertir id a string
    product_id = str(product_id)

    # Actualizar cantidad si el producto ya está
    if product_id in session["carrito"]:
        session["carrito"][product_id] += cantidad
    else:
        session["carrito"][product_id] = cantidad

    session.modified = True

    flash("Producto agregado al carrito", "success")
    return redirect("/cliente/carrito")

@bp_cliente.route("/carrito/eliminar/<product_id>")
@require_role('cliente')
def eliminar_del_carrito(product_id):

    product_id = str(product_id)

    if "carrito" in session and product_id in session["carrito"]:
        session["carrito"].pop(product_id)

    session.modified = True
    flash("Producto eliminado del carrito", "success")
    return redirect("/cliente/carrito")

@bp_cliente.route("/carrito/actualizar/<product_id>/<accion>")
@require_role('cliente')
def actualizar_cantidad(product_id, accion):

    product_id = str(product_id)

    if "carrito" not in session or product_id not in session["carrito"]:
        return redirect("/cliente/carrito")

    # SUMAR
    if accion == "sumar":
        session["carrito"][product_id] += 1

    # RESTAR
    elif accion == "restar":
        if session["carrito"][product_id] > 1:
            session["carrito"][product_id] -= 1
        else:
            session["carrito"].pop(product_id)

    session.modified = True
    return redirect("/cliente/carrito")

@bp_cliente.route("/pagar", methods=["POST"])
@require_role("cliente")
def cliente_pagar():

    if "carrito" not in session or not session["carrito"]:
        flash("Tu carrito está vacío", "error")
        return redirect("/cliente/carrito")

    carrito = session["carrito"]
    products_collection = db["products"]

    productos_pedido = []
    total = 0

    for product_id, cantidad in carrito.items():
        producto_db = products_collection.find_one({"_id": ObjectId(product_id)})

        if not producto_db:
            continue

        subtotal = producto_db["price"] * cantidad

        productos_pedido.append({
            "product_id": product_id,
            "nombre": producto_db["name"],
            "cantidad": cantidad,
            "precio": producto_db["price"],
            "subtotal": subtotal
        })

        total += subtotal

    # Guardar pedido en BD
    pedido = {
        "user_id": session["user_id"],
        "productos": productos_pedido,
        "total": total,
        "estado": "Pendiente",       # <-- ADMIN / EMPLEADO revisan esto
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    db["orders"].insert_one(pedido)

    # Vaciar carrito
    session["carrito"] = {}
    session.modified = True

    flash("¡Pedido realizado con éxito!", "success")
    return redirect("/cliente/mis_pedidos")

@bp_cliente.route("/producto/<product_id>")
@require_role('cliente')
def cliente_detalle_producto(product_id):
    products_collection = db['products']

    try:
        # Producto principal
        producto_db = products_collection.find_one({'_id': ObjectId(product_id)})
        if not producto_db:
            flash("Producto no encontrado", "error")
            return redirect("/cliente/productos")
        
        producto = format_product_for_template(producto_db)

       
        categoria = producto['categoria']

        relacionados_db = list(products_collection.find({
            "category": categoria,
            "_id": {"$ne": ObjectId(product_id)},   # excluir actual
            "status": "Disponible"
        }).limit(3))  # mostrar 3 o puedes usar limit(4)

        relacionados = [format_product_for_template(r) for r in relacionados_db]

        rol_actual = session.get("role", "cliente")

        return render_template(
            "cliente/detalle_producto.html",
            producto=producto,
            relacionados=relacionados,
            rol=rol_actual
        )

    except Exception as e:
        print("Error:", e)
        flash("ID de producto inválido", "error")
        return redirect("/cliente/productos")