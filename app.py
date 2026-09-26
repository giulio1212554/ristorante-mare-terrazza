from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# ---------------------------
# DATABASE INIT
# ---------------------------
def init_db():
    conn = sqlite3.connect("reservations.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            time TEXT,
            people INTEGER,
            age_group TEXT,
            antipasto TEXT,
            table_number INTEGER,
            name TEXT,
            phone TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# HOME
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------------------
# MENU PAGE
# ---------------------------
@app.route("/menu")
def menu():
    return render_template("menu.html")

# ---------------------------
# SEARCH (AREA RISERVATA)
# ---------------------------
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        code = request.form.get("code")
        if code == "x2100gh":
            conn = sqlite3.connect("reservations.db")
            c = conn.cursor()
            c.execute("SELECT * FROM reservations ORDER BY id DESC")
            data = c.fetchall()
            conn.close()
            return render_template("dashboard.html", data=data)
        else:
            return render_template("search.html", error="Codice errato")
    return render_template("search.html")

# ---------------------------
# PRENOTAZIONE STEP 1
# ---------------------------
@app.route("/prenota/step1")
def prenota_step1():
    return render_template("prenota_step1.html")

# ---------------------------
# PRENOTAZIONE STEP 2
# ---------------------------
@app.route("/prenota/step2", methods=["POST"])
def prenota_step2():
    day = request.form.get("day")
    return render_template("prenota_step2.html", day=day)

# ---------------------------
# PRENOTAZIONE STEP 3
# ---------------------------
@app.route("/prenota/step3", methods=["POST"])
def prenota_step3():
    day = request.form.get("day")
    time = request.form.get("time")
    return render_template("prenota_step3.html", day=day, time=time)

# ---------------------------
# PRENOTAZIONE STEP 4 (TAVOLI)
# ---------------------------
@app.route("/prenota/step4", methods=["POST"])
def prenota_step4():
    day = request.form.get("day")
    time = request.form.get("time")
    people = request.form.get("people")
    age_group = request.form.get("age_group")
    antipasto = request.form.get("antipasto")

    conn = sqlite3.connect("reservations.db")
    c = conn.cursor()

    # Tavoli occupati per quel giorno e ora
    c.execute("SELECT table_number FROM reservations WHERE day=? AND time=?", (day, time))
    occupied_tables = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template(
        "prenota_step4.html",
        day=day,
        time=time,
        people=people,
        age_group=age_group,
        antipasto=antipasto,
        occupied_tables=occupied_tables
    )

# ---------------------------
# PRENOTAZIONE STEP 5 (DATI FINALI)
# ---------------------------
@app.route("/prenota/step5", methods=["POST"])
def prenota_step5():
    day = request.form.get("day")
    time = request.form.get("time")
    people = request.form.get("people")
    age_group = request.form.get("age_group")
    antipasto = request.form.get("antipasto")
    table_number = request.form.get("table_number")

    return render_template(
        "prenota_step5.html",
        day=day,
        time=time,
        people=people,
        age_group=age_group,
        antipasto=antipasto,
        table_number=table_number
    )

# ---------------------------
# SALVATAGGIO PRENOTAZIONE
# ---------------------------
@app.route("/prenota/complete", methods=["POST"])
def prenota_complete():
    day = request.form.get("day")
    time = request.form.get("time")
    people = request.form.get("people")
    age_group = request.form.get("age_group")
    antipasto = request.form.get("antipasto")
    table_number = request.form.get("table_number")
    name = request.form.get("name")
    phone = request.form.get("phone")

    conn = sqlite3.connect("reservations.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO reservations (day, time, people, age_group, antipasto, table_number, name, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (day, time, people, age_group, antipasto, table_number, name, phone))

    conn.commit()
    conn.close()

    return render_template("prenotazione_completata.html")

# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
