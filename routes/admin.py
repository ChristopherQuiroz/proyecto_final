from flask import Blueprint, render_template, request, flash, redirect, jsonify
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os

from routes.auth import require_role
from database import dbConnection
from routes.services import (
    get_all_categories, create_category, update_category, delete_category,
    get_all_products, create_product, update_product, delete_product, get_product_by_id,
    get_all_stock, update_stock
)

UPLOAD_FOLDER = 'static/img/products'
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
    orders = db['orders'] if 'orders' in db.list_collection_names() else []

    total_productos = products.count_documents({})
    total_categorias = categories.count_documents({})
    total_usuarios = users.count_documents({})
    pedidos_pendientes = orders.count_documents({"status": "pendiente"}) if orders else 0

    productos_bajo_stock = list(products.find({'quantity': {'$lt': 5}}))
    productos_top = list(products.find().sort("price", -1).limit(3))

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
    categorias = get_all_categories(with_count=True)
    return render_template("admin/categorias.html", categorias=categorias, rol="admin")


@bp_admin.route("/categorias/agregar", methods=["POST"])
@require_role('admin')
def admin_categorias_agregar():
    nombre = request.form.get("name")
    ok, msg = create_category(nombre)
    flash(msg, "success" if ok else "error")
    return redirect("/admin/categorias")

@bp_admin.route("/categorias/editar/<string:category_id>", methods=["POST"])
@require_role('admin')
def admin_categorias_editar(category_id):
    nuevo_nombre = request.form.get("name")
    ok, msg = update_category(category_id, {"name": nuevo_nombre})
    flash(msg, "success" if ok else "error")
    return redirect("/admin/categorias")

@bp_admin.route("/categorias/eliminar/<string:category_id>")
@require_role('admin')
def admin_categorias_eliminar(category_id):
    ok, msg = delete_category(category_id)
    flash(msg, "success" if ok else "error")
    return redirect("/admin/categorias")
# ============================================================
#                        PRODUCTOS
# ============================================================
@bp_admin.route("/productos")
@require_role('admin')
def ver_productos():
    productos = get_all_products()
    categorias = get_all_categories()
    return render_template("admin/productos.html", productos=productos, categorias=categorias, rol="admin")

@bp_admin.route("/productos/agregar", methods=['POST'])
@require_role('admin')
def admin_productos_agregar():
    name = request.form.get('name')
    description = request.form.get('description', '')
    category = request.form.get('category')
    price = float(request.form.get('price', 0))
    status = request.form.get('status', 'Disponible')
    quantity = int(request.form.get('quantity', 0))

    # Manejo de imagen
    image_file = request.files.get('image')
    image_filename = None
    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(UPLOAD_FOLDER, filename))
        image_filename = filename

    ok, msg = create_product(name, description, category, price, status, quantity, image_filename)
    flash(msg, "success" if ok else "error")
    return redirect('/admin/productos')


@bp_admin.route("/productos/editar/<product_id>", methods=['POST'])
@require_role('admin')
def admin_productos_editar(product_id):
    data = {
        'name': request.form.get('name'),
        'description': request.form.get('description', ''),
        'category': request.form.get('category'),
        'price': float(request.form.get('price', 0)),
        'status': request.form.get('status', 'Disponible'),
        'quantity': int(request.form.get('quantity', 0))
    }

    # Manejo de imagen
    image_file = request.files.get('image')
    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(UPLOAD_FOLDER, filename))
        data['image'] = filename

    ok, msg = update_product(product_id, data)
    flash(msg, "success" if ok else "error")
    return redirect('/admin/productos')


@bp_admin.route("/productos/eliminar/<product_id>")
@require_role('admin')
def admin_productos_eliminar(product_id):
    ok, msg = delete_product(product_id)
    flash(msg, "success" if ok else "error")
    return redirect('/admin/productos')


# ============================================================
#                      STOCK 
# ============================================================
@bp_admin.route("/inventario")
@require_role('admin')
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
@require_role('admin')
def admin_reportes():
    products_collection = db['products']
    categories_collection = db['categories']

    # Ventas y stock
    ventas_hoy = sum(p.get('price', 0) * p.get('quantity', 0) for p in products_collection.find())
    ventas_mes = ventas_hoy * 30
    ventas_anio = ventas_mes * 12

    productos_bajo_stock = list(products_collection.find({'quantity': {'$lt': 5}}))
    productos_top = list(products_collection.find().sort('price', -1).limit(5))

    # Productos por categoría
    categorias = list(categories_collection.find())
    productos_por_categoria = []
    for cat in categorias:
        count = products_collection.count_documents({'category_id': cat['_id']})
        productos_por_categoria.append({'categoria': cat['name'], 'cantidad': count})

    return render_template(
        "admin/reportes.html",
        rol="admin",
        ventas_hoy=ventas_hoy,
        ventas_mes=ventas_mes,
        ventas_anio=ventas_anio,
        pedidos_completados=db['orders'].count_documents({'status': 'pagado'}) if 'orders' in db.list_collection_names() else 0,
        promedio_pedido=ventas_hoy / db['orders'].count_documents({}) if 'orders' in db.list_collection_names() and db['orders'].count_documents({}) else 0,
        productos_top=productos_top,
        productos_bajo_stock=productos_bajo_stock,
        productos_por_categoria=productos_por_categoria
    )

    
@bp_admin.errorhandler(404)
def not_found(error=None):
    message = {'message': 'No encontrado: ' + request.url, 'status': 404}
    return jsonify(message), 404

