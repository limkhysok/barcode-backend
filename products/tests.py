
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Product


class ProductAPITestCase(APITestCase):
	def setUp(self):
		# Create user 'limkhi' in the test database
		User = get_user_model()
		User.objects.create_user(username='limkhi', password='passwordctk2026*')

		# Obtain JWT access token for user 'limkhi'
		login_data = {
			"username": "limkhi",
			"password": "passwordctk2026*"
		    }
		response = self.client.post("/api/auth/login", login_data, format="json")
		self.assertEqual(response.status_code, 200)
		self.access_token = response.data["access"]
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

	def test_product_crud_and_id_field(self):
		# Create
		create_data = {
			"product_name": "Test Product",
			"category": "Fasteners",
			"cost_per_unit": 1.23,
			"reorder_level": 10,
			"supplier": "Test Supplier"
		}
		response = self.client.post(reverse('product-list'), create_data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn('id', response.data)
		product_id = response.data['id']

		# List
		response = self.client.get(reverse('product-list'))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(any('id' in prod for prod in response.data))
		ids = [prod['id'] for prod in response.data]
		self.assertEqual(len(ids), len(set(ids)))  # No duplicates

		# Retrieve
		response = self.client.get(reverse('product-detail', args=[product_id]))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['id'], product_id)

		# Patch
		patch_data = {"product_name": "Updated Product"}
		response = self.client.patch(reverse('product-detail', args=[product_id]), patch_data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['id'], product_id)
		self.assertEqual(response.data['product_name'], "Updated Product")

		# Delete
		response = self.client.delete(reverse('product-detail', args=[product_id]))
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

		# Ensure deleted
		response = self.client.get(reverse('product-detail', args=[product_id]))
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
