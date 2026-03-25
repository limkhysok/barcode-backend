from django.db import models
from django.conf import settings
import random
import string

def generate_barcode():
    """ Generate a random string like SN-XXXXXX (6 alphanumeric chars) """
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=6))
    return f"SN-{code}"

class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Fasteners", "Fasteners"),
        ("Accessories", "Accessories"),
    ]

    # Explicit productid — maps to the 'id' column in the database
    productid = models.BigAutoField(primary_key=True, db_column='id')

    # Barcode starting with SN-
    barcode = models.CharField(
        max_length=20, 
        unique=True, 
        default=generate_barcode,
        help_text="Barcode format: SN-XXXXXX (Randomly generated)"
    )
    product_name = models.CharField(max_length=255, null=False, blank=False)
    category = models.CharField(
        max_length=255, choices=CATEGORY_CHOICES, default="Fasteners"
    )
    cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reorder_level = models.IntegerField(default=5)
    supplier = models.CharField(max_length=255, null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"#{self.productid} - {self.product_name} ({self.barcode})"
