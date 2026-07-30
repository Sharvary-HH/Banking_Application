from datetime import datetime, timedelta, timezone

from tests.conftest import auth_headers, register_and_login


async def _open_account(client, token, account_type="checking"):
    resp = await client.post("/api/v1/accounts", json={"account_type": account_type}, headers=auth_headers(token))
    return resp.json()


async def test_create_list_cancel_scheduled_transfer(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account_a = await _open_account(client, session["access_token"])
    account_b = await _open_account(client, session["access_token"], "savings")

    resp = await client.post(
        "/api/v1/scheduled-transfers",
        json={
            "from_account_id": account_a["id"],
            "to_account_id": account_b["id"],
            "amount_cents": 1000,
            "frequency": "monthly",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_active"] is True
    assert body["frequency"] == "monthly"

    list_resp = await client.get("/api/v1/scheduled-transfers", headers=headers)
    assert len(list_resp.json()) == 1

    cancel_resp = await client.post(f"/api/v1/scheduled-transfers/{body['id']}/cancel", headers=headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["is_active"] is False


async def test_cannot_schedule_from_account_you_dont_own(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)
    account_a = await _open_account(client, session_a["access_token"])
    account_b = await _open_account(client, session_b["access_token"])

    resp = await client.post(
        "/api/v1/scheduled-transfers",
        json={
            "from_account_id": account_a["id"],
            "to_account_id": account_b["id"],
            "amount_cents": 1000,
            "frequency": "once",
        },
        headers=auth_headers(session_b["access_token"]),
    )
    assert resp.status_code == 404


async def test_cannot_schedule_transfer_to_same_account(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account = await _open_account(client, session["access_token"])

    resp = await client.post(
        "/api/v1/scheduled-transfers",
        json={
            "from_account_id": account["id"],
            "to_account_id": account["id"],
            "amount_cents": 100,
            "frequency": "once",
        },
        headers=headers,
    )
    assert resp.status_code == 400


async def test_due_once_transfer_executes_and_deactivates(client, db_sessionmaker):
    from app.services.scheduler_job import run_due_scheduled_transfers

    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account_a = await _open_account(client, session["access_token"])
    account_b = await _open_account(client, session["access_token"], "savings")
    await client.post(f"/api/v1/accounts/{account_a['id']}/deposit", json={"amount_cents": 5000}, headers=headers)

    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    create_resp = await client.post(
        "/api/v1/scheduled-transfers",
        json={
            "from_account_id": account_a["id"],
            "to_account_id": account_b["id"],
            "amount_cents": 2000,
            "frequency": "once",
            "start_at": past,
        },
        headers=headers,
    )
    assert create_resp.status_code == 200

    processed = await run_due_scheduled_transfers(sessionmaker=db_sessionmaker)
    assert processed == 1

    accounts = await client.get("/api/v1/accounts", headers=headers)
    by_id = {a["id"]: a["balance_cents"] for a in accounts.json()}
    assert by_id[account_a["id"]] == 3000
    assert by_id[account_b["id"]] == 2000

    list_resp = await client.get("/api/v1/scheduled-transfers", headers=headers)
    row = list_resp.json()[0]
    assert row["is_active"] is False
    assert row["last_run_status"] == "success"


async def test_due_monthly_transfer_executes_and_reschedules(client, db_sessionmaker):
    from app.services.scheduler_job import run_due_scheduled_transfers

    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account_a = await _open_account(client, session["access_token"])
    account_b = await _open_account(client, session["access_token"], "savings")
    await client.post(f"/api/v1/accounts/{account_a['id']}/deposit", json={"amount_cents": 50000}, headers=headers)

    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    create_resp = await client.post(
        "/api/v1/scheduled-transfers",
        json={
            "from_account_id": account_a["id"],
            "to_account_id": account_b["id"],
            "amount_cents": 1000,
            "frequency": "monthly",
            "start_at": past,
        },
        headers=headers,
    )
    original_next_run = datetime.fromisoformat(create_resp.json()["next_run_at"].replace("Z", "+00:00"))

    await run_due_scheduled_transfers(sessionmaker=db_sessionmaker)

    list_resp = await client.get("/api/v1/scheduled-transfers", headers=headers)
    row = list_resp.json()[0]
    assert row["is_active"] is True
    assert row["last_run_status"] == "success"
    new_next_run = datetime.fromisoformat(row["next_run_at"].replace("Z", "+00:00"))
    assert (new_next_run - original_next_run) > timedelta(days=25)


async def test_due_transfer_with_insufficient_funds_fails_gracefully(client, db_sessionmaker):
    from app.services.scheduler_job import run_due_scheduled_transfers

    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account_a = await _open_account(client, session["access_token"])
    account_b = await _open_account(client, session["access_token"], "savings")
    # No deposit — account_a has a zero balance, so this transfer can't succeed.

    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    await client.post(
        "/api/v1/scheduled-transfers",
        json={
            "from_account_id": account_a["id"],
            "to_account_id": account_b["id"],
            "amount_cents": 5000,
            "frequency": "once",
            "start_at": past,
        },
        headers=headers,
    )

    processed = await run_due_scheduled_transfers(sessionmaker=db_sessionmaker)
    assert processed == 1

    accounts = await client.get("/api/v1/accounts", headers=headers)
    by_id = {a["id"]: a["balance_cents"] for a in accounts.json()}
    assert by_id[account_a["id"]] == 0
    assert by_id[account_b["id"]] == 0

    list_resp = await client.get("/api/v1/scheduled-transfers", headers=headers)
    row = list_resp.json()[0]
    assert row["is_active"] is True
    assert row["last_run_status"] == "failed"
    next_run = datetime.fromisoformat(row["next_run_at"].replace("Z", "+00:00"))
    assert next_run > datetime.now(timezone.utc) + timedelta(minutes=30)
