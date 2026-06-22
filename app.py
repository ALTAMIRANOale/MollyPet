from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'mundo_animal_key'

# Configuración de la carpeta para guardar fotos y videos del foro
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_NAME = "petmatch.db"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS productos')
    
    # Agregamos la columna 'imagen' para el catálogo visual
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
    
    # Catálogo de Mundo Animal con imágenes demostrativas temáticas
    # Catálogo de Mundo Animal con imágenes demostrativas temáticas corregidas
    nuevos_productos = [
        ("Collar Regulable Confort", "Collares", 1800.0, "mercaderia", "https://images.unsplash.com/photo-1601758124510-52d02ddb7cbd?w=500"),
        
        # 👕 CORREGIDO: Foto real de un perrito abrigado con ropa polar
        ("Buzo de Polar Abrigo Extremo", "Ropa Perros/Gatos", 4500.0, "mercaderia", "https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcQaEEGbnUUmB4efmuFiNrOIrneThYEeW4eHvlVok8XllN2FXQq8Jk0RUNq7tyRTqkVh-i1H3q3QRldywl4"),
        
        ("Alimento Premium Gato Adulto 3kg", "Alimentos", 5200.0, "mercaderia", "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=500"),
        ("Pipeta Antiparasitaria Completa", "Salud", 1500.0, "mercaderia", "https://images.unsplash.com/photo-1628009368231-7bb7cfcb0def?w=500"),
        
        # 🏷️ CORREGIDO: Imagen clara de chapitas identificatorias metálicas de mascotas
        ("Chapita de Identificación Grabada", "Identificación", 1200.0, "chapita", "https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcQ7QmWtQou2bLhfBKaJYeJkH4tGdN6t777S--SvxNjw7o0iV7Hibpu3ENccNq2ubPKU5NANgMPqqUia4l8"),
        
        # 🩺 CORREGIDO: Imagen de un médico veterinario atendiendo en consulta
        ("Consulta Veterinaria General", "Servicio Médico", 4000.0, "servicio", "https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcRI9cJJ_HXKRqCDyAdNXGTPD8IaOpmYvFm-Jn8cMf0sxpjQDmRz0sbixQE2EJgkeB9AL4Fa50lxZHFjvos"),
        
        ("Aplicación de Vacuna Quintuple", "Servicio Médico", 3500.0, "servicio", "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=500"),
        ("Sesión de Peluquería Canina SPA", "Estética", 3800.0, "servicio", "https://images.unsplash.com/photo-1516734212186-a967f81ad0d7?w=500")
    ]
    
    cursor.executemany("INSERT INTO productos (nombre, categoria, precio, tipo_formulario, imagen) VALUES (?, ?, ?, ?, ?)", nuevos_productos)
    conn.commit()
    conn.close()

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
        
        # Procesar archivo subido (Foto o Video)
        if 'multimedia_file' in request.files:
            file = request.files['multimedia_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Guarda el archivo en static/uploads/
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filename_guardado = filename

        cursor.execute('''
            INSERT INTO publicaciones (autor, tipo, titulo, contenido, multimedia)
            VALUES (?, ?, ?, ?, ?)
        ''', (autor, tipo, titulo, contenido, filename_guardado))
        conn.commit()
        return redirect(url_for('foro'))
        
    cursor.execute("SELECT * FROM publicaciones ORDER BY id DESC")
    posts = cursor.fetchall()
    conn.close()
    return render_template('foro.html', posts=posts)

if __name__ == '__main__':
    # Asegura que la carpeta de subidas exista en el sistema
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)