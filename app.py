from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'molly_pet_premium_secret_key' # Clave para asegurar las sesiones del carrito

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_NAME = "petmatch.db"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- INICIALIZACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Recreamos la tabla de productos para actualizar las categorías y tipos
    cursor.execute('DROP TABLE IF EXISTS productos')
    cursor.execute('''
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            tipo_formulario TEXT NOT NULL,
            imagen TEXT NOT NULL
        )
    ''')
    
    # Creamos la tabla del foro si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT NOT NULL,
            tipo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            multimedia TEXT
        )
    ''')
    
    # Catálogo optimizado con los formularios específicos de Molly Pet
    nuevos_productos = [
        ("Collar Regulable Confort", "Collares", 1800.0, "mercaderia", "https://images.unsplash.com/photo-1601758124510-52d02ddb7cbd?w=500"),
        ("Buzo de Polar Abrigo Extremo", "Ropa Perros/Gatos", 4500.0, "mercaderia", "https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcQaEEGbnUUmB4efmuFiNrOIrneThYEeW4eHvlVok8XllN2FXQq8Jk0RUNq7tyRTqkVh-i1H3q3QRldywl4"),
        
        # Formulario exclusivo para Alimentos (Precio base inicial por 1 Kilo de Perro)
        ("Alimento Balanceado por Kilo", "Alimentos", 1200.0, "alimento", "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=500"),
        
        # Formulario exclusivo para Pipetas (Solo cantidad)
        ("Pipeta Antiparasitaria Completa", "Salud", 1500.0, "pipeta", "https://images.unsplash.com/photo-1628009368231-7bb7cfcb0def?w=500"),
        
        ("Chapita de Identificación Grabada", "Identificación", 1200.0, "chapita", "https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcQ7QmWtQou2bLhfBKaJYeJkH4tGdN6t777S--SvxNjw7o0iV7Hibpu3ENccNq2ubPKU5NANgMPqqUia4l8"),
        ("Consulta Veterinaria General", "Servicio Médico", 4000.0, "servicio", "https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcRI9cJJ_HXKRqCDyAdNXGTPD8IaOpmYvFm-Jn8cMf0sxpjQDmRz0sbixQE2EJgkeB9AL4Fa50lxZHFjvos"),
        ("Aplicación de Vacuna Quintuple", "Servicio Médico", 3500.0, "servicio", "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=500"),
        ("Sesión de Peluquería Canina SPA", "Estética", 3800.0, "servicio", "https://images.unsplash.com/photo-1516734212186-a967f81ad0d7?w=500")
    ]
    
    cursor.executemany("INSERT INTO productos (nombre, categoria, precio, tipo_formulario, imagen) VALUES (?, ?, ?, ?, ?)", nuevos_productos)
    conn.commit()
    conn.close()

# --- RUTAS DE LA TIENDA Y EL FORO ---

@app.route('/')
def home():
    return redirect(url_for('tienda'))

@app.route('/tienda')
def tienda():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    items = cursor.fetchall()
    conn.close()
    return render_template('tienda.html', items=items)

# --- RUTAS PARA EL CONTROL DEL CARRITO ---

@app.route('/agregar_al_carrito', methods=['POST'])
def agregar_al_carrito():
    if 'carrito' not in session:
        session['carrito'] = {}
    
    id_producto = request.form['id_producto']
    nombre = request.form['nombre']
    precio = float(request.form['precio'])
    
    # Capturar personalizaciones si existen
    detalle = request.form.get('detalle', 'Estándar/Por defecto')
    fecha_turno = request.form.get('fecha_turno', '')
    horario_turno = request.form.get('horario_turno', '')
    
    if fecha_turno or horario_turno:
        detalle = f"Turno: {fecha_turno} a las {horario_turno}"

    # Crear una clave única para la combinación producto + personalización
    item_key = f"{id_producto}_{detalle}"
    
    carrito = session['carrito']
    if item_key in carrito:
        carrito[item_key]['cantidad'] += 1
    else:
        carrito[item_key] = {
            'id': id_producto,
            'nombre': nombre,
            'precio': precio,
            'detalle': detalle,
            'cantidad': 1
        }
    
    session['carrito'] = carrito
    flash(f"🐾 '{nombre}' se agregó al carrito.")
    return redirect(url_for('tienda'))

@app.route('/carrito')
def ver_carrito():
    carrito = session.get('carrito', {})
    subtotal = sum(item['precio'] * item['cantidad'] for item in carrito.values())
    donacion = session.get('donacion', 0.0)
    total = subtotal + donacion
    return render_template('carrito.html', carrito=carrito, subtotal=subtotal, donacion=donacion, total=total)

@app.route('/actualizar_carrito/<item_key>', methods=['POST'])
def actualizar_carrito(item_key):
    carrito = session.get('carrito', {})
    nueva_cantidad = int(request.form['cantidad'])
    
    if item_key in carrito:
        if nueva_cantidad > 0:
            carrito[item_key]['cantidad'] = nueva_cantidad
        else:
            carrito.pop(item_key)
            
    session['carrito'] = carrito
    return redirect(url_for('ver_carrito'))

@app.route('/eliminar_del_carrito/<item_key>')
def eliminar_del_carrito(item_key):
    carrito = session.get('carrito', {})
    if item_key in carrito:
        carrito.pop(item_key)
    session['carrito'] = carrito
    flash("Artículo eliminado del carrito.")
    return redirect(url_for('ver_carrito'))

@app.route('/agregar_donacion_web', methods=['POST'])
def agregar_donacion_web():
    try:
        monto = float(request.form['monto_donacion'])
        session['donacion'] = monto if monto > 0 else 0.0
    except ValueError:
        session['donacion'] = 0.0
    return redirect(url_for('ver_carrito'))

@app.route('/finalizar_pago', methods=['POST'])
def finalizar_pago():
    session.pop('carrito', None)
    session.pop('donacion', None)
    flash("🎉 ¡Pedido realizado con éxito en Molly Pet! Nos pondremos en contacto para coordinar los detalles.")
    return redirect(url_for('tienda'))

# --- RUTA DEL FORO ---

@app.route('/foro', methods=['GET', 'POST'])
def foro():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if request.method == 'POST':
        autor = request.form['autor']
        tipo = request.form['tipo']
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        filename_guardado = ""
        if 'multimedia_file' in request.files:
            file = request.files['multimedia_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filename_guardado = filename
        cursor.execute('INSERT INTO publicaciones (autor, tipo, titulo, contenido, multimedia) VALUES (?, ?, ?, ?, ?)', (autor, tipo, titulo, contenido, filename_guardado))
        conn.commit()
        return redirect(url_for('foro'))
    cursor.execute("SELECT * FROM publicaciones ORDER BY id DESC")
    posts = cursor.fetchall()
    conn.close()
    return render_template('foro.html', posts=posts)

if __name__ == '__main__':
    # Forzar la recreación limpia de la base de datos con los nuevos productos
    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)