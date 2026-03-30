# Barcode Backend - API Documentation

This backend uses **Django Rest Framework** and **SimpleJWT** for secure authentication.

> All endpoints except login/register require `Authorization: Bearer <access_token>` header.

---

## 1. User Registration
Create a new user account.

- **Endpoint:** `POST /api/v1/users/register`

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
  "name": "Full Name",
  "is_boss": false,
  "is_staff": false,
  "is_superuser": false
}
```

---

## 2. User Login (Obtain Token)

- **Endpoint:** `POST /api/v1/users/login`

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

- **Endpoint:** `GET / PATCH / PUT /api/v1/users/me`

### Response (200 OK)
```json
{
  "id": 2,
  "username": "your_username",
  "email": "user@example.com",
  "name": "Full Name",
  "is_boss": false,
  "is_staff": false,
  "is_superuser": false
}
```

---

## 4. Token Refresh

- **Endpoint:** `POST /api/v1/users/token/refresh`

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

- **Base Endpoint:** `/api/v1/products/`
- **Methods:**
  - `GET /api/v1/products/` — List all products (paginated) → `200 OK`
  - `GET /api/v1/products/{id}/` — Retrieve a product → `200 OK`
  - `POST /api/v1/products/` — Create a new product → `201 Created`
  - `PUT /api/v1/products/{id}/` — Replace a product → `200 OK`
  - `DELETE /api/v1/products/{id}/` — Delete a product → `204 No Content`

### List Products (GET)
`GET /api/v1/products/` — returns page 1 by default (20 items). Use `?page=2` for the next page.

#### Response (200 OK)
```json
{
  "count": 85,
  "next": "http://localhost:8000/api/v1/products?page=2",
  "previous": null,
  "results": [
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
  ]
}
```

> **Note:** The `<id>` in the URL is the product's `id` field (the primary key in the database and in API responses).

### Authentication Required
All product endpoints require the following header:

```
Authorization: Bearer <access_token>
```

You must first obtain an access token via the login endpoint (`POST /api/v1/users/login`).

#### Example using curl:
```
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/products/
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

#### Success (201 Created)
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

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400 Bad Request` | `product_name` missing | `{ "product_name": ["This field may not be blank."] }` |
| `400 Bad Request` | `supplier` missing | `{ "supplier": ["This field may not be blank."] }` |
| `400 Bad Request` | Invalid `category` | `{ "category": ["\"X\" is not a valid choice."] }` |
| `409 Conflict` | Duplicate `barcode` | `{ "detail": "A product with this barcode already exists." }` |

---

### Retrieve Product (GET)
`GET /api/v1/products/{id}/`

#### Success (200 OK) — returns the product object above

#### Errors
| Status | Response |
|--------|----------|
| `404 Not Found` | `{ "detail": "No Product matches the given query." }` |

---

### Update Product (PUT / PATCH)
`PUT /api/v1/products/{id}/` — full replace
`PATCH /api/v1/products/{id}/` — partial update

#### Success (200 OK) — returns the updated product object

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400 Bad Request` | Invalid field value | `{ "field": ["error message"] }` |
| `404 Not Found` | Product not found | `{ "detail": "No Product matches the given query." }` |

---

### Delete Product (DELETE)
`DELETE /api/v1/products/{id}/`

#### Success (204 No Content) — empty body

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `409 Conflict` | Has linked transactions | `{ "detail": "Cannot delete product with existing transactions." }` |
| `404 Not Found` | Product not found | `{ "detail": "No Product matches the given query." }` |

---

## 6. Inventory Management

Track stock levels across sites and locations. **All endpoints require authentication with a JWT access token.**

- **Base Endpoint:** `/api/v1/inventory/`
- **Methods:** `GET` / `POST` / `PUT` / `PATCH` / `DELETE`

### List Inventory (GET)
`GET /api/v1/inventory/` — returns page 1 by default (20 items). Use `?page=2` for the next page.

