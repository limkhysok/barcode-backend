# 1 Minor Code Issues

1. Duplicate URL registrations in core/urls.py lines 33–36 — both inventory/ and inventory are registered separately (and same for transactions). This is redundant since APPEND_SLASH=False is set. //done

2. Redundant id = models.BigAutoField() in products/models.py — Django adds this automatically. //done

3. No DB-level constraints for transaction integrity — relies entirely on application logic in the serializer's validate(). //done

# 2 Design / Architecture
1. No pagination — list endpoints (/api/products, /api/inventory, /api/transactions) can return unbounded results. Add DEFAULT_PAGINATION_CLASS in settings. // done

2. No role-based permissions — all authenticated users have full CRUD access everywhere. No admin/staff/read-only distinction.

3. No rate limiting — add DEFAULT_THROTTLE_CLASSES in DRF settings.

4. No tests — zero test files in the project.

5. No logging — errors and transactions aren't logged.

6. No soft deletes — deleted records are unrecoverable; no audit trail.




# 3 URL Routing Note

The scan custom action in both inventory and transactions apps uses url_path='scan'. Because DefaultRouter(trailing_slash=False) is used, the route /api/inventory/scan works, but it must be registered before <id> routes or it will be interpreted as a detail lookup. This currently works because routers handle custom actions before {pk} patterns, but worth being aware of.

# 4 Missing Features Worth Considering

1. Pagination (highest priority for scalability)

2. Permission classes per role (e.g., IsAdminUser for delete/create)

3. Filtering/ordering via django-filter — currently only manual request.query_params filtering

4. Transaction reversal — currently update() reverses effects, but no explicit "void transaction" concept

5. Unit/integration tests

6. API versioning (e.g., /api/v1/)