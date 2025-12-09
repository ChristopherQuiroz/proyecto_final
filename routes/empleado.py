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

    # Pedidos pendientes
    pedidos_pendientes = orders_collection.count_documents({"status": "pendiente"})
    # Pedidos de hoy
    hoy_inicio = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    pedidos_hoy = orders_collection.count_documents({"date": {"$gte": hoy_inicio}})
    # Productos bajo stock
    stock_bajo = productos_collection.count_documents({"quantity": {"$lt": 5}})
    productos_bajo_stock = list(productos_collection.find({"quantity": {"$lt": 5}}))
    # Total clientes
    clientes_hoy = users_collection.count_documents({"role": "cliente"})
    # Pedidos asignados al empleado
    pedidos_asignados_db = list(orders_collection.find({"employee_id": ObjectId(session.get("user_id"))}))
    pedidos_asignados = [Order.from_dict(p) for p in pedidos_asignados_db]

    return render_template(
        "empleado/dashboard.html",
        pedidos_pendientes=pedidos_pendientes,
        pedidos_hoy=pedidos_hoy,
        stock_bajo=stock_bajo,
        clientes_hoy=clientes_hoy,
        productos_bajo_stock=productos_bajo_stock,
        pedidos_asignados=pedidos_asignados,
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
    if request.method == "POST":
        customer_id = request.form.get("customer_id")  # opcional: cliente registrado
        detalles = request.form.getlist("detalles")  # [{"product_id":..., "quantity":..., "subtotal":...}, ...]
        detalles_list = []
        for d in detalles:
            detalles_list.append(OrderDetail(d['product_id'], int(d['quantity']), float(d['subtotal'])).to_dict())
        order_id, msg = None, ""
        if detalles_list:
            order_obj = Order(
                customer_id=customer_id or None,
                employee_id=session.get("user_id"),
                status="pendiente",
                total=sum(d["subtotal"] for d in detalles_list),
                details=[OrderDetail.from_dict(d) for d in detalles_list],
                created_in_person=not customer_id
            )
            result = db["orders"].insert_one(order_obj.to_dict())
            order_id = str(result.inserted_id)
            msg = "Pedido creado correctamente"
        else:
            msg = "No se pudo crear el pedido: detalles vacíos"

        flash(msg, "success")
        return redirect("/empleado/pedidos")

    # GET: mostrar formulario con productos y clientes
    productos = list(db["products"].find({"status": "available"}))
    clientes = list(db["users"].find({"role": "cliente"}))
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
        cliente = db["users"].find_one({"_id": p["customer_id"]})
        pedidos.append({
            "id": str(p["_id"]),
            "cliente": cliente["username"] if cliente else "Cliente",
            "total": p.get("total", 0),
            "estado": p.get("status", "pendiente"),
            "fecha": p.get("date", datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
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