#### Response (200 OK)
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/inventory?page=2",
  "previous": null,
  "results": [
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
      "quantity_on_hand": 500,
      "stock_value": "250.00",
      "reorder_status": "No",
      "created_at": "2026-03-25T08:00:00Z",
      "updated_at": "2026-03-25T08:00:00Z"
    }
  ]
}
```

> **Note:** All inventory endpoints require the following header:
>
> ```
> Authorization: Bearer <access_token>
> ```
>
> You must first obtain an access token via the login endpoint (`POST /api/users/login`).

#### Example using curl:
```
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/inventory/
```

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
  "quantity_on_hand": 500
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
  "quantity_on_hand": 500,
  "stock_value": "250.00",
  "reorder_status": "No",
  "created_at": "2026-03-25T08:00:00Z",
  "updated_at": "2026-03-25T08:00:00Z"
}
```

---

## 7. Barcode Scan Lookup
Resolve a scanned barcode into its inventory records. Used by the **scan page**.

- **Endpoint:** `GET /api/v1/inventory/scan/?barcode=<barcode>`

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
1. Scan barcode → `GET /api/inventory/scan/?barcode=<scanned_value>`
2. If `found: true` → show inventory list, user picks a site/location
3. If `found: false` with product → show "item not in inventory"
4. If 404 → show "unknown barcode"
5. User confirms quantity + type → `POST /api/transactions/`

---

## 8. Transactions (Stock In / Out)
Log stock movements. A single transaction has **one type** (`Receive` or `Sale`) and can contain **multiple items** across different inventory records. Creating a transaction automatically updates all linked inventory balances.

- **Base Endpoint:** `/api/v1/transactions/`
- **Methods:**
  - `GET /api/v1/transactions/` — List all transactions (paginated)
  - `POST /api/v1/transactions/` — Create a new transaction with items
  - `GET /api/v1/transactions/<id>/` — Retrieve a transaction by id
  - `PUT /api/v1/transactions/<id>/` — Replace a transaction by id
  - `PATCH /api/v1/transactions/<id>/` — Update part of a transaction by id
  - `DELETE /api/v1/transactions/<id>/` — Delete a transaction by id

### List Transactions (GET)
`GET /api/v1/transactions/` — returns page 1 by default (20 items). Use `?page=2` for the next page.

#### Response (200 OK)
```json
{
  "count": 200,
  "next": "http://localhost:8000/api/v1/transactions?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "transaction_type": "Receive",
      "performed_by": 2,
      "performed_by_username": "staff_user",
      "total_transaction_value": "262.50",
      "items": [ { "..." } ],
      "transaction_date": "2026-03-26T10:00:00Z"
    }
  ]
}
```

### Query Parameters (GET list)
| Param | Description |
|-------|-------------|
| `type=Receive\|Sale` | Filter by transaction type |
| `barcode=<barcode>` | Filter by product barcode (matches any item in the transaction) |
| `search=<term>` | Search by product name (matches any item in the transaction) |

> `inventory_id` filter removed — transactions now hold multiple items, filter by `barcode` or `search` instead.

### Create Transaction (POST)

- `transaction_type` is set **once at the header** — all items must follow it (no mixing)
- Use **positive** quantity for `Receive`, **negative** for `Sale`
- `cost_per_unit` is **auto-snapshotted** from the product at the time of creation — do not send it
- `performed_by` is **auto-assigned** from the JWT token

```json
{
  "transaction_type": "Receive",
  "items": [
    { "inventory": 1, "quantity": 10 },
    { "inventory": 3, "quantity": 5 },
    { "inventory": 7, "quantity": 20 }
  ]
}
```

Transaction types: `Receive`, `Sale`

### Auto-Update on Create
For each item when a transaction is posted:
1. `quantity_on_hand` on the linked inventory record is adjusted by the signed quantity.
2. `stock_value` and `reorder_status` are recalculated immediately.

