import io
import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, jsonify, url_for, g, abort, session, redirect, send_file
from werkzeug.security import generate_password_hash, check_password_hash

from pdf_report import generate_report_pdf

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "history.db"
DRL_LIMITS = {"PA": 0.30, "AP": 0.40}

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static")
app.config.from_mapping(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me")
)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def close_connection(exception=None):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            patient_name TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            xray_type TEXT NOT NULL,
            kvp REAL NOT NULL,
            mas REAL NOT NULL,
            fsd REAL NOT NULL,
            machine_output REAL NOT NULL,
            bsf REAL NOT NULL,
            esd_mgy REAL NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    # Ensure calculations table has a user_id column for per-user history
    info = db.execute("PRAGMA table_info(calculations)").fetchall()
    col_names = [r[1] if isinstance(r, tuple) else r["name"] for r in info]
    if "user_id" not in col_names:
        try:
            db.execute("ALTER TABLE calculations ADD COLUMN user_id INTEGER")
        except Exception:
            # If ALTER fails, ignore and continue; history will remain global
            pass
    db.commit()


@app.before_request
def ensure_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    init_db()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute(
            "SELECT id, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


@app.context_processor
def inject_user():
    return {"user": g.user}


@app.teardown_appcontext
def teardown_appcontext(exception=None):
    close_connection(exception)


@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not email or not password or not confirm:
            return render_template("register.html", error="All fields are required.")
        if password != confirm:
            return render_template("register.html", error="Passwords do not match.")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing is not None:
            return render_template("register.html", error="Email is already registered.")

        password_hash = generate_password_hash(password)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, password_hash, created_at),
        )
        db.commit()
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="Email and password are required.")

        row = get_db().execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
        if row is None or not check_password_hash(row["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session.clear()
        session["user_id"] = row["id"]
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    if request.method == "POST" or request.headers.get("Accept") == "application/json":
        return jsonify({"logged_in": False})
    return redirect(url_for("home"))


@app.route("/auth_status")
def auth_status():
    return jsonify({
        "logged_in": g.user is not None,
        "email": g.user["email"] if g.user is not None else None,
    })


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/calculator")
@login_required
def calculator():
    return render_template("calculator.html")


@app.route("/history")
@login_required
def history():
    return render_template("history.html")


@app.route("/history_data")
@login_required
def history_data():
    db = get_db()
    user_id = g.user["id"] if g.user is not None else None
    if user_id is None:
        return jsonify([])
    rows = db.execute(
        "SELECT id, created_at, patient_name, patient_id, xray_type, esd_mgy, status FROM calculations WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/results")
@login_required
def results():
    record_id = request.args.get("id", type=int)
    if record_id is None:
        abort(400, description="Missing record id.")

    db = get_db()
    user_id = g.user["id"] if g.user is not None else None
    if user_id is None:
        abort(403, description="Not authorized.")

    row = db.execute(
        "SELECT * FROM calculations WHERE id = ? AND user_id = ?",
        (record_id, user_id),
    ).fetchone()

    if row is None:
        abort(404, description="Record not found.")

    drl_limit = DRL_LIMITS.get(row["xray_type"], 0.40)
    status = row["status"]
    badge_class = "success" if status == "PASS" else "warning"

    return render_template(
        "results.html",
        record_id=row["id"],
        created_at=row["created_at"],
        patient_name=row["patient_name"],
        patient_id=row["patient_id"],
        age=row["age"],
        sex=row["sex"],
        xray_type=row["xray_type"],
        kvp=row["kvp"],
        mas=row["mas"],
        fsd=row["fsd"],
        machine_output=row["machine_output"],
        bsf=row["bsf"],
        esd_mgy=row["esd_mgy"],
        drl_limit=drl_limit,
        status=status,
        badge_class=badge_class,
    )


@app.route("/report.pdf")
@login_required
def report_pdf():
    record_id = request.args.get("id", type=int)
    if record_id is None:
        abort(400, description="Missing record id.")

    db = get_db()
    user_id = g.user["id"] if g.user is not None else None
    if user_id is None:
        abort(403, description="Not authorized.")

    row = db.execute(
        "SELECT * FROM calculations WHERE id = ? AND user_id = ?",
        (record_id, user_id),
    ).fetchone()

    if row is None:
        abort(404, description="Record not found.")

    record = {
        "record_id": row["id"],
        "created_at": row["created_at"],
        "patient_name": row["patient_name"],
        "patient_id": row["patient_id"],
        "age": row["age"],
        "sex": row["sex"],
        "xray_type": row["xray_type"],
        "kvp": row["kvp"],
        "mas": row["mas"],
        "fsd": row["fsd"],
        "machine_output": row["machine_output"],
        "bsf": row["bsf"],
        "esd_mgy": row["esd_mgy"],
        "drl_limit": DRL_LIMITS.get(row["xray_type"], 0.40),
        "status": row["status"],
    }
    pdf_bytes = generate_report_pdf(record)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"chest_xray_report_{record_id}.pdf",
    )


@app.route("/calculate", methods=["POST"])
@login_required
def calculate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid request payload."}), 400

    required_fields = [
        "patient_name",
        "patient_id",
        "age",
        "sex",
        "xray_type",
        "kvp",
        "mas",
        "fsd",
        "machine_output",
        "bsf",
    ]

    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        age = int(data["age"])
        kvp = float(data["kvp"])
        mas = float(data["mas"])
        fsd = float(data["fsd"])
        machine_output = float(data["machine_output"])
        bsf = float(data["bsf"])
    except (ValueError, TypeError):
        return jsonify({"error": "Numeric fields must contain valid numbers."}), 400

    if fsd <= 0:
        return jsonify({"error": "FSD must be larger than zero."}), 400

    esd_mgy = machine_output * mas * (100.0 / fsd) ** 2 * bsf
    esd_mgy = round(esd_mgy, 4)

    drl_limit = DRL_LIMITS.get(data["xray_type"], 0.40)
    status = "PASS" if esd_mgy <= drl_limit else "EXCEEDS"

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db = get_db()
    user_id = g.user["id"] if g.user is not None else None
    cursor = db.execute(
        "INSERT INTO calculations (created_at, patient_name, patient_id, age, sex, xray_type, kvp, mas, fsd, machine_output, bsf, esd_mgy, status, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            created_at,
            data["patient_name"].strip(),
            data["patient_id"].strip(),
            age,
            data["sex"].strip(),
            data["xray_type"].strip(),
            kvp,
            mas,
            fsd,
            machine_output,
            bsf,
            esd_mgy,
            status,
            user_id,
        ),
    )
    db.commit()
    record_id = cursor.lastrowid

    return jsonify({"redirect": url_for("results", id=record_id)})


if __name__ == "__main__":
    app.run(debug=True)
