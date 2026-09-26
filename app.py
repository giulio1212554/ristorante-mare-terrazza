from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, date
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"

DB_PATH = "reservations.db"
ADMIN_CODE = "x2100gh"  # codice accesso area riservata

TOTAL_TABLES = 20  # numero tavoli totali

# -----------------------------
# DB SETUP
# -----------------------------
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            time TEXT,
            people INTEGER,
            age_group TEXT,
            antipasto TEXT,
            area TEXT,
            water TEXT,
            table_number INTEGER
        )
        """)
        conn.commit()
        conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cleanup_old():
    conn = get_db()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("DELETE FROM reservations WHERE day < ?", (today,))
    conn.commit()
    conn.close()

# -----------------------------
# HOME – FACCIATA
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

# -----------------------------
# PAGINA CERCA (CODICE)
# -----------------------------
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        code = request.form.get('code')
        if code == ADMIN_CODE:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            return "Codice non valido"
    return render_template('search.html')

# -----------------------------
# DASHBOARD
# -----------------------------
@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('search'))

    cleanup_old()

    conn = get_db()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT * FROM reservations WHERE day = ?", (today,))
    rows = c.fetchall()
    conn.close()

    booked_tables = len(rows)
    free_tables = max(TOTAL_TABLES - booked_tables, 0)

    # dati per grafico: prenotazioni per fascia oraria
    time_buckets = {}
    for r in rows:
        t = r["time"][:2]  # ora (HH)
        time_buckets[t] = time_buckets.get(t, 0) + 1

    chart_labels = sorted(time_buckets.keys())
    chart_values = [time_buckets[h] for h in chart_labels]

    # mappa tavoli: lista da 1 a TOTAL_TABLES con stato
    table_map = []
    booked_numbers = {r["table_number"] for r in rows}
    for n in range(1, TOTAL_TABLES + 1):
        table_map.append({
            "number": n,
            "status": "booked" if n in booked_numbers else "free"
        })

    return render_template(
        'dashboard.html',
        reservations=rows,
        total_tables=TOTAL_TABLES,
        booked_tables=booked_tables,
        free_tables=free_tables,
        today=today,
        chart_labels=chart_labels,
        chart_values=chart_values,
        table_map=table_map
    )

# -----------------------------
# PRENOTAZIONE – STEP 1: persone
# -----------------------------
@app.route('/prenota/step1', methods=['GET', 'POST'])
def prenota_step1():
    if request.method == 'POST':
        session['people'] = int(request.form.get('people'))
        return redirect(url_for('prenota_step2'))
    return render_template('prenota_step1.html')

# -----------------------------
# STEP 2: età
# -----------------------------
@app.route('/prenota/step2', methods=['GET', 'POST'])
def prenota_step2():
    if request.method == 'POST':
        age_group = request.form.get('age_group')
        session['age_group'] = age_group
        return redirect(url_for('prenota_step3'))
    return render_template('prenota_step2.html')

# -----------------------------
# STEP 3: antipasto
# -----------------------------
@app.route('/prenota/step3', methods=['GET', 'POST'])
def prenota_step3():
    if request.method == 'POST':
        antipasto = request.form.get('antipasto')
        session['antipasto'] = antipasto
        return redirect(url_for('prenota_step4'))
    return render_template('prenota_step3.html')

# -----------------------------
# STEP 4: data, ora, posizione, tavolo
# -----------------------------
@app.route('/prenota/step4', methods=['GET', 'POST'])
def prenota_step4():
    if request.method == 'POST':
        day = request.form.get('day')
        time = request.form.get('time')
        area = request.form.get('area')
        table_number = int(request.form.get('table_number'))

        session['day'] = day
        session['time'] = time
        session['area'] = area
        session['table_number'] = table_number

        return redirect(url_for('prenota_step5'))
    return render_template('prenota_step4.html', total_tables=TOTAL_TABLES)

# -----------------------------
# STEP 5: acqua
# -----------------------------
@app.route('/prenota/step5', methods=['GET', 'POST'])
def prenota_step5():
    if request.method == 'POST':
        water = request.form.get('water')
        session['water'] = water

        conn = get_db()
        c = conn.cursor()
        c.execute("""
        INSERT INTO reservations (day, time, people, age_group, antipasto, area, water, table_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session['day'],
            session['time'],
            session['people'],
            session['age_group'],
            session['antipasto'],
            session['area'],
            session['water'],
            session['table_number']
        ))
        conn.commit()
        conn.close()

        return render_template('prenotazione_completata.html')
    return render_template('prenota_step5.html')

# -----------------------------
# LOGOUT
# -----------------------------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# -----------------------------
# AVVIO
# -----------------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="127.0.0.1")
