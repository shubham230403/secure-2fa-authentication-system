from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import sqlite3
import pyotp
import qrcode
from pathlib import Path
from datetime import timedelta
import os
import re


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# APPLICATION SETUP
# ============================================================

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not configured. Add SECRET_KEY to the .env file."
    )

app.config["SECRET_KEY"] = SECRET_KEY

# Session security
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=15)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Local development uses HTTP.
# Set this to True when deployed behind HTTPS.
app.config["SESSION_COOKIE_SECURE"] = False

# Limit incoming request size
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024


# ============================================================
# CSRF PROTECTION
# ============================================================

csrf = CSRFProtect(app)


# ============================================================
# RATE LIMITING
# ============================================================

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=[
        "200 per day",
        "50 per hour"
    ]
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "users.db"
QR_DIRECTORY = BASE_DIR / "static" / "qr"

QR_DIRECTORY.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def add_security_headers(response):

    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["X-Frame-Options"] = "DENY"

    response.headers["Referrer-Policy"] = (
        "strict-origin-when-cross-origin"
    )

    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=()"
    )

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "font-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    return response


# ============================================================
# INPUT VALIDATION
# ============================================================

def valid_username(username):
    """
    Username:
    - 3 to 30 characters
    - Letters, numbers and underscore only
    """

    return bool(
        re.fullmatch(
            r"[A-Za-z0-9_]{3,30}",
            username
        )
    )


def valid_email(email):
    """
    Basic email validation.
    """

    return bool(
        re.fullmatch(
            r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
            r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$",
            email
        )
    )


def valid_otp(otp):
    """
    OTP must contain exactly 6 digits.
    """

    return bool(
        re.fullmatch(
            r"\d{6}",
            otp
        )
    )


def strong_password(password):
    """
    Password policy:
    - Minimum 12 characters
    - Maximum 128 characters
    - Uppercase
    - Lowercase
    - Number
    - Special character
    - Reject common passwords
    """

    common_passwords = {
        "password",
        "password123",
        "12345678",
        "123456789",
        "qwerty123",
        "admin123",
        "welcome123",
        "letmein123",
        "password@123"
    }

    if len(password) < 12:
        return False

    if len(password) > 128:
        return False

    if password.lower() in common_passwords:
        return False

    if not any(char.isupper() for char in password):
        return False

    if not any(char.islower() for char in password):
        return False

    if not any(char.isdigit() for char in password):
        return False

    if not any(not char.isalnum() for char in password):
        return False

    return True


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("home.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Length validation
        if len(username) > 30:
            return render_template(
                "register.html",
                error="Username must not exceed 30 characters."
            )

        if len(email) > 254:
            return render_template(
                "register.html",
                error="Invalid email address."
            )

        # Username validation
        if not valid_username(username):
            return render_template(
                "register.html",
                error=(
                    "Username must contain only letters, "
                    "numbers and underscores, and be 3-30 characters."
                )
            )

        # Email validation
        if not valid_email(email):
            return render_template(
                "register.html",
                error="Please enter a valid email address."
            )

        # Password validation
        if not strong_password(password):
            return render_template(
                "register.html",
                error=(
                    "Password must be 12-128 characters and contain "
                    "uppercase, lowercase, number and special character."
                )
            )

        password_hash = generate_password_hash(password)

        # Generate TOTP secret
        totp_secret = pyotp.random_base32()

        connection = get_db_connection()

        try:

            cursor = connection.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password_hash,
                    totp_secret,
                    two_factor_enabled
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    username,
                    email,
                    password_hash,
                    totp_secret,
                    0
                )
            )

            connection.commit()

            user_id = cursor.lastrowid

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error="Username or email already exists."
            )

        finally:

            try:
                connection.close()
            except Exception:
                pass

        # Clear previous session data
        session.clear()

        # Store temporary setup state
        session["setup_user_id"] = user_id
        session.permanent = True

        return redirect(url_for("setup_2fa"))

    return render_template("register.html")


# ============================================================
# SETUP 2FA
# ============================================================

