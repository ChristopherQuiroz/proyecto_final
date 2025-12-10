from flask import Blueprint, render_template, request, flash, redirect, jsonify
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime
from entities.product import Product
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

# ============================================================
#                   ROL: ADMIN
# ============================================================
@bp_admin.route("/")
@require_role('admin')
def admin_dashboard():
    products = db['products']
    categories = db['categories']
    users = db['users']
    orders = db['orders']

    total_productos = products.count_documents({})
    total_categorias = categories.count_documents({})
    total_usuarios = users.count_documents({})
    pedidos_pendientes = orders.count_documents({"status": "pendiente"})

    productos_bajo_stock = list(products.find({'quantity': {'$lt': 5}}))
    productos_top = list(products.find().sort("price", -1).limit(3))

    ultimos_pedidos_db = orders.find().sort("date", -1).limit(5)
    ultimos_pedidos = []
    for p in ultimos_pedidos_db:
        cliente_nombre = "Cliente no registrado"
        if p.get("customer_id"):
            cliente = users.find_one({"_id": ObjectId(p["customer_id"])})
            if cliente:
                cliente_nombre = cliente.get("username", "Cliente")
        fecha = p.get("date", datetime.utcnow())
        if isinstance(fecha, datetime):
            fecha = fecha.strftime("%Y-%m-%d %H:%M")
        ultimos_pedidos.append({
            "id": str(p["_id"]),
            "cliente": cliente_nombre,
            "fecha": fecha,
            "estado": p.get("status", "pendiente")
        })

    productos_populares = []
    for prod in products.find().sort("quantity", -1).limit(5):
        productos_populares.append({
            "nombre": prod.get("name"),
            "cantidad": prod.get("quantity", 0)
        })

    pipeline = [
        {"$group": {"_id": "$customer_id", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 5}
    ]
    top_clientes_db = list(orders.aggregate(pipeline))
    clientes_top = []
    for c in top_clientes_db:
        cliente = users.find_one({"_id": c["_id"]}) if c["_id"] else None
        clientes_top.append({
            "nombre": cliente.get("username") if cliente else "Cliente",
            "total": c["total"]
        })

    return render_template(
        "admin/dashboard.html",
        rol="admin",
        total_productos=total_productos,
        total_categorias=total_categorias,
        total_usuarios=total_usuarios,
        pedidos_pendientes=pedidos_pendientes,
        stock_bajo=len(productos_bajo_stock),
        productos_bajo_stock=productos_bajo_stock,
        ultimos_pedidos=ultimos_pedidos,
        productos_populares=productos_populares,
        clientes_top=clientes_top,
        productos_top=productos_top
    )

@bp_admin.route("/categorias")
@require_role('admin')
def ver_categorias():
    categorias = get_all_categories(with_count=True)
    # Convertir ObjectId a string
    for cat in categorias:
        cat['_id'] = str(cat['_id'])
    return render_template("admin/categorias.html", categorias=categorias, rol="admin")


@bp_admin.route("/categorias/agregar", methods=["POST"])
@require_role('admin')
def admin_categorias_agregar():
    name = request.form.get('name')
    icon = request.form.get('icon', '')  # si deseas guardar icono
    description = request.form.get('description', '')
    db['categories'].insert_one({
        "name": name,
        "icon": icon,
        "description": description
    })
    flash("Category added successfully", "success")
    return redirect("/admin/categorias")

@bp_admin.route("/categorias/editar/<string:category_id>", methods=["POST"])
@require_role('admin')
def admin_categorias_editar(category_id):
    name = request.form.get('name')
    description = request.form.get('description', '')
    icon = request.form.get('icon', '')
    db['categories'].update_one(
        {"_id": ObjectId(category_id)},
        {"$set": {"name": name, "description": description, "icon": icon}}
    )
    flash("Category updated successfully", "success")
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
    cat_dict = {c['_id']: c['name'] for c in categorias}

    # Ajustar stock y agregar nombre de categoría
    for p in productos:
        p['quantity'] = p.get('inventory', {}).get('current_quantity', 0)
        p['category_name'] = cat_dict.get(p.get('category_id'), "Sin categoría")

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

    product = Product(name=name,
                      description=description,
                      category_id=category,
                      price=price,
                      status=status,
                      quantity=quantity,
                      image=image_filename)
    db.products.insert_one(product.to_dict())

    flash("Producto agregado correctamente", "success")
    return redirect('/admin/productos')

@bp_admin.route("/productos/editar/<string:product_id>", methods=['POST'])
@require_role('admin')
def admin_productos_editar(product_id):
    data = {
        "name": request.form.get('name'),
        "description": request.form.get('description', ''),
        "category": request.form.get('category'),  # nombre de categoría
        "price": float(request.form.get('price', 0)),
        "status": request.form.get('status', 'Disponible'),
        "quantity": int(request.form.get('quantity', 0))
    }

    # Manejo de imagen
    image_file = request.files.get('image')
    if image_file and image_file.filename != '':
        filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(UPLOAD_FOLDER, filename))
        data['image'] = filename

    try:
        db.products.update_one({"_id": ObjectId(product_id)}, {"$set": data})
    except:
        db.products.update_one({"_id": product_id}, {"$set": data})  # fallback si _id es string

    flash("Producto actualizado correctamente", "success")
    return redirect('/admin/productos')

