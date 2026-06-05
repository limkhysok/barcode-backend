from __future__ import annotations

from datetime import date as date_cls, datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, DecimalField, IntegerField, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import Inventory
from products.models import Product
from transactions.models import Transaction, TransactionItem


VALID_RANGES = {"today", "7_days", "14_days", "30_days", "3_months", "12_months", "all_time", "custom"}


def _resolve_date_range(
    range_label: str | None,
    start_param: str | None,
    end_param: str | None,
) -> tuple[datetime | None, datetime | None, str]:
    """
    Return (range_start, range_end, resolved_label).

    Supported range_label values:
      today | 7_days | 14_days | 30_days | 3_months | 12_months | all_time | custom

    Returns (None, None, 'all_time') when no date filtering should apply.
    Returns (None, None, 'invalid_custom') when custom dates are missing/malformed.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1) - timedelta(microseconds=1)

    if range_label == "today":
        return today_start, today_end, "today"

    if range_label == "7_days":
        return today_start - timedelta(days=6), today_end, "7_days"

    if range_label == "14_days":
        return today_start - timedelta(days=13), today_end, "14_days"

    if range_label == "30_days":
        return today_start - timedelta(days=29), today_end, "30_days"

    if range_label == "3_months":
        return today_start - timedelta(days=89), today_end, "3_months"

    if range_label == "12_months":
        return today_start - timedelta(days=364), today_end, "12_months"

    if range_label == "all_time":
        return None, None, "all_time"

    if range_label == "custom":
        try:
            start = date_cls.fromisoformat(start_param or "")
            end = date_cls.fromisoformat(end_param or "")
        except (TypeError, ValueError):
            return None, None, "invalid_custom"
        # USE_TZ = False, so the DB stores naive datetimes — must not use make_aware()
        range_start = datetime(start.year, start.month, start.day, 0, 0, 0)
        range_end = datetime(end.year, end.month, end.day, 23, 59, 59, 999999)
        return range_start, range_end, "custom"

    # Unrecognised label → default to today
    return today_start, today_end, "today"


class DashboardStatsView(APIView):
    """
    GET /api/v1/dashboard/stats/

    Query params:
      - range : today | 7_days | 14_days | 30_days | 3_months | 12_months | all_time | custom
                (default: today)
      - start : YYYY-MM-DD  (required when range=custom)
      - end   : YYYY-MM-DD  (required when range=custom)

    All three data entities are scoped to the selected date range:
      - products     → created_at in range
      - inventory    → updated_at in range
      - transactions → transaction_date in range
    """

    def get(self, request: Request) -> Response:
        range_label: str | None = request.query_params.get("range", "today")
        start_param: str | None = request.query_params.get("start")
        end_param: str | None = request.query_params.get("end")

        if range_label not in VALID_RANGES:
            return Response(
                {"detail": f"Invalid range. Valid options: {', '.join(sorted(VALID_RANGES))}."},
                status=400,
            )

        range_start, range_end, resolved_label = _resolve_date_range(
            range_label, start_param, end_param
        )

        if resolved_label == "invalid_custom":
            return Response(
                {"detail": "Invalid date format for custom range. Use YYYY-MM-DD for start and end."},
                status=400,
            )

        if (
            resolved_label == "custom"
            and range_start is not None
            and range_end is not None
            and range_start > range_end
        ):
            return Response(
                {"detail": "start must be before or equal to end."},
                status=400,
            )

        # Cache implementation
        cache_key = f"dashboard_stats_{resolved_label}_{start_param}_{end_param}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        response_data: dict[str, Any] = {
            "range": {
                "label": resolved_label,
                "start": range_start.isoformat() if range_start else None,
                "end": range_end.isoformat() if range_end else None,
            },
            "products": self._product_stats(range_start, range_end),
            "inventory": self._inventory_stats(range_start, range_end),
            "transactions": self._transaction_stats(range_start, range_end),
        }

        # Cache for 5 minutes
        cache.set(cache_key, response_data, 300)

        return Response(response_data)

    # ── Products (scoped by created_at) ──────────────────────────────────────

    def _product_stats(
        self, range_start: datetime | None, range_end: datetime | None
    ) -> dict[str, Any]:
        qs = Product.objects.all()
        if range_start is not None:
            qs = qs.filter(created_at__gte=range_start, created_at__lte=range_end)

        total_in_range = qs.count()

        by_category: list[dict[str, Any]] = list(  # type: ignore[assignment]
            qs.values("category")
            .annotate(count=Count("id"))
            .order_by("category")
        )

        # Low-stock / out-of-stock: inventory records belonging to products in the range
        product_ids = qs.values_list("id", flat=True)
        low_stock = Inventory.objects.filter(
            product_id__in=product_ids,
            reorder_status__in=["LOW", "NO STOCK"],
        ).count()
        out_of_stock = Inventory.objects.filter(
            product_id__in=product_ids,
            quantity_on_hand=0,
        ).count()

        return {
            "total": total_in_range,
            "by_category": by_category,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
        }

    # ── Inventory (scoped by updated_at) ─────────────────────────────────────

    def _inventory_stats(
        self, range_start: datetime | None, range_end: datetime | None
    ) -> dict[str, Any]:
        qs = Inventory.objects.all()
        if range_start is not None:
            qs = qs.filter(updated_at__gte=range_start, updated_at__lte=range_end)

        totals: dict[str, Any] = qs.aggregate(  # type: ignore[assignment]
            total_records=Count("id"),
            total_quantity=Coalesce(Sum("quantity_on_hand"), 0, output_field=IntegerField()),
            total_stock_value=Coalesce(
                Sum("stock_value"), Decimal("0"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            needs_reorder=Count("id", filter=Q(reorder_status__in=["LOW", "NO STOCK"])),
        )

        by_site: list[dict[str, Any]] = list(  # type: ignore[assignment]
            qs.values("site")
            .annotate(
                records=Count("id"),
                total_quantity=Coalesce(Sum("quantity_on_hand"), 0, output_field=IntegerField()),
                total_stock_value=Coalesce(
                    Sum("stock_value"), Decimal("0"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            )
            .order_by("site")
        )

        return {
            "total_records": totals["total_records"],
            "total_quantity": totals["total_quantity"],
            "total_stock_value": str(totals["total_stock_value"]),
            "needs_reorder": totals["needs_reorder"],
            "by_site": [
                {
                    "site": row["site"],
                    "records": row["records"],
                    "total_quantity": row["total_quantity"],
                    "total_stock_value": str(row["total_stock_value"]),
                }
                for row in by_site
            ],
        }

    # ── Transactions (scoped by transaction_date) ─────────────────────────────

    def _transaction_stats(
        self, range_start: datetime | None, range_end: datetime | None
    ) -> dict[str, Any]:
        range_qs = Transaction.objects.all()
        if range_start is not None:
            range_qs = range_qs.filter(
                transaction_date__gte=range_start,
                transaction_date__lte=range_end,
            )

        by_type_rows: list[dict[str, Any]] = list(  # type: ignore[assignment]
            range_qs.values("transaction_type")
            .annotate(
                count=Count("id"),
                total_quantity=Coalesce(Sum("items__quantity"), 0, output_field=IntegerField()),
            )
            .order_by("transaction_type")
        )

        by_type: dict[str, dict[str, Any]] = {}
        total_in_range = 0
        for row in by_type_rows:
            txn_type: str = row["transaction_type"]
            qty: int = row["total_quantity"]
            if txn_type == "Sale":
                qty = abs(qty)
            by_type[txn_type] = {
                "count": row["count"],
                "total_quantity": qty,
            }
            total_in_range += row["count"]

        recent_qs = (
            range_qs
            .select_related("performed_by")
            .prefetch_related("items")
            .order_by("-transaction_date", "-id")[:10]
        )

        recent_activity: list[dict[str, Any]] = []
        for txn in recent_qs:
            # list() hits the prefetch cache instead of firing a COUNT query per row
            txn_items: list[TransactionItem] = list(txn.items.all())  # type: ignore[attr-defined, assignment]
            recent_activity.append({
                "id": txn.id,
                "transaction_type": txn.transaction_type,
                "transaction_date": txn.transaction_date.isoformat(),
                "performed_by": txn.performed_by.get_username() if txn.performed_by else None,
                "item_count": len(txn_items),
                "total_quantity": abs(sum(item.quantity for item in txn_items)),
            })

        return {
            "total": total_in_range,
            "by_type": by_type,
            "recent_activity": recent_activity,
        }
