from flask import Flask, request, jsonify, render_template
import sqlite3
import os

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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO sensores (co2, velocidad, temp, dB)
        VALUES (?, ?, ?, ?)
    ''', (co2, velocidad, temp, dB))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/ultimos')
def ultimos():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT timestamp, co2, velocidad, temp, dB FROM sensores ORDER BY id DESC LIMIT 20')
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

@app.route('/exportar')
def exportar():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM sensores ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    # Exportar como CSV para Excel
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'timestamp', 'co2', 'velocidad', 'temp', 'dB'])
    writer.writerows(rows)
    output.seek(0)
    return output.read(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=sensores.csv'
    }
