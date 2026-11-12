import pytest

from app.main import add, create_app, multiply


@pytest.fixture
def client():
    return create_app().test_client()


def test_add():
    assert add(2, 3) == 5


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"


def test_add_route(client):
    assert client.get("/add?a=1&b=2").json["result"] == 3


def test_add_route_bad_input(client):
    assert client.get("/add?a=x&b=2").status_code == 400


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (2, 3, 6),  # normal
        (-2, 3, 6),  # negative result returns absolute value
        (0, 5, 0.0),  # zero
        (100, 100, 1000.0),  # capped at 1000
    ],
)
def test_multiply(a, b, expected):
    assert multiply(a, b) == expected
