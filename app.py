import os
from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuración de Google Sheets (Conectando con tu Hoja de Cálculo)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def get_sheet_client():
    # Render leerá las credenciales de seguridad desde una variable de entorno
    # o de un archivo credentials.json si lo subes.
    creds_path = 'credentials.json'
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    else:
        # Si configuras las credenciales en Render directamente
        import json
        creds_json = os.environ.get('GOOGLE_CREDS_JSON')
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    
    client = gspread.authorize(creds)
    # Reemplaza con el nombre exacto de tu Google Sheet o su ID
    spreadsheet_id = os.environ.get('SPREADSHEET_ID', 'TU_ID_DE_GOOGLE_SHEET')
    return client.open_by_key(spreadsheet_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        ss = get_sheet_client()
        
        # 1. Leer Base de Datos de Artículos
        sheet_bd = ss.worksheet('Base de Datos')
        data_bd = sheet_bd.get_all_values()
        articulos = []
        
        header_idx = -1
        for idx, row in enumerate(data_bd[:15]):
            row_str = " ".join([str(cell).upper() for cell in row])
            if 'CODIGO' in row_str and 'DESCRIPCION' in row_str:
                header_idx = idx
                break
        
        if header_idx != -1:
            headers = [str(h).strip().upper() for h in data_bd[header_idx]]
            c_nro = headers.index('N°') if 'N°' in headers else -1
            c_cod = headers.index('CODIGO') if 'CODIGO' in headers else -1
            c_desc = headers.index('DESCRIPCION') if 'DESCRIPCION' in headers else -1
            c_alm = headers.index('ALMACEN') if 'ALMACEN' in headers else -1
            c_und = headers.index('UNIDAD') if 'UNIDAD' in headers else -1
            c_arm = headers.index('ARMADO') if 'ARMADO' in headers else -1
            c_mov = headers.index('MOVIMIENTO') if 'MOVIMIENTO' in headers else -1

            for row in data_bd[header_idx + 1:]:
                codigo = str(row[c_cod]).strip() if c_cod != -1 and len(row) > c_cod else ''
                nro = str(row[c_nro]).strip() if c_nro != -1 and len(row) > c_nro else ''
                if codigo or nro:
                    articulos.append({
                        'nro': nro or 'NO',
                        'codigo': codigo,
                        'descripcion': str(row[c_desc]).strip() if c_desc != -1 and len(row) > c_desc else '',
                        'almacen': str(row[c_alm]).strip() if c_alm != -1 and len(row) > c_alm else 'PT',
                        'unidad': str(row[c_und]).strip() if c_und != -1 and len(row) > c_und else 'UND',
                        'armado': float(row[c_arm]) if c_arm != -1 and len(row) > c_arm and row[c_arm] != '' else 0,
                        'movimiento': str(row[c_mov]).strip() if c_mov != -1 and len(row) > c_mov else 'ENT009'
                    })

        # 2. Leer Registros de la hoja "Ingreso"
        sheet_ing = ss.worksheet('Ingreso')
        data_ing = sheet_ing.get_all_values()
        registros = []
        
        if len(data_ing) > 1:
            headers_ing = [str(h).strip().upper() for h in data_ing[0]]
            # Mapeo de columnas de ingreso basado en tu versión original[cite: 10]
            for row in data_ing[1:]:
                if not any(row): continue
                registros.append({
                    'fecha': str(row[1] if len(row) > 1 else ''),
                    'hora': str(row[2] if len(row) > 2 else ''),
                    'nota': str(row[3] if len(row) > 3 else ''),
                    'nro': str(row[4] if len(row) > 4 else ''),
                    'peso': float(row[5]) if len(row) > 5 and row[5] != '' else 0,
                    'cantidad': float(row[6]) if len(row) > 6 and row[6] != '' else 0,
                    'movimiento': str(row[7] if len(row) > 7 else ''),
                    'unidad': str(row[8] if len(row) > 8 else 'UND'),
                    'codigo': str(row[9] if len(row) > 9 else ''),
                    'descripcion': str(row[10] if len(row) > 10 else ''),
                    'almacen': str(row[11] if len(row) > 11 else 'PT'),
                    'turno': 'Día'
                })

        return jsonify({'success': True, 'registros': registros, 'articulos': articulos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/guardar', methods=['POST'])
def guardar_ingreso():
    try:
        payload = request.json
        ss = get_sheet_client()
        sheet = ss.worksheet('Ingreso')
        
        fecha = payload.get('fecha')
        hora = payload.get('hora', '11:00:00 a. m.')
        nota = payload.get('nota')
        items = payload.get('items', [])
        
        mes_nombres = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        from datetime import datetime
        d_obj = datetime.strptime(fecha, '%Y-%m-%d')
        mes = mes_nombres[d_obj.month - 1]
        
        last_row = len(sheet.get_all_values())
        rows_to_add = []
        
        for idx, item in enumerate(items):
            rows_to_add.append([
                fecha,
                fecha,
                hora,
                nota,
                item.get('nro', 'NO'),
                item.get('peso', 0),
                item.get('cantidad', 0),
                item.get('movimiento', 'ENT009'),
                item.get('unidad', 'UND'),
                item.get('codigo', ''),
                item.get('descripcion', ''),
                item.get('almacen', 'PT'),
                mes,
                last_row + idx
            ])
            
        if rows_to_add:
            sheet.append_rows(rows_to_add)
            
        return jsonify({'success': True, 'count': len(rows_to_add), 'nota': nota})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
