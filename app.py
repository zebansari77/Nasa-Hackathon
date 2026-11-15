
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os


# ---------------- FLASK CONFIGURATION ----------------

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY", "orbitalcare_demo_secret_key"
)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "orbitalcare_fresh.db"
)



# ---------------- DATABASE CONNECTION ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- DATABASE INITIALIZATION ----------------

def init_db():

    conn = get_db()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Health records table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            heart_rate REAL,
            oxygen_level REAL,
            temperature REAL,
            blood_pressure TEXT,
            notes TEXT,
            date_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create demo account if it does not exist
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        ("demo@orbitalcare.com",)
    ).fetchone()

    if user is None:
        conn.execute("""
            INSERT INTO users (email, password)
            VALUES (?, ?)
        """, (
            "demo@orbitalcare.com",
            generate_password_hash("orbit123")
        ))

    conn.commit()
    conn.close()


# ---------------- LOGIN REQUIRED DECORATOR ----------------

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ---------------- LOGIN PAGE ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["email"] = user["email"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password!")

    return render_template("login.html")


# ---------------- DASHBOARD PAGE ----------------

@app.route("/dashboard")
@login_required
def dashboard():

    conn = get_db()

    # Get latest health record
    latest = conn.execute("""
        SELECT * FROM health_records
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (session["user_id"],)).fetchone()

    # Count total health records
    total_records = conn.execute("""
        SELECT COUNT(*) AS total
        FROM health_records
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()["total"]

    conn.close()

    # Demonstration alert calculation
    alert_count = 0
    health_score = None

    if latest:

        if latest["heart_rate"] < 60 or latest["heart_rate"] > 100:
            alert_count += 1

        if latest["oxygen_level"] < 95:
            alert_count += 1

        if latest["temperature"] < 36 or latest["temperature"] > 37.5:
            alert_count += 1

        health_score = max(0, 100 - (alert_count * 15))

    return render_template(
        "dashboard.html",
        latest=latest,
        total_records=total_records,
        email=session["email"],
        health_score=health_score,
        alert_count=alert_count
    )


# ---------------- HEALTH MONITORING PAGE ----------------

@app.route("/health", methods=["GET", "POST"])
@login_required
def health():

    if request.method == "POST":

        try:
            heart_rate = float(request.form["heart_rate"])
            oxygen_level = float(request.form["oxygen_level"])
            temperature = float(request.form["temperature"])

            blood_pressure = request.form["blood_pressure"].strip()
            notes = request.form.get("notes", "").strip()

            # Basic input validation
            if not (0 < heart_rate <= 300):
                raise ValueError

            if not (0 < oxygen_level <= 100):
                raise ValueError

            if not (25 <= temperature <= 45):
                raise ValueError

            if not blood_pressure:
                raise ValueError

            date_time = datetime.now().strftime(
                "%d-%m-%Y %I:%M:%S %p"
            )

            conn = get_db()

            conn.execute("""
                INSERT INTO health_records
                (user_id, heart_rate, oxygen_level,
                 temperature, blood_pressure, notes, date_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                heart_rate,
                oxygen_level,
                temperature,
                blood_pressure,
                notes,
                date_time
            ))

            conn.commit()
            conn.close()

            flash("Health information saved successfully!")

            return redirect(url_for("health"))

        except (ValueError, KeyError):
            flash("Please enter valid health information.")

    return render_template("health.html")


# ---------------- HISTORY PAGE ----------------

@app.route("/history")
@login_required
def history():

    conn = get_db()

    records = conn.execute("""
        SELECT * FROM health_records
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():

    session.clear()

    return redirect(url_for("login"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":

    init_db()

    app.run(debug=True)
