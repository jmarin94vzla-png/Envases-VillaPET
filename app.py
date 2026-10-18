import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from datetime import datetime

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")

MESES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/buscar_articulo/<nro>", methods=["GET"])
def buscar_articulo(nro):
    if not supabase:
        return jsonify({"exito": False, "error": "Supabase no está configurado"}), 500
    try:
        res = supabase.table("ARTICULOS").select("*").eq("NRO", int(nro)).execute()
        if res.data and len(res.data) > 0:
            articulo = res.data[0]
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

@app.route("/api/guardar_ingreso", methods=["POST"])
def guardar_ingreso():
    if not supabase:
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

        res = supabase.table("INGRESO").insert(nuevo_registro).execute()
        return jsonify({"exito": True, "datos": res.data})
    except Exception as e:
        return jsonify({"exito": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
