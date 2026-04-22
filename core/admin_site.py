from django.contrib.admin import AdminSite
from django.utils import timezone
from datetime import timedelta


class BarcodeAdminSite(AdminSite):
    site_header = "Barcode Admin"
    site_title = "Barcode Admin"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):
        from users.models import User, UserActivity
        from products.models import Product
        from inventory.models import Inventory
        from transactions.models import Transaction
        from django.contrib.admin.models import LogEntry
        from django.contrib.sessions.models import Session
        from django.db.models import Sum, Count

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        stats = {
            # Users
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "boss_users": User.objects.filter(is_boss=True).count(),
            "new_users_week": User.objects.filter(date_joined__gte=week_ago).count(),
            # Products
            "total_products": Product.objects.count(),
            # Inventory
            "total_inventory": Inventory.objects.count(),
            "low_stock": Inventory.objects.filter(reorder_status__in=["LOW", "NO STOCK"]).count(),
            "reorder_needed": Inventory.objects.filter(reorder_status="Yes").count(),
            "total_stock_value": Inventory.objects.aggregate(t=Sum("stock_value"))["t"] or 0,
            # Transactions
            "total_transactions": Transaction.objects.count(),
            "transactions_today": Transaction.objects.filter(transaction_date__date=now.date()).count(),
            "transactions_week": Transaction.objects.filter(transaction_date__gte=week_ago).count(),
            "sales_count": Transaction.objects.filter(transaction_type="Sale").count(),
            "receive_count": Transaction.objects.filter(transaction_type="Receive").count(),
            # Activity
            "active_sessions": Session.objects.filter(expire_date__gte=now).count(),
            "admin_actions_week": LogEntry.objects.filter(action_time__gte=week_ago).count(),
            "activity_logs_week": UserActivity.objects.filter(timestamp__gte=week_ago).count(),
        }

        recent_logs = (
            LogEntry.objects.select_related("user", "content_type")
            .order_by("-action_time")[:8]
        )

        recent_activity = (
            UserActivity.objects.select_related("user")
            .order_by("-timestamp")[:8]
        )

        low_stock_items = (
            Inventory.objects.select_related("product")
            .filter(reorder_status__in=["LOW", "NO STOCK", "Yes"])
            .order_by("quantity_on_hand")[:8]
        )

        extra_context = extra_context or {}
        extra_context.update({
            "stats": stats,
            "recent_logs": recent_logs,
            "recent_activity": recent_activity,
            "low_stock_items": low_stock_items,
        })
        return super().index(request, extra_context)


admin_site = BarcodeAdminSite(name="admin")
