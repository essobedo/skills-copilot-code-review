"""
Tests for activities routes
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def activities_client():
    """Create a test client for activities routes"""
    with patch('src.backend.database.init_database'):
        from src.app import app
        return TestClient(app)


class TestGetActivitiesEndpoint:
    """Test get activities endpoint"""
    
    def test_get_all_activities(self, activities_client, sample_activity):
        """Test getting all activities"""
        with patch('src.backend.routers.activities.activities_collection') as mock_activities:
            mock_activities.find.return_value = [sample_activity.copy()]
            
            response = activities_client.get("/activities")
            
            assert response.status_code == 200
            data = response.json()
            assert "Chess Club" in data
            assert data["Chess Club"]["description"] == sample_activity["description"]
    
    def test_get_activities_slash_endpoint(self, activities_client, sample_activity):
        """Test getting all activities with trailing slash"""
        with patch('src.backend.routers.activities.activities_collection') as mock_activities:
            mock_activities.find.return_value = [sample_activity.copy()]
            
            response = activities_client.get("/activities/")
            
            assert response.status_code == 200
    
    def test_get_activities_filter_by_day(self, activities_client, sample_activity):
        """Test filtering activities by day"""
        with patch('src.backend.routers.activities.activities_collection') as mock_activities:
            mock_activities.find.return_value = [sample_activity.copy()]
            
            response = activities_client.get("/activities?day=Monday")
            
            assert response.status_code == 200
            # Verify the query was built correctly
            call_args = mock_activities.find.call_args
            assert call_args[0][0] == {"schedule_details.days": {"$in": ["Monday"]}}
    
    def test_get_activities_filter_by_time(self, activities_client, sample_activity):
        """Test filtering activities by time"""
        with patch('src.backend.routers.activities.activities_collection') as mock_activities:
            mock_activities.find.return_value = [sample_activity.copy()]
            
            response = activities_client.get(
                "/activities?start_time=14:00&end_time=18:00"
            )
            
            assert response.status_code == 200
            call_args = mock_activities.find.call_args
            query = call_args[0][0]
            assert "schedule_details.start_time" in query
            assert "schedule_details.end_time" in query
    
    def test_get_activities_no_results(self, activities_client):
        """Test getting activities with no results"""
        with patch('src.backend.routers.activities.activities_collection') as mock_activities:
            mock_activities.find.return_value = []
            
            response = activities_client.get("/activities")
            
            assert response.status_code == 200
            data = response.json()
            assert data == {}


class TestGetAvailableDaysEndpoint:
    """Test get available days endpoint"""
    
    def test_get_available_days(self, activities_client):
        """Test getting available days"""
        with patch('src.backend.routers.activities.activities_collection') as mock_activities:
            mock_activities.aggregate.return_value = [
                {"_id": "Friday"},
                {"_id": "Monday"},
                {"_id": "Wednesday"}
            ]
            
            response = activities_client.get("/activities/days")
            
            assert response.status_code == 200
            data = response.json()
            assert "Friday" in data
            assert "Monday" in data
            assert "Wednesday" in data


class TestSignupForActivityEndpoint:
    """Test signup for activity endpoint"""
    
    def test_signup_success(self, activities_client, sample_activity, sample_teacher):
        """Test successful signup"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_activities.find_one.return_value = sample_activity.copy()
            
            mock_result = MagicMock()
            mock_result.modified_count = 1
            mock_activities.update_one.return_value = mock_result
            
            response = activities_client.post(
                "/activities/Chess Club/signup",
                params={
                    "email": "newstudent@mergington.edu",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_no_authentication(self, activities_client):
        """Test signup without authentication"""
        response = activities_client.post(
            "/activities/Chess Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_signup_invalid_teacher(self, activities_client):
        """Test signup with invalid teacher"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = None
            
            response = activities_client.post(
                "/activities/Chess Club/signup",
                params={
                    "email": "student@mergington.edu",
                    "teacher_username": "invalid_teacher"
                }
            )
            
            assert response.status_code == 401
            assert "Invalid teacher credentials" in response.json()["detail"]
    
    def test_signup_activity_not_found(self, activities_client, sample_teacher):
        """Test signup for non-existent activity"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_activities.find_one.return_value = None
            
            response = activities_client.post(
                "/activities/NonExistent/signup",
                params={
                    "email": "student@mergington.edu",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 404
            assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_signed_up(self, activities_client, sample_teacher, sample_activity):
        """Test signup when already signed up"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_activities.find_one.return_value = sample_activity.copy()
            
            response = activities_client.post(
                "/activities/Chess Club/signup",
                params={
                    "email": "michael@mergington.edu",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 400
            assert "Already signed up" in response.json()["detail"]
    
    def test_signup_update_failure(self, activities_client, sample_teacher, sample_activity):
        """Test signup when database update fails"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_activities.find_one.return_value = sample_activity.copy()
            
            mock_result = MagicMock()
            mock_result.modified_count = 0
            mock_activities.update_one.return_value = mock_result
            
            response = activities_client.post(
                "/activities/Chess Club/signup",
                params={
                    "email": "newstudent@mergington.edu",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 500
            assert "Failed to update" in response.json()["detail"]


class TestUnregisterFromActivityEndpoint:
    """Test unregister from activity endpoint"""
    
    def test_unregister_success(self, activities_client, sample_teacher, sample_activity):
        """Test successful unregister"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_activities.find_one.return_value = sample_activity.copy()
            
            mock_result = MagicMock()
            mock_result.modified_count = 1
            mock_activities.update_one.return_value = mock_result
            
            response = activities_client.post(
                "/activities/Chess Club/unregister",
                params={
                    "email": "michael@mergington.edu",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "michael@mergington.edu" in data["message"]
    
    def test_unregister_no_authentication(self, activities_client):
        """Test unregister without authentication"""
        response = activities_client.post(
            "/activities/Chess Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_unregister_invalid_teacher(self, activities_client):
        """Test unregister with invalid teacher"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = None
            
            response = activities_client.post(
                "/activities/Chess Club/unregister",
                params={
                    "email": "student@mergington.edu",
                    "teacher_username": "invalid_teacher"
                }
            )
            
            assert response.status_code == 401
            assert "Invalid teacher credentials" in response.json()["detail"]
    
    def test_unregister_activity_not_found(self, activities_client, sample_teacher):
        """Test unregister from non-existent activity"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_activities.find_one.return_value = None
            
            response = activities_client.post(
                "/activities/NonExistent/unregister",
                params={
                    "email": "student@mergington.edu",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 404
            assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_signed_up(self, activities_client, sample_teacher, sample_activity):
        """Test unregister when not signed up"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_activities.find_one.return_value = sample_activity.copy()
            
            response = activities_client.post(
                "/activities/Chess Club/unregister",
                params={
                    "email": "notstudent@mergington.edu",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 400
            assert "Not registered" in response.json()["detail"]
    
    def test_unregister_update_failure(self, activities_client, sample_teacher, sample_activity):
        """Test unregister when database update fails"""
        with patch('src.backend.routers.activities.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.activities.activities_collection') as mock_activities:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_activities.find_one.return_value = sample_activity.copy()
            
            mock_result = MagicMock()
            mock_result.modified_count = 0
            mock_activities.update_one.return_value = mock_result
            
            response = activities_client.post(
                "/activities/Chess Club/unregister",
                params={
                    "email": "michael@mergington.edu",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 500
            assert "Failed to update" in response.json()["detail"]
