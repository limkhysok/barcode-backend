# Barcode Backend — API Documentation

This backend uses **Django Rest Framework** and **SimpleJWT** for secure authentication.

> All endpoints except auth (login/register) require `Authorization: Bearer <access_token>` header.

---

## Base URL

```
http://localhost:8000/api/v1/
```

---

## URL Structure

| Prefix | Purpose |
|--------|---------|
| `/api/v1/auth/` | Authentication — login, register, token refresh |
| `/api/v1/users/` | Current user profile (`me/`) |
| `/api/v1/admin/` | User management and activity logs (admin/boss only) |
| `/api/v1/products/` | Product CRUD |
| `/api/v1/inventory/` | Inventory CRUD and scan lookup |
| `/api/v1/transactions/` | Transaction logging and export |
| `/api/v1/dashboard/` | Aggregate stats |

---

## Role-Based Access Control (RBAC)

All protected endpoints enforce the following permission rules based on the user's role:

| Method | Regular user | Staff | Boss | Superadmin |
|--------|-------------|-------|------|------------|
| `GET` — view/list | ✅ | ✅ | ✅ | ✅ |
| `POST` — create | ✅ | ✅ | ✅ | ✅ |
| `PUT` / `PATCH` — edit | ❌ 403 | ✅ | ✅ | ✅ |
| `DELETE` | ❌ 403 | ❌ 403 | ❌ 403 | ✅ |

> **Role mapping:**
> - **Regular user** — authenticated user with no special flags (`is_staff: false`, `is_boss: false`, `is_superuser: false`)
> - **Staff** — user with `is_staff: true` (can edit, cannot delete)
> - **Boss** — user with `is_boss: true` (can edit, cannot delete)
> - **Superadmin** — user with `is_superuser: true` (full access)

> **Exception:** `PATCH /api/v1/users/me/` is available to all authenticated users regardless of role.

### JWT Claims
The login response token includes role fields. Decode the `access` token to read:
```json
{
  "user_id": 2,
  "username": "staff_user",
  "is_boss": false,
  "is_staff": false,
  "is_superuser": false
}
```
Use these claims on the frontend to show/hide UI elements without an extra API call.

---

## 1. Authentication

### Register
Create a new user account. No authentication required.

- **Endpoint:** `POST /api/v1/auth/register/`

#### Payload
```json
{
  "username": "your_username",
  "email": "user@example.com",
  "name": "Full Name",
  "password": "your_secure_password"
}
```

#### Response (201 Created)
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

### Login (Obtain Token)
No authentication required.

- **Endpoint:** `POST /api/v1/auth/login/`

#### Payload
```json
{
  "username": "your_username",
  "password": "your_secure_password"
}
```

#### Response (200 OK)
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5..."
}
```

---

### Token Refresh

- **Endpoint:** `POST /api/v1/auth/token/refresh/`

#### Payload
```json
{ "refresh": "your_refresh_token" }
```

#### Response (200 OK)
```json
{ "access": "newly_generated_access_token" }
```

---

## 2. Current User

### Get / Update Profile
Retrieve or update the currently logged-in user's own profile.

- **Endpoint:** `GET / PATCH / PUT /api/v1/users/me/`
- **Auth required:** Yes

#### Response (200 OK)
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

## 3. Products

CRUD operations on products. **All endpoints require authentication.**

- **Base Endpoint:** `/api/v1/products/`

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/api/v1/products/` | List all products | `200 OK` |
| `POST` | `/api/v1/products/` | Create a product | `201 Created` |
| `GET` | `/api/v1/products/{id}/` | Retrieve a product | `200 OK` |
| `PUT` | `/api/v1/products/{id}/` | Full replace | `200 OK` |
| `PATCH` | `/api/v1/products/{id}/` | Partial update | `200 OK` |
| `DELETE` | `/api/v1/products/{id}/` | Delete a product | `204 No Content` |
| `GET` | `/api/v1/products/stats/` | Aggregate overview | `200 OK` |

```
Authorization: Bearer <access_token>
```