@bp_admin.route("/productos/eliminar/<string:product_id>")
@require_role('admin')
def admin_productos_eliminar(product_id):
    db['products'].delete_one({"_id": ObjectId(product_id)})
    flash("Product deleted successfully", "success")
    return redirect("/admin/productos")

# ============================================================
#                      STOCK 
# ============================================================

@bp_admin.route("/inventario")
@require_role('admin')
def admin_inventario():
    products = list(db['products'].find())
    categories = list(db['categories'].find())
    cat_dict = {str(c['_id']): c['name'] for c in categories}

    for p in products:
        p['quantity'] = p.get('inventory', {}).get('current_quantity', 0)
        p['category_name'] = cat_dict.get(str(p.get('category_id')), "No category")
        p['_id'] = str(p['_id'])

    return render_template("admin/inventario.html", products=products, categories=categories, rol="admin")


@bp_admin.route("/actualizar_stock", methods=['POST'])
def actualizar_stock():
    product_id = request.form.get('product_id')
    new_quantity = int(request.form.get('quantity', 0))

    db['products'].update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"inventory.current_quantity": new_quantity}}
    )
    flash("Stock updated successfully", "success")
    return redirect('/admin/inventario')

@bp_admin.route("/reportes")
@require_role('admin')
def admin_reportes():
    products_collection = db['products']
    orders_collection = db['orders']
    categories_collection = db['categories']
    users_collection = db['users']

    # =================== VENTAS ===================
    ventas_hoy = sum(p.get('price', 0) * p.get('quantity', 0) for p in products_collection.find())
    ventas_mes = ventas_hoy * 30
    ventas_anio = ventas_mes * 12
    pedidos_completados = orders_collection.count_documents({'status': 'pagado'})
    promedio_pedido = ventas_hoy / orders_collection.count_documents({}) if orders_collection.count_documents({}) > 0 else 0

    # PRODUCTOS BAJO STOCK
    productos_bajo_stock = list(products_collection.find({'inventory.current_quantity': {'$lt': 5}}))

