from flask import Blueprint, render_template, request, session, flash, redirect
from bson.objectid import ObjectId
from database import dbConnection
from routes.auth import require_role  

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

    
@bp_cliente.route("/index")
@require_role('cliente')
def cliente_home():
    # Obtener productos y categorías de la BD
    products_collection = db['products']
    categories_collection = db['categories']
    
    # Productos disponibles (limitar a 8 para home)
    productos_db = list(products_collection.find({'status': 'Available'}).limit(8))
    productos = [format_product_for_template(p) for p in productos_db]
    
    # Categorías
    categorias_db = list(categories_collection.find().limit(6))
    categorias = [format_category_for_template(c) for c in categorias_db]
    
    rol_actual = session.get('role', 'cliente')
    return render_template("cliente/index.html", 
                         productos=productos, 
                         categorias=categorias,
                         rol=rol_actual)

@bp_cliente.route("/productos")
@require_role('cliente')
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

@bp_cliente.route("/categorias")
@require_role('cliente')
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
                'fecha': pedido.get('fecha', '')
            })
    else:
        pedidos = []
    
    rol_actual = session.get('role', 'cliente')
    return render_template("cliente/mis_pedidos.html", 
                         pedidos=pedidos, 
                         rol=rol_actual)

@bp_cliente.route("/producto/<product_id>")
@require_role('cliente')
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
