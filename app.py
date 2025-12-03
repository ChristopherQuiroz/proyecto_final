from flask import Flask, render_template, request, Response, jsonify, redirect, url_for
import database as dbase
from entities.products import Product

db = dbase.dbConnection()

app = Flask(__name__)

# CLIENTES DEL EMPLEADO
@app.route("/empleado/clientes")
def empleado_clientes():
    clientesData = [
        {"id": 1, "nombre": "Juan Pérez", "telefono": "77777777", "correo": "juan@gmail.com"},
        {"id": 2, "nombre": "María López", "telefono": "60606060", "correo": "maria@gmail.com"},
    ]
    return render_template("empleado_clientes.html", clientes=clientesData)

# CREAR PEDIDO
@app.route("/empleado/crear_pedido")
def crear_pedido():
    return render_template("crear_pedido.html")

@app.route("/empleado")
def panel_empleado():
    productosData = [
        {
            "nombre": "Cupcake Vainilla",
            "precio": 10,
            "descripcion": "Delicioso cupcake suave",
            "imagen": "/static/img/cupcake.png"
        },
        {
            "nombre": "Galleta Chocolate",
            "precio": 5,
            "descripcion": "Galleta crujiente con chispas de chocolate",
            "imagen": "/static/img/galleta.png"
        },
        {
            "nombre": "Pan de Leche",
            "precio": 8,
            "descripcion": "Pan recién horneado",
            "imagen": "/static/img/pan.png"
        }
    ]
    
    return render_template("panel_empleado.html", productos=productosData)

@app.route('/categorias')
def mostrar_categorias():
    # Datos simulados
    categoriasData = [
        {'nombre': 'Pastelería'},
        {'nombre': 'Bebidas'},
        {'nombre': 'Panadería'},
        {'nombre': 'Dulces'},
        {'nombre': 'Salado'}
    ]
    productosData = [
        {'nombre': 'Cupcake', 'descripcion': 'Delicioso cupcake de vainilla', 'precio': 10, 'imagen': '/static/img/cupcake.png'},
        {'nombre': 'Galleta', 'descripcion': 'Galleta de chocolate', 'precio': 5, 'imagen': '/static/img/galleta.png'}
    ]
    return render_template('categorias.html', categorias=categoriasData, productos=productosData)

@app.route("/admin_categorias")
def admin_categorias():
    categoriasData = [
        {'nombre': 'Pastelería'},
        {'nombre': 'Bebidas'},
        {'nombre': 'Panadería'},
        {'nombre': 'Dulces'},
        {'nombre': 'Salado'}
    ]
    return render_template("admin_categorias.html", categorias=categoriasData)

# ==============================
# RUTAS GENERALES
# ==============================

@app.route('/')
def home():
    # Página principal, productos simulados
    productos = [
        {"nombre": "Cupcake Vainilla", "precio": 10, "descripcion": "Delicioso cupcake", "imagen": "/static/img/cupcake.png"},
        {"nombre": "Galleta Chocolate", "precio": 5, "descripcion": "Galleta crujiente", "imagen": "/static/img/galleta.png"}
    ]
    return render_template('index.html', products=productos)

# ==============================
# RUTAS DE PRODUCTOS (CRUD) SIMULADAS
# ==============================

# Nota: Estas rutas aún dependen de tu modelo Product y DB real
# Por ahora puedes comentarlas si quieres probar el frontend sin errores

"""
@app.route('/products', methods=['POST'])
def addProduct():
    # Aquí iría tu lógica para agregar productos a la DB
    return redirect(url_for('home'))

@app.route('/delete/<string:product_name>')
def delete(product_name):
    # Lógica para eliminar producto de la DB
    return redirect(url_for('home'))

@app.route('/edit/<string:product_name>', methods=['POST'])
def edit(product_name):
    # Lógica para actualizar producto
    return redirect(url_for('home'))
"""

# ==============================
# ERROR 404
# ==============================

@app.errorhandler(404)
def notFound(error=None):
    message = {
        'message': 'No encontrado ' + request.url,
        'status': '404 Not Found'
    }
    response = jsonify(message)
    response.status_code = 404
    return response

# ==============================
# MAIN
# ==============================

if __name__ == '__main__':
    app.run(debug=True, port=4000)