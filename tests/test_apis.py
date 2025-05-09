import pytest
import httpx


class TestAPIs:
    def test_ping(self):
        url = "http://localhost:8000/ping/"
        response = httpx.get(url)
        assert response.status_code == 200

        url = "http://localhost:8000/ping"
        response = httpx.get(url, follow_redirects=True)
        assert response.status_code == 200