@app.route("/setup-2fa", methods=["GET", "POST"])
def setup_2fa():

    user_id = session.get("setup_user_id")

    if not user_id:
        return redirect(url_for("register"))

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT id, username, email, totp_secret
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    if not user:
        session.clear()
        return redirect(url_for("register"))

    # Generate QR code
    issuer = "Secure 2FA Authentication System"

    provisioning_uri = pyotp.TOTP(
        user["totp_secret"]
    ).provisioning_uri(
        name=user["email"],
        issuer_name=issuer
    )

    # Use database ID instead of user-controlled username
    qr_filename = f"user_{user['id']}.png"

    qr_path = QR_DIRECTORY / qr_filename

    if not qr_path.exists():

        qr = qrcode.make(provisioning_uri)

        qr.save(qr_path)

    qr_url = url_for(
        "static",
        filename=f"qr/{qr_filename}"
    )

    if request.method == "POST":

        otp = request.form.get("otp", "").strip()

        if not valid_otp(otp):

            return render_template(
                "setup_2fa.html",
                qr_url=qr_url,
                username=user["username"],
                error="Authentication code must contain exactly 6 digits."
            )

        totp = pyotp.TOTP(user["totp_secret"])

        if not totp.verify(otp):

            return render_template(
                "setup_2fa.html",
                qr_url=qr_url,
                username=user["username"],
                error="Invalid or expired authentication code."
            )

        connection = get_db_connection()

        connection.execute(
            """
            UPDATE users
            SET two_factor_enabled = 1
            WHERE id = ?
            """,
            (user["id"],)
        )

        connection.commit()
        connection.close()

        session.clear()

        return redirect(url_for("login"))

    return render_template(
        "setup_2fa.html",
        qr_url=qr_url,
        username=user["username"]
    )


# ============================================================
# ENABLE 2FA
# ============================================================

@app.route("/enable-2fa", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def enable_2fa():

    user_id = session.get("setup_authenticated_user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT id, username, email, totp_secret
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    issuer = "Secure 2FA Authentication System"

    provisioning_uri = pyotp.TOTP(
        user["totp_secret"]
    ).provisioning_uri(
        name=user["email"],
        issuer_name=issuer
    )

    qr_filename = f"user_{user['id']}.png"

    qr_path = QR_DIRECTORY / qr_filename

    if not qr_path.exists():

        qr = qrcode.make(provisioning_uri)

        qr.save(qr_path)

    qr_url = url_for(
        "static",
        filename=f"qr/{qr_filename}"
    )

    if request.method == "POST":

        otp = request.form.get("otp", "").strip()

        if not valid_otp(otp):

            return render_template(
                "setup_2fa.html",
                qr_url=qr_url,
                username=user["username"],
                error="Authentication code must contain exactly 6 digits."
            )

        totp = pyotp.TOTP(user["totp_secret"])

        if not totp.verify(otp):

            return render_template(
                "setup_2fa.html",
                qr_url=qr_url,
                username=user["username"],
                error="Invalid or expired authentication code."
            )

        connection = get_db_connection()

        connection.execute(
            """
            UPDATE users
            SET two_factor_enabled = 1
            WHERE id = ?
            """,
            (user["id"],)
        )

        connection.commit()
        connection.close()

        session.clear()

        return redirect(url_for("login"))

    return render_template(
        "setup_2fa.html",
        qr_url=qr_url,
        username=user["username"]
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) > 30:

            return render_template(
                "login.html",
                error="Invalid username or password."
            )

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT
                id,
                username,
                email,
                password_hash,
                totp_secret,
                two_factor_enabled
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        connection.close()

        # Generic authentication error
        if not user or not check_password_hash(
            user["password_hash"],
            password
        ):

            return render_template(
                "login.html",
                error="Invalid username or password."
            )

        # Prevent session fixation
        session.clear()
        session.permanent = True

        # 2FA not enabled
        if not user["two_factor_enabled"]:

            session["setup_authenticated_user_id"] = user["id"]

            return redirect(url_for("enable_2fa"))

        # 2FA enabled
        session["pending_2fa_user_id"] = user["id"]

        return redirect(url_for("verify_2fa"))

    return render_template("login.html")


# ============================================================
# VERIFY 2FA
# ============================================================

@app.route("/verify-2fa", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def verify_2fa():

    user_id = session.get("pending_2fa_user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT
            id,
            username,
            email,
            totp_secret,
            two_factor_enabled
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    if not user or not user["two_factor_enabled"]:

        session.clear()

        return redirect(url_for("login"))

    if request.method == "POST":

        otp = request.form.get("otp", "").strip()

        # Server-side OTP validation
        if not valid_otp(otp):

            return render_template(
                "verify_2fa.html",
                error="Authentication code must contain exactly 6 digits."
            )

        totp = pyotp.TOTP(user["totp_secret"])

        if not totp.verify(otp):

            return render_template(
                "verify_2fa.html",
                error="Invalid or expired authentication code."
            )

        # Authentication successful
        session.pop("pending_2fa_user_id", None)

        session["user_id"] = user["id"]
        session["user"] = user["username"]

        session.permanent = True

        return redirect(url_for("dashboard"))

    return render_template("verify_2fa.html")


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    user_id = session.get("user_id")
    username = session.get("user")

    if not user_id or not username:

        session.clear()

        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT id, username, email, two_factor_enabled, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    if not user:

        session.clear()

        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user=user
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )