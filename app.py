from flask import Flask, render_template, request, jsonify, redirect, url_for
import database as dbase
from entities.products import Product

db = dbase.dbConnection()
app = Flask(__name__)

# ============================================================
#                   ROL: CLIENTE
# ============================================================

@app.route("/")
def cliente_home():
    productos = [
        {"id": 1, "nombre": "Cupcake Vainilla", "precio": 10, "descripcion": "Cupcake suave", "imagen": "/static/img/cupcake.png"},
        {"id": 2, "nombre": "Galleta Chocolate", "precio": 5, "descripcion": "Galleta crujiente", "imagen": "/static/img/galleta.png"},
        {"id": 3, "nombre": "Brownie", "precio": 8, "descripcion": "Brownie intenso", "imagen": "/static/img/cupcake.png"},
        {"id": 4, "nombre": "Pan de Leche", "precio": 6, "descripcion": "Pan fresco", "imagen": "/static/img/pan.png"},
        {"id": 5, "nombre": "Torta Fresa", "precio": 30, "descripcion": "Bizcocho con fresa", "imagen": "/static/img/pastel.png"},
        {"id": 6, "nombre": "Cupcake Oreo", "precio": 12, "descripcion": "Cupcake con Oreo", "imagen": "/static/img/cupcake.png"},
        {"id": 7, "nombre": "Empanada de Pollo", "precio": 7, "descripcion": "Rellena de pollo", "imagen": "/static/img/pan.png"},
        {"id": 8, "nombre": "Torta Chocolate", "precio": 35, "descripcion": "Chocolate 70%", "imagen": "/static/img/pastel.png"},
        {"id": 9, "nombre": "Galleta Vainilla", "precio": 4, "descripcion": "Galleta suave", "imagen": "/static/img/galleta.png"},
        {"id": 10, "nombre": "Pan Ciabatta", "precio": 5, "descripcion": "Pan crocante", "imagen": "/static/img/pan.png"},
    ]
    return render_template("cliente/index.html", productos=productos, rol="cliente")


@app.route("/cliente/productos")
def cliente_productos():
    productos = [
        {"id": i, "nombre": f"Producto {i}", "precio": i*3, "descripcion": f"Descripción del producto {i}", "imagen": "/static/img/cupcake.png"}
        for i in range(1, 11)
    ]
    return render_template("cliente/productos.html", productos=productos, rol="cliente")


@app.route("/cliente/categorias")
def cliente_categorias():
    categorias = [
        {"id": 1, "nombre": "Dulces"},
        {"id": 2, "nombre": "Salados"},
        {"id": 3, "nombre": "Pastelería"},
        {"id": 4, "nombre": "Bebidas"},
        {"id": 5, "nombre": "Galletas"},
        {"id": 6, "nombre": "Cupcakes"},
        {"id": 7, "nombre": "Tortas Especiales"},
        {"id": 8, "nombre": "Panadería"},
        {"id": 9, "nombre": "Decorados"},
        {"id": 10,"nombre": "Otros"},
    ]

    productos = [
        {"nombre": f"Producto {i}", "descripcion": f"Descripción {i}", "precio": 5*i, "imagen": "/static/img/cupcake.png"}
        for i in range(1, 11)
    ]

    return render_template("cliente/categorias.html", categorias=categorias, productos=productos, rol="cliente")


@app.route("/cliente/carrito")
def cliente_carrito():
    return render_template("cliente/carrito.html", rol="cliente")


@app.route("/cliente/mis_pedidos")
def cliente_mis_pedidos():
    pedidos = [
        {"id": i, "total": 10*i, "estado": "Entregado" if i % 2 == 0 else "Pendiente"}
        for i in range(1, 10)
    ]
    return render_template("cliente/mis_pedidos.html", pedidos=pedidos, rol="cliente")


# ============================================================
#                   ROL: EMPLEADO
# ============================================================

@app.route("/empleado")
def empleado_panel():
    productos = [
        {"nombre": f"Producto {i}", "precio": 3*i, "descripcion": f"Descripción {i}", "imagen": "/static/img/cupcake.png"}
        for i in range(1, 11)
    ]
    return render_template("empleado/panel_empleado.html", productos=productos, rol="empleado")


@app.route("/empleado/clientes")
def empleado_clientes():
    clientes = [
        {"id": i, "nombre": f"Cliente {i}", "telefono": f"7000000{i}", "correo": f"cliente{i}@gmail.com"}
        for i in range(1, 11)
    ]
    return render_template("empleado/empleado_clientes.html", clientes=clientes, rol="empleado")


@app.route("/empleado/crear_pedido")
def empleado_crear_pedido():
    return render_template("empleado/crear_pedido.html", rol="empleado")


@app.route("/empleado/productos")
def empleado_productos():
    return render_template("empleado/productos.html", rol="empleado")


@app.route("/empleado/inventario")
def empleado_inventario():
    return render_template("empleado/inventario.html", rol="empleado")


# ============================================================
#                   ROL: ADMIN
# ============================================================

@app.route("/admin")
def admin_dashboard():
    return render_template("admin/dashboard.html", rol="admin")


@app.route("/admin/categorias")
def admin_categorias():
    categorias = [{"nombre": f"Categoría {i}"} for i in range(1, 11)]
    return render_template("admin/categorias.html", categorias=categorias, rol="admin")


@app.route("/admin/productos")
def admin_productos():
    return render_template("admin/productos.html", rol="admin")


@app.route("/admin/inventario")
def admin_inventario():
    return render_template("admin/inventario.html", rol="admin")


@app.route("/admin/clientes")
def admin_clientes():
    return render_template("admin/clientes.html", rol="admin")


@app.route("/admin/empleados")
def admin_empleados():
    return render_template("admin/empleados.html", rol="admin")


@app.route("/admin/pedidos")
def admin_pedidos():
    return render_template("admin/pedidos.html", rol="admin")


# ============================================================
#                        ERROR 404
# ============================================================

@app.errorhandler(404)
def not_found(error=None):
    message = {
        'message': 'No encontrado: ' + request.url,
        'status': 404
    }
    return jsonify(message), 404

# ============================================================
#                        MAIN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, port=4000)
