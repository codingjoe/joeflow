from django.urls import reverse

from .testapp import models


class TestTaskViewMixin:
    def test_create_task__form_errors(self, db, admin_client, admin_user):
        url = reverse("shippingworkflow:checkout")
        response = admin_client.post(
            url, data={"shipping_address": 123, "email": "not a email"}
        )
        assert response.status_code == 200
        assert response.context_data["form"].errors == {
            "email": ["Enter a valid email address."]
        }

        assert models.Shipment.objects.count() == 0
