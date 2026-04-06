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
  - `GET /api/v1/products/stats/` — Overview stats (not paginated) → `200 OK`
  - `GET /api/v1/products/{id}/` — Retrieve a product → `200 OK`
  - `POST /api/v1/products/` — Create a new product → `201 Created`
  - `PUT /api/v1/products/{id}/` — Full replace of a product → `200 OK`
  - `PATCH /api/v1/products/{id}/` — Partial update of a product → `200 OK`
  - `DELETE /api/v1/products/{id}/` — Delete a product → `204 No Content`

> **Note:** The `{id}` in the URL is the product's `id` field (the primary key in the database and in API responses).

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

---

### List Products (GET)
`GET /api/v1/products/` — returns page 1 by default (20 rows per page).

#### Query Parameters

**List Limit**
| Param | Options | Default |
|-------|---------|---------|
| `page_size` | `20`, `40`, `100`, `200` | `20` (Max 200) |

> Control the number of results returned in a single list using the `page_size` parameter.

**Search**
| Param | Searches across |
|-------|----------------|
| `search=<term>` | `barcode`, `product_name`, `supplier` (case-insensitive, partial match) |

**Filter**
| Param | Options |
|-------|---------|
| `category=<name>` | `Fasteners`, `Accessories` |

**Ordering**
| Param | Description |
|-------|-------------|
| `ordering=product_name` | Product name — A to Z |
| `ordering=-product_name` | Product name — Z to A |
| `ordering=supplier` | Supplier — A to Z |
| `ordering=-supplier` | Supplier — Z to A |
| `ordering=cost_per_unit` | Cost per unit — Low to High |
| `ordering=-cost_per_unit` | Cost per unit — High to Low |
| `ordering=reorder_level` | Reorder level — Low to High |
| `ordering=-reorder_level` | Reorder level — High to Low |
| `ordering=created_at` | Oldest first |
| `ordering=-created_at` | Newest first |

**Examples**
```
GET /api/v1/products/?page_size=50
GET /api/v1/products/?search=bolt
GET /api/v1/products/?search=CTK&category=Fasteners
GET /api/v1/products/?category=Fasteners&ordering=cost_per_unit
GET /api/v1/products/?category=Accessories&ordering=-reorder_level&page_size=all
```

