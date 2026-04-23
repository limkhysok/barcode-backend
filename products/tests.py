from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Product
from inventory.models import Inventory

User = get_user_model()
LIST_URL  = '/api/v1/products/'
STATS_URL = '/api/v1/products/stats/'


def make_token(user):
    return str(RefreshToken.for_user(user).access_token)


class ProductStatsTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token(self.user)}')

        self.fastener = Product.objects.create(
            barcode='B1', product_name='Bolt M8', category='Fasteners',
            cost_per_unit=Decimal('0.50'), reorder_level=10, supplier='CTK',
        )
        self.accessory = Product.objects.create(
            barcode='B2', product_name='Safety Gloves', category='Accessories',
            cost_per_unit=Decimal('5.00'), reorder_level=5, supplier='CTK',
        )

        # Fastener has 2 inventory records across 2 sites
        Inventory.objects.create(
            product=self.fastener, site='Warehouse A', location='A1',
            quantity_on_hand=100, stock_value=Decimal('50.00'),
        )
        Inventory.objects.create(
            product=self.fastener, site='Warehouse B', location='B1',
            quantity_on_hand=200, stock_value=Decimal('100.00'),
        )
        Inventory.objects.create(
            product=self.accessory, site='Warehouse A', location='A2',
            quantity_on_hand=50, stock_value=Decimal('250.00'),
        )

    # --- Auth ---

    def test_requires_authentication(self):
        self.client.credentials()
        res = self.client.get(STATS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Response shape ---

    def test_returns_expected_keys(self):
        res = self.client.get(STATS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_products', res.data)
        self.assertIn('total_value', res.data)
        self.assertIn('by_category', res.data)

    # --- total_products ---

    def test_total_products_counts_all(self):
        res = self.client.get(STATS_URL)
        self.assertEqual(res.data['total_products'], 2)

    def test_total_products_updates_when_product_added(self):
        Product.objects.create(
            barcode='B3', product_name='New Bolt', category='Fasteners',
            cost_per_unit=Decimal('1.00'), reorder_level=5, supplier='CTK',
        )
        res = self.client.get(STATS_URL)
        self.assertEqual(res.data['total_products'], 3)

    # --- total_value (sum of cost_per_unit across all products) ---

    def test_total_value_is_sum_of_all_product_cost_per_unit(self):
        res = self.client.get(STATS_URL)
        print(f"\n[stats] total_value = {res.data['total_value']}")
        # fastener(0.50) + accessory(5.00) = 5.50
        self.assertEqual(Decimal(str(res.data['total_value'])), Decimal('5.50'))

    def test_total_value_not_limited_to_one_page(self):
        for i in range(25):
            Product.objects.create(
                barcode=f'EXTRA-{i}', product_name=f'Extra Bolt {i}', category='Fasteners',
                cost_per_unit=Decimal('1.00'), reorder_level=5, supplier='CTK',
            )
        res = self.client.get(STATS_URL)
        # 5.50 + (25 x 1.00) = 30.50
        self.assertEqual(Decimal(str(res.data['total_value'])), Decimal('30.50'))

    def test_total_value_zero_when_no_products(self):
        Inventory.objects.all().delete()
        Product.objects.all().delete()
        res = self.client.get(STATS_URL)
        self.assertEqual(res.data['total_value'], 0)

    # --- by_category counts ---

    def test_by_category_count_fasteners(self):
        res = self.client.get(STATS_URL)
        self.assertEqual(res.data['by_category']['Fasteners']['count'], 1)

    def test_by_category_count_accessories(self):
        res = self.client.get(STATS_URL)
        self.assertEqual(res.data['by_category']['Accessories']['count'], 1)

    # --- by_category total_value (sum of cost_per_unit per category) ---

    def test_by_category_fasteners_total_value(self):
        res = self.client.get(STATS_URL)
        self.assertEqual(
            Decimal(str(res.data['by_category']['Fasteners']['total_value'])),
            Decimal('0.50'),
        )

    def test_by_category_accessories_total_value(self):
        res = self.client.get(STATS_URL)
        self.assertEqual(
            Decimal(str(res.data['by_category']['Accessories']['total_value'])),
            Decimal('5.00'),
        )

    def test_by_category_total_value_zero_when_category_empty(self):
        Inventory.objects.filter(product__category='Accessories').delete()
        Product.objects.filter(category='Accessories').delete()
        res = self.client.get(STATS_URL)
        self.assertNotIn('Accessories', res.data['by_category'])


class ProductListTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {make_token(self.user)}')

        # 3 Fasteners
        self.f1 = Product.objects.create(
            barcode='F1', product_name='Bolt M6', category='Fasteners',
            cost_per_unit=Decimal('0.30'), reorder_level=5, supplier='CTK',
        )
        self.f2 = Product.objects.create(
            barcode='F2', product_name='Bolt M8', category='Fasteners',
            cost_per_unit=Decimal('0.50'), reorder_level=20, supplier='CTK',
        )
        self.f3 = Product.objects.create(
            barcode='F3', product_name='Nut M6', category='Fasteners',
            cost_per_unit=Decimal('0.20'), reorder_level=10, supplier='CTK',
        )
        # 2 Accessories
        self.a1 = Product.objects.create(
            barcode='A1', product_name='Safety Gloves', category='Accessories',
            cost_per_unit=Decimal('5.00'), reorder_level=3, supplier='CTK',
        )
        self.a2 = Product.objects.create(
            barcode='A2', product_name='Hard Hat', category='Accessories',
            cost_per_unit=Decimal('12.00'), reorder_level=8, supplier='CTK',
        )

    # --- page_size ---

    def test_list_all_products_by_default(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Verify it returns all 5 records without pagination links
        self.assertEqual(res.data['count'], 5)
        self.assertEqual(len(res.data['results']), 5)
        self.assertNotIn('next', res.data)
        self.assertNotIn('previous', res.data)

    def test_list_all_includes_products_beyond_20_by_default(self):
        for i in range(20):
            Product.objects.create(
                barcode=f'EXTRA-LIST-{i}', product_name=f'Extra {i}', category='Fasteners',
                cost_per_unit=Decimal('1.00'), reorder_level=5, supplier='CTK',
            )
        res = self.client.get(LIST_URL)
        self.assertEqual(len(res.data['results']), 25)
        self.assertEqual(res.data['count'], 25)

    def test_page_size_param_is_ignored(self):
        # We accept it but it doesn't change anything, returns all
        res = self.client.get(LIST_URL, {'page_size': 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 5)

    # --- category filter ---

    def test_filter_by_fasteners(self):
        res = self.client.get(LIST_URL, {'category': 'Fasteners'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 3)
        categories = {p['category'] for p in res.data['results']}
        self.assertEqual(categories, {'Fasteners'})

    def test_filter_by_accessories(self):
        res = self.client.get(LIST_URL, {'category': 'Accessories'})
        self.assertEqual(res.data['count'], 2)
        categories = {p['category'] for p in res.data['results']}
        self.assertEqual(categories, {'Accessories'})

    def test_filter_category_case_insensitive(self):
        res = self.client.get(LIST_URL, {'category': 'fasteners'})
        self.assertEqual(res.data['count'], 3)

    # --- ordering ---

    def test_ordering_cost_low_to_high(self):
        res = self.client.get(LIST_URL, {'ordering': 'cost_per_unit'})
        costs = [Decimal(str(p['cost_per_unit'])) for p in res.data['results']]
        self.assertEqual(costs, sorted(costs))

    def test_ordering_cost_high_to_low(self):
        res = self.client.get(LIST_URL, {'ordering': '-cost_per_unit'})
        costs = [Decimal(str(p['cost_per_unit'])) for p in res.data['results']]
        self.assertEqual(costs, sorted(costs, reverse=True))

    def test_ordering_reorder_level_low_to_high(self):
        res = self.client.get(LIST_URL, {'ordering': 'reorder_level'})
        levels = [p['reorder_level'] for p in res.data['results']]
        self.assertEqual(levels, sorted(levels))

    def test_ordering_reorder_level_high_to_low(self):
        res = self.client.get(LIST_URL, {'ordering': '-reorder_level'})
        levels = [p['reorder_level'] for p in res.data['results']]
        self.assertEqual(levels, sorted(levels, reverse=True))

    # --- combined ---

    def test_category_and_ordering_combined(self):
        res = self.client.get(LIST_URL, {
            'category': 'Fasteners',
            'ordering': 'cost_per_unit',
        })
        self.assertEqual(res.data['count'], 3)
        costs = [Decimal(str(p['cost_per_unit'])) for p in res.data['results']]
        self.assertEqual(costs, sorted(costs))

    def test_category_combined(self):
        res = self.client.get(LIST_URL, {'category': 'Accessories'})
        self.assertEqual(res.data['count'], 2)
        self.assertEqual(len(res.data['results']), 2)
