from tests.conftest import auth_headers, promote_to_admin, register_and_login


async def _open_account(client, token, account_type="checking"):
    resp = await client.post("/api/v1/accounts", json={"account_type": account_type}, headers=auth_headers(token))
    return resp.json()


LOAN_PAYLOAD = {"principal_cents": 1_000_000, "annual_interest_rate_bps": 1200, "term_months": 12}


async def test_calculate_emi_endpoint(client):
    session = await register_and_login(client)
    resp = await client.post("/api/v1/loans/calculate-emi", json=LOAN_PAYLOAD, headers=auth_headers(session["access_token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["emi_cents"] == 88849
    assert body["total_payment_cents"] == 1_066_188
    assert body["total_interest_cents"] == 66_188


async def test_apply_for_loan_stores_computed_emi(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])
    account = await _open_account(client, session["access_token"])

    resp = await client.post(
        "/api/v1/loans", json={**LOAN_PAYLOAD, "disbursement_account_id": account["id"]}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["emi_cents"] == 88849
    assert body["decided_at"] is None

    list_resp = await client.get("/api/v1/loans", headers=headers)
    assert len(list_resp.json()) == 1


async def test_apply_for_loan_rejects_account_you_dont_own(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)
    account_b = await _open_account(client, session_b["access_token"])

    resp = await client.post(
        "/api/v1/loans",
        json={**LOAN_PAYLOAD, "disbursement_account_id": account_b["id"]},
        headers=auth_headers(session_a["access_token"]),
    )
    assert resp.status_code == 404


async def test_idor_user_cannot_read_another_users_loan(client):
    session_a = await register_and_login(client)
    session_b = await register_and_login(client)
    account_a = await _open_account(client, session_a["access_token"])

    create_resp = await client.post(
        "/api/v1/loans",
        json={**LOAN_PAYLOAD, "disbursement_account_id": account_a["id"]},
        headers=auth_headers(session_a["access_token"]),
    )
    loan_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/loans/{loan_id}", headers=auth_headers(session_b["access_token"]))
    assert resp.status_code == 404


async def test_non_admin_cannot_access_admin_loan_endpoints(client):
    session = await register_and_login(client)
    resp = await client.get("/api/v1/admin/loans", headers=auth_headers(session["access_token"]))
    assert resp.status_code == 403


async def test_admin_approve_disburses_principal(client, db_sessionmaker):
    applicant = await register_and_login(client)
    applicant_headers = auth_headers(applicant["access_token"])
    account = await _open_account(client, applicant["access_token"])

    create_resp = await client.post(
        "/api/v1/loans", json={**LOAN_PAYLOAD, "disbursement_account_id": account["id"]}, headers=applicant_headers
    )
    loan_id = create_resp.json()["id"]

    admin = await register_and_login(client)
    await promote_to_admin(db_sessionmaker, admin["email"])
    admin_headers = auth_headers(admin["access_token"])

    pending_resp = await client.get("/api/v1/admin/loans?status=pending", headers=admin_headers)
    assert pending_resp.status_code == 200
    assert any(loan["id"] == loan_id for loan in pending_resp.json())

    approve_resp = await client.post(f"/api/v1/admin/loans/{loan_id}/approve", headers=admin_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    account_resp = await client.get(f"/api/v1/accounts/{account['id']}", headers=applicant_headers)
    assert account_resp.json()["balance_cents"] == 1_000_000

    history_resp = await client.get(f"/api/v1/accounts/{account['id']}/transactions", headers=applicant_headers)
    types = [tx["type"] for tx in history_resp.json()["items"]]
    assert "loan_disbursement" in types


async def test_admin_reject_leaves_balance_untouched(client, db_sessionmaker):
    applicant = await register_and_login(client)
    applicant_headers = auth_headers(applicant["access_token"])
    account = await _open_account(client, applicant["access_token"])

    create_resp = await client.post(
        "/api/v1/loans", json={**LOAN_PAYLOAD, "disbursement_account_id": account["id"]}, headers=applicant_headers
    )
    loan_id = create_resp.json()["id"]

    admin = await register_and_login(client)
    await promote_to_admin(db_sessionmaker, admin["email"])
    admin_headers = auth_headers(admin["access_token"])

    reject_resp = await client.post(f"/api/v1/admin/loans/{loan_id}/reject", headers=admin_headers)
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    account_resp = await client.get(f"/api/v1/accounts/{account['id']}", headers=applicant_headers)
    assert account_resp.json()["balance_cents"] == 0


async def test_cannot_decide_a_loan_twice(client, db_sessionmaker):
    applicant = await register_and_login(client)
    account = await _open_account(client, applicant["access_token"])

    create_resp = await client.post(
        "/api/v1/loans",
        json={**LOAN_PAYLOAD, "disbursement_account_id": account["id"]},
        headers=auth_headers(applicant["access_token"]),
    )
    loan_id = create_resp.json()["id"]

    admin = await register_and_login(client)
    await promote_to_admin(db_sessionmaker, admin["email"])
    admin_headers = auth_headers(admin["access_token"])

    await client.post(f"/api/v1/admin/loans/{loan_id}/approve", headers=admin_headers)
    second_resp = await client.post(f"/api/v1/admin/loans/{loan_id}/reject", headers=admin_headers)
    assert second_resp.status_code == 400
