# Barcode Backend API

Django Rest Framework project with JWT authentication.

## Installation

1.  Create a virtual environment:
    ```bash
    python -m venv venv
    ```
2.  Activate it:
    -   Windows: `.\venv\Scripts\activate`
    -   Mac/Linux: `source venv/bin/activate`
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run migrations:
    ```bash
    python manage.py migrate
    ```
5.  Run the server:
    ```bash
    python manage.py runserver
    ```

## Authentication Endpoints

| Endpoint | Method | Description | Authentication |
| :--- | :--- | :--- | :--- |
| `/api/auth/register/` | POST | Register a new user | None |
| `/api/auth/login/` | POST | Login with username and password | None |
| `/api/auth/token/refresh/` | POST | Refresh access token | Refresh Token |
| `/api/auth/me/` | GET | Get current user details | Access Token (Bearer) |

## Superuser Credentials

**Username:** ctkadmin
**Password:** passwordctk2026*
**Email:** ctkadmin@example.com