#### Response (200 OK)
```json
{
  "count": 85,
  "next": "http://localhost:8000/api/v1/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "barcode": "4006381333931",
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

---

### Product Stats (GET)
`GET /api/v1/products/stats/` — returns aggregate overview for the dashboard. Not paginated.

#### Response (200 OK)
```json
{
  "total_products": 85,
  "total_value": "13250.00",
  "by_category": {
    "Fasteners": {
      "count": 60,
      "total_value": "9800.00"
    },
    "Accessories": {
      "count": 25,
      "total_value": "3450.00"
    }
  }
}
```

| Field | Description |
|-------|-------------|
| `total_products` | Total number of products in the system |
| `total_value` | Sum of `cost_per_unit` across all products |
| `by_category.*.count` | Number of products in that category |
| `by_category.*.total_value` | Sum of `cost_per_unit` for products in that category |

---

### Create Product (POST)
`POST /api/v1/products/`

`barcode` is the **physical barcode scanned from the product** — it is required and must be unique. It cannot be changed after creation.

```json
{
  "barcode": "4006381333931",
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
  "barcode": "4006381333931",
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
| `400 Bad Request` | `barcode` missing | `{ "barcode": ["This field is required."] }` |
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
`PUT /api/v1/products/{id}/` — full replace (all fields required except `barcode`)
`PATCH /api/v1/products/{id}/` — partial update (only send fields to change)

> `barcode` is **read-only after creation** — it is silently ignored if included in the request body.

#### PUT Payload
```json
{
  "product_name": "Zinc Bolt M8 Updated",
  "category": "Fasteners",
  "cost_per_unit": 0.75,
  "reorder_level": 150,
  "supplier": "New Supplier Ltd"
}
```

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
| `409 Conflict` | Has linked inventory/transactions | `{ "detail": "Cannot delete product with existing inventory records or transactions." }` |
| `404 Not Found` | Product not found | `{ "detail": "No Product matches the given query." }` |

---

## 6. Inventory Management

Track stock levels across sites and locations. **All endpoints require authentication with a JWT access token.**

- **Base Endpoint:** `/api/v1/inventory/`
- **Methods:**
  - `GET /api/v1/inventory/` — List all inventory records (paginated) → `200 OK`
  - `GET /api/v1/inventory/stats/` — Overview stats (not paginated) → `200 OK`
  - `GET /api/v1/inventory/{id}/` — Retrieve a single record → `200 OK`
  - `POST /api/v1/inventory/` — Create a new inventory record → `201 Created`
  - `PUT /api/v1/inventory/{id}/` — Full replace of a record → `200 OK`
  - `PATCH /api/v1/inventory/{id}/` — Partial update of a record → `200 OK`
  - `DELETE /api/v1/inventory/{id}/` — Delete a record → `204 No Content`

> **Note:** `stock_value` and `reorder_status` are **read-only** — they are auto-calculated whenever `quantity_on_hand` changes via a transaction. Do not send them in POST/PUT/PATCH requests.

> **Uniqueness:** Each combination of `product` + `site` + `location` must be unique. Attempting to create a duplicate returns `400 Bad Request`.

### Authentication Required
```
Authorization: Bearer <access_token>
```

#### Example using curl:
```
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/inventory/
```

---

### Inventory Stats (GET)
`GET /api/v1/inventory/stats/` — returns aggregate overview + time-based activity for charts. Not paginated.

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
    },
    "Warehouse B": {
      "records": 17,
      "total_quantity_on_hand": 4500,
      "total_stock_value": "4750.00"
    }
  },
  "activity": {
    "last_7_days": {
      "data": [
        { "date": "2026-03-25", "new_records": 3 },
        { "date": "2026-03-27", "new_records": 1 }
      ]
    },
    "last_14_days": {
      "data": [
        { "date": "2026-03-18", "new_records": 5 },
        { "date": "2026-03-25", "new_records": 3 }
      ]
    },
    "last_30_days": {
      "data": [
        { "date": "2026-03-01", "new_records": 8 },
        { "date": "2026-03-15", "new_records": 4 }
      ]
    },
    "last_3_months": {
      "data": [
        { "week_start": "2026-01-05", "new_records": 12 },
        { "week_start": "2026-01-12", "new_records": 7 }
      ]
    }
  }
}
```

| Field | Description |
|-------|-------------|
| `total_records` | Total number of inventory records |
| `total_quantity_on_hand` | Sum of all stock quantities across all sites |
| `total_stock_value` | Sum of all `stock_value` across all records |
| `needs_reorder` | Count of records where `reorder_status = "Yes"` |
| `by_site.*.records` | Number of inventory records at that site |
| `by_site.*.total_quantity_on_hand` | Total stock quantity at that site |
| `by_site.*.total_stock_value` | Total stock value at that site |
| `activity.last_7_days.data` | Daily new inventory records — last 7 days |
| `activity.last_14_days.data` | Daily new inventory records — last 14 days |
| `activity.last_30_days.data` | Daily new inventory records — last 30 days |
| `activity.last_3_months.data` | Weekly new inventory records — last 90 days (`week_start` = Monday) |

> **Chart note:** Only dates/weeks with activity are included — days with zero new records are omitted. Fill missing dates with `0` on the frontend before rendering.

---

### List Inventory (GET)
`GET /api/v1/inventory/` — returns the most recently updated records first, limited to `page_size` (default 20). No page navigation — increase `page_size` to fetch more.

#### Query Parameters
| Param | Options | Description |
|-------|---------|-------------|
| `page_size=<n>` | `20`, `50`, `100`, `200`, `500`, `1000`, `all` | Max records to return |
| `ordering=<field>`| `product_name`, `site`, `location`, `reorder_status`, `updated_at`, `quantity_on_hand` | Sort results. Use `-` prefix for Z-A or oldest first. |
| `product_id=<id>` | — | Filter by product ID |
| `site=<name>` | `SITE A`, `SITE B`, `SITE C`, `SITE D` | Filter by exact site |
| `reorder_status=<val>`| `Yes`, `No` | Filter by reorder status |
| `search=<term>` | — | Search logic: partial product name |

**Examples**
```
GET /api/v1/inventory/?ordering=product_name
GET /api/v1/inventory/?ordering=-updated_at&site=SITE+A
GET /api/v1/inventory/?reorder_status=Yes&ordering=location
GET /api/v1/inventory/?page_size=50&ordering=-quantity_on_hand
```

#### Response (200 OK)
```json
{
  "count": 42,
  "page_size": 20,
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

| Field | Description |
|-------|-------------|
| `count` | Total matching records in the database (before the limit) |
| `page_size` | Number of records actually returned |
| `results` | Array of inventory records |

---

### Create Inventory Record (POST)
`POST /api/v1/inventory/`

Only send the writable fields — `stock_value` and `reorder_status` are calculated automatically.

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
| `product` | Yes | Product ID (foreign key) |
| `site` | Yes | Site name (e.g. "Warehouse A") |
| `location` | Yes | Location within the site (e.g. "A1-Shelf-5") |
| `quantity_on_hand` | No | Starting quantity — defaults to `0`, must be ≥ 0 |

#### Success (201 Created)
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

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400 Bad Request` | `product`, `site`, or `location` missing | `{ "field": ["This field is required."] }` |
| `400 Bad Request` | `quantity_on_hand` is negative (API level) | `{ "quantity_on_hand": ["Ensure this value is greater than or equal to 0."] }` |
| `500 Server Error` | `quantity_on_hand` is negative (DB level) | `{ "detail": "Database integrity error: quantity cannot be negative." }` |
| `400 Bad Request` | Duplicate `product` + `site` + `location` | `{ "non_field_errors": ["The fields product, site, location must make a unique set."] }` |

---

### Retrieve Inventory Record (GET)
`GET /api/v1/inventory/{id}/`

#### Errors
| Status | Response |
|--------|----------|
| `404 Not Found` | `{ "detail": "No Inventory matches the given query." }` |

---

### Update Inventory Record (PUT / PATCH)
`PUT /api/v1/inventory/{id}/` — full replace (all writable fields required)
`PATCH /api/v1/inventory/{id}/` — partial update (only send fields to change)

> `stock_value` and `reorder_status` are ignored if included — they are always recalculated from transactions.

#### PATCH Payload Example
```json
{
  "location": "B2-Shelf-3"
}
```

#### Errors
| Status | Scenario | Response |
|--------|----------|----------|
| `400 Bad Request` | Duplicate `product` + `site` + `location` | `{ "non_field_errors": ["The fields product, site, location must make a unique set."] }` |
| `404 Not Found` | Record not found | `{ "detail": "No Inventory matches the given query." }` |

---

### Delete Inventory Record (DELETE)
`DELETE /api/v1/inventory/{id}/`

#### Success (204 No Content) — empty body

#### Errors
| Status | Response |
|--------|----------|
| `404 Not Found` | `{ "detail": "No Inventory matches the given query." }` |

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
1. Scan barcode → `GET /api/v1/inventory/scan/?barcode=<scanned_value>`
2. If `found: true` → show inventory list, user picks a site/location
3. If `found: false` with product → show "item not in inventory"
4. If 404 → show "unknown barcode"
5. User confirms quantity + type → `POST /api/v1/transactions/scan/` (for single item) or `POST /api/v1/transactions/` (for bulk)

---

## 8. Transactions (Stock In / Out)
Log stock movements. A single transaction has **one type** (`Receive` or `Sale`) and can contain **multiple items** across different inventory records. Creating a transaction automatically updates all linked inventory balances.

- **Base Endpoint:** `/api/v1/transactions/`
- **Methods:**
  - `GET /api/v1/transactions/` — List all transactions (no pagination)
  - `GET /api/v1/transactions/stats/` — Overview stats (not paginated) → `200 OK`
  - `POST /api/v1/transactions/` — Create a new transaction with items
  - `POST /api/v1/transactions/scan/` — Quick create single-item transaction by barcode scan
  - `GET /api/v1/transactions/<id>/` — Retrieve a transaction by id
  - `PUT /api/v1/transactions/<id>/` — Replace a transaction by id
  - `PATCH /api/v1/transactions/<id>/` — Update part of a transaction by id
  - `DELETE /api/v1/transactions/<id>/` — Delete a transaction by id

### Transaction Stats (GET)
`GET /api/v1/transactions/stats/` — returns aggregate overview for the dashboard. Not paginated.

#### Response (200 OK)
```json
{
  "total_transactions": 200,
  "today_transactions": 15,
  "by_type": {
    "Receive": {
      "total_count": 120,
      "today_count": 10
    },
    "Sale": {
      "total_count": 80,
      "today_count": 5
    }
  }
}
```

| Field | Description |
|-------|-------------|
| `total_transactions` | Total number of transactions (all time) |
| `today_transactions` | Number of transactions created today |
| `by_type.*.total_count` | Total number of transactions of that type (all time) |
| `by_type.*.today_count` | Number of transactions of that type created today |

---

### List Transactions (GET)
`GET /api/v1/transactions/` — returns all transactions with no limit.

#### Query Parameters
| Param | Options | Default |
|-------|---------|---------|
| `type` | `Receive`, `Sale` | — |
| `barcode` | string | Filter by product barcode |
| `search` | string | Search by product name |

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

