from flask import Flask, render_template, request, session, redirect
import sqlite3
import re
import random
import string

app = Flask(__name__)
app.secret_key = "clave_secreta"
# Función para conectar a la base de datos
def conectar_db():
    return sqlite3.connect("database.db")

# Generar captcha
def generar_captcha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

@app.route("/")
def index():
    return render_template("index.html")

# Ruta principal
@app.route("/holamundo", methods=["GET", "POST"])
def hola():
    mensaje = ""
    if request.method == "POST":
        try:
            conexion = conectar_db()
            cursor = conexion.cursor()

            # Ejemplo de consulta
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()

            conexion.close()
            mensaje = f"Conexión exitosa a SQL versión: {version[0]}"

        except Exception as e:
            mensaje = f"Error de conexión: {e}"

    return render_template("holamundo.html", mensaje=mensaje,breadcrumb=["Inicio", "Captcha", "Formulario"])

@app.route("/formulario", methods=["GET", "POST"])
def formulario():
    errores = []
    datos = {}

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar", "")

        datos = {
            "nombre": nombre,
            "correo": correo
        }

        # 🔴 Campos obligatorios
        if not nombre:
            errores.append("Campo vacío")

        # 🔴 Nombre y apellido: solo letras y acentos
        patron_nombre = r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$"
        if nombre and not re.match(patron_nombre, nombre):
            errores.append("Nombre incorrecto escribe uno valido")

        if not correo:
            errores.append("Campo vacío")
        
        # 🔴 Correo
        patron_correo = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if correo and not re.match(patron_correo, correo):
            errores.append("Correo incorrecto")

        # 🔴 Longitud máxima (40 caracteres)
        if len(nombre) > 40 or len(correo) > 40 or len(password) > 40 or len(confirmar) > 40:
            errores.append("Máximo 40 caracteres permitidos")
        
        
        if not password:
            errores.append("Campo vacío")
        # 🔴 Contraseña incorrecta
        patron_password = r"^(?=.*[A-Z])(?=.*\d).{8,}$"
        if password and not re.match(patron_password, password):
            errores.append("Contraseña incorrecta, debe incluir minimo 8 caracteres, una malluscula y un numero")

        if not confirmar:
            errores.append("Campo vacío")
        # 🔴 Confirmación
        if password and confirmar and password != confirmar:
            errores.append("Las contraseñas no coinciden")

        # ✅ Sin errores
        if not errores:
            return render_template("formulario.html", exito=True)

    return render_template(
        "formulario.html",
        errores=errores,
        datos=datos,
        breadcrumb=["Inicio", "Captcha", "Formulario"]
    )

@app.route("/captcha", methods=["GET", "POST"])
def captcha():
    error = ""
    exito = False

    if request.method == "POST":
        captcha_usuario = request.form.get("captcha", "").strip()
        captcha_real = session.get("captcha")

        if not captcha_usuario:
            error = "Campo vacío"
        elif captcha_usuario != captcha_real:
            error = "Captcha incorrecto"
        else:
            exito = True

    # Generar nuevo captcha
    session["captcha"] = generar_captcha()

    return render_template(
        "captcha.html",
        captcha=session["captcha"],
        error=error,
        exito=exito,
        breadcrumb=["Inicio", "Captcha" ]
    )


# ---------------- LISTAR PRODUCTOS ----------------
@app.route("/productos")
def productos():

    pagina = request.args.get("pagina", 1, type=int)
    por_pagina = 5

    conexion = conectar_db()
    cursor = conexion.cursor()

    # Contar total de productos
    cursor.execute("SELECT COUNT(*) FROM productos")
    total_productos = cursor.fetchone()[0]

    total_paginas = (total_productos + por_pagina - 1) // por_pagina

    offset = (pagina - 1) * por_pagina

    cursor.execute(
        "SELECT * FROM productos LIMIT ? OFFSET ?",
        (por_pagina, offset)
    )

    productos = cursor.fetchall()

    conexion.close()

    return render_template(
        "productos.html",
        productos=productos,
        pagina=pagina,
        total_paginas=total_paginas,
        total_productos=total_productos
    )

# ---------------- AGREGAR PRODUCTO ----------------
@app.route("/agregar_producto", methods=["GET","POST"])
def agregar_producto():

    if request.method == "POST":

        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        descripcion = request.form["descripcion"]

        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute("""
        INSERT INTO productos(nombre,precio,stock,descripcion)
        VALUES (?,?,?,?)
        """,(nombre,precio,stock,descripcion))

        conexion.commit()
        conexion.close()

        return redirect("/productos")

    return render_template("agregar_producto.html")

# ---------------- ELIMINAR ----------------
@app.route("/eliminar/<int:id>")
def eliminar(id):

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM productos WHERE id=?",(id,))

    conexion.commit()
    conexion.close()

    return redirect("/productos")

# ---------------- EDITAR ----------------
@app.route("/editar/<int:id>", methods=["GET","POST"])
def editar(id):

    conexion = conectar_db()
    cursor = conexion.cursor()

    if request.method == "POST":

        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        descripcion = request.form["descripcion"]

        cursor.execute("""
        UPDATE productos
        SET nombre=?, precio=?, stock=?, descripcion=?
        WHERE id=?
        """,(nombre,precio,stock,descripcion,id))

        conexion.commit()
        conexion.close()

        return redirect("/productos")

    cursor.execute("SELECT * FROM productos WHERE id=?",(id,))
    producto = cursor.fetchone()

    conexion.close()

    return render_template("editar_producto.html", producto=producto)


if __name__ == "__main__":
    app.run(debug=True)
