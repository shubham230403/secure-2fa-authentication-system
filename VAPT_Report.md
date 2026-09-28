# 🔎 Vulnerability Assessment & Penetration Testing Report

## Secure 2FA Authentication System

**Project:** Secure 2FA Authentication System
**Assessment Type:** Project-Level Vulnerability Assessment & Security Validation
**Application:** Flask Web Application
**Testing Environment:** Local Windows 11 Environment
**Assessment Status:** Completed
**Author:** Shubham Bora

---

# 1. Executive Summary

The Secure 2FA Authentication System is a Flask-based web application designed to provide password authentication combined with Time-Based One-Time Password (TOTP) two-factor authentication.

A structured security validation was performed against the application to identify and verify common web application security weaknesses.

The assessment covered:

* Authentication
* Authorization
* Two-factor authentication
* Session management
* Session fixation
* CSRF
* SQL injection
* Input validation
* Password policy
* Brute-force protection
* Rate limiting
* Security headers
* Cookie security
* Open redirect behavior
* Debug information exposure

A total of **20 security validation scenarios** were tested.

The implemented controls passed the tested scenarios after remediation of identified issues involving weak password acceptance and unsafe user-controlled filename handling.

> This report represents project-level security validation and is not a certification, formal penetration-testing attestation, or guarantee of production security.

---

# 2. Assessment Objectives

The primary objectives were to:

1. Verify the security of the authentication mechanism.
2. Validate TOTP-based 2FA implementation.
3. Test whether authentication controls can be bypassed.
4. Identify weaknesses in session management.
5. Test protection against common web attacks.
6. Validate input-handling controls.
7. Verify rate limiting and brute-force protections.
8. Review security response headers.
9. Validate secure cookie configuration.
10. Document security issues and remediation.

---

# 3. Scope

## In Scope

The assessment covered the following application components:

```text
Registration
Login
2FA Enrollment
2FA Verification
Dashboard
Logout
Session Management
SQLite Database
HTTP Responses
Application Input Handling
```

## Out of Scope

The following were not assessed:

* Operating system penetration testing
* Network infrastructure penetration testing
* Third-party authenticator applications
* Physical security
* Social engineering
* Cloud infrastructure
* Production deployment infrastructure
* Denial-of-service testing
* Source-code dependency supply-chain audit

---

# 4. Application Architecture

The application follows a simple Flask-based architecture.

```text
                    ┌──────────────────┐
                    │      Browser     │
                    └────────┬─────────┘
                             │
                             │ HTTP
                             ▼
                    ┌──────────────────┐
                    │   Flask App      │
                    │                  │
                    │ Authentication   │
                    │ CSRF Protection  │
                    │ Rate Limiting    │
                    │ Session Control  │
                    └────────┬─────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
        ┌─────────────────┐     ┌─────────────────┐
        │     SQLite      │     │      PyOTP      │
        │    Database     │     │   TOTP Engine   │
        └─────────────────┘     └─────────────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │ Authenticator   │
                                │      App        │
                                └─────────────────┘
```

---

# 5. Technology Stack

| Component            | Technology                                |
| -------------------- | ----------------------------------------- |
| Programming Language | Python                                    |
| Web Framework        | Flask                                     |
| Database             | SQLite                                    |
| Authentication       | Username + Password                       |
| 2FA                  | TOTP                                      |
| TOTP Library         | PyOTP                                     |
| QR Generation        | QRCode                                    |
| Password Hashing     | Werkzeug                                  |
| CSRF Protection      | Flask-WTF                                 |
| Rate Limiting        | Flask-Limiter                             |
| Configuration        | python-dotenv                             |
| Testing              | Browser, PowerShell, curl, Python, SQLite |

---

# 6. Security Methodology

Testing followed a manual security validation approach.

The general process was:

```text
Reconnaissance
      ↓
Application Understanding
      ↓
Threat Identification
      ↓
Security Testing
      ↓
Issue Identification
      ↓
Remediation
      ↓
Retesting
      ↓
Documentation
```

