from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Product
from .models import Inventory

User = get_user_model()


def make_product(n):
    return Product.objects.create(
        barcode=f"TEST-BARCODE-{n:04d}",
        product_name=f"Test Product {n}",
        supplier="Test Supplier",
        category="Fasteners",
        cost_per_unit="1.00",
        reorder_level=5,
    )


def make_inventory(product, n):
    return Inventory.objects.create(
        product=product,
        site=f"Site-{n}",
        location=f"Loc-{n}",
        quantity_on_hand=10,
    )


class InventoryListAllTest(APITestCase):
    """
    Verifies that the inventory list returns all records without pagination.
    """

    TOTAL = 30

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("tester", None, "t3st-u$er!")
        cls.products = [make_product(i) for i in range(1, cls.TOTAL + 1)]
        cls.records = [make_inventory(p, i) for i, p in enumerate(cls.products, 1)]

    def setUp(self):
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # --- response shape ---

    def test_response_shape(self):
        res = self.client.get("/api/v1/inventory/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("results", res.data)
        # Pagination keys must NOT be present
        self.assertNotIn("page_size", res.data)
        self.assertNotIn("next", res.data)
        self.assertNotIn("previous", res.data)

    def test_list_returns_all_by_default(self):
        """Should return all records regardless of any default limits."""
        res = self.client.get("/api/v1/inventory/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), self.TOTAL)
        self.assertEqual(res.data["count"], self.TOTAL)

    def test_page_size_param_is_ignored(self):
        """page_size query param should have no effect."""
        res = self.client.get("/api/v1/inventory/?page_size=5")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), self.TOTAL)

    # --- ordering ---

    def test_default_ordering_is_newest_first(self):
        """Records should be ordered by -updated_at (most recently updated first)."""
        res = self.client.get("/api/v1/inventory/")
        ids = [r["id"] for r in res.data["results"]]
        self.assertEqual(ids, sorted(ids, reverse=True))

    # --- filtering ---

    def test_filter_by_site(self):
        res = self.client.get("/api/v1/inventory/?site=Site-1")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # With Site-1, it could match Site-1, Site-10, Site-11...
        # But we check that it at least contains Site-1
        for record in res.data["results"]:
            self.assertIn("Site-1", record["site"])

    def test_filter_by_product_id(self):
        product = self.products[0]
        res = self.client.get(f"/api/v1/inventory/?product_id={product.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["product"], product.id)

    def test_search_by_product_name(self):
        res = self.client.get("/api/v1/inventory/?search=Test Product 1")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for record in res.data["results"]:
            # Test Product 1 matches 1, 10, 11, etc.
            self.assertIn("Test Product 1", record["product_details"]["product_name"])

    # --- sorting ---

    def test_sorting_by_quantity_on_hand(self):
        """Check if we can sort by quantity_on_hand."""
        all_records = list(Inventory.objects.all())
        for i, record in enumerate(all_records):
            record.quantity_on_hand = i * 10
            record.save()

        # Ascending
        res = self.client.get("/api/v1/inventory/?ordering=quantity_on_hand")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        quantities = [r["quantity_on_hand"] for r in res.data["results"]]
        self.assertEqual(quantities, sorted(quantities))

        # Descending
        res_desc = self.client.get("/api/v1/inventory/?ordering=-quantity_on_hand")
        self.assertEqual(res_desc.status_code, status.HTTP_200_OK)
        quantities_desc = [r["quantity_on_hand"] for r in res_desc.data["results"]]
        self.assertEqual(quantities_desc, sorted(quantities, reverse=True))

    # --- auth ---

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        res = self.client.get("/api/v1/inventory/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class InventoryIntegrityTest(APITestCase):
    """
    Verifies data integrity rules:
    1. Cannot delete product if it has inventory records (PROTECT).
    2. Cannot have negative quantity_on_hand (CheckConstraint).
    """

    def setUp(self):
        self.user = User.objects.create_user("integrator", None, "t3st-u$er!")
        self.product = make_product(1)
        self.inventory = make_inventory(self.product, 1)

    def test_product_deletion_is_protected(self):
        """Deleting a product should raise ProtectedError if inventory exists."""
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):
            self.product.delete()

    def test_negative_quantity_is_blocked_by_db(self):
        """Database should block saving an inventory record with negative quantity."""
        from django.db import IntegrityError
        self.inventory.quantity_on_hand = -10
        # save() triggers the DB constraint
        with self.assertRaises(IntegrityError):
            self.inventory.save()