# PRODUCTOS AGOTADOS (opcional)
    productos_agotados = list(products_collection.find({'inventory.current_quantity': 0}))

    # =================== PRODUCTOS POR CATEGORÍA ===================
    categorias = list(categories_collection.find())
    productos_por_categoria = []
    for cat in categorias:
        count = products_collection.count_documents({'category_id': cat['_id']})
        productos_por_categoria.append({'categoria': cat['name'], 'cantidad': count})

    # =================== PRODUCTOS MÁS VENDIDOS ===================
    pipeline_productos_top = [
        {"$unwind": "$details"},  # Separar cada detalle del pedido
        {"$group": {
            "_id": "$details.product_id",
            "total_vendido": {"$sum": "$details.quantity"}
        }},
        {"$sort": {"total_vendido": -1}},  # De mayor a menor
        {"$limit": 5}
    ]
    top_productos_db = list(orders_collection.aggregate(pipeline_productos_top))
    productos_top = []
    for p in top_productos_db:
        prod = products_collection.find_one({"_id": ObjectId(p["_id"])})
        if prod:
            productos_top.append({
                "nombre": prod["name"],
                "cantidad": p["total_vendido"]
            })

    # =================== CLIENTES CON MÁS COMPRAS ===================
    pipeline_clientes_top = [
        {"$group": {"_id": "$customer_id", "total_compras": {"$sum": 1}}},
        {"$sort": {"total_compras": -1}},
        {"$limit": 5}
    ]
    top_clientes_db = list(orders_collection.aggregate(pipeline_clientes_top))
    clientes_top = []
    for c in top_clientes_db:
        cliente = users_collection.find_one({"_id": c["_id"]}) if c["_id"] else None
        clientes_top.append({
            "nombre": cliente["username"] if cliente else "Cliente",
            "compras": c["total_compras"]
        })

    # =================== VENTAS POR MES (OPCIONAL) ===================
    # Puedes calcular un resumen simple por mes si quieres
    ventas_por_mes = []
    for i in range(1, 13):
        inicio_mes = datetime(datetime.utcnow().year, i, 1)
        if i == 12:
            fin_mes = datetime(datetime.utcnow().year + 1, 1, 1)
        else:
            fin_mes = datetime(datetime.utcnow().year, i + 1, 1)
        total_mes = sum(
            detail['quantity'] * products_collection.find_one({"_id": ObjectId(detail['product_id'])})['price']
            for order in orders_collection.find({"date": {"$gte": inicio_mes, "$lt": fin_mes}})
            for detail in order['details']
        )
        ventas_por_mes.append({"mes": inicio_mes.strftime("%B"), "total": total_mes})

    return render_template(
        "admin/reportes.html",
        rol="admin",
        ventas_hoy=ventas_hoy,
        ventas_mes=ventas_mes,
        ventas_anio=ventas_anio,
        pedidos_completados=pedidos_completados,
        promedio_pedido=promedio_pedido,
        productos_top=productos_top,
        clientes_top=clientes_top,
        productos_bajo_stock=productos_bajo_stock,
        productos_por_categoria=productos_por_categoria,
        ventas_por_mes=ventas_por_mes
    )

@bp_admin.route("/pedidos")
@require_role('admin')
def ver_pedidos():
    orders_collection = db['orders']
    users_collection = db['users']
    products_collection = db['products']

    pedidos = []
    for o in orders_collection.find().sort("date", -1):
        cliente_nombre = "Cliente no registrado"
        if o.get("customer_id"):
            cliente = users_collection.find_one({"_id": ObjectId(o["customer_id"])})
            if cliente:
                cliente_nombre = cliente.get("username", "Cliente")
        fecha = o.get("date", datetime.utcnow())
        if isinstance(fecha, datetime):
            fecha = fecha.strftime("%Y-%m-%d %H:%M")
        total = sum(
            item['quantity'] * products_collection.find_one({"_id": ObjectId(item['product_id'])})['price'] 
            for item in o.get("details", [])
        )
        pedidos.append({
            "id": str(o["_id"]),
            "cliente": cliente_nombre,
            "fecha": fecha,
            "total": total,
            "estado": o.get("status", "pendiente")
        })

    return render_template("admin/pedidos.html", pedidos=pedidos, rol="admin")

# ===================== CLIENTES =====================
@bp_admin.route("/clientes")
@require_role('admin')
def admin_clientes():
    users_collection = db['users']
    clientes = list(users_collection.find({"role": "cliente"}))
    
    # Preparar para enviar al template (convertir ObjectId a string)
    clientes_list = []
    for c in clientes:
        clientes_list.append({
            "id": str(c["_id"]),
            "nombre": c.get("username"),
            "correo": c.get("email"),
            "telefono": c.get("telefono"),
            "direccion": c.get("direccion")
        })
    
    return render_template("admin/clientes.html", clientes=clientes_list, rol="admin")


@bp_admin.route("/clientes/crear", methods=["POST"])
@require_role('admin')
def admin_clientes_crear():
    data = request.get_json()
    users_collection = db['users']
    
    if not data.get("nombre") or not data.get("correo"):
        return jsonify({"ok": False, "msg": "Nombre y correo son obligatorios"})
    
    # Insertar nuevo cliente
    users_collection.insert_one({
        "username": data["nombre"],
        "email": data["correo"],
        "telefono": data.get("telefono"),
        "direccion": data.get("direccion"),
        "role": "cliente"
    })
    return jsonify({"ok": True, "msg": "Cliente creado correctamente"})


@bp_admin.route("/clientes/editar/<id>", methods=["POST"])
@require_role('admin')
def admin_clientes_editar(id):
    data = request.get_json()
    users_collection = db['users']
    
    users_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "username": data.get("nombre"),
            "email": data.get("correo"),
            "telefono": data.get("telefono"),
            "direccion": data.get("direccion")
        }}
    )
    return jsonify({"ok": True, "msg": "Cliente actualizado correctamente"})


@bp_admin.route("/clientes/eliminar/<id>", methods=["POST"])
@require_role('admin')
def admin_clientes_eliminar(id):
    users_collection = db['users']
    users_collection.delete_one({"_id": ObjectId(id)})
    return jsonify({"ok": True, "msg": "Cliente eliminado correctamente"})

# ===================== EMPLEADOS =====================
@bp_admin.route("/empleados")
@require_role('admin')
def admin_empleados():
    users_collection = db['users']
    empleados = list(users_collection.find({"role": "empleado"}))
    
    empleados_list = []
    for e in empleados:
        empleados_list.append({
            "id": str(e["_id"]),
            "nombre": e.get("username"),
            "cargo": e.get("cargo", "Empleado"),
            "correo": e.get("email")
        })
    
    return render_template("admin/empleados.html", empleados=empleados_list, rol="admin")


@bp_admin.route("/empleados/crear", methods=["POST"])
@require_role('admin')
def admin_empleados_crear():
    data = request.get_json()
    users_collection = db['users']
    
    users_collection.insert_one({
        "username": data.get("nombre"),
        "email": data.get("correo"),
        "cargo": data.get("cargo"),
        "role": "empleado"
    })
    return jsonify({"ok": True, "msg": "Empleado creado correctamente"})


@bp_admin.route("/empleados/editar/<id>", methods=["POST"])
@require_role('admin')
def admin_empleados_editar(id):
    data = request.get_json()
    users_collection = db['users']
    
    users_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "username": data.get("nombre"),
            "email": data.get("correo"),
            "cargo": data.get("cargo")
        }}
    )
    return jsonify({"ok": True, "msg": "Empleado actualizado correctamente"})


@bp_admin.route("/empleados/eliminar/<id>", methods=["POST"])
@require_role('admin')
def admin_empleados_eliminar(id):
    users_collection = db['users']
    users_collection.delete_one({"_id": ObjectId(id)})
    return jsonify({"ok": True, "msg": "Empleado eliminado correctamente"})


@bp_admin.errorhandler(404)
def not_found(error=None):
    message = {'message': 'No encontrado: ' + request.url, 'status': 404}
    return jsonify(message), 404

