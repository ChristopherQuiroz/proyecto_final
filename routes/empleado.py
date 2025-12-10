from flask import Blueprint, render_template, request, redirect, flash, session
from bson.objectid import ObjectId
from routes.auth import require_employee_or_admin
from database import dbConnection
from entities.product import Product
from entities.category import Category
from entities.order import Order
from entities.orderDetail import OrderDetail
from entities.user import User
from datetime import datetime

bp_empleado = Blueprint("empleado", __name__, url_prefix="/empleado")
db = dbConnection()


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
#                CREAR PEDIDO
# ============================================================
@bp_empleado.route("/crear_pedido", methods=["GET", "POST"])
@require_employee_or_admin
def empleado_crear_pedido():

    # ===============================
    # POST → REGISTRAR PEDIDO
    # ===============================
    if request.method == "POST":
        data = request.get_json()

        cliente_id = data.get("cliente")
        productos = data.get("detalles")

        if not cliente_id:
            return {"ok": False, "msg": "Debes seleccionar un cliente"}, 400

        if not productos or len(productos) == 0:
            return {"ok": False, "msg": "El pedido está vacío"}, 400

        # Convertir detalles
        detalles_convertidos = []
        total = 0

        for p in productos:
            subtotal = float(p["subtotal"])
            total += subtotal

            detalles_convertidos.append({
                "product_id": ObjectId(p["id"]),
                "quantity": int(p["cantidad"]),
                "subtotal": subtotal
            })

        # ===============================
        # OBJETO FINAL QUE SE GUARDA EN MONGO
        # ===============================
        order_obj = {
            "customer_id": ObjectId(cliente_id),
            "employee_id": None,                      # aún no aceptado por nadie
            "created_by": ObjectId(session.get("user_id")),  # empleado que creó el pedido
            "status": "pendiente",
            "total": total,
            "details": detalles_convertidos,
            "date": datetime.utcnow()
        }

        db["orders"].insert_one(order_obj)

        return {"ok": True, "msg": "Pedido registrado correctamente"}, 200

    # ===============================
    # GET → FORMULARIO
    # ===============================
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

    return render_template(
        "empleado/crear_pedido.html",
        productos=productos,
        clientes=clientes,
        rol="empleado"
    )


# ============================================================
#                PRODUCTOS 
# ============================================================
@bp_empleado.route("/productos")
@require_employee_or_admin
def empleado_productos():
    productos = list(db["products"].find())
    categorias = list(db["categories"].find())  
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
    productos = list(db["products"].find())
    return render_template(
        "empleado/inventario.html",
        productos=productos,
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

        # --- Obtener cliente ---
        cliente_nombre = "Cliente no registrado"

        if p.get("customer_id"):
            try:
                cliente = db["users"].find_one({"_id": ObjectId(p["customer_id"])})
                if cliente:
                    cliente_nombre = cliente.get("username", "Cliente")
            except:
                cliente_nombre = "Cliente inválido"

        # --- Obtener fecha ---
        fecha = p.get("date", datetime.utcnow())
        fecha = fecha.strftime("%Y-%m-%d %H:%M") if isinstance(fecha, datetime) else fecha

        pedidos.append({
            "id": str(p["_id"]),
            "cliente": cliente_nombre,
            "total": p.get("total", 0),
            "estado": p.get("status", "pendiente"),
            "fecha": fecha,
            "empleado": str(p.get("employee_id")) if p.get("employee_id") else None
        })

    return render_template("empleado/pedidos.html", pedidos=pedidos, rol="empleado")

# ============================================================
#                   ACEPTAR PEDIDO
# ============================================================
@bp_empleado.route("/pedidos/aceptar/<order_id>")
@require_employee_or_admin
def empleado_aceptar_pedido(order_id):
    order = db["orders"].find_one({"_id": ObjectId(order_id)})
    if not order:
        flash("Pedido no encontrado", "error")
        return redirect("/empleado/pedidos")

    if order.get("status") != "pendiente":
        flash("Solo se pueden aceptar pedidos pendientes", "warning")
        return redirect("/empleado/pedidos")

    db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "aceptado", "employee_id": ObjectId(session.get("user_id"))}}
    )

    flash("Pedido aceptado correctamente", "success")
    return redirect("/empleado/pedidos")

@bp_empleado.route("/pedidos/entregar/<order_id>")
@require_employee_or_admin
def empleado_entregar_pedido(order_id):
    order = db["orders"].find_one({"_id": ObjectId(order_id)})

    if not order:
        flash("Pedido no encontrado", "error")
        return redirect("/empleado/pedidos")

    if order["status"] != "aceptado":
        flash("Solo puedes entregar pedidos ya aceptados", "warning")
        return redirect("/empleado/pedidos")

    db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "entregado"}}
    )

    flash("Pedido marcado como entregado", "success")
    return redirect("/empleado/pedidos")

@bp_empleado.route("/pedidos/cancelar/<order_id>")
@require_employee_or_admin
def empleado_cancelar_pedido(order_id):
    order = db["orders"].find_one({"_id": ObjectId(order_id)})

    if not order:
        flash("Pedido no encontrado", "error")
        return redirect("/empleado/pedidos")

    if order["status"] == "entregado":
        flash("No puedes cancelar un pedido entregado", "error")
        return redirect("/empleado/pedidos")

    db["orders"].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "cancelado"}}
    )

    flash("Pedido cancelado correctamente", "success")
    return redirect("/empleado/pedidos")

@bp_empleado.route("/pedidos/editar/<order_id>", methods=["GET", "POST"])
@require_employee_or_admin
def empleado_editar_pedido(order_id):
    order = db["orders"].find_one({"_id": ObjectId(order_id)})

    if not order:
        flash("Pedido no encontrado", "error")
        return redirect("/empleado/pedidos")

    if order["status"] != "pendiente":
        flash("Solo puedes editar pedidos pendientes", "warning")
        return redirect("/empleado/pedidos")

    if request.method == "POST":
        detalles = []
        productos = request.form.getlist("product_id")
        cantidades = request.form.getlist("quantity")

        for i in range(len(productos)):
            prod = productos[i]
            cant = int(cantidades[i])
            producto = db["products"].find_one({"_id": ObjectId(prod)})
            subtotal = cant * float(producto["price"])
            detalles.append({
                "product_id": prod,
                "quantity": cant,
                "subtotal": subtotal
            })

        total = sum(d["subtotal"] for d in detalles)

        db["orders"].update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"details": detalles, "total": total}}
        )

        flash("Pedido actualizado correctamente", "success")
        return redirect("/empleado/pedidos")

    productos = list(db["products"].find())
    return render_template(
        "empleado/editar_pedido.html",
        pedido=order,
        productos=productos,
        rol="empleado"
    )
