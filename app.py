from flask import Flask, render_template, request
import sqlite3
from datetime import datetime
import secrets

app = Flask(__name__)

DB = "/data/data/com.termux/files/home/storage/shared/قرعه کشی/top_film.db"


def init_db():
    conn = sqlite3.connect(DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            father_mobile TEXT,
            age TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            national_id TEXT NOT NULL,
            province TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            referral_code TEXT,
            created_at TEXT NOT NULL
        )
    """)

    try:
        conn.execute("ALTER TABLE registrations ADD COLUMN father_mobile TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE registrations ADD COLUMN age TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    success = False
    error = None
    referral_generated = "TF-" + secrets.token_hex(5).upper()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        father_mobile = request.form.get("father_mobile", "").strip()
        age = request.form.get("age", "").strip()
        birth_date = request.form.get("birth_date", "").strip()
        national_id = request.form.get("national_id", "").strip()
        province = request.form.get("province", "").strip()
        city = request.form.get("city", "").strip()
        address = request.form.get("address", "").strip()
        postal_code = request.form.get("postal_code", "").strip()
        referral_code = request.form.get("referral_code", "").strip()

        required = [
            full_name,
            age,
            mobile,
            birth_date,
            national_id,
            province,
            city,
            address,
            postal_code
        ]

        if not all(required):
            error = "لطفاً تمام فیلدهای الزامی را تکمیل کنید."
        else:
            try:
                conn = sqlite3.connect(DB)

                conn.execute("""
                    INSERT INTO registrations (
                        full_name,
                        mobile,
                        father_mobile,
                        age,
                        birth_date,
                        national_id,
                        province,
                        city,
                        address,
                        postal_code,
                        referral_code,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name,
                    mobile,
                    father_mobile,
                    age,
                    birth_date,
                    national_id,
                    province,
                    city,
                    address,
                    postal_code,
                    referral_code,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                conn.commit()
                conn.close()

                referral_generated = "TOP-" + secrets.token_hex(3).upper()
                success = True

            except Exception as e:
                error = f"خطا در ثبت اطلاعات: {e}"

    return render_template(
        "index.html",
        success=success,
        error=error,
        referral_generated=referral_generated
    )


@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    registrations = conn.execute(
        "SELECT * FROM registrations ORDER BY id ASC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        registrations=registrations
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8081, debug=False)