---

### List Products
`GET /api/v1/products/`

#### Query Parameters

| Param | Description |
|-------|-------------|
| `search=<term>` | Search across `barcode`, `product_name`, `supplier` (case-insensitive) |
| `category=<name>` | Filter by category (e.g. `Fasteners`, `Accessories`) |
| `supplier=<name>` | Filter by supplier (case-insensitive) |
| `ordering=<field>` | Sort results — see table below |

**Ordering options**

| Value | Description |
|-------|-------------|
| `product_name` / `-product_name` | Name A→Z / Z→A |
| `supplier` / `-supplier` | Supplier A→Z / Z→A |
| `cost_per_unit` / `-cost_per_unit` | Cost low→high / high→low |
| `reorder_level` / `-reorder_level` | Reorder level low→high / high→low |
| `created_at` / `-created_at` | Oldest first / Newest first |

**Examples**
```
GET /api/v1/products/
GET /api/v1/products/?search=bolt
GET /api/v1/products/?search=CTK&category=Fasteners
GET /api/v1/products/?category=Fasteners&ordering=cost_per_unit
```

#### Response (200 OK)
```json
{
  "count": 85,
  "results": [
    {
      "id": 1,
      "barcode": "4006381333931",
      "product_name": "Zinc Bolt M8",
      "category": "Fasteners",
      "cost_per_unit": "0.50",
      "reorder_level": 100,
      "supplier": "CTK Industrial",
      "product_picture": "/media/products/images/zinc_bolt_m8.jpg",
      "created_at": "2026-03-25T08:00:00Z",
      "updated_at": "2026-03-25T08:00:00Z",
      "created_by": 2
    }
  ]
}
```

---

### Product Stats
`GET /api/v1/products/stats/`

#### Response (200 OK)
```json
{
  "total_products": 85,
  "total_value": "13250.00",
  "by_category": {
    "Fasteners": { "count": 60, "total_value": "9800.00" },
    "Accessories": { "count": 25, "total_value": "3450.00" }
  }
}
```

---

### Create Product
`POST /api/v1/products/`

`barcode` is required and must be unique. It cannot be changed after creation.

> Use `multipart/form-data` when uploading an image. Use `application/json` otherwise.

```
Content-Type: multipart/form-data

barcode=4006381333931
product_name=Zinc Bolt M8
category=Fasteners
cost_per_unit=0.50
reorder_level=100
supplier=CTK Industrial
product_picture=<file>   ← optional
```

Category choices: `Fasteners`, `Accessories`

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400 Bad Request` | Missing required field | `{ "field": ["This field is required."] }` |
| `400 Bad Request` | Invalid category | `{ "category": ["\"X\" is not a valid choice."] }` |
| `409 Conflict` | Duplicate barcode | `{ "detail": "A product with this barcode already exists." }` |

---

### Update Product
`PUT /api/v1/products/{id}/` — full replace (all fields except `barcode`)
`PATCH /api/v1/products/{id}/` — partial update

> `barcode` is **read-only after creation** — ignored if included in the request body.

To **remove** `product_picture`:
```json
{ "product_picture": "" }
```

---

### Delete Product
`DELETE /api/v1/products/{id}/`

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `409 Conflict` | Has linked inventory/transactions | `{ "detail": "Cannot delete product with existing inventory records or transactions." }` |
| `404 Not Found` | Product not found | `{ "detail": "No Product matches the given query." }` |

---

## 4. Inventory

Track stock levels across sites and locations. **All endpoints require authentication.**

- **Base Endpoint:** `/api/v1/inventory/`

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/api/v1/inventory/` | List all records | `200 OK` |
| `POST` | `/api/v1/inventory/` | Create a record | `201 Created` |
| `GET` | `/api/v1/inventory/{id}/` | Retrieve a record | `200 OK` |
| `PUT` | `/api/v1/inventory/{id}/` | Full replace | `200 OK` |
| `PATCH` | `/api/v1/inventory/{id}/` | Partial update | `200 OK` |
| `DELETE` | `/api/v1/inventory/{id}/` | Delete a record | `204 No Content` |
| `GET` | `/api/v1/inventory/stats/` | Aggregate overview | `200 OK` |
| `GET` | `/api/v1/inventory/scan/` | Barcode lookup | `200 OK` |

