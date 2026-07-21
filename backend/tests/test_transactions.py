import asyncio

from tests.conftest import auth_headers, register_and_login


async def _open_account(client, token, account_type="checking"):
    resp = await client.post("/api/v1/accounts", json={"account_type": account_type}, headers=auth_headers(token))
    return resp.json()


async def test_deposit_increases_balance(client):
    session = await register_and_login(client)
    account = await _open_account(client, session["access_token"])

    resp = await client.post(
        f"/api/v1/accounts/{account['id']}/deposit",
        json={"amount_cents": 50000, "description": "paycheck"},
        headers=auth_headers(session["access_token"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "deposit"
    assert body["balance_after_cents"] == 50000


async def test_withdraw_decreases_balance(client):
    session = await register_and_login(client)
    account = await _open_account(client, session["access_token"])
    headers = auth_headers(session["access_token"])

    await client.post(f"/api/v1/accounts/{account['id']}/deposit", json={"amount_cents": 50000}, headers=headers)
    resp = await client.post(f"/api/v1/accounts/{account['id']}/withdraw", json={"amount_cents": 20000}, headers=headers)

    assert resp.status_code == 200
    assert resp.json()["balance_after_cents"] == 30000


async def test_withdraw_rejects_insufficient_funds(client):
    session = await register_and_login(client)
    account = await _open_account(client, session["access_token"])
    headers = auth_headers(session["access_token"])

    resp = await client.post(f"/api/v1/accounts/{account['id']}/withdraw", json={"amount_cents": 100}, headers=headers)
    assert resp.status_code == 400


async def test_withdraw_rejects_negative_amount(client):
    session = await register_and_login(client)
    account = await _open_account(client, session["access_token"])
    headers = auth_headers(session["access_token"])

    resp = await client.post(f"/api/v1/accounts/{account['id']}/withdraw", json={"amount_cents": -500}, headers=headers)
    assert resp.status_code == 422


async def test_transfer_moves_money_atomically(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account_a = await _open_account(client, session["access_token"])
    account_b = await _open_account(client, session["access_token"], "savings")

    await client.post(f"/api/v1/accounts/{account_a['id']}/deposit", json={"amount_cents": 100000}, headers=headers)

    resp = await client.post(
        "/api/v1/transfers",
        json={"from_account_id": account_a["id"], "to_account_id": account_b["id"], "amount_cents": 40000},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["debit"]["balance_after_cents"] == 60000
    assert body["credit"]["balance_after_cents"] == 40000
    assert body["debit"]["reference_id"] == body["credit"]["reference_id"]


async def test_transfer_rejects_insufficient_funds_and_leaves_balances_unchanged(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account_a = await _open_account(client, session["access_token"])
    account_b = await _open_account(client, session["access_token"], "savings")

    await client.post(f"/api/v1/accounts/{account_a['id']}/deposit", json={"amount_cents": 1000}, headers=headers)

    resp = await client.post(
        "/api/v1/transfers",
        json={"from_account_id": account_a["id"], "to_account_id": account_b["id"], "amount_cents": 5000},
        headers=headers,
    )
    assert resp.status_code == 400

    balances = await client.get("/api/v1/accounts", headers=headers)
    by_id = {a["id"]: a["balance_cents"] for a in balances.json()}
    assert by_id[account_a["id"]] == 1000
    assert by_id[account_b["id"]] == 0


async def test_cannot_transfer_to_same_account(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account = await _open_account(client, session["access_token"])
    await client.post(f"/api/v1/accounts/{account['id']}/deposit", json={"amount_cents": 5000}, headers=headers)

    resp = await client.post(
        "/api/v1/transfers",
        json={"from_account_id": account["id"], "to_account_id": account["id"], "amount_cents": 100},
        headers=headers,
    )
    assert resp.status_code == 400


async def test_cannot_transfer_from_account_you_dont_own(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)
    account_a = await _open_account(client, session_a["access_token"])
    account_b = await _open_account(client, session_b["access_token"])

    await client.post(
        f"/api/v1/accounts/{account_a['id']}/deposit", json={"amount_cents": 5000}, headers=auth_headers(session_a["access_token"])
    )

    # User B tries to move money OUT of user A's account into their own.
    resp = await client.post(
        "/api/v1/transfers",
        json={"from_account_id": account_a["id"], "to_account_id": account_b["id"], "amount_cents": 1000},
        headers=auth_headers(session_b["access_token"]),
    )
    assert resp.status_code == 404


async def test_transaction_history_filters_and_paginates(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account = await _open_account(client, session["access_token"])

    for _ in range(5):
        await client.post(f"/api/v1/accounts/{account['id']}/deposit", json={"amount_cents": 1000}, headers=headers)
    await client.post(f"/api/v1/accounts/{account['id']}/withdraw", json={"amount_cents": 500}, headers=headers)

    page1 = await client.get(f"/api/v1/accounts/{account['id']}/transactions?page=1&page_size=3", headers=headers)
    assert page1.status_code == 200
    body1 = page1.json()
    assert body1["total"] == 6
    assert len(body1["items"]) == 3

    page2 = await client.get(f"/api/v1/accounts/{account['id']}/transactions?page=2&page_size=3", headers=headers)
    assert len(page2.json()["items"]) == 3

    deposits_only = await client.get(f"/api/v1/accounts/{account['id']}/transactions?type=deposit", headers=headers)
    assert deposits_only.json()["total"] == 5

    withdrawals_only = await client.get(f"/api/v1/accounts/{account['id']}/transactions?type=withdraw", headers=headers)
    assert withdrawals_only.json()["total"] == 1


async def test_concurrent_withdrawals_never_overdraw_the_account(client):
    """The core correctness guarantee: two withdrawals racing against the same account,
    where only one can be satisfied by the balance, must never both succeed and must
    never leave the balance negative. This is what SELECT ... FOR UPDATE row locking
    inside the withdraw DB transaction is for."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account = await _open_account(client, session["access_token"])

    await client.post(f"/api/v1/accounts/{account['id']}/deposit", json={"amount_cents": 10000}, headers=headers)

    async def withdraw():
        # Separate client/connection per concurrent request so they truly race at the
        # DB level instead of serializing through one shared httpx connection.
        c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        try:
            return await c.post(
                f"/api/v1/accounts/{account['id']}/withdraw", json={"amount_cents": 6000}, headers=headers
            )
        finally:
            await c.aclose()

    results = await asyncio.gather(withdraw(), withdraw())
    statuses = sorted(r.status_code for r in results)

    assert statuses == [200, 400]

    final = await client.get(f"/api/v1/accounts/{account['id']}", headers=headers)
    assert final.json()["balance_cents"] == 4000
    assert final.json()["balance_cents"] >= 0
