from tests.conftest import auth_headers, register_and_login


async def _open_account(client, token, account_type="checking"):
    resp = await client.post("/api/v1/accounts", json={"account_type": account_type}, headers=auth_headers(token))
    return resp.json()


async def test_create_and_list_beneficiary(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account = await _open_account(client, session["access_token"])

    resp = await client.post(
        "/api/v1/beneficiaries", json={"nickname": "Rent", "account_id": account["id"]}, headers=headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["nickname"] == "Rent"
    assert body["account_id"] == account["id"]

    list_resp = await client.get("/api/v1/beneficiaries", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


async def test_create_beneficiary_for_nonexistent_account_fails(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    resp = await client.post(
        "/api/v1/beneficiaries",
        json={"nickname": "Ghost", "account_id": "00000000-0000-0000-0000-000000000000"},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_delete_beneficiary(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account = await _open_account(client, session["access_token"])

    create_resp = await client.post(
        "/api/v1/beneficiaries", json={"nickname": "Rent", "account_id": account["id"]}, headers=headers
    )
    beneficiary_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/beneficiaries/{beneficiary_id}", headers=headers)
    assert delete_resp.status_code == 204

    list_resp = await client.get("/api/v1/beneficiaries", headers=headers)
    assert list_resp.json() == []


async def test_idor_user_cannot_delete_another_users_beneficiary(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)
    account_a = await _open_account(client, session_a["access_token"])

    create_resp = await client.post(
        "/api/v1/beneficiaries",
        json={"nickname": "Rent", "account_id": account_a["id"]},
        headers=auth_headers(session_a["access_token"]),
    )
    beneficiary_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/beneficiaries/{beneficiary_id}", headers=auth_headers(session_b["access_token"])
    )
    assert resp.status_code == 404


async def test_account_lookup_by_number_hides_balance_and_owner(client):
    session = await register_and_login(client)
    account = await _open_account(client, session["access_token"])

    other_session = await register_and_login(client)
    resp = await client.get(
        f"/api/v1/accounts/lookup?account_number={account['account_number']}",
        headers=auth_headers(other_session["access_token"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"id", "account_number", "account_type"}


async def test_account_lookup_nonexistent_number_404s(client):
    session = await register_and_login(client)
    resp = await client.get(
        "/api/v1/accounts/lookup?account_number=0000000000", headers=auth_headers(session["access_token"])
    )
    assert resp.status_code == 404
