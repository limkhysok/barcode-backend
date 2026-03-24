# Barcode Backend - API Documentation

This backend uses **Django Rest Framework** and **SimpleJWT** for secure authentication. 

## 1. User Registration
Create a new user account.

- **Endpoint:** `/api/auth/register/`
- **Method:** `POST`
- **Header:** `Content-Type: application/json`

### Payload
```json
{
  "username": "your_username",
  "email": "user@example.com",
  "name": "Full Name",
  "password": "your_secure_password"
}
```

### Success Response (201 Created)
```json
{
  "id": 2,
  "username": "your_username",
  "email": "user@example.com",
  "name": "Full Name"
}
```

---

## 2. User Login (Obtain Token)
Authenticates a user and returns a set of tokens.

- **Endpoint:** `/api/auth/login/`
- **Method:** `POST`
- **Header:** `Content-Type: application/json`

### Payload
```json
{
  "username": "your_username",
  "password": "your_secure_password"
}
```

### Success Response (200 OK)
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5...", 
  "access": "eyJhbGciOiJIUzI1NiIsInR5..."
}
```

---

## 3. Get Current User / Profile
Retrieve or update the details of the currently logged-in user.

- **Endpoint:** `/api/auth/me/`
- **Method:** `GET` / `PATCH` / `PUT`
- **Header:** `Authorization: Bearer <your_access_token>`

### Success Response (200 OK)
```json
{
  "id": 2,
  "username": "your_username",
  "email": "user@example.com",
  "name": "Full Name"
}
```

---

## 4. Token Refresh
Use the `refresh` token to get a new `access` token when it expires.

- **Endpoint:** `/api/auth/token/refresh/`
- **Method:** `POST`
- **Header:** `Content-Type: application/json`

### Payload
```json
{
  "refresh": "your_refresh_token_string"
}
```

### Success Response (200 OK)
```json
{
  "access": "newly_generated_access_token"
}
```

---

## 5. Product Management
Perform CRUD operations on products.

- **Base Endpoint:** `/api/products/`
- **Method:** `GET` / `POST` / `PUT` / `PATCH` / `DELETE`
- **Header:** `Authorization: Bearer <your_access_token>`

### Create Product Example (POST)
```json
{
  "product_name": "Screws M5",
  "category": "Fasteners",
  "cost_per_unit": 12.50,
  "reorder_level": 50,
  "supplier": "CTK Supply Co."
}
```

### Response Example
```json
{
  "id": 1,
  "product_name": "Screws M5",
  "category": "Fasteners",
  "cost_per_unit": "12.50",
  "reorder_level": 50,
  "supplier": "CTK Supply Co.",
  "created_at": "2026-03-24T...",
  "updated_at": "2026-03-24T...",
  "created_by": 2
}
```
