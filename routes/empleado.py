from flask import Blueprint, render_template, request, redirect, flash, session,jsonify
from bson.objectid import ObjectId
from routes.auth import require_employee_or_admin
from database import dbConnection
from entities.user import User
from datetime import datetime
from werkzeug.security import generate_password_hash
from routes.services import verificar_y_ajustar_stock


UPLOAD_FOLDER = 'static/img/products'  # misma carpeta que admin

bp_empleado = Blueprint("empleado", __name__, url_prefix="/empleado")
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
#                   PANEL PRINCIPAL EMPLEADO
# ============================================================
@bp_empleado.route("/")
@require_employee_or_admin
def empleado_panel():
    productos_collection = db["products"]
    orders_collection = db["orders"]
    users_collection = db["users"]

    empleado_id = ObjectId(session.get("user_id"))

    # ==================================================
    # PEDIDOS CREADOS POR EL EMPLEADO
    # ==================================================
    pedidos_creados_db = list(orders_collection.find({
        "created_by": empleado_id
    }))

    pedidos_creados = []
    for p in pedidos_creados_db:
        # buscar cliente si existe
        cliente = None
        if p.get("customer_id"):
            cliente = users_collection.find_one({"_id": ObjectId(p["customer_id"])})

        fecha = p.get("date", datetime.utcnow())
        if isinstance(fecha, datetime):
            fecha = fecha.strftime("%Y-%m-%d %H:%M")

        pedidos_creados.append({
            "id": str(p["_id"]),
            "cliente": cliente.get("username") if cliente else "Cliente",
            "total": p.get("total", 0),
            "estado": p.get("status", "pendiente"),
            "fecha": fecha
        })

    # ==================================================
    # PEDIDOS ACEPTADOS POR EL EMPLEADO
    # ==================================================
    pedidos_asignados_db = list(orders_collection.find({
        "employee_id": empleado_id
    }))

    pedidos_asignados = []
    for p in pedidos_asignados_db:
        cliente = None
        if p.get("customer_id"):
            cliente = users_collection.find_one({"_id": ObjectId(p["customer_id"])})

        fecha = p.get("date", datetime.utcnow())
        if isinstance(fecha, datetime):
            fecha = fecha.strftime("%Y-%m-%d %H:%M")

        pedidos_asignados.append({
            "id": str(p["_id"]),
            "cliente": cliente.get("username") if cliente else "Cliente",
            "total": p.get("total", 0),
            "estado": p.get("status", "pendiente"),
            "fecha": fecha
        })

    # ==================================================
    # DATOS GENERALES DEL DASHBOARD
    # ==================================================
    pedidos_pendientes = orders_collection.count_documents({"status": "pendiente"})

    hoy_inicio = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    pedidos_hoy = orders_collection.count_documents({"date": {"$gte": hoy_inicio}})

    stock_bajo = productos_collection.count_documents({"quantity": {"$lt": 5}})
    productos_bajo_stock = list(productos_collection.find({"quantity": {"$lt": 5}}))

    clientes_hoy = users_collection.count_documents({"role": "cliente"})

    return render_template(
        "empleado/dashboard.html",
        pedidos_creados=pedidos_creados,
        pedidos_asignados=pedidos_asignados,
        pedidos_pendientes=pedidos_pendientes,
        pedidos_hoy=pedidos_hoy,
        stock_bajo=stock_bajo,
        clientes_hoy=clientes_hoy,
        productos_bajo_stock=productos_bajo_stock,
        rol="empleado"
    )

# ============================================================
#                   CLIENTES 
# ============================================================
@bp_empleado.route("/clientes")
@require_employee_or_admin
def empleado_clientes():
    users_collection = db["users"]
    clientes_db = list(users_collection.find({"role": "cliente"}))
    clientes = []
    for c in clientes_db:
        clientes.append({
            "id": str(c.get("_id")),
            "nombre": c.get("username"),
            "telefono": c.get("phone"),
            "correo": c.get("email")
        })

    return render_template(
        "empleado/empleado_clientes.html",
        clientes=clientes,
        rol="empleado"
    )
