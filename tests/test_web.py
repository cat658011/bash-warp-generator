"""Tests for the Flask web application."""

from __future__ import annotations

from web.app import app


def test_index_returns_200() -> None:
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200


def test_index_contains_form() -> None:
    with app.test_client() as client:
        html = client.get("/").data.decode()
        assert "<form" in html
        assert 'action="/generate"' in html


def test_index_lists_formats() -> None:
    with app.test_client() as client:
        html = client.get("/").data.decode()
        assert "WIREGUARD" in html
        assert "AMNEZIA" in html
        assert "CLASH" in html
        assert "WIRESOCK" in html


def test_index_lists_dns_servers() -> None:
    with app.test_client() as client:
        html = client.get("/").data.decode()
        assert "Cloudflare" in html


def test_health_returns_ok() -> None:
    with app.test_client() as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json == {"status": "ok"}
