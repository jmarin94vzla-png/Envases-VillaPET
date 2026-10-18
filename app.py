import os
from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Cabeceras estándar para la API REST de Supabase
def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

MESES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
}

@app.route("/")
def index():
    return render_template("index.html")

# Endpoint tipo "BUSCARV" consultando directamente la API de Supabase
@app.route("/api/buscar_articulo/<nro>", methods=["GET"])
def buscar_articulo(nro):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"exito": False, "error": "Supabase no está configurado"}), 500
    try:
        url = f"{SUPABASE_URL}/rest/v1/ARTICULOS?NRO=eq.{nro}&select=*"
        response = requests.get(url, headers=get_headers())
        data = response.json()
        
        if data and len(data) > 0:
            articulo = data[0]
            return jsonify({
                "exito": True,
                "codigo": articulo.get("CODIGO", ""),
                "descripcion": articulo.get("DESCRIPCION", ""),
                "almacen": articulo.get("ALMACEN", ""),
                "unidad": articulo.get("UNIDAD", ""),
                "armado": articulo.get("ARMADO", 0),
                "movimiento": articulo.get("MOVIMIENTO", "ENT0009")
            })
        else:
            return jsonify({"exito": False, "mensaje": "Artículo no encontrado"}), 404
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500

# Endpoint para guardar registros de INGRESO directamente en Supabase
@app.route("/api/guardar_ingreso", methods=["POST"])
def guardar_ingreso():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"exito": False, "error": "Supabase no está configurado"}), 500
    
    data = request.json
    try:
        fecha_ent_str = data.get("fecha_ent")
        mes_nombre = ""
        if fecha_ent_str:
            fecha_obj = datetime.strptime(fecha_ent_str, "%Y-%m-%d")
            mes_nombre = MESES.get(fecha_obj.month, "")

        nuevo_registro = {
            "fecha_prod": data.get("fecha_prod"),
            "fecha_ent": fecha_ent_str,
            "hora": data.get("hora"),
            "nota": data.get("nota"),
            "nro": str(data.get("nro")),
            "codigo": data.get("codigo"),
            "descripcion": data.get("descripcion"),
            "almacen": data.get("almacen"),
            "cantidad": float(data.get("cantidad", 0)),
            "peso": float(data.get("peso", 0)),
            "unidad": data.get("unidad"),
            "movimiento": data.get("movimiento"),
            "mes": mes_nombre,
            "secuencia": int(data.get("secuencia", 1)) if data.get("secuencia") else None
        }

        url = f"{SUPABASE_URL}/rest/v1/INGRESO"
        response = requests.post(url, headers=get_headers(), json=nuevo_registro)
        
        if response.status_code in [200, 201]:
            return jsonify({"exito": True, "datos": response.json()})
        else:
            return jsonify({"exito": False, "error": response.text}), 400
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
