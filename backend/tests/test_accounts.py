from tests.conftest import auth_headers, register_and_login


async def test_create_account(client):
    session = await register_and_login(client)
    resp = await client.post(
        "/api/v1/accounts", json={"account_type": "checking"}, headers=auth_headers(session["access_token"])
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["account_type"] == "checking"
    assert body["balance_cents"] == 0
    assert len(body["account_number"]) == 10


async def test_create_account_requires_auth(client):
    resp = await client.post("/api/v1/accounts", json={"account_type": "checking"})
    assert resp.status_code == 401


async def test_list_accounts_only_returns_own_accounts(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)

    await client.post("/api/v1/accounts", json={"account_type": "checking"}, headers=auth_headers(session_a["access_token"]))
    await client.post("/api/v1/accounts", json={"account_type": "savings"}, headers=auth_headers(session_b["access_token"]))

    resp_a = await client.get("/api/v1/accounts", headers=auth_headers(session_a["access_token"]))
    assert resp_a.status_code == 200
    assert len(resp_a.json()) == 1
    assert resp_a.json()[0]["account_type"] == "checking"


async def test_idor_user_cannot_read_another_users_account(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)

    create_resp = await client.post(
        "/api/v1/accounts", json={"account_type": "checking"}, headers=auth_headers(session_a["access_token"])
    )
    account_id = create_resp.json()["id"]

    # User B tries to fetch user A's account by guessing/copying its ID.
    resp = await client.get(f"/api/v1/accounts/{account_id}", headers=auth_headers(session_b["access_token"]))
    assert resp.status_code == 404


async def test_idor_user_cannot_deposit_into_another_users_account(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)

    create_resp = await client.post(
        "/api/v1/accounts", json={"account_type": "checking"}, headers=auth_headers(session_a["access_token"])
    )
    account_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/accounts/{account_id}/deposit",
        json={"amount_cents": 10000},
        headers=auth_headers(session_b["access_token"]),
    )
    assert resp.status_code == 404