# ============================================================
#              CREAR CLIENTE DESDE EMPLEADO
# ============================================================
@bp_empleado.route("/clientes/crear", methods=["POST"])
@require_employee_or_admin # o el decorador que uses
def empleado_crear_cliente():
    data = request.get_json()

    nombre = data.get("nombre")
    correo = data.get("correo")
    telefono = data.get("telefono")
    direccion = data.get("direccion")
    posicion = data.get("position")  # solo si lo usas

    if not nombre or not correo:
        return {"ok": False, "msg": "Nombre y correo son obligatorios"}, 400

    users_collection = db["users"]

    # Verificar si ya existe el correo
    if users_collection.find_one({"email": correo}):
        return {"ok": False, "msg": "El correo ya está registrado"}, 400

    # Contraseña por defecto para nuevos clientes
    password_default = "cliente123"

    # Crear instancia del usuario usando tu clase
    nuevo_cliente = User(
        username=nombre,
        email=correo,
        password=password_default,
        role="cliente",
        phone=telefono,
        address=direccion,
        position=posicion
    )

    # Insertar en Mongo
    users_collection.insert_one(nuevo_cliente.to_dict())

    return {"ok": True, "msg": "Cliente creado correctamente"}

# ============================================================
#                 EDITAR CLIENTE
# ============================================================
@bp_empleado.route("/clientes/editar/<cliente_id>", methods=["POST"])
@require_employee_or_admin
def empleado_editar_cliente(cliente_id):
    data = request.get_json()
    update_data = {}

    if "nombre" in data:
        update_data["username"] = data["nombre"]
    if "correo" in data:
        update_data["email"] = data["correo"]
    if "telefono" in data:
        update_data["phone"] = data["telefono"]
    if "direccion" in data:
        update_data["address"] = data["direccion"]

    if not update_data:
        return {"ok": False, "msg": "No hay datos para actualizar"}, 400

    users_collection = db["users"]
   
    result = users_collection.update_one({"_id": ObjectId(cliente_id)}, {"$set": update_data})
    if result.matched_count:
        return {"ok": True, "msg": "Cliente actualizado correctamente"}
    return {"ok": False, "msg": "Cliente no encontrado"}, 404


# ============================================================
#                 ELIMINAR CLIENTE
# ============================================================
@bp_empleado.route("/clientes/eliminar/<cliente_id>", methods=["POST"])
@require_employee_or_admin
def empleado_eliminar_cliente(cliente_id):
    users_collection = db["users"]
    # Opción 1: eliminar físicamente
    result = users_collection.delete_one({"_id": ObjectId(cliente_id)})

    # Opción 2: marcar como inactivo en vez de eliminar
    # result = users_collection.update_one({"_id": ObjectId(cliente_id)}, {"$set": {"is_active": False}})

    if result.deleted_count:
        return {"ok": True, "msg": "Cliente eliminado correctamente"}
    return {"ok": False, "msg": "Cliente no encontrado"}, 404

