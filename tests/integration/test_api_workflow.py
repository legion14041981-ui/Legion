"""Integration Tests - End-to-End API Workflows"""

import pytest
import asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAPIWorkflows:
    """Test complete API workflows end-to-end"""
    
    @pytest.fixture
    async def client(self):
        """Create test HTTP client"""
        # TODO: Initialize FastAPI app when available
        # from src.main import app
        # async with AsyncClient(app=app, base_url="http://test") as client:
        #     yield client
        yield None
    
    @pytest.mark.skip(reason="Requires FastAPI app initialization - will enable in future PR")
    async def test_complete_task_workflow(self, client):
        """Test: Create → Execute → Monitor → Complete task"""
        if client is None:
            pytest.skip("FastAPI app not available")
        
        # 1. Authenticate
        auth_response = await client.post("/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        assert auth_response.status_code == 200
        token = auth_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create task
        task_response = await client.post(
            "/api/v2/tasks",
            json={
                "title": "Test Task",
                "description": "Integration test",
                "task_type": "code_analysis"
            },
            headers=headers
        )
        assert task_response.status_code == 201
        task_id = task_response.json()["id"]
        
        # 3. Execute task
        execute_response = await client.post(
            f"/api/v2/tasks/{task_id}/execute",
            json={"command": "start"},
            headers=headers
        )
        assert execute_response.status_code == 200
        
        # 4. Monitor status
        await asyncio.sleep(2)  # Wait for processing
        status_response = await client.get(
            f"/api/v2/tasks/{task_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        
        # 5. Verify result
        result = status_response.json()
        assert result["id"] == task_id
        assert result["status"] in ["running", "completed"]
