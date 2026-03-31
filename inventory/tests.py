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

    # --- sorting and page size consistency ---

    def test_sorting_and_page_size_consistency(self):
        """
        Verify that requesting page_size 20 and 50 maintains the same primary ordering
        and that the first 20 records of page_size 50 match those of page_size 20.
        """
        # Create 100 records to ensure we have enough for both 20 and 50
        # (We already have 30 from setUpTestData, let's add 70 more)
        extra_products = [make_product(i) for i in range(31, 101)]
        [make_inventory(p, i) for i, p in enumerate(extra_products, 31)]
        total_count = 100

        # 1. Test page_size=20
        res_20 = self.client.get("/api/v1/inventory/?page_size=20")
        self.assertEqual(res_20.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_20.data["results"]), 20)
        self.assertEqual(res_20.data["count"], total_count)
        ids_20 = [r["id"] for r in res_20.data["results"]]

        # 2. Test page_size=50
        res_50 = self.client.get("/api/v1/inventory/?page_size=50")
        self.assertEqual(res_50.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_50.data["results"]), 50)
        self.assertEqual(res_50.data["count"], total_count)
        ids_50 = [r["id"] for r in res_50.data["results"]]

        # 3. First 20 of 50 should match the 20 from page_size=20
        self.assertEqual(ids_20, ids_50[:20], "The first 20 items should be consistent regardless of page size.")

        # 4. Check ordering - by default it should be newest first (highest ID if sequential)
        self.assertEqual(ids_50, sorted(ids_50, reverse=True), "Results should be ordered by ID descending (newest first).")

    def test_sorting_by_other_fields(self):
        """
        Check if we can sort by other fields like quantity_on_hand.
        If not yet implemented, this test will fail.
        """
        # Update records to have unique quantities for sorting
        # We have 30 records from setup, plus 70 from previous test if they persist
        # (but they don't, as tests are isolated). 
        # Wait, setUpTestData runs once for the class. 
        # My previous test added records but they were deleted after the test? 
        # No, class-level data persists.
        
        all_records = list(Inventory.objects.all())
        for i, record in enumerate(all_records):
            record.quantity_on_hand = i * 10
            record.save()

        # Try to sort by quantity_on_hand (ascending)
        res = self.client.get("/api/v1/inventory/?page_size=50&ordering=quantity_on_hand")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        quantities = [r["quantity_on_hand"] for r in res.data["results"]]
        self.assertEqual(quantities, sorted(quantities), f"Expected sorted quantities, got {quantities}")

        # Try to sort by quantity_on_hand (descending)
        res_desc = self.client.get("/api/v1/inventory/?page_size=50&ordering=-quantity_on_hand")
        self.assertEqual(res_desc.status_code, status.HTTP_200_OK)
        quantities_desc = [r["quantity_on_hand"] for r in res_desc.data["results"]]
        self.assertEqual(quantities_desc, sorted(quantities, reverse=True), "Should be descending.")

    # --- auth ---

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        res = self.client.get("/api/v1/inventory/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
