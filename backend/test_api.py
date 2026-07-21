import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register_user(async_client: AsyncClient):
    response = await async_client.post("/api/auth/register", json={
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com",
        "name": "Test User"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully"

async def test_login_user(async_client: AsyncClient):
    response = await async_client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

async def test_get_current_user(async_client: AsyncClient):
    login_res = await async_client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    token = login_res.json()["access_token"]
    
    me_res = await async_client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "testuser"

async def test_create_project(async_client: AsyncClient):
    login_res = await async_client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    token = login_res.json()["access_token"]
    
    proj_res = await async_client.post("/api/projects/", json={
        "name": "Test Project",
        "description": "Test Description",
        "status": "planning",
        "start_date": "2026-06-26T00:00:00Z",
        "end_date": "2026-12-31T23:59:59Z"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    assert proj_res.status_code == 200
    assert "Test Project" in proj_res.json()["name"]

async def test_get_projects(async_client: AsyncClient):
    login_res = await async_client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    token = login_res.json()["access_token"]
    
    proj_res = await async_client.get("/api/projects/", headers={
        "Authorization": f"Bearer {token}"
    })
    assert proj_res.status_code == 200
    assert isinstance(proj_res.json(), list)
    assert len(proj_res.json()) >= 1
