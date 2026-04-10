def test_place_order_success(client, auth_headers, sample_product):
    # Add to cart first
    client.post("/cart/", json={
        "product_id": sample_product["id"],
        "quantity": 2
    }, headers=auth_headers)
    
    # Place order
    response = client.post("/orders/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["total"] == round(sample_product["price"] * 2, 2)
    assert len(data["order_items"]) == 1
    
def test_place_order_empty_cart(client, auth_headers):
    response = client.post("/orders/", headers=auth_headers)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]
    
def test_place_order_clears_cart(client, auth_headers, sample_product):
    client.post("/cart/", json={
        "product_id": sample_product["id"],
        "quantity": 1
    }, headers=auth_headers)
    client.post("/orders/", headers=auth_headers)

    # Cart should be empty
    cart = client.get("/cart/", headers=auth_headers).json()
    assert len(cart["items"]) == 0
    
def test_place_order_reduces_stock(client, auth_headers,
    admin_headers, sample_product):
    initial_stock = sample_product["stock"]
    client.post("/cart/", json={
        "product_id": sample_product["id"],
        "quantity": 3
    }, headers=auth_headers)
    client.post("/orders/", headers=auth_headers)

    # Check stock reduced
    product = client.get(
        f"/products/{sample_product['id']}"
    ).json()
    assert product["stock"] == initial_stock - 3
    
def test_cancel_order_restores_stock(client, auth_headers,
    admin_headers, sample_product):
    initial_stock = sample_product["stock"]

    # Place order
    client.post("/cart/", json={
        "product_id": sample_product["id"],
        "quantity": 2
    }, headers=auth_headers)
    order = client.post("/orders/", headers=auth_headers).json()

    # Cancel it
    client.put(f"/orders/{order['id']}/cancel",
        headers=auth_headers)

    # Stock should be restored
    product = client.get(
        f"/products/{sample_product['id']}"
    ).json()
    assert product["stock"] == initial_stock
    
def test_invalid_status_transition(client, auth_headers,
    admin_headers, sample_product):
    # Place and cancel order
    client.post("/cart/", json={
        "product_id": sample_product["id"],
        "quantity": 1
    }, headers=auth_headers)
    order = client.post("/orders/", headers=auth_headers).json()
    client.put(f"/orders/{order['id']}/cancel",
        headers=auth_headers)

    # Try to ship cancelled order — should fail
    response = client.put(
        f"/orders/{order['id']}/status?status=shipped",
        headers=admin_headers
    )
    assert response.status_code == 400
    assert "Cannot move" in response.json()["detail"]
    
def test_cannot_see_other_users_orders(client, sample_product):
    # Create two users
    client.post("/users/register", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "securepass123"
    })
    client.post("/users/register", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "securepass123"
    })

    # User 1 places order
    token1 = client.post("/auth/login", data={
        "username": "user1", "password": "securepass123"
    }).json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    token2 = client.post("/auth/login", data={
        "username": "user2", "password": "securepass123"
    }).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    client.post("/cart/", json={
        "product_id": sample_product["id"],
        "quantity": 1
    }, headers=headers1)
    order = client.post("/orders/", headers=headers1).json()

    # User 2 tries to access user 1's order
    response = client.get(
        f"/orders/{order['id']}",
        headers=headers2
    )
    assert response.status_code == 404       