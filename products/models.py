from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Fasteners", "Fasteners"),
        ("Accessories", "Accessories"),
    ]

    id: int
    barcode: str = models.CharField(  # type: ignore[assignment]
        max_length=20,
        unique=True,
        db_collation='utf8mb4_bin',
        help_text="Physical barcode scanned from the product. Must be unique."
    )
    product_name: str = models.CharField(max_length=255, db_index=True)  # type: ignore[assignment]
    category: str = models.CharField(  # type: ignore[assignment]
        max_length=255, choices=CATEGORY_CHOICES, default="Fasteners", db_index=True
    )
    # Using DecimalField is correct for currency—never use FloatField!
    cost_per_unit: Decimal | None = models.DecimalField(  # type: ignore[assignment]
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reorder_level: int = models.PositiveIntegerField(default=5)  # type: ignore[assignment]
    supplier: str = models.CharField(max_length=255, db_index=True)  # type: ignore[assignment]
    product_picture: Any = models.ImageField(
        upload_to='products/images/',
        null=True,
        blank=True
    )

    created_at: datetime = models.DateTimeField(auto_now_add=True)  # type: ignore[assignment]
    updated_at: datetime = models.DateTimeField(auto_now=True)  # type: ignore[assignment]
    created_by: Any = models.ForeignKey(  # type: ignore[assignment]
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-id']

    def __str__(self) -> str:
        return f"#{self.id} - {self.product_name} ({self.barcode})"