Testing focused on realistic attacks against the authentication and authorization workflow.

---

# 7. Authentication Testing

## 7.1 Invalid Password

### Objective

Determine whether an attacker can authenticate using an incorrect password.

### Test

A valid username was supplied with an incorrect password.

### Expected Result

Authentication should fail.

### Actual Result

The application returned a generic authentication error.

```text
Invalid username or password.
```

### Result

**PASS**

### Security Control

The application uses Werkzeug password hashing and password verification.

---

# 8. Invalid Username Testing

## Objective

Determine whether authentication succeeds when an unknown username is supplied.

### Test

A non-existent username was submitted.

### Expected Result

Authentication should fail without revealing whether the account exists.

### Result

The application returned:

```text
Invalid username or password.
```

### Result

**PASS**

### Security Benefit

Generic authentication errors reduce unnecessary account-enumeration information.

---

# 9. Two-Factor Authentication Testing

## 9.1 Invalid OTP

### Objective

Determine whether an incorrect TOTP code can authenticate a user.

### Test

An incorrect six-digit OTP was submitted.

### Expected Result

Authentication must fail.

### Result

```text
Invalid or expired authentication code.
```

**PASS**

---

# 10. Expired OTP Testing

## Objective

Determine whether an expired TOTP code can be reused.

### Test

An expired OTP was submitted.

### Expected Result

The expired code must be rejected.

### Result

The application rejected the code.

**PASS**

---

# 11. 2FA Bypass Testing

## Objective

Determine whether a user can access the authenticated dashboard without completing 2FA.

### Test Procedure

1. Valid username and password were supplied.
2. The application reached the 2FA verification stage.
3. OTP verification was intentionally skipped.
4. Direct access to `/dashboard` was attempted.

### Expected Result

The dashboard must not be accessible.

### Actual Result

The application redirected the request to the login flow.

### Result

**PASS**

### Security Control

The application maintains a separate pending 2FA session state and only creates the authenticated `user_id` session after successful OTP verification.

---

# 12. SQL Injection Testing

## Objective

Test whether user-controlled username input can manipulate SQL queries.

### Test Payload

```text
' OR '1'='1
```

### Expected Result

The payload must not bypass authentication.

### Result

Authentication was not bypassed.

**PASS**

### Security Control

The application uses parameterized SQL queries.

Example:

```python
connection.execute(
    """
    SELECT id, username
    FROM users
    WHERE username = ?
    """,
    (username,)
)
```

User input is supplied separately from the SQL statement.

---

# 13. CSRF Testing

## Objective

Determine whether state-changing POST requests require a valid CSRF token.

### Test

The CSRF token was removed from a POST request.

### Expected Result

The request must be rejected.

### Result

The application returned a CSRF error:

```text
CSRF TOKEN MISSING
```

### Result

**PASS**

### Security Control

Flask-WTF CSRF protection is enabled.

---

# 14. Dashboard Authorization Testing

## Objective

Determine whether an unauthenticated user can directly access the dashboard.

### Test

The following endpoint was accessed without authentication:

```text
/dashboard
```

### Expected Result

The user must not access protected content.

### Result

The application redirected the user to the login page.

**PASS**

---

# 15. Logout and Session Testing

## Objective

Determine whether a logged-out user can continue accessing protected resources.

### Test Procedure

1. User authenticated successfully.
2. Dashboard was accessed.
3. Logout was performed.
4. Dashboard was accessed again.

### Expected Result

The previous authenticated session should no longer provide access.

### Result

The dashboard redirected to login.

**PASS**

### Security Control

The application uses:

```python
session.clear()
```

during logout.

---

# 16. Session Fixation Testing

## Objective

Validate that authentication state is not retained through a potentially attacker-controlled pre-authentication session.

### Security Control

After successful password authentication:

```python
session.clear()
```

is executed before assigning the pending authentication state.

After successful OTP verification, the pending 2FA identifier is removed and the authenticated session is established.

### Result

Authentication/session flow completed successfully during testing.

**PASS**

---

# 17. Login Rate-Limiting Testing

