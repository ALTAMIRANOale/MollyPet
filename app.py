from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'mundo_animal_premium_secret_key' # Clave para asegurar las sesiones del carrito

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_NAME = "petmatch.db"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# --- NUEVAS RUTAS PARA EL CONTROL DEL CARRITO ---

@app.route('/agregar_al_carrito', methods=['POST'])
def agregar_al_carrito():
    # Inicializar carrito en la sesión si no existe
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
            carrito.pop(item_key) # Si es 0, lo elimina
            
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
    # Simulamos el procesamiento final del pedido borrando el carrito
    session.pop('carrito', None)
    session.pop('donacion', None)
    flash("🎉 ¡Pedido realizado con éxito en Mundo Animal! Nos pondremos en contacto para coordinar los detalles.")
    return redirect(url_for('tienda'))

# (Mantené tu código de la ruta @app.route('/foro') igual que antes aquí abajo)
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
    if not os.path.exists(DB_NAME):
        # Ejecutar inicialización de tablas si no existe la BD
        pass 
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)