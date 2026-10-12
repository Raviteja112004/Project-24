from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from models_registry.models import Model
from tenants.models import Tenant


class ModelAPITestCase(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Acme", slug="acme")
        self.model = Model.objects.create(
            tenant=self.tenant,
            name="Test Model",
            description="Example model",
        )

    def test_list_models(self):
        url = reverse("model-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_model(self):
        url = reverse("model-detail", args=[self.model.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Model")

    def test_create_model(self):
        url = reverse("model-list")
        payload = {
            "tenant": self.tenant.pk,
            "name": "New Model",
            "description": "Created via API",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Model.objects.count(), 2)
