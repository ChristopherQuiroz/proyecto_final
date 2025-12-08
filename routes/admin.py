from flask import Blueprint, render_template, request, flash, redirect, session, jsonify
from bson.objectid import ObjectId
from routes.auth import require_role
from database import dbConnection
from entities.product import Product
from entities.category import Category, category_manager

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")
db = dbConnection()

# ============================================================
#                   ROL: ADMIN
# ============================================================
@bp_admin.route("/")
@require_role('admin')
def admin_dashboard():

    products = db['products']
    categories = db['categories']
    users = db['users']

    total_productos = products.count_documents({})
    total_categorias = categories.count_documents({})
    total_usuarios = users.count_documents({})

    productos_bajo_stock = list(products.find({'quantity': {'$lt': 5}}))
    productos_top = list(products.find().sort("price", -1).limit(3))

    pedidos_pendientes = db['orders'].count_documents({"estado": "Pendiente"}) if "orders" in db.list_collection_names() else 0

    return render_template(
        "admin/dashboard.html",
        rol="admin",
        total_productos=total_productos,
        total_categorias=total_categorias,
        total_usuarios=total_usuarios,
        productos_bajo_stock=productos_bajo_stock,
        productos_top=productos_top,
        pedidos_pendientes=pedidos_pendientes
    )
@bp_admin.route("/categorias")
@require_role('admin')
def ver_categorias():
    categories_collection = db['categories']
    categorias = list(categories_collection.find())
    return render_template("admin/categorias.html", categorias=categorias, rol="admin")

@bp_admin.route("/categorias/agregar", methods=["GET", "POST"])
@require_role('admin')
def admin_categorias():

    categories_collection = db['categories']

    if request.method == "POST":
        nombre = request.form.get("name")

        if not nombre:
            flash("El nombre es obligatorio", "error")
            return redirect("/admin/categorias")

        if categories_collection.find_one({"name": nombre}):
            flash("La categoría ya existe", "error")
            return redirect("/admin/categorias")

        # Usar entidad Category
        categoria = Category(nombre)
        
        # Guardar en MongoDB
        categories_collection.insert_one(categoria.toDBCollection())

        # Guardar en manager de memoria
        category_manager.add_category(categoria)

        flash("Categoría creada correctamente", "success")
        return redirect("/admin/categorias")

    categorias = list(categories_collection.find())
    return render_template("admin/categorias.html", categorias=categorias, rol="admin")

@bp_admin.route("/categorias/editar/<string:nombre_actual>", methods=["POST"])
@require_role('admin')
def editar_categoria(nombre_actual):

    categories = db['categories']
    nuevo_nombre = request.form.get("name")

    if not nuevo_nombre:
        flash("El nombre es obligatorio", "error")
        return redirect("/admin/categorias")

    categories.update_one(
        {"name": nombre_actual},
        {"$set": {"name": nuevo_nombre}}
    )

    flash("Categoría actualizada", "success")
    return redirect("/admin/categorias")

@bp_admin.route("/categorias/eliminar/<string:category_name>")
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
@bp_admin.route("/productos")
@require_role('admin')
def ver_productos():
    products_collection = db['products']
    categories_collection = db['categories']

    productos = list(products_collection.find())
    categorias = list(categories_collection.find())
    return render_template("admin/productos.html", productos=productos, categorias=categorias, rol="admin")

@bp_admin.route("/productos/agregar", methods=['GET', 'POST'])
@require_role('admin')
def admin_productos():
    
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

@bp_admin.route("/productos/editar", methods=['POST'])
@require_role('admin')
def editar_producto():

    products_collection = db['products']
    
    product_id = request.form.get('product_id')
    name = request.form.get('name')
    description = request.form.get('description', '')
    category = request.form.get('category')
    price = float(request.form.get('price', 0))
    status = request.form.get('status', 'Disponible')
    quantity = int(request.form.get('quantity', 0))
    
    
    # Determinar filtro correctamente (usar ObjectId si viene id)
    if product_id:
        try:
            filtro = {'_id': ObjectId(product_id)}
        except:
            filtro = {'_id': product_id}  # fallback (no suele usarse)
    else:
        filtro = {'name': name}
    
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

@bp_admin.route("/productos/eliminar/<string:product_name>")
def eliminar_producto(product_name):
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
@bp_admin.route("/inventario")
def admin_inventario():
 
    products_collection = db['products']
    productos = list(products_collection.find())
    
    return render_template("admin/inventario.html", 
                         productos=productos, 
                         rol="admin")

@bp_admin.route("/actualizar_stock", methods=['POST'])
def actualizar_stock():
    
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

@bp_admin.route("/reportes")
def admin_reportes():

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
    
@bp_admin.errorhandler(404)
def not_found(error=None):
    message = {'message': 'No encontrado: ' + request.url, 'status': 404}
    return jsonify(message), 404

