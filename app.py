from flask import Flask, render_template, request, Response, jsonify, redirect, url_for
import database as dbase
from entities.products import Product

db = dbase.dbConnection()

app = Flask(__name__)

@app.route('/pedido')
def pedido_cliente():
    # Productos simulados para pruebas
    productos = [
        {"id": 1, "nombre": "Cupcake Vainilla", "precio": 10.0, "descripcion": "Delicioso cupcake", "imagen": "/static/img/cupcake.png"},
        {"id": 2, "nombre": "Cupcake Chocolate", "precio": 12.0, "descripcion": "Chocolate intenso", "imagen": "/static/img/cupcake.png"},
        {"id": 3, "nombre": "Galleta Chocolate", "precio": 5.0, "descripcion": "Galleta crujiente", "imagen": "/static/img/galleta.png"}
    ]
    return render_template('pedido_cliente.html', productos=productos)

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