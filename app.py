from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pyotp
import qrcode
from pathlib import Path
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets


app = Flask(__name__)

# =========================================================
# APPLICATION SECURITY CONFIGURATION
# =========================================================

# Generate a random secret key when the application starts.
# For production, store this in an environment variable.
app.secret_key = secrets.token_hex(32)

# Session configuration
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # True when using HTTPS

DATABASE = "database/users.db"

QR_FOLDER = Path("static/qr")
QR_FOLDER.mkdir(parents=True, exist_ok=True)


# =========================================================
# RATE LIMITING
# =========================================================

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    if session.get("user"):
        return redirect(url_for("dashboard"))

    return render_template("home.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        # Basic password policy
        if len(password) < 8:
            return render_template(
                "register.html",
                error="Password must contain at least 8 characters."
            )

        # Hash password
        password_hash = generate_password_hash(password)

        # Generate TOTP secret
        totp_secret = pyotp.random_base32()

        connection = get_db_connection()

        try:

            connection.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password_hash,
                    totp_secret,
                    two_factor_enabled
                )
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    username,
                    email,
                    password_hash,
                    totp_secret
                )
            )

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error="Username or email already exists."
            )

        connection.close()

        # Temporary enrollment session
        session["setup_username"] = username
        session.permanent = True

        return redirect(url_for("setup_2fa"))

    return render_template("register.html")


# =========================================================
# SETUP 2FA AFTER REGISTRATION
# =========================================================

@app.route("/setup-2fa", methods=["GET", "POST"])
def setup_2fa():

    username = session.get("setup_username")

    if not username:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    connection.close()

    if not user:
        session.pop("setup_username", None)
        return redirect(url_for("register"))

    # If already enabled, don't enroll again
    if user["two_factor_enabled"]:
        session.pop("setup_username", None)
        return redirect(url_for("login"))

    secret = user["totp_secret"]

    # Generate authenticator provisioning URI
    totp = pyotp.TOTP(secret)

    otp_uri = totp.provisioning_uri(
        name=user["email"],
        issuer_name="Secure 2FA System"
    )

    # Generate QR code
    qr_path = QR_FOLDER / f"{username}.png"

    img = qrcode.make(otp_uri)
    img.save(qr_path)

    if request.method == "POST":

        otp = request.form["otp"].strip()

        # Verify TOTP
        if totp.verify(otp):

            connection = get_db_connection()

            connection.execute(
                """
                UPDATE users
                SET two_factor_enabled = 1
                WHERE username = ?
                """,
                (username,)
            )

            connection.commit()
            connection.close()

            session.pop("setup_username", None)

            return redirect(url_for("login"))

        return render_template(
            "setup_2fa.html",
            username=username,
            qr_code=f"qr/{username}.png",
            error="Invalid or expired authentication code."
        )

    return render_template(
        "setup_2fa.html",
        username=username,
        qr_code=f"qr/{username}.png"
    )


# =========================================================
# EXISTING USER — START 2FA SETUP
# =========================================================

@app.route("/enable-2fa", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def enable_2fa():

    # Existing user must first authenticate with password
    if "setup_authenticated_user" not in session:
        return redirect(url_for("login"))

    username = session["setup_authenticated_user"]

    connection = get_db_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    connection.close()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    # Already enabled
    if user["two_factor_enabled"]:
        session.pop("setup_authenticated_user", None)
        return redirect(url_for("dashboard"))

    secret = user["totp_secret"]

    # Create TOTP object
    totp = pyotp.TOTP(secret)

    otp_uri = totp.provisioning_uri(
        name=user["email"],
        issuer_name="Secure 2FA System"
    )

    # Generate QR code
    qr_path = QR_FOLDER / f"{username}.png"

    img = qrcode.make(otp_uri)
    img.save(qr_path)

    if request.method == "POST":

        otp = request.form["otp"].strip()

        if totp.verify(otp):

            connection = get_db_connection()

            connection.execute(
                """
                UPDATE users
                SET two_factor_enabled = 1
                WHERE username = ?
                """,
                (username,)
            )

            connection.commit()
            connection.close()

            session.pop("setup_authenticated_user", None)

            return redirect(url_for("login"))

        return render_template(
            "setup_2fa.html",
            username=username,
            qr_code=f"qr/{username}.png",
            error="Invalid or expired authentication code."
        )

    return render_template(
        "setup_2fa.html",
        username=username,
        qr_code=f"qr/{username}.png"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        connection.close()

        # Verify username and password
        if not user or not check_password_hash(
            user["password_hash"],
            password
        ):

            return render_template(
                "login.html",
                error="Invalid username or password."
            )

        session.permanent = True

        # =================================================
        # EXISTING USER WITHOUT 2FA
        # =================================================

        if not user["two_factor_enabled"]:

            session["setup_authenticated_user"] = username

            return redirect(url_for("enable_2fa"))

        # =================================================
        # EXISTING USER WITH 2FA
        # =================================================

        session["pending_2fa_user"] = username

        return redirect(url_for("verify_2fa"))

    return render_template("login.html")


# =========================================================
# VERIFY 2FA DURING LOGIN
# =========================================================

@app.route("/verify-2fa", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def verify_2fa():

    username = session.get("pending_2fa_user")

    if not username:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    connection.close()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":

        otp = request.form["otp"].strip()

        totp = pyotp.TOTP(user["totp_secret"])

        if totp.verify(otp):

            # Remove temporary authentication state
            session.pop("pending_2fa_user", None)

            # Create authenticated session
            session["user"] = username
            session.permanent = True

            return redirect(url_for("dashboard"))

        return render_template(
            "verify_2fa.html",
            error="Invalid or expired authentication code."
        )

    return render_template("verify_2fa.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    username = session.get("user")

    if not username:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=username
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)