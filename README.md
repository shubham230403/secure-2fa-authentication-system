\# 🔐 Secure 2FA Authentication System



A security-focused web authentication system built with Python Flask that combines password authentication with Time-Based One-Time Password (TOTP) two-factor authentication.



This project was developed with a security-first approach and validated through structured Vulnerability Assessment and Penetration Testing (VAPT) covering authentication, authorization, session management, input validation, CSRF, SQL injection, rate limiting, and security headers.



\---



\## 📌 Project Overview



Traditional username/password authentication can be compromised through credential theft, password reuse, phishing, or brute-force attacks.



This project adds a second authentication factor using TOTP-based 2FA.



\### Authentication Flow



```text

Username + Password

&#x20;       ↓

Password Verification

&#x20;       ↓

TOTP Verification

&#x20;       ↓

Authenticated Session

&#x20;       ↓

Dashboard

```



\---



\## 🎯 Objectives



\* Implement secure user registration and authentication

\* Protect passwords using secure password hashing

\* Implement TOTP-based two-factor authentication

\* Generate QR codes for authenticator enrollment

\* Protect state-changing requests using CSRF tokens

\* Prevent SQL injection through parameterized queries

\* Implement rate limiting against repeated authentication attempts

\* Validate user-controlled input

\* Secure Flask sessions and cookies

\* Implement security response headers

\* Prevent unauthorized dashboard access

\* Perform VAPT testing against common attack scenarios



\---



\## ✨ Features



\### Authentication



\* User registration

\* Username and email validation

\* Strong password policy

\* Secure password hashing

\* Username/password login

\* Generic authentication error messages

\* Session-based authentication



\### Two-Factor Authentication



\* TOTP-based 2FA

\* QR-code enrollment

\* Authenticator application compatibility

\* Six-digit OTP validation

\* OTP expiration handling

\* OTP brute-force rate limiting



\### Session Security



\* 15-minute session lifetime

\* HttpOnly session cookies

\* SameSite=Lax cookies

\* Session clearing during authentication transitions

\* Session fixation protection

\* Protected dashboard routes

\* POST-based logout

\* CSRF-protected logout



\### Web Security



\* CSRF protection

\* SQL injection prevention

\* Input validation

\* Rate limiting

\* Content Security Policy

\* Clickjacking protection

\* MIME-sniffing protection

\* Referrer Policy

\* Permissions Policy

\* Debug mode disabled



\---



\## 🏗️ Technology Stack



| Technology    | Purpose                   |

| ------------- | ------------------------- |

| Python        | Application development   |

| Flask         | Web framework             |

| SQLite        | Database                  |

| PyOTP         | TOTP-based 2FA            |

| QRCode        | QR-code generation        |

| Flask-WTF     | CSRF protection           |

| Flask-Limiter | Rate limiting             |

| Werkzeug      | Password hashing          |

| python-dotenv | Environment configuration |

| HTML/CSS      | Frontend                  |



\---



\## 📂 Project Structure



```text

Secure-2FA/

│

├── app.py

├── init\_db.py

├── requirements.txt

├── .gitignore

├── README.md

│

├── database/

│   └── users.db

│

├── templates/

│   ├── home.html

│   ├── login.html

│   ├── register.html

│   ├── setup\_2fa.html

│   ├── verify\_2fa.html

│   └── dashboard.html

│

└── static/

&#x20;   └── qr/

```



\---



\## 🔄 Authentication Flow



\### 1. User Registration



The user provides:



\* Username

\* Email

\* Password



The application validates the supplied information before creating the account.



Passwords are never stored as plaintext.



```text

Password

&#x20;  ↓

Werkzeug Password Hashing

&#x20;  ↓

Password Hash

&#x20;  ↓

SQLite Database

```



\### 2. TOTP Enrollment



After registration, the application generates a unique TOTP secret.



A QR code is generated from the TOTP provisioning URI.



The user scans the QR code using an authenticator application.



```text

TOTP Secret

&#x20;    ↓

Provisioning URI

&#x20;    ↓

QR Code

&#x20;    ↓

Authenticator App

```



\### 3. 2FA Verification



During login:



```text

Username

&#x20;  +

Password

&#x20;  ↓

Password Verification

&#x20;  ↓

TOTP Code

&#x20;  ↓

TOTP Verification

&#x20;  ↓

Authenticated Session

```



