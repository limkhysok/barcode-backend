# Barcode Backend API

A robust Django-based backend system for barcode-based inventory and transaction management, featuring JWT authentication, real-time tracking, and high-security standards.

---

## 🚀 Core Modules & Architecture

The project is structured into several modular applications:

- **`users`**: Custom user management, authentication (JWT), role-based access control (Staff/Boss/Admin), and user activity logging.
- **`products`**: Product catalog management including barcode generation, category mapping, and media handling.
- **`inventory`**: Real-time stock tracking, stock-in/out operations, and historical inventory logs.
- **`transactions`**: Sales and purchase transaction processing with barcode scanning integration.
- **`dashboard`**: Analytics and reporting module for business insights.
- **`core`**: Central project configuration, middleware, and security settings.

---

## ✨ Key Features

- **JWT Authentication**: Secure stateless authentication using `djangorestframework-simplejwt`.
- **Brute-Force Protection**: Integrated `django-axes` to prevent login attacks with configurable lockouts.
- **High Performance**: Optimized with **Redis caching** and **WhiteNoise** for efficient static file serving.
- **Media Support**: Robust handling of product images and documents using `Pillow`.
- **Production Ready**: Configured with `gunicorn` and ready for containerization.
- **Security First**: Implementation of security middleware, CSRF protection, and environment-based configuration.
- **Barcode Scanning Ready**: Designed to work seamlessly with client-side scanning using `html5-qrcode`.


---

## 🛠️ Technology Stack & Dependencies

| Library | Version | Description |
| :--- | :--- | :--- |
| **Django** | `6.0.3` | Core Web Framework |
| **Django Rest Framework** | `3.17.0` | API Development |
| **SimpleJWT** | `5.5.1` | Authentication |
| **MySQL Client** | `2.2.8` | Database Driver |
| **Redis** | `5.4.0` | Caching & Lockout Storage |
| **WhiteNoise** | `6.9.0` | Static File Serving |
| **Gunicorn** | `23.0.0` | WSGI HTTP Server |

---

## 🐳 Docker Setup

Run the entire stack easily using Docker:

1.  **Build the Image:**
    ```bash
    docker build -t barcode-backend .
    ```

2.  **Run with Environment Variables:**
    ```bash
    docker run -p 8000:8000 \
      --env-file .env \
      barcode-backend
    ```

> [!NOTE]
> Ensure your `DB_HOST` in `.env` points to your database container or external host when running in Docker.

---

## 💻 Local Development

### 1. Prerequisites
- Python 3.13+
- MySQL Server
- Redis Server (Optional, but recommended)

### 2. Installation
```bash
# Clone and enter directory
cd barcode-backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

### 4. Database & Static Files
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5. Run Server
```bash
python manage.py runserver
```

---

## 🔑 Authentication Endpoints (v1)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/auth/register/` | POST | Register a new user |
| `/api/v1/auth/login/` | POST | Login & get JWT tokens |
| `/api/v1/auth/token/refresh/` | POST | Refresh expired access token |
| `/api/v1/users/me/` | GET | Retrieve user profile |

> [!TIP]
> For a full list of endpoints, please refer to the [API_DOCS.md](./API_DOCS.md) file.

---

## 📱 Frontend Integration

This backend is designed to be paired with the **Barcode App** (Next.js/React).

- **Frontend Repository**: [barcode-app](https://github.com/limkhysok/barcode-app)
- **Scanning Technology**: Utilizes `html5-qrcode` for high-performance, client-side barcode and QR code scanning directly in the browser.
- **Integration**: The backend provides the necessary REST APIs for product lookups and transaction processing once a barcode is scanned.

---

## 🛡️ Superuser Credentials

**Username:** `habibi`  
**Password:** `habibi`  
**Email:** [EMAIL_ADDRESS]`
