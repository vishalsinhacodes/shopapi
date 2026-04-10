def test_create_product_as_admin(client, admin_headers):
    response = client.post("/products/", json={
        "name": "Keyboard",
        "description": "Mechanical keyboard",
        "price": 79.99,
        "stock": 50
    }, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Keyboard"
    assert data["price"] == 79.99
    
def test_create_product_as_customer(client, auth_headers):
    response = client.post("/products/", json={
        "name": "Mouse",
        "price": 29.99,
        "stock": 10
    }, headers=auth_headers)
    assert response.status_code == 403
    
def test_get_products_public(client, sample_product):
    response = client.get("/products/")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    
def test_search_products(client, sample_product):
    response = client.get("/products/?search=Laptop")
    assert response.status_code == 200
    assert len(response.json()) >= 1    
    
def test_search_products_no_results(client, sample_product):
    response = client.get("/products/?search=nonexistent")
    assert response.status_code == 200
    assert len(response.json()) == 0
    
def test_get_product_not_found(client):
    response = client.get("/products/99999")
    assert response.status_code == 404
    
def test_update_product_as_admin(client, admin_headers, sample_product):
    product_id = sample_product["id"]
    response = client.put(f"/products/{product_id}", json={
        "price": 89.99
    }, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["price"] == 89.99
    # name unchanged
    assert response.json()["name"] == sample_product["name"]
    
def test_soft_delete_product(client, admin_headers, sample_product):
    product_id = sample_product["id"]
    # Delete
    response = client.delete(f"/products/{product_id}", headers=admin_headers)
    assert response.status_code == 200
    # Should not appear in list anymore
    response = client.get("/products/")
    ids = [p["id"] for p in response.json()]
    assert product_id not in ids