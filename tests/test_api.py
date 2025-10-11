import pytest
from httpx import AsyncClient

class TestAuth:
    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient):
        response = await client.post("/auth/register", json={
            "username": "testuser",
            "password": "testpass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Пользователь зарегистрирован"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_existing_user(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "duplicate",
            "password": "pass123",
        })
        response = await client.post("/auth/register", json={
            "username": "duplicate",
            "password": "pass123",
        })
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        await client.post("/auth/register", json={
            "username": "loginuser",
            "password": "loginpass123",
        })
        response = await client.post("/auth/login", json={
            "username": "loginuser",
            "password": "loginpass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data['token_type'] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid(self, client: AsyncClient):
        response = await client.post("/auth/login", json={
            "username": "nonexistentuser",
            "password": "wrong123",
        })
        assert response.status_code == 401

class TestLogs:
    @pytest.mark.asyncio
    async def test_add_log(self, client: AsyncClient):
        response = await client.post("/add_log", json={
            "timestamp": "2025-05-14T12:00:00Z",
            "level": "INFO",
            "service": "testservice",
            "message": "testmessage",
            "metadata": {}
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_add_and_get_logs(self, client: AsyncClient, admin_user):
        login_resp = await client.post("/auth/login", json={
            "username": admin_user.username,
            "password": "adminpass123",
        })
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        log_data = {
            "timestamp": "2025-05-14T12:00:00Z",
            "level": "ERROR",
            "service": "test_service",
            "message": "Test error",
            "metadata": {"user_id": admin_user.id},
        }
        add_resp = await client.post("/add_log", headers=headers, json=log_data)
        assert add_resp.status_code == 200
        log_id = add_resp.json()["id"]

        get_resp = await client.get("/logs", headers=headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["total"] == 1
        assert len(data["logs"]) == 1
        log = data["logs"][0]
        assert log["id"] == log_id
        assert log["level"] == "ERROR"
        assert log["metadata"]["user_id"] == 1

    @pytest.mark.asyncio
    async def test_get_logs_filtered(self, client: AsyncClient, admin_user):
        login_resp = await client.post("/auth/login", json={
            "username": admin_user.username,
            "password": "adminpass123",
        })
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        await client.post("/add_log", json={
            "timestamp": "2025-05-14T10:00:00Z",
            "level": "INFO",
            "service": "service_a",
            "message": "Info log",
            "metadata": {},
        }, headers=headers)

        await client.post("/add_log", json={
            "timestamp": "2025-05-14T11:00:00Z",
            "level": "ERROR",
            "service": "service_b",
            "message": "Error log",
            "metadata": {}
        }, headers=headers)

        resp = await client.get("/logs?level=ERROR", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["logs"][0]["level"] == "ERROR"

        resp = await client.get("/logs?service=service_a", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["logs"][0]["service"] == "service_a"
