"""Security Tests - Authentication & Authorization"""

import pytest
from datetime import datetime, timedelta
import asyncio

from legion.infrastructure.auth import JWTManager


@pytest.mark.asyncio
class TestJWTAuthentication:
    """Test JWT authentication flow"""
    
    @pytest.fixture
    async def jwt_manager(self, mock_redis):
        """Create JWT manager for testing with mock Redis"""
        manager = JWTManager(
            secret_key="test-secret-key-do-not-use-in-production",
            redis_url="redis://localhost:6379/15",  # Not used (mocked)
            access_token_expire_minutes=15,
            refresh_token_expire_days=7
        )
        # Inject mock Redis
        manager.redis = mock_redis
        yield manager
        # Cleanup
        await manager.redis.close()
    
    async def test_create_session(self, jwt_manager):
        """Test session creation with JWT tokens"""
        tokens = await jwt_manager.create_session(
            user_id="test_user",
            roles=["user", "admin"]
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] > 0
    
    async def test_validate_token_success(self, jwt_manager):
        """Test successful token validation"""
        tokens = await jwt_manager.create_session(
            user_id="test_user",
            roles=["user"]
        )
        
        token_data = await jwt_manager.validate_token(tokens["access_token"])
        
        assert token_data is not None
        assert token_data.user_id == "test_user"
        assert "user" in token_data.roles
    
    async def test_validate_token_invalid(self, jwt_manager):
        """Test invalid token rejection"""
        token_data = await jwt_manager.validate_token("invalid.token.here")
        assert token_data is None
    
    async def test_session_revocation(self, jwt_manager):
        """Test session revocation (logout)"""
        tokens = await jwt_manager.create_session(
            user_id="test_user",
            roles=["user"]
        )
        
        # Validate token works
        token_data = await jwt_manager.validate_token(tokens["access_token"])
        assert token_data is not None
        
        # Revoke session
        await jwt_manager.revoke_session(token_data.session_id)
        
        # Token should now be invalid
        token_data = await jwt_manager.validate_token(tokens["access_token"])
        assert token_data is None
