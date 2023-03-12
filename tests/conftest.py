import pytest

from app import settings, views


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(settings, "ELECTIONS_HOST", "https://michiganelections.io")
    monkeypatch.setattr(settings, "BUDDIES_HOST", "https://app.michiganelections.io")
    return views.app
