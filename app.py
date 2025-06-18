from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

DB_FILE = 'datos_sensores.db'

def init_db():
    if not os.path.isfile(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            co2 REAL, velocidad REAL, temp REAL, dB REAL
        )''')
        conn.commit()
        conn.close()

@app.route('/data', methods=['POST'])
def recibir_datos():
    data = request.get_json()
    co2 = data.get('co2')
    velocidad = data.get('velocidad')
    temp = data.get('temp')
    dB = data.get('dB')
    
    # Validar datos
    if None in [co2, velocidad, temp, dB]:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO sensores (co2, velocidad, temp, dB)
        VALUES (?, ?, ?, ?)
    ''', (co2, velocidad, temp, dB))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/ultimos')
def ultimos():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT timestamp, co2, velocidad, temp, dB FROM sensores ORDER BY id DESC LIMIT 20')
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/exportar')
def exportar():
    import io, csv
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM sensores ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'timestamp', 'co2', 'velocidad', 'temp', 'dB'])
    writer.writerows(rows)
    output.seek(0)
    return output.read(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=sensores.csv'
    }

@app.route('/borrar', methods=['POST'])
def borrar():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM sensores')
    conn.commit()
    conn.close()
    return jsonify({"status": "tabla sensores vaciada"})

@app.route('/stats')
def estadisticas():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT 
            COUNT(*) as total,
            AVG(co2) as co2_avg,
            MIN(co2) as co2_min,
            MAX(co2) as co2_max,
            AVG(temp) as temp_avg,
            MIN(temp) as temp_min,
            MAX(temp) as temp_max,
            AVG(dB) as db_avg,
            MIN(dB) as db_min,
            MAX(dB) as db_max
        FROM sensores 
        WHERE timestamp >= datetime('now', '-24 hours')
    ''')
    stats = c.fetchone()
    conn.close()
    
    if stats[0] > 0:  # Si hay datos
        return jsonify({
            "total_lecturas": stats[0],
            "co2": {"avg": round(stats[1], 2), "min": round(stats[2], 2), "max": round(stats[3], 2)},
            "temp": {"avg": round(stats[4], 2), "min": round(stats[5], 2), "max": round(stats[6], 2)},
            "db": {"avg": round(stats[7], 2), "min": round(stats[8], 2), "max": round(stats[9], 2)}
        })
    else:
        return jsonify({"message": "No hay datos en las últimas 24 horas"})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)