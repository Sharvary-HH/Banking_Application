from datetime import datetime, timedelta, timezone

from tests.conftest import auth_headers, register_and_login


async def _open_account(client, token, account_type="checking"):
    resp = await client.post("/api/v1/accounts", json={"account_type": account_type}, headers=auth_headers(token))
    return resp.json()


async def test_summary_is_all_zero_with_no_transactions(client):
    session = await register_and_login(client)
    resp = await client.get("/api/v1/analytics/summary", headers=auth_headers(session["access_token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_credits_cents"] == 0
    assert body["total_debits_cents"] == 0
    assert body["net_cents"] == 0
    assert body["by_type"] == []
    assert body["by_month"] == []


async def test_summary_aggregates_across_accounts_and_types(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account_a = await _open_account(client, session["access_token"])
    account_b = await _open_account(client, session["access_token"], "savings")

    await client.post(f"/api/v1/accounts/{account_a['id']}/deposit", json={"amount_cents": 10000}, headers=headers)
    await client.post(f"/api/v1/accounts/{account_b['id']}/deposit", json={"amount_cents": 5000}, headers=headers)
    await client.post(f"/api/v1/accounts/{account_a['id']}/withdraw", json={"amount_cents": 2000}, headers=headers)

    resp = await client.get("/api/v1/analytics/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_credits_cents"] == 15000
    assert body["total_debits_cents"] == 2000
    assert body["net_cents"] == 13000

    by_type = {t["type"]: t for t in body["by_type"]}
    assert by_type["deposit"]["total_cents"] == 15000
    assert by_type["deposit"]["count"] == 2
    assert by_type["withdraw"]["total_cents"] == 2000
    assert by_type["withdraw"]["count"] == 1

    assert len(body["by_month"]) == 1
    this_month = body["by_month"][0]
    assert this_month["credits_cents"] == 15000
    assert this_month["debits_cents"] == 2000
    assert this_month["net_cents"] == 13000


async def test_summary_scoped_to_single_account(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account_a = await _open_account(client, session["access_token"])
    account_b = await _open_account(client, session["access_token"], "savings")

    await client.post(f"/api/v1/accounts/{account_a['id']}/deposit", json={"amount_cents": 10000}, headers=headers)
    await client.post(f"/api/v1/accounts/{account_b['id']}/deposit", json={"amount_cents": 5000}, headers=headers)

    resp = await client.get(f"/api/v1/analytics/summary?account_id={account_a['id']}", headers=headers)
    body = resp.json()
    assert body["total_credits_cents"] == 10000


async def test_summary_idor_rejects_another_users_account_id(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)
    account_a = await _open_account(client, session_a["access_token"])

    resp = await client.get(
        f"/api/v1/analytics/summary?account_id={account_a['id']}", headers=auth_headers(session_b["access_token"])
    )
    assert resp.status_code == 404


async def test_summary_date_range_excludes_out_of_range_transactions(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account = await _open_account(client, session["access_token"])

    await client.post(f"/api/v1/accounts/{account['id']}/deposit", json={"amount_cents": 10000}, headers=headers)

    now = datetime.now(timezone.utc)

    # Passed via params= (not embedded in the URL string) so httpx properly percent-encodes
    # the "+00:00" UTC offset — a raw "+" in a query string decodes to a space and would
    # otherwise corrupt the datetime and trip a 422 instead of testing the filter.
    future_start = (now + timedelta(hours=1)).isoformat()
    excluded_resp = await client.get("/api/v1/analytics/summary", params={"start_date": future_start}, headers=headers)
    assert excluded_resp.json()["total_credits_cents"] == 0

    past_start = (now - timedelta(hours=1)).isoformat()
    included_resp = await client.get("/api/v1/analytics/summary", params={"start_date": past_start}, headers=headers)
    assert included_resp.json()["total_credits_cents"] == 10000
