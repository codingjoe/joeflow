import pytest

from tests.testapp import workflows


class TestStartView:
    def test_get(self, client):
        response = client.get("/simple/start_view/custom/postfix/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_post(self, client):
        assert not workflows.SimpleWorkflow.objects.exists()
        response = client.post("/simple/start_view/custom/postfix/")
        assert response.status_code == 302
        assert response["Location"] == "/simple/1/"
        assert workflows.SimpleWorkflow.objects.exists()
