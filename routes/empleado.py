from flask import Blueprint, render_template, session
from routes.auth import require_employee_or_admin

bp_empleado = Blueprint("empleado", __name__, url_prefix="/empleado")


# ============================================================
#                   ROL: EMPLEADO
# ============================================================

@bp_empleado.route("/")
@require_employee_or_admin
def empleado_panel():
    productos = [
        {"nombre": f"Producto {i}", "precio": 3*i, "descripcion": f"Descripción {i}", "imagen": "/static/img/cupcake.png"}
        for i in range(1, 11)
    ]
    return render_template("empleado/panel_empleado.html", productos=productos, rol="empleado")


@bp_empleado.route("/clientes")
@require_employee_or_admin
def empleado_clientes():
    clientes = [
        {"id": i, "nombre": f"Cliente {i}", "telefono": f"7000000{i}", "correo": f"cliente{i}@gmail.com"}
        for i in range(1, 11)
    ]
    return render_template("empleado/empleado_clientes.html", clientes=clientes, rol="empleado")


@bp_empleado.route("/crear_pedido")
@require_employee_or_admin
def empleado_crear_pedido():
    return render_template("empleado/crear_pedido.html", rol="empleado")


@bp_empleado.route("/productos")
@require_employee_or_admin
def empleado_productos():
    return render_template("empleado/productos.html", rol="empleado")


@bp_empleado.route("/inventario")
@require_employee_or_admin
def empleado_inventario():
    return render_template("empleado/inventario.html", rol="empleado")
