from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
from entities.user import User
from database import dbConnection
from functools import wraps

auth_bp = Blueprint("auth", __name__)
db = dbConnection()

@auth_bp.route("/")
def home():
    if 'role' in session:
        return redirect(get_redirect_url(session['role']))
    return render_template("cliente/dashboard.html", rol="invitado")

# ============================================================
#                          LOGIN
# ============================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and 'user_id' in session:
        return render_template("auth/login.html")

    if request.method == "POST":
        username = request.form.get("usuario")
        password = request.form.get("password")

        user_data = db['users'].find_one({'username': username})
        if not user_data:
            return render_template("auth/login.html", error="Usuario no encontrado")

        user = User.from_dict(user_data)

        if not user.verify_password(password):
            return render_template("auth/login.html", error="Contraseña incorrecta")

        if not user.is_active:
            return render_template("auth/login.html", error="Cuenta desactivada")

        session['user_id'] = str(user_data['_id'])
        session['username'] = user.username
        session['role'] = user.role.strip().lower()
        session['email'] = user.email
        session['inicial'] = user.username[0].upper()

        return redirect(get_redirect_url(session['role']))

    return render_template("auth/login.html")


# ============================================================
#                        REGISTER
# ============================================================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["usuario"]
        email = request.form["correo"]
        password = request.form["password"]
        role = request.form.get("rol", "cliente").strip().lower()

        if not username or not email or not password:
            return render_template("auth/register.html",
                                   error="Todos los campos son obligatorios")

        users_collection = db['users']

        existing_user = users_collection.find_one({
            '$or': [{'username': username}, {'email': email}]
        })

        if existing_user:
            return render_template("auth/register.html",
                                   error="El usuario o email ya están registrados")

        if role == 'admin' and session.get('role') != 'admin':
            role = 'cliente'

        new_user = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': role,
            'is_active': True,
            'created_at': datetime.utcnow()
        }

        result = users_collection.insert_one(new_user)

        if result.inserted_id:
            session['user_id'] = str(result.inserted_id)
            session['username'] = username
            session['email'] = email
            session['role'] = role
            session['inicial'] = username[0].upper()

            return redirect(get_redirect_url(session['role']))

        return render_template("auth/register.html",
                               error="Error al crear usuario")

    return render_template("auth/register.html")


# ============================================================
#                        LOGOUT
# ============================================================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ============================================================
#                MIDDLEWARE GENERAL DE SESIÓN
# ============================================================
@auth_bp.before_app_request
def before_request():
    # Rutas completamente públicas
    public_endpoints = [
        'auth.login',
        'auth.register',
        'auth.home',
        'static',
        'not_found'
    ]

    # Rutas del cliente accesibles sin iniciar sesión
    public_cliente = [
        'cliente.cliente_dashboard',
        'cliente.cliente_productos',
        'cliente.cliente_categorias',
        'cliente.cliente_detalle_producto'
    ]

    # Rutas protegidas del cliente (necesitan login, pero middleware debe dejarlas pasar)
    protected_cliente = [
        'cliente.cliente_carrito',
        'cliente.cliente_mis_pedidos',
        'cliente.agregar_al_carrito',
        'cliente.eliminar_del_carrito',
        'cliente.actualizar_cantidad',
        'cliente.cliente_pagar'
    ]

    endpoint = request.endpoint or ""

    # Público total
    if endpoint in public_endpoints or endpoint in public_cliente:
        return

    # Estas rutas SÍ deben ejecutarse y el decorador require_role decidirá el permiso
    if endpoint in protected_cliente:
        return

    # Para el resto → requiere login
    if 'user_id' not in session:
        return redirect('/login')

    # Verificar usuario activo
    try:
        user_data = db['users'].find_one({'_id': ObjectId(session['user_id'])})
        if not user_data or not user_data.get('is_active', True):
            session.clear()
            return redirect('/login')
    except:
        session.clear()
        return redirect('/login')


# ============================================================
#          FUNCIÓN DE REDIRECCIÓN
# ============================================================
def get_redirect_url(role):
    role = str(role).strip().lower()

    if role == "admin":
        return "/admin"
    elif role == "empleado":
        return "/empleado"
    elif role == "cliente":
        return "/cliente"
    return "/login"


# ============================================================
#                 DECORADOR DE ROLES
# ============================================================
def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'role' not in session:
                return redirect('/login')

            if session['role'].strip().lower() != role.strip().lower():
                flash('No tienes permisos para acceder a esta página', 'error')
                return redirect(get_redirect_url(session['role']))

            return f(*args, **kwargs)
        return decorated
    return decorator


def require_employee_or_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect('/login')

        if session.get('role') not in ['empleado', 'admin']:
            flash('No tienes permisos', 'error')
            return redirect(get_redirect_url(session.get('role', 'cliente')))

        return f(*args, **kwargs)
    return decorated_function
