from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
from entities.user import User
from database import dbConnection
from functools import wraps

auth_bp = Blueprint("auth", __name__)
db = dbConnection()

# LOGIN
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Si ya está logueado, redirigir según su rol
    if 'user_id' in session:
        return redirect(get_redirect_url(session.get('role', 'cliente')))
    
    if request.method == "POST":
        username = request.form["usuario"]
        password = request.form["password"]
        
        # Buscar usuario en la base de datos
        users_collection = db['users']
        user_data = users_collection.find_one({'username': username})
        
        if not user_data:
            return render_template("auth/login.html", error="Usuario no encontrado")
        
        # Verificar contraseña
        if not check_password_hash(user_data['password_hash'], password):
            return render_template("auth/login.html", error="Contraseña incorrecta")
        
        # Verificar si el usuario está activo
        if not user_data.get('is_active', True):
            return render_template("auth/login.html", error="Cuenta desactivada")
        
        # Guardar sesión
        session['user_id'] = str(user_data['_id'])
        session['usuario'] = user_data['username']
        session['role'] = user_data['role']
        session['email'] = user_data.get('email', '')
        
        # Redireccionar según rol
        return redirect(get_redirect_url(user_data['role']))
    
    return render_template("auth/login.html")


#REGISTER

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["usuario"]
        email = request.form["correo"]
        password = request.form["password"]
        role = request.form.get("rol", "cliente")
        
        # Validaciones básicas
        if not username or not email or not password:
            return render_template("auth/register.html", error="Todos los campos son obligatorios")
        
        users_collection = db['users']
        
        # Verificar si el usuario ya existe
        existing_user = users_collection.find_one({
            '$or': [
                {'username': username},
                {'email': email}
            ]
        })
        
        if existing_user:
            return render_template("auth/register.html", 
                                 error="El usuario o email ya están registrados")
        
        # Validar que solo un admin pueda crear otros admins
        if role == 'admin' and ('role' not in session or session.get('role') != 'admin'):
            role = 'cliente'  # Degradar a cliente si no es admin quien crea
        
        # Crear nuevo usuario
        new_user = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': role,
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        
        # Insertar en la base de datos
        result = users_collection.insert_one(new_user)
        
        # Si el registro fue exitoso, iniciar sesión automáticamente
        if result.inserted_id:
            session['user_id'] = str(result.inserted_id)
            session['usuario'] = username
            session['role'] = role
            session['email'] = email
            
            return redirect(get_redirect_url(role))
        else:
            return render_template("auth/register.html", error="Error al crear usuario")
    
    return render_template("auth/register.html")

# LOGOUT

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ============================================================
#                FUNCIONES AUXILIARES DE AUTENTICACIÓN
# ============================================================

# Función para crear admin inicial
def create_initial_admin():
    """Crear usuario admin si no existe ninguno"""
    users_collection = db['users']
    
    # Verificar si ya existe un admin
    admin_exists = users_collection.find_one({'role': 'admin'})
    
    if not admin_exists:
        admin_user = {
            'username': 'admin',
            'email': 'admin@pasteleria.com',
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        users_collection.insert_one(admin_user)
        print("✅ Usuario admin creado:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("   Email: admin@pasteleria.com")

# Middleware para verificar sesión
@auth_bp.before_app_request
def before_request():
    # Rutas públicas que no requieren autenticación
    public_routes = ['login', 'register', 'cliente_home', 'cliente_productos', 
                     'cliente_categorias', 'static', 'not_found']
    
    if request.endpoint in public_routes:
        return
    
    # Verificar si el usuario está logueado
    if 'user_id' not in session:
        return redirect('/login')
    
    # Verificar si el usuario existe y está activo
    try:
        user_data = db['users'].find_one({'_id': ObjectId(session['user_id'])})
        if not user_data or not user_data.get('is_active', True):
            session.clear()
            return redirect('/login')
    except:
        session.clear()
        return redirect('/login')

# Función para obtener URL de redirección
def get_redirect_url(role):
    """Obtener la URL de redirección según el rol"""
    if role == "admin":
        return "/admin"
    elif role == "empleado":
        return "/empleado"
    else:
        return "/cliente"

# Decoradores para verificar roles
def require_role(role):
    """Decorador para verificar rol del usuario"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                return redirect('/login')
            if session['role'] != role:
                flash('No tienes permisos para acceder a esta página', 'error')
                return redirect(get_redirect_url(session['role']))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_employee_or_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect('/login')
        if session['role'] not in ['empleado', 'admin']:
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

