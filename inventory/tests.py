from django.contrib.auth import get_user_model
from django.urls import reverse
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


class InventoryListPageSizeTest(APITestCase):
    """
    Verifies that ?page_size correctly limits the number of returned records.
    Creates 30 unique inventory records so we can test 20 vs 30 vs all.
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
        self.assertIn("page_size", res.data)
        self.assertIn("results", res.data)
        # Old pagination keys must NOT be present
        self.assertNotIn("next", res.data)
        self.assertNotIn("previous", res.data)

    def test_count_reflects_total_not_limit(self):
        """count should always be the full total, not the slice size."""
        res = self.client.get("/api/v1/inventory/?page_size=20")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], self.TOTAL)

    # --- page_size limits ---

    def test_default_returns_20(self):
        res = self.client.get("/api/v1/inventory/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 20)
        self.assertEqual(res.data["page_size"], 20)

    def test_page_size_20(self):
        res = self.client.get("/api/v1/inventory/?page_size=20")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 20)
        self.assertEqual(res.data["page_size"], 20)

    def test_page_size_50_returns_all_when_total_less_than_50(self):
        """With only 30 records, page_size=50 should return all 30."""
        res = self.client.get("/api/v1/inventory/?page_size=50")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), self.TOTAL)

    def test_page_size_100_returns_all_when_total_less_than_100(self):
        """With only 30 records, page_size=100 should return all 30."""
        res = self.client.get("/api/v1/inventory/?page_size=100")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), self.TOTAL)

    def test_page_size_all(self):
        res = self.client.get("/api/v1/inventory/?page_size=all")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), self.TOTAL)
        self.assertEqual(res.data["page_size"], self.TOTAL)

    def test_invalid_page_size_falls_back_to_20(self):
        res = self.client.get("/api/v1/inventory/?page_size=999")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 20)

    def test_page_param_is_ignored(self):
        """page= should have no effect — backend no longer uses it."""
        res = self.client.get("/api/v1/inventory/?page=99&page_size=20")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 20)

    # --- ordering ---

    def test_default_ordering_is_newest_first(self):
        """Records should be ordered by -updated_at (most recently updated first)."""
        res = self.client.get("/api/v1/inventory/?page_size=all")
        ids = [r["id"] for r in res.data["results"]]
        self.assertEqual(ids, sorted(ids, reverse=True))

    # --- filtering ---

    def test_filter_by_site(self):
        res = self.client.get("/api/v1/inventory/?site=Site-1")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
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
            self.assertIn("Test Product 1", record["product_details"]["product_name"])

    # --- auth ---

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        res = self.client.get("/api/v1/inventory/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
