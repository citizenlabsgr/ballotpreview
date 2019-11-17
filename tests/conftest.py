import pytest

from app import views


@pytest.fixture
def app():
    return views.app