Only after successful TOTP verification is the authenticated session created.



\---



\## 🗄️ Database Design



The application uses SQLite.



\### Users Table



| Column               | Description                |

| -------------------- | -------------------------- |

| `id`                 | Unique user identifier     |

| `username`           | Unique username            |

| `email`              | Unique email address       |

| `password\_hash`      | Secure password hash       |

| `totp\_secret`        | TOTP secret                |

| `two\_factor\_enabled` | 2FA status                 |

| `created\_at`         | Account creation timestamp |



SQL queries use parameterized statements to prevent SQL injection.



\---



\# 🛡️ Security Controls



\## Password Security



The application enforces:



\* Minimum 12 characters

\* Maximum 128 characters

\* Uppercase character

\* Lowercase character

\* Numeric character

\* Special character

\* Rejection of common passwords



Passwords are stored using Werkzeug password hashing.



\---



\## CSRF Protection



Flask-WTF CSRF protection is enabled.



POST forms contain CSRF tokens, and requests with missing or invalid tokens are rejected.



\---



\## SQL Injection Protection



Database operations use parameterized SQL queries.



User input is passed separately from the SQL statement rather than being concatenated into queries.



\---



\## Rate Limiting



Authentication endpoints are rate limited.



```text

/login       → 10 requests per minute

/verify-2fa  → 10 requests per minute

/register    → 5 requests per minute

/enable-2fa  → 10 requests per minute

```



This reduces the effectiveness of repeated password and OTP guessing attempts.



\---



\## Session Security



The application uses:



\* HttpOnly cookies

\* SameSite=Lax

\* 15-minute session lifetime

\* Session clearing during authentication transitions

\* Session fixation protection

\* Protected authenticated routes



\---



\## Security Headers



The application implements:



\* X-Content-Type-Options

\* X-Frame-Options

\* Referrer-Policy

\* Permissions-Policy

\* Content-Security-Policy



These controls help reduce risks such as clickjacking, MIME sniffing, and unauthorized browser-side behavior.



\---



\# 🔎 VAPT Testing



A structured security validation was performed against the application.



|  # | Security Test              | Result |

| -: | -------------------------- | :----: |

|  1 | Wrong password             | ✅ PASS |

|  2 | Wrong username             | ✅ PASS |

|  3 | Invalid OTP                | ✅ PASS |

|  4 | Expired OTP                | ✅ PASS |

|  5 | Direct dashboard access    | ✅ PASS |

|  6 | SQL Injection              | ✅ PASS |

|  7 | CSRF protection            | ✅ PASS |

|  8 | Logout/session protection  | ✅ PASS |

|  9 | Login rate limiting        | ✅ PASS |

| 10 | Weak password rejection    | ✅ PASS |

| 11 | Strong password acceptance | ✅ PASS |

| 12 | Malicious username input   | ✅ PASS |

| 13 | OTP format validation      | ✅ PASS |

| 14 | Security headers           | ✅ PASS |

| 15 | Debug information exposure | ✅ PASS |

| 16 | Cookie security            | ✅ PASS |

| 17 | 2FA bypass                 | ✅ PASS |

| 18 | Session fixation           | ✅ PASS |

| 19 | Open redirect              | ✅ PASS |

| 20 | OTP brute-force protection | ✅ PASS |



\### Testing Tools



\* Browser-based testing

\* PowerShell

\* curl

\* Python

\* SQLite

\* Manual VAPT techniques



> These are project-level security validation tests and do not represent a certification or guarantee of production security.



\---



\## 🧪 Example Security Tests



\### SQL Injection



Test input:



```text

' OR '1'='1

```



Expected behavior:



```text

Invalid username or password.

```



The application does not authenticate the attacker.



\---



\### CSRF



Removing the CSRF token from a POST request results in a rejected request.



Expected behavior:



```text

CSRF TOKEN MISSING

```



\---



\### OTP Brute Force



Repeated invalid OTP submissions eventually result in:



```text

429 Too Many Requests

```



\---



\### 2FA Bypass



Attempting to access:



```text

/dashboard

```



before completing OTP authentication redirects the user to the login flow.



\---



\## ⚙️ Installation



\### 1. Clone the Repository



```bash

git clone https://github.com/shubham230403/secure-2fa-authentication-system.git

cd secure-2fa-authentication-system

```



