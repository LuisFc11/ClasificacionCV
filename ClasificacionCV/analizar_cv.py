from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
import PyPDF2
import json
import os

app = Flask(__name__)
app.secret_key = "supersecreto"

# Carpeta para guardar PDFs
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Archivo JSON para persistir metadatos del historial
HISTORIAL_JSON = "historial.json"

# Cargar historial desde JSON
if os.path.exists(HISTORIAL_JSON):
    with open(HISTORIAL_JSON, "r", encoding="utf-8") as f:
        historial = json.load(f)
else:
    historial = []

def guardar_historial():
    with open(HISTORIAL_JSON, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

def predecir_area(texto):
    puntuaciones = {
        "Desarrollador Web": texto.lower().count("html") + texto.lower().count("css"),
        "Desarrollador Videojuegos": texto.lower().count("unity") + texto.lower().count("juegos"),
        "Desarrollo de app móviles": texto.lower().count("android") + texto.lower().count("flutter")
    }

    total = sum(puntuaciones.values())
    if total == 0:
        return {"Ninguna": 100}
    
    porcentajes = {k: round((v/total)*100, 2) for k, v in puntuaciones.items()}
    return porcentajes

def obtener_historial_completo():
    """
    Combina el historial del JSON con los archivos que hay en la carpeta uploads.
    Si un archivo está en uploads pero no en JSON, se agrega con estado Pendiente.
    """
    archivos_en_carpeta = os.listdir(UPLOAD_FOLDER)
    archivos_pdf = [f for f in archivos_en_carpeta if f.lower().endswith('.pdf')]

    # Mapear nombres guardados en historial
    nombres_historial = {h['nombre'] for h in historial}

    # Agregar archivos no listados en JSON con estado "Pendiente"
    nuevos = []
    for archivo in archivos_pdf:
        if archivo not in nombres_historial:
            nuevos.append({
                "nombre": archivo,
                "area": "Pendiente",
                "estado": "Pendiente"
            })

    return historial + nuevos

@app.route('/', methods=['GET', 'POST'])
def analizar_cv():
    resultados = None
    mensaje = ""
    area = None

    if request.method == 'POST':
        file = request.files['cv_pdf']
        if file and file.filename.endswith('.pdf'):
            filename = file.filename

            # Guardar archivo en carpeta uploads
            ruta_guardado = os.path.join(UPLOAD_FOLDER, filename)
            file.save(ruta_guardado)

            texto = ""
            try:
                pdf_reader = PyPDF2.PdfReader(ruta_guardado)
                for page in pdf_reader.pages:
                    texto += page.extract_text() or ""
            except Exception as e:
                flash("Error leyendo el PDF.")
                return redirect(url_for('analizar_cv'))

            resultados = predecir_area(texto)
            area = max(resultados, key=resultados.get)

            if area == "Ninguna" or resultados[area] < 30:
                mensaje = "El candidato no está apto para ninguna de las áreas."
                area = None
            else:
                mensaje = f"Área seleccionada: {area} con {resultados[area]}%"
                # Guardar o actualizar el historial JSON
                existe = False
                for h in historial:
                    if h['nombre'] == filename:
                        h['area'] = area
                        h['estado'] = "Aprobado"
                        existe = True
                        break
                if not existe:
                    historial.append({
                        "nombre": filename,
                        "area": area,
                        "estado": "Aprobado"
                    })
                guardar_historial()

    historial_completo = obtener_historial_completo()

    return render_template("index.html", resultados=resultados, mensaje=mensaje, area=area, historial=historial_completo)

@app.route('/editar/<nombre>', methods=['GET', 'POST'])
def editar_historial(nombre):
    flash(f'Función de editar para "{nombre}" no implementada aún.')
    return redirect(url_for('analizar_cv'))

@app.route('/eliminar/<nombre>', methods=['GET'])
def eliminar_historial(nombre):
    global historial
    # Quitar del JSON
    nuevo_historial = [h for h in historial if h['nombre'] != nombre]

    # Si se borró algo, actualizar JSON
    if len(nuevo_historial) < len(historial):
        historial = nuevo_historial
        guardar_historial()

    # Borrar archivo físico si existe
    ruta_archivo = os.path.join(UPLOAD_FOLDER, nombre)
    if os.path.exists(ruta_archivo):
        os.remove(ruta_archivo)
        flash(f'Registro y archivo "{nombre}" eliminados correctamente.')
    else:
        flash(f'Archivo "{nombre}" no encontrado en carpeta.')

    return redirect(url_for('analizar_cv'))

@app.route('/uploads/<filename>')
def descargar_archivo(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