### Response Example
```json
{
  "id": 1,
  "transaction_type": "Receive",
  "performed_by": 2,
  "performed_by_username": "staff_user",
  "total_transaction_value": "262.50",
  "items": [
    {
      "id": 1,
      "inventory": 1,
      "product_name": "Zinc Bolt M8",
      "quantity": 10,
      "cost_per_unit": "14.00",
      "line_total": "140.00"
    },
    {
      "id": 2,
      "inventory": 3,
      "product_name": "Hex Nut M8",
      "quantity": 5,
      "cost_per_unit": "8.50",
      "line_total": "42.50"
    },
    {
      "id": 3,
      "inventory": 7,
      "product_name": "Steel Washer",
      "quantity": 20,
      "cost_per_unit": "4.00",
      "line_total": "80.00"
    }
  ],
  "transaction_date": "2026-03-26T10:00:00Z"
}
```

### Validation Errors

**No items sent (400)**
```json
{ "items": "At least one item is required." }
```

**Invalid transaction type (400)**
```json
{ "transaction_type": "Must be Receive or Sale." }
```

**Per-item errors (400)**
```json
{
  "items": [
    { "item": 2, "quantity": "Sale quantities must be negative." },
    { "item": 3, "quantity": "Insufficient stock. Current balance is only 4 units." }
  ]
}
```

| Scenario | Error |
|----------|-------|
| Sale quantity is positive or zero | `"Sale quantities must be negative."` |
| Sale exceeds current stock | `"Insufficient stock. Current balance is only X units."` |
| Receive quantity is negative or zero | `"Receive quantities must be positive."` |

### Frontend flow (transaction page)
1. User selects `Receive` or `Sale` — this locks the type for all items
2. User searches products → `GET /api/inventory?search=<term>` → add items to the list
3. User enters quantity for each item
4. `POST /api/v1/transactions` with `{ transaction_type, items: [{ inventory, quantity }, ...] }`

---

## 9. Scan Transaction (Stock In / Out via Barcode)
Create a **single-item** transaction by scanning a product barcode. The frontend handles the camera and sends the barcode to this endpoint.

- **Endpoint:** `POST /api/v1/transactions/scan/`
- **Auth required:** Yes

### Payload
```json
{
  "barcode": "SN-A1B2C3",
  "transaction_type": "Receive",
  "quantity": 10,
  "inventory_id": 1
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `barcode` | Yes | Scanned product barcode |
| `transaction_type` | Yes | `Receive` or `Sale` |
| `quantity` | Yes | Positive for Receive, negative for Sale |
| `inventory_id` | Conditional | Required only if the product has multiple inventory records (different sites/locations) |

### Response (201 Created)
Same shape as `POST /api/transactions` — full transaction object with one item in the `items` array.

### Error Responses

**Missing required field (400)**
```json
{ "barcode": "This field is required." }
```

**Barcode not found (404)**
```json
{ "detail": "No product found with this barcode." }
```

**Product has no inventory record (404)**
```json
{ "detail": "Product found but has no inventory record.", "product": "Zinc Bolt M8" }
```

**Multiple inventory records — inventory_id not specified (400)**
```json
{
  "detail": "Multiple inventory records found for this product. Please specify inventory_id.",
  "inventory": [ { "id": 1, "site": "Warehouse A", ... }, { "id": 2, "site": "Warehouse B", ... } ]
}
```

**inventory_id doesn't belong to this product (400)**
```json
{ "detail": "The specified inventory_id does not belong to this product." }
```

**Insufficient stock for Sale (400)**
```json
{ "items": [ { "item": 1, "quantity": "Insufficient stock. Current balance is only X units." } ] }
```

### Frontend flow (scan page)
1. Camera scans barcode → `POST /api/v1/transactions/scan/` with `{ barcode, transaction_type, quantity }`
2. If **400 with inventory list** → show site picker → re-submit with `inventory_id`
3. If **404** → show "Unknown barcode" or "Not in inventory" message
4. If **201** → show success with `total_transaction_value` and updated stock


# http://127.0.0.1:8000/api/v1/products/ # correct