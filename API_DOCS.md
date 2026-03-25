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
- **Note:** `barcode` is optional. If not provided, the system generates a random 8-character ID (mixed case).
```json
{
  "product_name": "Zinc Bolt M8",
  "category": "Fasteners",
  "cost_per_unit": 0.50,
  "reorder_level": 100,
  "supplier": "CTK Industrial"
}
```

### Response Example
```json
{
  "id": 1,
  "barcode": "128vj2-B8",
  "product_name": "Zinc Bolt M8",
  "category": "Fasteners",
  "cost_per_unit": "0.50",
  "reorder_level": 100,
  "supplier": "CTK Industrial",
  "created_at": "...",
  "updated_at": "...",
  "created_by": 2
}
```

---

## 6. Inventory Management
Track stock levels across different sites and locations.

- **Base Endpoint:** `/api/inventory/`
- **Method:** `GET` / `POST` / `PUT` / `PATCH` / `DELETE`
- **Header:** `Authorization: Bearer <your_access_token>`

### Create Inventory Record (POST)
Use this to set initial stock or add stock at a new location.
```json
{
  "product": 1, 
  "site": "Warehouse A",
  "location": "A1-Shelf-5",
  "product_description": "Zinc Bolt M8 - 50mm",
  "quantity_on_hand": 500,
  "stock_value": 250.00,
  "reorder_status": "no",
  "order_date": "2026-03-24"
}
```

### Response Example (Rich Data)
The response includes detailed information about the product and site.
```json
{
  "id": 1,
  "product": 1,
  "product_details": {
      "id": 1,
      "product_name": "Zinc Bolt M8",
      "category": "Fasteners",
      "supplier": "CTK Industrial",
      "cost_per_unit": "0.50",
      "reorder_level": 100
  },
  "site": "Warehouse A",
  "location": "A1-Shelf-5",
  "product_description": "Zinc Bolt M8 - 50mm",
  "quantity_on_hand": 500,
  "stock_value": "250.00",
  "reorder_status": "no",
  "order_date": "2026-03-24",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 7. Transactions (Stock In/Out)
Track movement of goods. Creating a transaction automatically updates the linked inventory balance.

- **Base Endpoint:** `/api/transactions/`
- **Method:** `GET` / `POST` / `DELETE`
- **Header:** `Authorization: Bearer <your_access_token>`

### Create Transaction (POST)
Types allowed: `Receive` (Stock In), `Sale` (Stock Out).
**Note:** Use **positive** quantities for `Receive` and **negative** quantities for `Sale`.
```json
{
  "inventory": 1,
  "transaction_type": "Receive",
  "quantity": 25
}
```

### Auto-Update Feature
When you POST a transaction:
1.  The `quantity_on_hand` in the linked Inventory record is updated.
2.  The `stock_value` and `reorder_status` are recalculated instantly.

### Response Example
```json
{
  "id": 1,
  "inventory": 1,
  "inventory_details": { ... },
  "transaction_type": "Receive",
  "quantity": 25,
  "performed_by": 2,
  "performed_by_username": "staff_user",
  "transaction_date": "..."
}
```