## Objective

Determine whether repeated login attempts are rate limited.

### Test

Multiple rapid login requests were generated.

### Observed Result

After repeated requests, the application returned:

```text
429 Too Many Requests
```

with a configured limit of:

```text
10 per 1 minute
```

### Result

**PASS**

---

# 18. OTP Brute-Force Testing

## Objective

Determine whether repeated incorrect OTP submissions are rate limited.

### Test

Repeated invalid OTP requests were submitted.

### Expected Result

Repeated attempts should eventually be throttled.

### Result

The application returned:

```text
429 Too Many Requests
```

### Result

**PASS**

---

# 19. Password Policy Testing

## 19.1 Weak Password

### Test

A common weak password was submitted:

```text
password
```

### Initial Result

The password was initially accepted.

### Remediation

A stronger password policy was implemented requiring:

* Minimum 12 characters
* Maximum 128 characters
* Uppercase character
* Lowercase character
* Number
* Special character
* Rejection of selected common passwords

### Retest Result

The weak password was rejected.

**PASS AFTER REMEDIATION**

---

## 19.2 Strong Password

### Test

A strong password satisfying the configured policy was submitted.

### Result

The password was accepted.

**PASS**

---

# 20. Input Validation Testing

## 20.1 Malicious Username Input

### Test

A username containing HTML/script-like content was submitted.

Example:

```text
<script>alert(1)</script>
```

### Initial Behavior

The application encountered an application error because the user-controlled value was involved in QR filename construction.

### Security Concern

This demonstrated unsafe handling of user-controlled input and unsafe file path construction.

This was **not treated as a confirmed XSS vulnerability** because JavaScript execution in a browser was not demonstrated.

### Remediation

The application now restricts usernames using:

```python
re.fullmatch(r"[A-Za-z0-9_]{3,30}", username)
```

QR filenames are generated from the numeric database user ID rather than the username.

### Retest

The malicious username was rejected without an application crash.

**PASS AFTER REMEDIATION**

---

# 21. OTP Format Validation

## Objective

Determine whether malformed OTP values are accepted.

### Security Control

OTP values must match:

```text
6 digits
```

Implemented validation:

```python
re.fullmatch(r"\d{6}", otp)
```

### Result

Malformed OTP values were rejected.

**PASS**

---

# 22. Security Header Testing

## Objective

Verify whether security-related HTTP response headers are implemented.

### Headers Observed

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: ...
```

### Result

The expected security headers were present.

**PASS**

---

# 23. Debug Information Exposure

## Objective

Determine whether Flask debug mode is enabled.

### Test

The application was started and its server configuration was observed.

### Result

```text
Debug mode: off
```

No Flask interactive debugger or debugger PIN was exposed.

**PASS**

---

# 24. Cookie Security Testing

## Objective

Validate important session cookie attributes.

### Observed Configuration

```text
HttpOnly
SameSite=Lax
```

### Security Benefit

`HttpOnly` reduces JavaScript access to the session cookie.

`SameSite=Lax` provides additional protection against certain cross-site request scenarios.

### Production Note

The application currently runs over local HTTP, so:

```python
SESSION_COOKIE_SECURE = False
```

is used for local development.

For HTTPS production deployment:

```python
SESSION_COOKIE_SECURE = True
```

should be enabled.

### Result

**PASS FOR LOCAL DEVELOPMENT CONFIGURATION**

---

# 25. Open Redirect Testing

## Objective

Determine whether user-controlled redirect parameters can force the application to redirect to an external website.

### Test

A URL parameter similar to:

```text
?next=https://google.com
```

was supplied.

### Expected Result

The application should not redirect the user to an attacker-controlled external domain.

### Result

The application remained within the authentication flow.

**PASS**

---

# 26. Complete Security Validation Matrix

|  # | Test           | Result |
| -: | -------------- | :----: |
|  1 | Wrong password |  PASS  |
|  2 | Wrong username |  PASS  |
|  3 | Invalid OTP    |  PASS  |
|  4 | Expired OTP    |   PAS  |
