from flask import Flask, render_template, request, jsonify, redirect, url_for, session

import database as dbase
from entities.products import Product

db = dbase.dbConnection()
app = Flask(__name__)

'''

#Rutas de la aplicación
@app.route('/')
def home():
    products = db['products']
    productsReceived = products.find()
    return render_template('index.html', products = productsReceived)

#Method Post
@app.route('/products', methods=['POST'])
def addProduct():
    products = db['products']
    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    price = request.form['price']
    status = request.form['status']
    quantity = request.form['quantity']

    if name and description and category and price and status and quantity:
        product = Product(name, description, category, price, status, quantity)
        products.insert_one(product.toDBCollection())
        response = jsonify({
            'name' : name,
            'description' : description,
            'category' : category,
            'price' : price,
            'status' : status,
            'quantity' : quantity
        })
        return redirect(url_for('home'))
    else:
        return notFound()

#Method delete
@app.route('/delete/<string:product_name>')
def delete(product_name):
    products = db['products']
    products.delete_one({'name' : product_name})
    return redirect(url_for('home'))

#Method Put
@app.route('/edit/<string:product_name>', methods=['POST'])
def edit(product_name):
    products = db['products']
    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    price = request.form['price']
    status = request.form['status']
    quantity = request.form['quantity']

    if name and description and category and price and status and quantity:
        products.update_one({'name' : product_name}, {'$set' : {'name' : name, 'description' : description, 'category' : category, 'price' : price, 'status' : status, 'quantity' : quantity}})
        response = jsonify({'message' : 'Producto ' + product_name + ' actualizado correctamente'})
        return redirect(url_for('home'))
    else:
        return notFound()

@app.errorhandler(404)
def notFound(error=None):
    message ={
        'message': 'No encontrado ' + request.url,
        'status': '404 Not Found'
    }
    response = jsonify(message)
    response.status_code = 404
    return response

'''

app.secret_key = "clave_super_segura"   # Necesario para sesión


# ============================================================
#                LOGIN (CON DATOS SIMULADOS)
# ============================================================

usuarios_simulados = [
    {"usuario": "admin", "password": "123", "rol": "admin"},
    {"usuario": "empleado1", "password": "123", "rol": "empleado"},
    {"usuario": "cliente1", "password": "123", "rol": "cliente"},
]

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        # Buscar usuario
        user = next((u for u in usuarios_simulados
                     if u["usuario"] == usuario and u["password"] == password), None)

        if not user:
            return render_template("auth/login.html", error="Usuario o contraseña incorrectos")

        # Guardar sesión
        session["usuario"] = usuario
        session["rol"] = user["rol"]

        # Redireccionar por rol
        if user["rol"] == "admin":
            return redirect("/admin")
        if user["rol"] == "empleado":
            return redirect("/empleado")
        return redirect("/")

    return render_template("auth/login.html")


# ============================================================
#                REGISTRO (SE GUARDA EN MEMORIA)
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        usuario = request.form["usuario"]
        correo = request.form["correo"]
        password = request.form["password"]
        rol = request.form["rol"]

        usuarios_simulados.append({
            "usuario": usuario,
            "password": password,
            "rol": rol
        })

        return redirect("/login")

    return render_template("auth/register.html")


# ============================================================
#                LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


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

    # Simulación (luego reemplazas por consultas a tu BD)
    total_productos = 120
    total_categorias = 8
    total_usuarios = 45
    pedidos_pendientes = 3

    stock_bajo = ["Mouse Gamer", "Teclado Mecánico"]  # ejemplo

    ultimos_pedidos = [
        {"id": 101, "cliente": "Ana", "fecha": "2025-12-01", "estado": "Pendiente"},
        {"id": 102, "cliente": "Pedro", "fecha": "2025-12-01", "estado": "Enviado"},
    ]

    productos_populares = [
        {"nombre": "Audífonos Bluetooth", "cantidad": 58},
        {"nombre": "Laptop Lenovo", "cantidad": 34},
        {"nombre": "Mouse Gamer", "cantidad": 33},
    ]

    clientes_top = [
        {"nombre": "Juan Pérez", "total": 16},
        {"nombre": "María López", "total": 12},
        {"nombre": "Carlos Ruiz", "total": 10},
    ]

    return render_template(
        "admin/dashboard.html",
        rol="admin",
        total_productos=total_productos,
        total_categorias=total_categorias,
        total_usuarios=total_usuarios,
        pedidos_pendientes=pedidos_pendientes,
        stock_bajo=stock_bajo,
        ultimos_pedidos=ultimos_pedidos,
        productos_populares=productos_populares,
        clientes_top=clientes_top
    )

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

@app.route("/admin/reportes")
def admin_reportes():

    # EJEMPLOS, los reemplazas con datos reales de tu BD
    ventas_hoy = 1500
    ventas_mes = 32400
    ventas_anio = 280000
    pedidos_completados = 87
    promedio_pedido = 175

    ventas_por_mes = [
        {"mes": "Enero", "total": 12000},
        {"mes": "Febrero", "total": 9800},
        {"mes": "Marzo", "total": 15200},
        {"mes": "Abril", "total": 14300},
    ]

    productos_top = [
        {"nombre": "Producto A", "cantidad": 40},
        {"nombre": "Producto B", "cantidad": 28},
        {"nombre": "Producto C", "cantidad": 21},
    ]

    clientes_top = [
        {"nombre": "Juan Pérez", "compras": 12},
        {"nombre": "Ana López", "compras": 9},
        {"nombre": "Carlos Ríos", "compras": 8},
    ]

    return render_template(
        "admin/reportes.html",
        rol="admin",
        ventas_hoy=ventas_hoy,
        ventas_mes=ventas_mes,
        ventas_anio=ventas_anio,
        pedidos_completados=pedidos_completados,
        promedio_pedido=promedio_pedido,
        ventas_por_mes=ventas_por_mes,
        productos_top=productos_top,
        clientes_top=clientes_top
    )

@app.route("/admin/usuarios")
def admin_usuarios():
    # Simulación de usuarios
    usuarios = [
        {"nombre": "Juan", "rol": "empleado"},
        {"nombre": "Maria", "rol": "cliente"},
        {"nombre": "Pedro", "rol": "empleado"},
        {"nombre": "Ana", "rol": "cliente"},
        {"nombre": "Carlos", "rol": "admin"},  # otro admin
    ]

    # Agrupar usuarios por rol
    usuarios_por_rol = {}
    for u in usuarios:
        usuarios_por_rol.setdefault(u["rol"], []).append(u)

    return render_template("admin/usuarios.html", usuarios_por_rol=usuarios_por_rol, rol="admin")

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
