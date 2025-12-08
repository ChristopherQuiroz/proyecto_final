from flask import Blueprint, render_template, session
from routes.auth import require_employee_or_admin
from database import dbConnection
from entities.category import Category, category_manager
from entities.product import Product

bp_empleado = Blueprint("empleado", __name__, url_prefix="/empleado")
db = dbConnection()


# ============================================================
#                   PANEL PRINCIPAL EMPLEADO
# ============================================================
@bp_empleado.route("/")
@require_employee_or_admin
def empleado_panel():

    productos = db["products"]

    pedidos_pendientes = db["orders"].count_documents({"estado": "Pendiente"}) if "orders" in db.list_collection_names() else 0
    pedidos_hoy = pedidos_pendientes
    stock_bajo = productos.count_documents({"quantity": {"$lt": 5}})
    clientes_hoy = db["users"].count_documents({"role": "cliente"})

    productos_bajo_stock = list(productos.find({"quantity": {"$lt": 5}}))

    pedidos_asignados = []  # pendiente

    return render_template(
        "empleado/dashboard.html",   # ← ESTE ES EL NOMBRE REAL DEL ARCHIVO
        pedidos_pendientes=pedidos_pendientes,
        pedidos_hoy=pedidos_hoy,
        stock_bajo=stock_bajo,
        clientes_hoy=clientes_hoy,
        productos_bajo_stock=productos_bajo_stock,
        pedidos_asignados=pedidos_asignados,
        rol="empleado"
    )


# ============================================================
#                   CLIENTES (DATOS SIMULADOS POR AHORA)
# ============================================================

@bp_empleado.route("/clientes")
@require_employee_or_admin
def empleado_clientes():

    clientes = [
        {"id": i, "nombre": f"Cliente {i}", "telefono": f"7000000{i}", "correo": f"cliente{i}@gmail.com"}
        for i in range(1, 11)
    ]

    return render_template(
        "empleado/empleado_clientes.html",
        clientes=clientes,
        rol="empleado"
    )


# ============================================================
#                CREAR PEDIDO
# ============================================================

@bp_empleado.route("/crear_pedido")
@require_employee_or_admin
def empleado_crear_pedido():
    return render_template("empleado/crear_pedido.html", rol="empleado")


# ============================================================
#                PRODUCTOS (BD REAL)
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
#                INVENTARIO (BD REAL)
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
#                VER PEDIDOS (SIMULADO POR AHORA)
# ============================================================
@bp_empleado.route("/pedidos")
@require_employee_or_admin
def empleado_pedidos():

    # Más adelante se conectará con la colección "orders"
    pedidos = [
        {"id": 1, "cliente": "Juan Pérez", "total": 85, "estado": "Pendiente"},
        {"id": 2, "cliente": "Ana López", "total": 120, "estado": "Completado"},
        {"id": 3, "cliente": "Luis García", "total": 60, "estado": "Pendiente"},
    ]

    return render_template(
        "empleado/pedidos.html",
        pedidos=pedidos,
        rol="empleado"
    )
