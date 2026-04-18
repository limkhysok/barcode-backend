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
