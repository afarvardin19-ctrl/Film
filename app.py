from flask import Flask, render_template, render_template_string, request
import sqlite3
import os
import secrets
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
DB = os.path.join(os.path.dirname(__file__), "top_film.db")


def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect(DB)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id SERIAL PRIMARY KEY,
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
    else:
        cursor.execute("""
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

    conn.commit()

    try:
        if DATABASE_URL:
            cursor.execute("""
                ALTER TABLE registrations
                ADD COLUMN IF NOT EXISTS father_mobile TEXT
            """)
        else:
            columns = [row[1] for row in cursor.execute(
                "PRAGMA table_info(registrations)"
            ).fetchall()]

            if "father_mobile" not in columns:
                cursor.execute("""
                    ALTER TABLE registrations
                    ADD COLUMN father_mobile TEXT
                """)

        conn.commit()

    except Exception as e:
        print("DB migration:", e)

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
        age = ""
        birth_date = ""
        national_id = request.form.get("national_id", "").strip()
        province = request.form.get("province", "").strip()
        city = request.form.get("city", "").strip()
        address = request.form.get("address", "").strip()
        postal_code = request.form.get("postal_code", "").strip()
        referral_code = request.form.get("referral_code", "").strip()

        required = [
            full_name,
            mobile,
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
                conn = get_connection()

                created_at = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                if DATABASE_URL:
                    cursor = conn.cursor()

                    cursor.execute("""
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
                        VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s
                        )
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
                        created_at
                    ))

                    cursor.close()

                else:
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
                        created_at
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



@app.route("/db-viewer")
def db_viewer():
    conn = get_connection()

    try:
        if DATABASE_URL:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM registrations ORDER BY id DESC")
            rows = cursor.fetchall()
            cursor.close()
            database_type = "PostgreSQL / Render"
        else:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM registrations ORDER BY id DESC"
            ).fetchall()
            database_type = "SQLite / Local"

        columns = list(rows[0].keys()) if rows else []

        html = """
        <!doctype html>
        <html lang="fa" dir="rtl">
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>مرورگر دیتابیس TOP FILM</title>
        <style>
        body{
            background:#10131a;
            color:#fff;
            font-family:Tahoma,Arial,sans-serif;
            margin:20px;
        }
        h1{text-align:center}
        .info{
            background:#181d27;
            padding:15px;
            border-radius:12px;
            margin-bottom:20px;
        }
        .table-wrap{overflow-x:auto}
        table{
            width:100%;
            border-collapse:collapse;
            background:#181d27;
        }
        th,td{
            padding:10px;
            border:1px solid #333;
            text-align:right;
            white-space:nowrap;
        }
        th{background:#252c3b}
        .count{
            font-size:18px;
            font-weight:bold;
        }
        </style>
        </head>
        <body>
        <h1>🎬 مرورگر دیتابیس TOP FILM</h1>

        <div class="info">
            <div>دیتابیس فعال: <strong>{{ database_type }}</strong></div>
            <div>تعداد رکوردها: <span class="count">{{ rows|length }}</span></div>
        </div>

        <div class="table-wrap">
        <table>
        {% if columns %}
        <tr>
        {% for col in columns %}
            <th>{{ col }}</th>
        {% endfor %}
        </tr>

        {% for row in rows %}
        <tr>
        {% for col in columns %}
            <td>{{ row[col] }}</td>
        {% endfor %}
        </tr>
        {% endfor %}

        {% else %}
        <tr><td>هیچ رکوردی وجود ندارد.</td></tr>
        {% endif %}
        </table>
        </div>

        </body>
        </html>
        """

        return render_template_string(
            html,
            rows=rows,
            columns=columns,
            database_type=database_type
        )

    finally:
        conn.close()

@app.route("/admin")
def admin():
    conn = get_connection()
    try:
        if DATABASE_URL:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT *
                FROM registrations
                ORDER BY id ASC
            """)
            registrations = cursor.fetchall()
            cursor.close()
        else:
            conn.row_factory = sqlite3.Row
            registrations = conn.execute("""
                SELECT *
                FROM registrations
                ORDER BY id ASC
            """).fetchall()
    finally:
        conn.close()

    return render_template(
        "admin.html",
        registrations=registrations
    )


@app.route("/admin/delete/<int:registration_id>", methods=["POST"])
def delete_registration(registration_id):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM registrations WHERE id = %s"
            if DATABASE_URL
            else "DELETE FROM registrations WHERE id = ?",
            (registration_id,)
        )

        if cursor.rowcount == 0:
            conn.rollback()
            return "رکورد پیدا نشد", 404

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return redirect("/admin")


init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
