def test_create_user(test_db, client):
    response = client.post(
        "/users/",
        json={"email": "deadpool@example.com", "password": "chimichangas4life"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "deadpool@example.com"
    assert "id" in data
    user_id = data["id"]
    api_token = data["api_token"]

    response = client.get(f"/users/{user_id}", headers={"X-API-TOKEN": api_token})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "deadpool@example.com"
    assert data["id"] == user_id

def test_deplicate_create_user(test_db, client):
    _response = client.post(
        "/users/",
        json={"email": "deadpool@example.com", "password": "chimichangas4life"},
    )
    response = client.post(
        "/users/",
        json={"email": "deadpool@example.com", "password": "chimichangas4life"},
    )
    assert response.status_code == 400, response.text

def test_get_users_valid(test_db, client, user):
    api_token=user["api_token"]
    response = client.get(f"/users/", headers={"X-API-TOKEN": api_token})
    assert response.status_code == 200, response.text

# 認証の異常系はここでテストする
def test_get_users_wrong_token(test_db, client, user):
    response = client.get(f"/users/", headers={"X-API-TOKEN": "wrong token"})
    assert response.status_code == 401, response.text

# 認証の異常系はここでテストする
def test_get_users_missing_token(test_db, client):
    response = client.get(f"/users/")
    assert response.status_code == 401, response.text


def test_get_users_by_id(test_db, client, user):
    user_id = user["user_id"]
    api_token = user["api_token"]
    response = client.get(f"/users/{user_id}/", headers={"X-API-TOKEN": api_token})
    assert response.status_code == 200, response.text


def test_user_items(test_db, client, user):
    user_id = user["user_id"]
    api_token = user["api_token"]
    response = client.post(f"/users/{user_id}/items/", headers={"X-API-TOKEN": api_token}, json={"title": "test","description": "description"})
    assert response.status_code == 200, response.text

    response = client.get(f"/items/", headers={"X-API-TOKEN": api_token})
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"]=="test"
    assert data[0]["description"]=="description"
    assert data[0]["id"]==1
    assert data[0]["owner_id"]==1

def test_my_items(test_db, client, user):
    user_id = user["user_id"]
    api_token = user["api_token"]

    # 自分で作ったItemが自分から見えるかテスト
    response = client.post(f"/users/{user_id}/items/", headers={"X-API-TOKEN": api_token}, json={"title": "test","description": "description"})
    assert response.status_code == 200, response.text

    response = client.get(f"/me/items/", headers={"X-API-TOKEN": api_token})
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"]=="test"
    assert data[0]["description"]=="description"
    assert data[0]["id"]==1
    assert data[0]["owner_id"]==1

    # 他のユーザからは見えないことをテスト
    response = client.post(
        "/users/",
        json={"email": "another@example.com", "password": "chimichangas4life"},
    )
    assert response.status_code == 200
    user_data = response.json()
    another_api_token = user_data["api_token"]
    response = client.get(f"/me/items/", headers={"X-API-TOKEN": another_api_token})
    data = response.json()
    assert len(data)  == 0

def test_delete_user(test_db, client, user):
    user_id1 = user["user_id"]
    api_token1 = user["api_token"]
    response = client.post(f"/users/{user_id1}/items/", headers={"X-API-TOKEN": api_token1}, json={"title": "user1-item","description": "user1-description"})

    response = client.post(
        "/users/",
        json={"email": "deadpool2@example.com", "password": "chimichangas4life"},
    )
    user_data2 = response.json()
    user_id2 = user_data2["id"]
    api_token2 = user_data2["api_token"]
    response = client.post(f"/users/{user_id2}/items/", headers={"X-API-TOKEN": api_token2}, json={"title": "user2-item","description": "user2-description"})

    # user1は消せない
    response = client.delete(f"/users/{user_id1}/", headers={"X-API-TOKEN": api_token2})
    assert response.status_code == 403
    
    # 存在しないユーザは消せない
    user_id99999 = 99999 # 存在しないユーザ
    response = client.delete(f"/users/{user_id99999}/", headers={"X-API-TOKEN": api_token2})
    assert response.status_code == 404

    # user2を消すとItemがuser1に移動する
    response = client.delete(f"/users/{user_id2}/", headers={"X-API-TOKEN": api_token2})
    assert response.status_code == 200

    response = client.get(f"/users/{user_id2}/", headers={"X-API-TOKEN": api_token2})
    user_data2_delete = response.json()
    assert user_data2_delete["is_active"] == False, response.text

    response = client.get(f"/users/{user_id1}/", headers={"X-API-TOKEN": api_token2})
    user_data1_delete = response.json()
    assert len(user_data1_delete["items"]) == 2, response.text

def test_health_check(test_db, client, user):
    user_id = user["user_id"]
    api_token = user["api_token"]
    response = client.get(f"/health-check/", headers={"X-API-TOKEN": api_token})
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["status"] == "ok"