\### 2. Create a Virtual Environment



Windows:



```powershell

python -m venv venv

```



Activate:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



\### 3. Install Dependencies



```powershell

pip install -r requirements.txt

```



\### 4. Configure Environment Variables



Create a `.env` file in the project root:



```text

SECRET\_KEY=your-long-random-secret-key

```



Do not commit `.env` to GitHub.



\### 5. Initialize the Database



```powershell

python init\_db.py

```



\### 6. Start the Application



```powershell

python app.py

```



Open:



```text

http://127.0.0.1:5000

```



\---



\# 🔐 Production Security Notes



The project currently uses:



```python

SESSION\_COOKIE\_SECURE = False

```



because local development uses HTTP.



For HTTPS production deployment:



```python

SESSION\_COOKIE\_SECURE = True

```



A production deployment should also use:



\* HTTPS

\* Production WSGI server

\* Persistent rate-limit storage

\* Secure secret management

\* Database protection and backups

\* Centralized logging

\* Monitoring and alerting



\---



\# ⚠️ Security Limitations



This is a security-focused educational and portfolio application, not a production-ready authentication service.



Current limitations include:



\* Flask development server is used for local testing

\* Rate limiting uses in-memory storage

\* No account lockout mechanism

\* No email verification

\* No password reset workflow

\* No centralized audit logging

\* QR files are stored locally

\* Secure cookie flag is disabled for local HTTP



\---



\# 🚀 Future Improvements



\* Redis-backed distributed rate limiting

\* Account-level OTP attempt controls

\* Temporary account lockout

\* Password reset with secure tokens

\* Email verification

\* Audit logging

\* Login anomaly detection

\* Device/session management

\* Backup/recovery codes

\* HTTPS deployment

\* Reverse proxy configuration

\* Automated security testing

\* SAST/DAST integration

\* CI/CD security pipeline

\* Dependency vulnerability scanning



\---



\# 📚 Security Concepts Demonstrated



\* Authentication

\* Authorization

\* Multi-factor authentication

\* TOTP

\* Password hashing

\* Session management

\* Session fixation

\* CSRF

\* SQL injection

\* Input validation

\* Rate limiting

\* Brute-force protection

\* Clickjacking protection

\* Content Security Policy

\* Security headers

\* Secure cookie attributes

\* VAPT methodology

\* OWASP web security concepts



\---



\# 🎓 OWASP Security Mapping



| Security Control          | OWASP-Relevant Area             |

| ------------------------- | ------------------------------- |

| Password hashing          | Authentication failures         |

| TOTP 2FA                  | Authentication failures         |

| Rate limiting             | Authentication failures         |

| SQL parameterization      | Injection                       |

| CSRF protection           | Request integrity               |

| Input validation          | Injection / validation          |

| Session controls          | Identification \& authentication |

| HttpOnly/SameSite cookies | Session management              |

| Authorization checks      | Broken access control           |

| Security headers          | Security misconfiguration       |

| Debug disabled            | Security misconfiguration       |



\---



\# 📸 Screenshots



Recommended screenshots for the GitHub repository:



1\. Registration page

2\. QR-code 2FA enrollment

3\. OTP verification page

4\. Login page

5\. Authenticated dashboard

6\. Security-header response

7\. VAPT testing evidence



\### Never upload screenshots containing:



\* `.env` secrets

\* TOTP secrets

\* Active OTP codes

\* Session cookies

\* Real passwords

\* API keys

\* Personal credentials



\---



\# 👨‍💻 Author



\*\*Shubham Bora\*\*



B.Tech — Computer Science \& Engineering (Cyber Security)



\### Cybersecurity Interests



\* Vulnerability Assessment \& Penetration Testing

\* Application Security

\* Governance, Risk \& Compliance

\* Security Operations

\* Secure Software Development



\---



\# 📄 License



This project is intended for educational, cybersecurity learning, portfolio, and authorized security-testing purposes.



\---



\## ⭐ Project Highlights



```text

Python + Flask

&#x20;       +

SQLite

&#x20;       +

Secure Password Hashing

&#x20;       +

TOTP 2FA

&#x20;       +

CSRF Protection

&#x20;       +

Rate Limiting

&#x20;       +

Session Security

&#x20;       +

Security Headers

&#x20;       +

VAPT Testing

```



\*\*Built with a security-first approach.\*\*