# ============================================================
#                CREAR / EDITAR PEDIDO
# ============================================================
@bp_empleado.route("/crear_pedido", methods=["GET", "POST"])
@require_employee_or_admin
def empleado_crear_pedido():
    if request.method == "POST":
        data = request.get_json()
        order_id = data.get("order_id")  # Para edición

        # -------------------------
        # EDITAR PEDIDO EXISTENTE
        # -------------------------
        if order_id:
            order = db["orders"].find_one({"_id": ObjectId(order_id)})
            if not order:
                return {"ok": False, "msg": "Pedido no encontrado"}, 404
            if order["status"] != "pendiente":
                return {"ok": False, "msg": "Solo se pueden editar pedidos pendientes"}, 400

            total = 0
            nuevos_detalles = []
            detalles_viejos = order.get("details", [])

            for p in data["detalles"]:
                product_id = p["id"]
                cantidad_nueva = int(p["cantidad"])
                subtotal = float(p["subtotal"])
                total += subtotal

                # Buscar si existía antes
                viejo = next((d for d in detalles_viejos if str(d["product_id"]) == product_id), None)
                cantidad_vieja = int(viejo["quantity"]) if viejo else 0

                diferencia = cantidad_vieja - cantidad_nueva  # >0 devuelve stock, <0 resta stock
                ok, msg = verificar_y_ajustar_stock(product_id, diferencia)
                if not ok:
                    return {"ok": False, "msg": msg}, 400

                nuevos_detalles.append({
                    "product_id": ObjectId(product_id),
                    "quantity": cantidad_nueva,
                    "subtotal": subtotal
                })

            db["orders"].update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {"details": nuevos_detalles, "total": total}}
            )
            return {"ok": True, "msg": "Pedido actualizado correctamente"}, 200

        # -------------------------
        # CREAR NUEVO PEDIDO
        # -------------------------
        cliente_id = data.get("cliente")
        productos = data.get("detalles")
        if not cliente_id:
            return {"ok": False, "msg": "Debes seleccionar un cliente"}, 400
        if not productos or len(productos) == 0:
            return {"ok": False, "msg": "El pedido está vacío"}, 400

        detalles_convertidos = []
        total = 0

        for p in productos:
            product_id = p["id"]
            cantidad = int(p["cantidad"])
            subtotal = float(p["subtotal"])
            total += subtotal

            # Reservar stock
            ok, msg = verificar_y_ajustar_stock(product_id, -cantidad)
            if not ok:
                return {"ok": False, "msg": msg}, 400

            detalles_convertidos.append({
                "product_id": ObjectId(product_id),
                "quantity": cantidad,
                "subtotal": subtotal
            })

        order_obj = {
            "customer_id": ObjectId(cliente_id),
            "employee_id": None,
            "created_by": ObjectId(session.get("user_id")),
            "status": "pendiente",
            "total": total,
            "details": detalles_convertidos,
            "date": datetime.utcnow()
        }

        db["orders"].insert_one(order_obj)
        return {"ok": True, "msg": "Pedido registrado correctamente"}, 200

    # -------------------------
    # GET → cargar formulario
    # -------------------------
    productos_db = list(db["products"].find({"status": "Disponible"}))
    clientes_db = list(db["users"].find({"role": "cliente"}))

    productos = [{
        "id": str(p["_id"]),
        "name": p.get("name"),
        "price": p.get("price"),
        "description": p.get("description"),
        "image": p.get("image")
    } for p in productos_db]

    clientes = [{
        "id": str(c["_id"]),
        "username": c.get("username"),
        "email": c.get("email")
    } for c in clientes_db]

    # Detectar si venimos a editar
    order_id = request.args.get("id")
    pedido_editar = None
    if order_id:
        order = db["orders"].find_one({"_id": ObjectId(order_id)})
        if order:
            pedido_editar = {
                "id": str(order["_id"]),
                "cliente_id": str(order["customer_id"]),
                "detalles": [
                    {
                        "id": str(d["product_id"]),
                        "nombre": db["products"].find_one({"_id": d["product_id"]})["name"],
                        "precio": db["products"].find_one({"_id": d["product_id"]})["price"],
                        "cantidad": d["quantity"],
                        "subtotal": d["subtotal"]
                    }
                    for d in order.get("details", [])
                ]
            }

    return render_template(
        "empleado/crear_pedido.html",
        productos=productos,
        clientes=clientes,
        rol="empleado",
        pedido=pedido_editar
    )

def format_product_for_template(product):
    return {
        'id': str(product.get('_id', '')),
        'name': product.get('name', 'Sin nombre'),
        'description': product.get('description', ''),
        'price': product.get('price', 0),
        'quantity': product.get('inventory', {}).get('current_quantity', 0),
        'category': product.get('category_name', 'General'),
        'status': product.get('status', 'Desconocido'),
        'image': product.get('image', 'cupcake.jpg')
    }
# ============================================================
#                PRODUCTOS 
# ============================================================
@bp_empleado.route("/productos")
@require_employee_or_admin
def empleado_productos():
    products_collection = db['products']
    categories_collection = db['categories']

    # Obtener categorías
    categorias_db = list(categories_collection.find())
    categorias = []
    cat_dict = {}
    for c in categorias_db:
        cat_dict[str(c['_id'])] = c['name']
        categorias.append({'id': str(c['_id']), 'name': c['name']})

    # Obtener productos
    productos_db = list(products_collection.find())
    productos = []
    for p in productos_db:
        # Agregar nombre de categoría
        category_name = cat_dict.get(str(p.get('category_id', '')), 'Sin categoría')
        p['category_name'] = category_name
        productos.append(format_product_for_template(p))

    return render_template(
        "empleado/productos.html",
        productos=productos,
        categorias=categorias,
        rol="empleado"
    )

# ============================================================
#                INVENTARIO 
# ============================================================

@bp_empleado.route("/inventario")
@require_employee_or_admin
def empleado_inventario():
    # Traer productos y categorías
    products = list(db['products'].find())
    categories = list(db['categories'].find())
    
    # Crear diccionario de categorías
    cat_dict = {str(c['_id']): c['name'] for c in categories}
    
    # Preparar productos con stock y nombre de categoría
    for p in products:
        # Obtener cantidad del inventario (si existe)
        p['quantity'] = p.get('inventory', {}).get('current_quantity', 0)
        # Mapear el category_id al nombre de categoría
        p['category'] = cat_dict.get(str(p.get('category_id')), "Sin categoría")
        # Convertir _id a string por seguridad
        p['_id'] = str(p['_id'])
    
    return render_template(
        "empleado/inventario.html",
        productos=products,
        rol="empleado"
    )

