import pyotp

from tests.conftest import auth_headers, register_and_login, unique_email


async def test_register_creates_user(client):
    email = unique_email()
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == email
    assert body["role"] == "customer"


async def test_register_rejects_duplicate_email(client):
    email = unique_email()
    await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert resp.status_code == 400


async def test_register_rejects_short_password(client):
    resp = await client.post("/api/v1/auth/register", json={"email": unique_email(), "password": "short"})
    assert resp.status_code == 422


async def test_login_success_returns_tokens(client):
    email = unique_email()
    await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_rejected(client):
    email = unique_email()
    await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"})
    assert resp.status_code == 401


async def test_login_nonexistent_user_rejected(client):
    resp = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(client):
    session = await register_and_login(client)
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(session["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["email"] == session["email"]


async def test_refresh_rotates_token_and_old_one_is_rejected(client):
    session = await register_and_login(client)
    old_refresh = session["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["refresh_token"] != old_refresh

    # The rotated-out token must not be usable again (replay protection).
    replay_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay_resp.status_code == 401


async def test_two_fa_full_flow(client):
    session = await register_and_login(client)
    headers = auth_headers(session["access_token"])

    setup_resp = await client.post("/api/v1/auth/2fa/setup", headers=headers)
    assert setup_resp.status_code == 200
    secret = setup_resp.json()["secret"]

    code = pyotp.TOTP(secret).now()
    enable_resp = await client.post("/api/v1/auth/2fa/enable", json={"code": code}, headers=headers)
    assert enable_resp.status_code == 200
    assert enable_resp.json()["enabled"] is True

    # Login should now require a second step instead of returning tokens directly.
    login_resp = await client.post("/api/v1/auth/login", json={"email": session["email"], "password": session["password"]})
    assert login_resp.status_code == 200
    login_body = login_resp.json()
    assert login_body["two_fa_required"] is True

    bad_code_resp = await client.post(
        "/api/v1/auth/login/verify-2fa", json={"two_fa_token": login_body["two_fa_token"], "code": "000000"}
    )
    assert bad_code_resp.status_code == 401

    good_code = pyotp.TOTP(secret).now()
    verify_resp = await client.post(
        "/api/v1/auth/login/verify-2fa", json={"two_fa_token": login_body["two_fa_token"], "code": good_code}
    )
    assert verify_resp.status_code == 200
    assert "access_token" in verify_resp.json()
