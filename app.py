from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from functools import wraps
import database as dbase

from routes.cliente import bp_cliente
from routes.empleado import bp_empleado
from routes.admin import bp_admin
from routes.auth import auth_bp
db = dbase.dbConnection()
app = Flask(__name__)
app.secret_key = "clave_super_segura"

app.register_blueprint(auth_bp)
app.register_blueprint(bp_cliente)
app.register_blueprint(bp_empleado)
app.register_blueprint(bp_admin)

if __name__ == '__main__':
    app.run(debug=True, port=4000)