# ============================================================
#                 PEDIDOS 
# ============================================================
@bp_empleado.route("/pedidos")
@require_employee_or_admin
def empleado_pedidos():
    pedidos_db = list(db["orders"].find())
    pedidos = []

    for p in pedidos_db:
        cliente_nombre = "Cliente no registrado"
        if p.get("customer_id"):
            cliente = db["users"].find_one({"_id": ObjectId(p["customer_id"])})
            if cliente:
                cliente_nombre = cliente.get("username", "Cliente")

        fecha = p.get("date", datetime.utcnow())
        if isinstance(fecha, datetime):
            fecha = fecha.strftime("%Y-%m-%d %H:%M")

        detalles_con_nombre = []
        for d in p.get("details", []):
            prod = db["products"].find_one({"_id": ObjectId(d["product_id"])})
            detalles_con_nombre.append({
                "product_id": str(d["product_id"]),
                "product_name": prod["name"] if prod else "Producto eliminado",
                "quantity": d.get("quantity", 0),
                "subtotal": d.get("subtotal", 0)
            })

        pedidos.append({
            "id": str(p["_id"]),
            "cliente": cliente_nombre,
            "total": p.get("total", 0),
            "estado": p.get("status", "pendiente"),
            "fecha": fecha,
            "detalles": detalles_con_nombre
        })

    return render_template(
        "empleado/pedidos.html",
        pedidos=pedidos,
        rol="empleado"
    )

@bp_empleado.route("/pedidos/detalle/<order_id>")
@require_employee_or_admin
def empleado_detalle_pedido(order_id):
    try:
        order_data = db["orders"].find_one({"_id": ObjectId(order_id)})
    except:
        return jsonify({"ok": False, "msg": "ID de pedido inválido"})

    if not order_data:
        return jsonify({"ok": False, "msg": "Pedido no encontrado"})

    detalles = []
    for d in order_data.get("details", []):
        product_id = d.get("product_id")
        if not product_id:
            continue
        product_data = db["products"].find_one({"_id": ObjectId(product_id)})
        detalles.append({
            "product_name": product_data["name"] if product_data else "Producto eliminado",
            "quantity": d.get("quantity", 0),
            "subtotal": d.get("subtotal", 0)
        })

    return jsonify({"ok": True, "detalles": detalles})
# ============================================================
#                   ACEPTAR PEDIDO
# ============================================================
@bp_empleado.route("/pedidos/aceptar/<order_id>", methods=["POST"])
@require_employee_or_admin
def empleado_aceptar_pedido(order_id):
    order = db["orders"].find_one({"_id": ObjectId(order_id)})
    if not order:
        return jsonify({"ok": False, "msg": "Pedido no encontrado"})

    if order.get("status") != "pendiente":
        return jsonify({"ok": False, "msg": "Solo se pueden aceptar pedidos pendientes"})

    db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "aceptado", "employee_id": ObjectId(session.get("user_id"))}}
    )

    return jsonify({"ok": True, "new_status": "aceptado"})

@bp_empleado.route("/pedidos/entregar/<order_id>", methods=["POST"])
@require_employee_or_admin
def empleado_entregar_pedido(order_id):
    order = db["orders"].find_one({"_id": ObjectId(order_id)})

    if not order:
        return jsonify({"ok": False, "msg": "Pedido no encontrado"})

    if order["status"] != "aceptado":
        return jsonify({"ok": False, "msg": "Solo puedes entregar pedidos ya aceptados"})

    db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "entregado"}}
    )

    return jsonify({"ok": True, "new_status": "entregado"})


@bp_empleado.route("/pedidos/cancelar/<order_id>", methods=["POST"])
@require_employee_or_admin
def empleado_cancelar_pedido(order_id):
    order = db["orders"].find_one({"_id": ObjectId(order_id)})
    if not order:
        return jsonify({"ok": False, "msg": "Pedido no encontrado"})

    if order["status"] == "entregado":
        for item in order.get("details", []):
            product = db["products"].find_one({"_id": ObjectId(item["product_id"])})
            if product:
                db["products"].update_one({"_id": ObjectId(item["product_id"])}, {"$inc": {"inventory.current_quantity": item["quantity"]}})

    db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "cancelado"}}
    )

    return jsonify({"ok": True, "new_status": "cancelado"})
