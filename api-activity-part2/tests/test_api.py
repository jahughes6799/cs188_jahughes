import pytest

from api_activity.app import initialize_api, instantiate_app

@pytest.fixture
def client():
    app = instantiate_app()
    initialize_api(app)
    with app.test_client() as client:
        yield client

def test_hello(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json == {"message": "Hello World!"}

