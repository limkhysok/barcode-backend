# Frontend Integration Update — Inventory & Products API

Several backend fixes have been applied to the `/api/v1/inventory/` endpoints.
Read this before touching any inventory-related UI code.

---

## 1. `reorder_status` — Three Possible Values (was broken, now fixed)

The `reorder_status` field on every inventory record can be **one of three exact string values**:

| Value | Meaning | When |
|-------|---------|------|
| `"No"` | Stock is healthy | `quantity_on_hand > reorder_level` |
| `"LOW"` | Stock is low | `0 < quantity_on_hand <= reorder_level` |
| `"NO STOCK"` | Out of stock | `quantity_on_hand === 0` |

**What changed:** The backend was previously filtering `needs_reorder` using an old value `"Yes"` that no longer exists — so `stats.needs_reorder` was always `0`. This is now fixed.

**Frontend action required:**
- Any badge, chip, tag, or row colour that checks `reorder_status` must handle all three values.
- Do **not** use `=== "Yes"` anywhere — remove it if it exists.
- Suggested mapping:

```ts
const STATUS_COLOR = {
  'No':       'green',
  'LOW':      'orange',
  'NO STOCK': 'red',
};
```

---

## 2. `stats.needs_reorder` — Now Returns Real Count

`GET /api/v1/inventory/stats/` → `needs_reorder`

This now correctly counts records where `reorder_status` is `"LOW"` **or** `"NO STOCK"`.
Previously it always returned `0`. Your dashboard card for "Needs Reorder" should now show
a real number.

---

## 3. `stock_value` and `reorder_status` — Now Auto-Updated on Direct Inventory Writes

Previously these fields were only recalculated when a **transaction** was posted.
Now they are also recalculated immediately when:
- A new inventory record is created via `POST /api/v1/inventory/`
- An existing record is updated via `PUT` or `PATCH /api/v1/inventory/{id}/`

**Frontend action required:** None — the API response already returns the updated values.
Just make sure you read `stock_value` and `reorder_status` from the response body after
a create or update, and update your local state accordingly.

---

## 4. Duplicate Inventory Record — Error Code Changed (400 → 409)

`POST /api/v1/inventory/` with a duplicate `product` + `site` + `location` combination
now returns **`409 Conflict`** instead of `400 Bad Request`.

**Response body:**
```json
{ "detail": "An inventory record for this product, site, and location already exists." }
```

**Frontend action required:** If you handle duplicate errors on the inventory create form,
update your error check from `status === 400` to `status === 409` for this specific case.

---

## 5. No Changes to These Endpoints

The following are **unchanged** — no frontend work needed:
- `GET /api/v1/inventory/` (list)
- `GET /api/v1/inventory/{id}/` (retrieve)
- `DELETE /api/v1/inventory/{id}/`
- `GET /api/v1/inventory/scan/`
- All `/api/v1/products/` endpoints
- All `/api/v1/transactions/` endpoints

---

## Quick Checklist

- [ ] Replace any `reorder_status === "Yes"` checks with `!== "No"` or explicit `"LOW"` / `"NO STOCK"` checks
- [ ] Dashboard "Needs Reorder" card reads from `stats.needs_reorder` (now correct)
- [ ] Inventory create error handler updated: `400` → `409` for duplicate conflict
- [ ] Colour/badge map covers all three `reorder_status` values

---

# Frontend Integration Update — Boss Dashboard: Staff Users

A new endpoint has been added that allows boss-role users to view all staff users in the system. Read this before building any boss-specific dashboard UI.

---

## New Endpoint

```
GET /api/v1/users/boss/staff-users/
Authorization: Bearer <access_token>
```

- Returns a flat array (no pagination) of staff users sorted by username.
- Only callable by users where `is_boss: true` (decoded from the JWT).
- Returns `403` for any other role — guard the route before calling this.

---

## Response Shape

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

Superadmins (`is_superuser: true`) and other bosses (`is_boss: true`) are **excluded** — this list contains only pure staff accounts.

---

## How to Gate This in the Frontend

Read the role flags from the decoded JWT access token (already available from login):

```ts
import { jwtDecode } from 'jwt-decode';

const token = jwtDecode(accessToken);
const isBoss = token.is_boss === true;
```

Only render the Boss Dashboard route / nav item when `isBoss` is `true`. Do not rely on the API returning `403` to hide UI — check the token first.

```ts
// Before calling the endpoint
if (!isBoss) return; // skip entirely

const res = await fetch('/api/v1/users/boss/staff-users/', {
  headers: { Authorization: `Bearer ${accessToken}` },
});
const staffUsers = await res.json(); // array of user objects
```

---

## What to Build

Add a **Staff Users** section to the Boss Dashboard page:

| UI Element | Detail |
|------------|--------|
| Page / route | `/dashboard/boss/staff` or a tab inside the boss dashboard |
| Nav item | Visible only when `is_boss: true` |
| Table columns | Name, Username, Email, Status (active/inactive if needed) |
| Empty state | "No staff users found." |
| Error state | Show a message on `403` — should not happen if the gate is correct |

The list is **read-only** — this endpoint does not support creating or editing users. If the boss needs to create/edit staff, that goes through `POST /api/v1/users/admin/users/` (which bosses also have access to).

---

## Quick Checklist

- [ ] Decode JWT on login and store `is_boss` in auth state alongside `is_staff` and `is_superuser`
- [ ] Boss Dashboard nav item / route is conditionally rendered based on `is_boss`
- [ ] `GET /api/v1/users/boss/staff-users/` is called only when `is_boss === true`
- [ ] Staff list table renders `id`, `username`, `email`, `name`
- [ ] Empty state handled (empty array `[]`)
- [ ] `403` error handled gracefully (should not be reachable if gating is correct)
