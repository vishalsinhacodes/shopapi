import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

import models

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)     # fresh DB for every test run
    Base.metadata.create_all(bind=engine)
    return TestClient(app)

# ----- Reusable helper fixtures ---------------------------------------------------------

@pytest.fixture
def registered_user(client):
    client.post("/users/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123"
    })
    return {
        "username": "testuser",
        "password": "securepass123"
    }
    
@pytest.fixture
def auth_headers(client, registered_user):
    response = client.post("/auth/login", data={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client):
    # Create admin user directly in DB
    db = TestingSessionLocal()
    from auth.hashing import hash_password
    admin = models.User(
        username="admin",
        email="admin@example.com",
        password=hash_password("adminpass123"),
        is_admin=True
    )
    db.add(admin)
    db.commit()
    db.close()
    
    response = client.post("/auth/login", data={
        "username": "admin",
        "password": "adminpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_product(client, admin_headers):
    response = client.post("/products/", json={
        "name": "Test Laptop",
        "description": "A test laptop",
        "price": 999.99,
        "stock": 10
    }, headers=admin_headers)
    return response.json()