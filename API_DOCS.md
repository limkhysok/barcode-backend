# Barcode Backend - API Documentation

This backend uses **Django Rest Framework** and **SimpleJWT** for secure authentication.

> All endpoints except login/register require `Authorization: Bearer <access_token>` header.

---

## 1. User Registration
Create a new user account.

- **Endpoint:** `POST /api/auth/register`

### Payload
```json
{
  "username": "your_username",
  "email": "user@example.com",
  "name": "Full Name",
  "password": "your_secure_password"
}
```

### Response (201 Created)
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

- **Endpoint:** `POST /api/auth/login`

### Payload
```json
{
  "username": "your_username",
  "password": "your_secure_password"
}
```

### Response (200 OK)
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5..."
}
```

---

## 3. Get / Update Current User
Retrieve or update the currently logged-in user.

- **Endpoint:** `GET / PATCH / PUT /api/auth/me`

### Response (200 OK)
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

- **Endpoint:** `POST /api/auth/token/refresh`

### Payload
```json
{ "refresh": "your_refresh_token" }
```

### Response (200 OK)
```json
{ "access": "newly_generated_access_token" }
```

---

## 5. Product Management


CRUD operations on products. **All endpoints require authentication with a JWT access token.**

- **Base Endpoint:** `/api/products`
- **Methods:**
  - `GET /api/products` — List all products
  - `POST /api/products` — Create a new product
  - `GET /api/products/<id>` — Retrieve a product by id
  - `PUT /api/products/<id>` — Replace a product by id
  - `PATCH /api/products/<id>` — Update part of a product by id
  - `DELETE /api/products/<id>` — Delete a product by id

> **Note:** The `<id>` in the URL is the product's `id` field (the primary key in the database and in API responses).

### Authentication Required
All product endpoints require the following header:

```
Authorization: Bearer <access_token>
```

You must first obtain an access token via the login endpoint (`POST /api/auth/login`).

#### Example using curl:
```
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/products/
```

### Create Product (POST)
`barcode` is optional — auto-generated as `SN-XXXXXX` if omitted.
```json
{
  "product_name": "Zinc Bolt M8",
  "category": "Fasteners",
  "cost_per_unit": 0.50,
  "reorder_level": 100,
  "supplier": "CTK Industrial"
}
```

Category choices: `Fasteners`, `Accessories`

### Response Example (POST/GET)
```json
{
  "id": 1,
  "barcode": "SN-A1B2C3",
  "product_name": "Zinc Bolt M8",
  "category": "Fasteners",
  "cost_per_unit": "0.50",
  "reorder_level": 100,
  "supplier": "CTK Industrial",
  "created_at": "2026-03-25T08:00:00Z",
  "updated_at": "2026-03-25T08:00:00Z",
  "created_by": 2
}
```

### Retrieve Product (GET)
`GET /api/products/<id>`

### Update Product (PUT/PATCH)
`PUT /api/products/<id>` or `PATCH /api/products/<id>`

#### Example PATCH payload
```json
{
  "product_name": "Updated Name"
}
```

### Delete Product (DELETE)
`DELETE /api/products/<id>`

> All detail, update, and delete operations require the correct product `id` in the URL. If the product does not exist, a 404 Not Found will be returned.

---

## 6. Inventory Management
Track stock levels across sites and locations.

- **Base Endpoint:** `/api/inventory`
- **Methods:** `GET` / `POST` / `PUT` / `PATCH` / `DELETE`

### Query Parameters (GET list)
| Param | Description |
|-------|-------------|
| `product_id=<id>` | Filter by product ID |
| `site=<name>` | Filter by site name (case-insensitive) |
| `search=<term>` | Search by product name — used by the **transaction page** dropdown |

### Create Inventory Record (POST)
```json
{
  "product": 1,
  "site": "Warehouse A",
  "location": "A1-Shelf-5",
  "product_description": "Zinc Bolt M8 - 50mm",
  "quantity_on_hand": 500,
  "order_date": "2026-03-24"
}
```

### Response Example
```json
{
  "id": 1,
  "product": 1,
  "product_details": {
    "id": 1,
    "barcode": "SN-A1B2C3",
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
  "reorder_status": "No",
  "order_date": "2026-03-24",
  "created_at": "2026-03-25T08:00:00Z",
  "updated_at": "2026-03-25T08:00:00Z"
}
```

---

## 7. Barcode Scan Lookup
Resolve a scanned barcode into its inventory records. Used by the **scan page**.

- **Endpoint:** `GET /api/inventory/scan?barcode=<barcode>`

### Responses

**Product found and in inventory (200 OK)**
```json
{
  "found": true,
  "product": {
    "id": 1,
    "barcode": "SN-A1B2C3",
    "product_name": "Zinc Bolt M8",
    "category": "Fasteners",
    "supplier": "CTK Industrial",
    "cost_per_unit": "0.50",
    "reorder_level": 100
  },
  "inventory": [
    {
      "id": 1,
      "site": "Warehouse A",
      "location": "A1-Shelf-5",
      "quantity_on_hand": 500,
      "stock_value": "250.00",
      "reorder_status": "No",
      ...
    }
  ]
}
```

**Product exists but has no inventory record (200 OK)**
```json
{
  "found": false,
  "product": { ... },
  "inventory": []
}
```

**Barcode not found (404)**
```json
{
  "found": false,
  "detail": "No product found with this barcode."
}
```

**Missing barcode param (400)**
```json
{
  "detail": "barcode query parameter is required."
}
```

### Frontend flow (scan page)
1. Scan barcode → `GET /api/inventory/scan?barcode=<scanned_value>`
2. If `found: true` → show inventory list, user picks a site/location
3. If `found: false` with product → show "item not in inventory"
4. If 404 → show "unknown barcode"
5. User confirms quantity + type → `POST /api/transactions/`

---

## 8. Transactions (Stock In / Out)
Log stock movements. Creating a transaction automatically updates the linked inventory balance.

- **Base Endpoint:** `/api/transactions`
- **Methods:** `GET` / `POST` / `DELETE`

### Query Parameters (GET list)
| Param | Description |
|-------|-------------|
| `inventory_id=<id>` | Filter by inventory record |
| `type=Receive\|Sale` | Filter by transaction type |
| `barcode=<barcode>` | Filter by product barcode |
| `search=<term>` | Search by product name |

### Create Transaction (POST)
Used by **both** the scan page and the transaction page after the user has selected an inventory record.

- Use **positive** quantity for `Receive` (stock in)
- Use **negative** quantity for `Sale` (stock out)

```json
{
  "inventory": 1,
  "transaction_type": "Receive",
  "quantity": 25
}
```

Transaction types: `Receive`, `Sale`

### Auto-Update on Create
When a transaction is posted:
1. `quantity_on_hand` on the linked inventory record is adjusted by the signed quantity.
2. `stock_value` and `reorder_status` are recalculated immediately.

### Response Example
```json
{
  "id": 1,
  "inventory": 1,
  "inventory_details": { ... },
  "product_name": "Zinc Bolt M8",
  "barcode": "SN-A1B2C3",
  "site": "Warehouse A",
  "location": "A1-Shelf-5",
  "transaction_type": "Receive",
  "quantity": 25,
  "performed_by": 2,
  "performed_by_username": "staff_user",
  "transaction_date": "2026-03-25T08:00:00Z"
}
```

### Validation Errors
| Scenario | Error |
|----------|-------|
| Sale quantity is positive | `"Sales must be recorded as negative numbers."` |
| Sale exceeds current stock | `"Insufficient stock. Current balance is only X units."` |
| Receive quantity is negative | `"Receives must be recorded as positive numbers."` |

### Frontend flow (transaction page)
1. User types product name → `GET /api/inventory?search=<term>` → populate dropdown
2. User selects inventory record, enters quantity and type
3. `POST /api/transactions` with `{ inventory, quantity, transaction_type }`
