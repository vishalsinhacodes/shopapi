def test_register_success(client):
    response = client.post("/users/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "securepass123"
    })
    assert response.status_code == 200
    data = response.json()
    
    assert data["username"] == "newuser"
    assert "password" not in data
    assert data["is_admin"] == False
    
def test_register_duplicate_username(client):
    client.post("/users/register", json={
        "username": "dupeuser",
        "email": "dupe@example.com",
        "password": "securepass123"
    })
    
    response = client.post("/users/register", json={
        "username": "dupeuser",
        "email": "other@example.com",
        "password": "securepass123"
    })
    
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"]
    
def test_register_duplicate_email(client):
    client.post("/users/register", json={
        "username": "user1",
        "email": "same@example.com",
        "password": "securepass123"
    })
    
    response = client.post("/users/register", json={
        "username": "user2",
        "email": "same@example.com",
        "password": "securepass123"
    })
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]
    
def test_register_short_password(client):
    response = client.post("/users/register", json={
        "username": "shortpass",
        "email": "short@example.com",
        "password": "123"
    })
    
    assert response.status_code == 422
    
def test_get_me_authenticated(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    
def test_get_me_unauthenticated(client):
    response = client.get("/users/me")
    assert response.status_code == 401
    
def test_update_me(client, auth_headers):
    response = client.put("/users/me", json={
        "username": "updateduser",
        "email": "user@example.com"
    }, headers=auth_headers)           
    assert response.status_code == 200
    assert response.json()["username"] == "updateduser"