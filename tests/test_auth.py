"""
Tests for auth routes
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def auth_client():
    """Create a test client for auth routes"""
    with patch('src.backend.database.init_database'):
        from src.app import app
        return TestClient(app)


class TestLoginEndpoint:
    """Test login endpoint"""
    
    def test_login_success(self, auth_client, sample_teacher):
        """Test successful login"""
        with patch('src.backend.routers.auth.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.auth.verify_password') as mock_verify:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_verify.return_value = True
            
            response = auth_client.post(
                "/auth/login",
                params={"username": "mrodriguez", "password": "art123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "mrodriguez"
            assert data["display_name"] == "Ms. Rodriguez"
            assert data["role"] == "teacher"
    
    def test_login_invalid_username(self, auth_client):
        """Test login with invalid username"""
        with patch('src.backend.routers.auth.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = None
            
            response = auth_client.post(
                "/auth/login",
                params={"username": "nonexistent", "password": "wrongpass"}
            )
            
            assert response.status_code == 401
            assert "Invalid username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, auth_client, sample_teacher):
        """Test login with invalid password"""
        with patch('src.backend.routers.auth.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.auth.verify_password') as mock_verify:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_verify.return_value = False
            
            response = auth_client.post(
                "/auth/login",
                params={"username": "mrodriguez", "password": "wrongpass"}
            )
            
            assert response.status_code == 401
            assert "Invalid username or password" in response.json()["detail"]
    
    def test_login_teacher_no_password_field(self, auth_client):
        """Test login when teacher has no password field"""
        teacher_no_pass = {
            "_id": "mrodriguez",
            "username": "mrodriguez",
            "display_name": "Ms. Rodriguez",
            "role": "teacher"
        }
        
        with patch('src.backend.routers.auth.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.auth.verify_password') as mock_verify:
            
            mock_teachers.find_one.return_value = teacher_no_pass
            mock_verify.return_value = False
            
            response = auth_client.post(
                "/auth/login",
                params={"username": "mrodriguez", "password": "anypass"}
            )
            
            assert response.status_code == 401


class TestCheckSessionEndpoint:
    """Test check-session endpoint"""
    
    def test_check_session_success(self, auth_client, sample_teacher):
        """Test successful session check"""
        with patch('src.backend.routers.auth.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = auth_client.get(
                "/auth/check-session",
                params={"username": "mrodriguez"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "mrodriguez"
            assert data["display_name"] == "Ms. Rodriguez"
            assert data["role"] == "teacher"
    
    def test_check_session_teacher_not_found(self, auth_client):
        """Test session check with non-existent teacher"""
        with patch('src.backend.routers.auth.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = None
            
            response = auth_client.get(
                "/auth/check-session",
                params={"username": "nonexistent"}
            )
            
            assert response.status_code == 404
            assert "Teacher not found" in response.json()["detail"]
