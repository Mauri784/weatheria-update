from flask import Flask, jsonify, send_file
from flask_cors import CORS
import os
import json
import threading

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(BASE_DIR, "history")
INDEX_FILE = os.path.join(HISTORY_DIR, "index.json")

# Variable global para almacenar el estado
estado_actual = {
    "files": [],
    "total": 0,
    "ultima_actualizacion": None
}


def get_csv_files():
    """Obtiene los nombres de archivos CSV en la carpeta."""
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)
        return []
    
    return sorted([
        f for f in os.listdir(HISTORY_DIR)
        if f.lower().endswith(".csv")
    ])


def update_index_json():
    """Actualiza el archivo index.json con la lista actual de CSV."""
    from datetime import datetime
    
    files = get_csv_files()
    data = {"files": files}

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Actualizar estado global
    global estado_actual
    estado_actual = {
        "files": files,
        "total": len(files),
        "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    print(f"[{estado_actual['ultima_actualizacion']}] index.json actualizado con {len(files)} archivos.")
    return files


# --- ENDPOINTS DE LA API ---

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'API de Update Index funcionando',
        'total_archivos': estado_actual.get('total', 0),
        'ultima_actualizacion': estado_actual.get('ultima_actualizacion')
    })


@app.route('/actualizar', methods=['GET', 'POST'])
def actualizar_index():
    """Forzar actualización del index.json"""
    try:
        files = update_index_json()
        return jsonify({
            'status': 'success',
            'message': f'Index actualizado con {len(files)} archivos',
            'files': files
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/index', methods=['GET'])
def obtener_index():
    """Obtener el contenido del index.json"""
    try:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({
                'status': 'success',
                'data': data
            })
        else:
            return jsonify({
                'status': 'success',
                'data': {"files": []}
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/archivos', methods=['GET'])
def listar_archivos():
    """Listar todos los archivos CSV disponibles"""
    try:
        files = get_csv_files()
        return jsonify({
            'status': 'success',
            'total': len(files),
            'files': files
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/descargar-index', methods=['GET'])
def descargar_index():
    """Descargar el archivo index.json"""
    try:
        if os.path.exists(INDEX_FILE):
            return send_file(INDEX_FILE, as_attachment=True, download_name='index.json')
        else:
            return jsonify({
                'status': 'error',
                'message': 'Archivo index.json no encontrado'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def inicializar():
    """Generar index.json al iniciar"""
    print("🔄 Inicializando Update Index API...")
    try:
        update_index_json()
        print("✅ Index.json generado correctamente")
    except Exception as e:
        print(f"❌ Error al generar index.json: {e}")


if __name__ == '__main__':
    # Crear directorio y generar index inicial
    threading.Thread(target=inicializar, daemon=True).start()
    
    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5004, debug=False)