> `stock_value` and `reorder_status` are **read-only** — auto-calculated whenever `quantity_on_hand` changes.

> **`reorder_status` values:**
> | Value | Meaning |
> |-------|---------|
> | `"No"` | Stock above reorder level |
> | `"LOW"` | At or below product's `reorder_level` |
> | `"NO STOCK"` | `quantity_on_hand` is 0 |

> **Uniqueness:** Each `product` + `site` + `location` combination must be unique.

---

### List Inventory
`GET /api/v1/inventory/`

#### Query Parameters
| Param | Description |
|-------|-------------|
| `product_id=<id>` | Filter by product ID |
| `site=<name>` | Filter by site (case-insensitive) |
| `search=<term>` | Search by product name |

#### Response (200 OK)
```json
{
  "count": 42,
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

---

### Inventory Stats
`GET /api/v1/inventory/stats/`

#### Response (200 OK)
```json
{
  "total_records": 42,
  "total_quantity_on_hand": 12500,
  "total_stock_value": "13250.00",
  "needs_reorder": 5,
  "by_site": {
    "Warehouse A": {
      "records": 25,
      "total_quantity_on_hand": 8000,
      "total_stock_value": "8500.00"
    }
  },
  "activity": {
    "last_7_days":   { "data": [{ "date": "2026-03-25", "new_records": 3 }] },
    "last_14_days":  { "data": [{ "date": "2026-03-18", "new_records": 5 }] },
    "last_30_days":  { "data": [{ "date": "2026-03-01", "new_records": 8 }] },
    "last_3_months": { "data": [{ "week_start": "2026-01-05", "new_records": 12 }] }
  }
}
```

> **Chart note:** Only dates/weeks with activity are included. Fill missing dates with `0` on the frontend before rendering.

---

### Create Inventory Record
`POST /api/v1/inventory/`

#### Payload
```json
{
  "product": 1,
  "site": "Warehouse A",
  "location": "A1-Shelf-5",
  "quantity_on_hand": 500
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `product` | Yes | Product ID |
| `site` | Yes | Site name |
| `location` | Yes | Location within the site |
| `quantity_on_hand` | No | Starting quantity — defaults to `0`, must be ≥ 0 |

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400 Bad Request` | Missing required field | `{ "field": ["This field is required."] }` |
| `409 Conflict` | Duplicate product + site + location | `{ "detail": "An inventory record for this product, site, and location already exists." }` |

---

## 5. Barcode Scan Lookup

Resolve a scanned barcode into its inventory records. Used by the **scan page**.

- **Endpoint:** `GET /api/v1/inventory/scan/?barcode=<barcode>`
- **Auth required:** Yes

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
      "reorder_status": "No"
    }
  ]
}
```

**Product exists but no inventory record (200 OK)**
```json
{ "found": false, "product": { "..." }, "inventory": [] }
```

**Barcode not found (404)**
```json
{ "found": false, "detail": "No product found with this barcode." }
```

**Missing barcode param (400)**
```json
{ "detail": "barcode query parameter is required." }
```

### Frontend flow (scan page)
1. Scan barcode → `GET /api/v1/inventory/scan/?barcode=<value>`
2. `found: true` → show inventory list, user picks site/location
3. `found: false` with product → show "item not in inventory"
4. `404` → show "unknown barcode"
5. User confirms → `POST /api/v1/transactions/scan/` (single item) or `POST /api/v1/transactions/` (bulk)

---

## 6. Transactions

Log stock movements. A transaction has **one type** (`Receive` or `Sale`) and can contain **multiple items**. Creating a transaction automatically updates all linked inventory balances.

- **Base Endpoint:** `/api/v1/transactions/`

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/api/v1/transactions/` | List all transactions | `200 OK` |
| `POST` | `/api/v1/transactions/` | Create a transaction | `201 Created` |
| `GET` | `/api/v1/transactions/{id}/` | Retrieve a transaction | `200 OK` |
| `PUT` | `/api/v1/transactions/{id}/` | Full replace | `200 OK` |
| `PATCH` | `/api/v1/transactions/{id}/` | Partial update | `200 OK` |
| `DELETE` | `/api/v1/transactions/{id}/` | Delete a transaction | `204 No Content` |
| `GET` | `/api/v1/transactions/stats/` | Aggregate overview | `200 OK` |
| `GET` | `/api/v1/transactions/export/` | Export as CSV | `200 OK` |
| `POST` | `/api/v1/transactions/scan/` | Quick single-item transaction | `201 Created` |

---

### List Transactions
`GET /api/v1/transactions/`

#### Query Parameters
| Param | Description |
|-------|-------------|
| `type=Receive\|Sale` | Filter by transaction type |
| `barcode=<barcode>` | Filter by product barcode |
| `search=<term>` | Search by product name |

#### Response (200 OK)
```json
[
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
```

---

### Transaction Stats
`GET /api/v1/transactions/stats/`

#### Response (200 OK)
```json
{
  "total_transactions": 200,
  "today_transactions": 15,
  "by_type": {
    "Receive": { "total_count": 120, "today_count": 10, "today_total_quantity": 85 },
    "Sale":    { "total_count": 80,  "today_count": 5,  "today_total_quantity": 22 }
  }
}
```

---

### Export Transactions
`GET /api/v1/transactions/export/`

Returns a `.csv` file (one row per item) for a given day.

#### Query Parameters
| Param | Format | Default | Description |
|-------|--------|---------|-------------|
| `date` | `YYYY-MM-DD` | today | Day to export |
| `type` | `Receive` \| `Sale` | — (both) | Filter by type |

**CSV columns:** `transaction_id`, `transaction_type`, `transaction_date`, `performed_by`, `product_name`, `barcode`, `site`, `location`, `quantity`, `cost_per_unit`, `line_total`

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400 Bad Request` | Invalid date format | `{ "detail": "Invalid date format. Use YYYY-MM-DD." }` |
| `400 Bad Request` | Invalid type | `{ "detail": "Invalid type. Use Receive or Sale." }` |

---

### Create Transaction
`POST /api/v1/transactions/`

- `transaction_type` applies to all items — no mixing
- Use **positive** quantity for `Receive`, **negative** for `Sale`
- `cost_per_unit` is auto-snapshotted from the product — do not send it
- `performed_by` is auto-assigned from the JWT token

#### Payload
```json
{
  "transaction_type": "Receive",
  "items": [
    { "inventory": 1, "quantity": 10 },
    { "inventory": 3, "quantity": 5 }
  ]
}
```

#### Response (201 Created)
```json
{
  "id": 1,
  "transaction_type": "Receive",
  "performed_by": 2,
  "performed_by_username": "staff_user",
  "total_transaction_value": "262.50",
  "items": [
    { "id": 1, "inventory": 1, "product_name": "Zinc Bolt M8", "quantity": 10, "cost_per_unit": "14.00", "line_total": "140.00" },
    { "id": 2, "inventory": 3, "product_name": "Hex Nut M8",   "quantity": 5,  "cost_per_unit": "8.50",  "line_total": "42.50" }
  ],
  "transaction_date": "2026-03-26T10:00:00Z"
}
```

#### Validation Errors
| Scenario | Response |
|----------|----------|
| No items | `{ "items": "At least one item is required." }` |
| Invalid type | `{ "transaction_type": "Must be Receive or Sale." }` |
| Sale qty positive | `{ "items": [{ "item": 1, "quantity": "Sale quantities must be negative." }] }` |
| Insufficient stock | `{ "items": [{ "item": 1, "quantity": "Insufficient stock. Current balance is only 4 units." }] }` |

---

### Scan Transaction (Single Item via Barcode)
`POST /api/v1/transactions/scan/`

#### Payload
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
| `inventory_id` | Conditional | Required only if the product has multiple inventory records |

#### Response (201 Created)
Same shape as `POST /api/v1/transactions/` with one item in `items`.

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400` | Missing field | `{ "barcode": "This field is required." }` |
| `404` | Barcode not found | `{ "detail": "No product found with this barcode." }` |
| `404` | No inventory record | `{ "detail": "Product found but has no inventory record.", "product": "Zinc Bolt M8" }` |
| `400` | Multiple records, no `inventory_id` | `{ "detail": "Multiple inventory records found. Please specify inventory_id.", "inventory": [...] }` |
| `400` | Wrong `inventory_id` | `{ "detail": "The specified inventory_id does not belong to this product." }` |

---

## 7. Dashboard Stats

Aggregate stats scoped to a date range.

- **Endpoint:** `GET /api/v1/dashboard/stats/`
- **Auth required:** Yes

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `range` | string | `today` | Date range label (see table below) |
| `start` | `YYYY-MM-DD` | — | Required when `range=custom` |
| `end` | `YYYY-MM-DD` | — | Required when `range=custom` |

| `range` value | Window |
|---------------|--------|
| `today` | Midnight → end of today |
| `7_days` | Last 7 days including today |
| `14_days` | Last 14 days including today |
| `30_days` | Last 30 days including today |
| `3_months` | Last 90 days including today |
| `12_months` | Last 365 days including today |
| `all_time` | No date filter |
| `custom` | Requires `start` and `end` |

**Examples**
```
GET /api/v1/dashboard/stats/
GET /api/v1/dashboard/stats/?range=7_days
GET /api/v1/dashboard/stats/?range=custom&start=2026-01-01&end=2026-03-31
```

### Response (200 OK)
```json
{
  "range": {
    "label": "7_days",
    "start": "2026-04-15T00:00:00+07:00",
    "end": "2026-04-21T23:59:59.999999+07:00"
  },
  "products": {
    "total": 12,
    "by_category": [
      { "category": "Fasteners", "count": 8 },
      { "category": "Accessories", "count": 4 }
    ],
    "low_stock": 3,
    "out_of_stock": 1
  },
  "inventory": {
    "total_records": 42,
    "total_quantity": 12500,
    "total_stock_value": "13250.00",
    "needs_reorder": 5,
    "by_site": [
      { "site": "Warehouse A", "records": 25, "total_quantity": 8000, "total_stock_value": "8500.00" }
    ]
  },
  "transactions": {
    "total": 38,
    "by_type": {
      "Receive": { "count": 24, "total_quantity": 480 },
      "Sale":    { "count": 14, "total_quantity": 120 }
    },
    "recent_activity": [
      {
        "id": 101,
        "transaction_type": "Sale",
        "transaction_date": "2026-04-21T09:15:00Z",
        "performed_by": "staff_user",
        "item_count": 2,
        "total_quantity": 15
      }
    ]
  }
}
```

> - For `all_time`, `range.start` and `range.end` are `null` — guard before formatting.
> - `total_stock_value` is a string — parse with `parseFloat()` before arithmetic.
> - `by_type` may be missing a key if no transactions of that type exist — always default: `stats.by_type?.Sale ?? { count: 0, total_quantity: 0 }`.
> - `recent_activity` is limited to 10 — no pagination needed.

### Error Responses
| Status | Scenario | Response |
|--------|----------|----------|
| `400` | Unknown range | `{ "detail": "Invalid range. Valid options: ..." }` |
| `400` | Custom range missing/invalid dates | `{ "detail": "Invalid date format for custom range. Use YYYY-MM-DD for start and end." }` |
| `400` | `start` after `end` | `{ "detail": "start must be before or equal to end." }` |

---

## 8. Admin — User Management

Manage all users in the system. **Requires `is_staff`, `is_boss`, or `is_superuser`.**

- **Base Endpoint:** `/api/v1/admin/`

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/api/v1/admin/users/` | List all users | `200 OK` |
| `POST` | `/api/v1/admin/users/` | Create a user | `201 Created` |
| `GET` | `/api/v1/admin/users/{id}/` | Retrieve a user | `200 OK` |
| `PUT` | `/api/v1/admin/users/{id}/` | Full replace | `200 OK` |
| `PATCH` | `/api/v1/admin/users/{id}/` | Partial update | `200 OK` |
| `DELETE` | `/api/v1/admin/users/{id}/` | Delete a user | `204 No Content` |
| `GET` | `/api/v1/admin/users/{id}/logs/` | Activity logs for a user | `200 OK` |
| `GET` | `/api/v1/admin/logs/` | All activity logs | `200 OK` |
| `GET` | `/api/v1/admin/staff/` | List staff users | `200 OK` |
| `POST` | `/api/v1/admin/staff/` | Create staff/boss user | `201 Created` |
| `GET` | `/api/v1/admin/staff/{id}/` | Retrieve staff user | `200 OK` |
| `PUT` | `/api/v1/admin/staff/{id}/` | Replace staff user | `200 OK` |
| `PATCH` | `/api/v1/admin/staff/{id}/` | Update staff user | `200 OK` |
| `DELETE` | `/api/v1/admin/staff/{id}/` | Delete staff user | `204 No Content` |

> **Field restriction:** `is_superuser` is only writable by a superadmin. `is_staff` is writable by superadmins and bosses. Other roles' attempts to set these fields are silently ignored.

---

### List All Users
`GET /api/v1/admin/users/` — returns all users, newest first.

#### Response (200 OK)
```json
[
  {
    "id": 2,
    "username": "john_doe",
    "email": "john@example.com",
    "name": "John Doe",
    "is_boss": false,
    "is_staff": false,
    "is_superuser": false,
    "is_active": true,
    "date_joined": "2026-03-25T08:00:00Z",
    "last_login": "2026-04-20T09:30:00Z"
  }
]
```

---

### Create User
`POST /api/v1/admin/users/`

#### Payload
```json
{
  "username": "new_user",
  "email": "new@example.com",
  "name": "New User",
  "password": "secure_password",
  "is_boss": false,
  "is_active": true
}
```

| Field | Required | Writable by | Description |
|-------|----------|-------------|-------------|
| `username` | Yes | All | Unique login name |
| `email` | No | All | Email address |
| `name` | No | All | Display name |
| `password` | Yes | All | Write-only, never returned |
| `is_boss` | No | All | Grant boss-level rights |
| `is_active` | No | All | Set `false` to deactivate without deleting |
| `is_staff` | No | Superadmin only | Grant staff-level rights |
| `is_superuser` | No | Superadmin only | Grant full admin rights |

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400` | Username taken | `{ "username": ["A user with that username already exists."] }` |
| `400` | Password missing | `{ "password": ["This field is required."] }` |

---

### Staff Users
`GET /api/v1/admin/staff/` — returns all users where `is_staff=true` and `is_superuser=false`, ordered by username.

> Superusers are protected and cannot be modified via these endpoints.

#### Response (200 OK)
```json
[
  {
    "id": 3,
    "username": "jane_staff",
    "email": "jane@example.com",
    "name": "Jane Smith",
    "is_boss": false,
    "is_staff": true,
    "is_superuser": false
  }
]
```

---

### Activity Logs

`GET /api/v1/admin/users/{id}/logs/` — logs for a specific user, newest first.

`GET /api/v1/admin/logs/` — logs for all users, newest first.

#### Response (200 OK)
```json
[
  {
    "id": 12,
    "user": 2,
    "username": "john_doe",
    "action": "login",
    "timestamp": "2026-04-20T09:30:00Z",
    "ip_address": "192.168.1.10",
    "details": ""
  }
]
```

| Field | Description |
|-------|-------------|
| `action` | One of: `login`, `logout`, `register`, `profile_update`, `password_change`, `other` |
| `ip_address` | Client IP (supports `X-Forwarded-For` for proxied environments) |
| `details` | Free-text context (e.g. `"Created by admin john_doe"`) |
