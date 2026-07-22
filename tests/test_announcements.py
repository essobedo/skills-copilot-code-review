"""
Tests for announcements routes
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import date, timedelta


@pytest.fixture
def announcements_client():
    """Create a test client for announcements routes"""
    with patch('src.backend.database.init_database'):
        from src.app import app
        return TestClient(app)


class TestAnnouncementToDict:
    """Test _announcement_to_dict helper function"""
    
    def test_announcement_to_dict_with_start_date(self, sample_announcement):
        """Test converting announcement to dict with start_date"""
        from src.backend.routers.announcements import _announcement_to_dict
        
        result = _announcement_to_dict(sample_announcement)
        
        assert result["id"] == str(sample_announcement["_id"])
        assert result["message"] == sample_announcement["message"]
        assert result["start_date"] == sample_announcement["start_date"]
        assert result["expiration_date"] == sample_announcement["expiration_date"]
    
    def test_announcement_to_dict_without_start_date(self):
        """Test converting announcement to dict without start_date"""
        from src.backend.routers.announcements import _announcement_to_dict
        
        ann = {
            "_id": ObjectId(),
            "message": "Test message",
            "expiration_date": "2026-12-31"
        }
        
        result = _announcement_to_dict(ann)
        
        assert result["message"] == "Test message"
        assert result["start_date"] is None
        assert result["expiration_date"] == "2026-12-31"


class TestRequireTeacher:
    """Test _require_teacher helper function"""
    
    def test_require_teacher_success(self, sample_teacher):
        """Test _require_teacher with valid teacher"""
        from src.backend.routers.announcements import _require_teacher
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            result = _require_teacher("mrodriguez")
            
            assert result["username"] == "mrodriguez"
    
    def test_require_teacher_no_username(self):
        """Test _require_teacher without username"""
        from src.backend.routers.announcements import _require_teacher
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            _require_teacher(None)
        
        assert exc.value.status_code == 401
        assert "Authentication required" in exc.value.detail
    
    def test_require_teacher_invalid_username(self):
        """Test _require_teacher with invalid username"""
        from src.backend.routers.announcements import _require_teacher
        from fastapi import HTTPException
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = None
            
            with pytest.raises(HTTPException) as exc:
                _require_teacher("invalid")
            
            assert exc.value.status_code == 401
            assert "Invalid teacher credentials" in exc.value.detail


class TestGetActiveAnnouncementsEndpoint:
    """Test get active announcements endpoint"""
    
    def test_get_active_announcements(self, announcements_client):
        """Test getting active announcements"""
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=10)).isoformat()
        
        announcement = {
            "_id": ObjectId(),
            "message": "Active announcement",
            "expiration_date": future,
        }
        
        with patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            mock_ann.find.return_value = [announcement]
            
            response = announcements_client.get("/announcements")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["message"] == "Active announcement"
    
    def test_get_active_announcements_slash_endpoint(self, announcements_client):
        """Test getting active announcements with trailing slash"""
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=10)).isoformat()
        
        with patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            mock_ann.find.return_value = []
            
            response = announcements_client.get("/announcements/")
            
            assert response.status_code == 200
    
    def test_get_active_announcements_expired(self, announcements_client):
        """Test that expired announcements are not returned"""
        past = (date.today() - timedelta(days=1)).isoformat()
        
        announcement = {
            "_id": ObjectId(),
            "message": "Expired announcement",
            "expiration_date": past,
        }
        
        with patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            mock_ann.find.return_value = []
            
            response = announcements_client.get("/announcements")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0
    
    def test_get_active_announcements_with_future_start_date(self, announcements_client):
        """Test that announcements with future start_date are not returned"""
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=10)).isoformat()
        future_start = (date.today() + timedelta(days=20)).isoformat()
        
        announcement = {
            "_id": ObjectId(),
            "message": "Future announcement",
            "start_date": future_start,
            "expiration_date": future,
        }
        
        with patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            mock_ann.find.return_value = [announcement]
            
            response = announcements_client.get("/announcements")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0
    
    def test_get_active_announcements_with_valid_start_date(self, announcements_client):
        """Test that announcements with valid start_date are returned"""
        today = date.today().isoformat()
        past_start = (date.today() - timedelta(days=5)).isoformat()
        future = (date.today() + timedelta(days=10)).isoformat()
        
        announcement = {
            "_id": ObjectId(),
            "message": "Valid announcement",
            "start_date": past_start,
            "expiration_date": future,
        }
        
        with patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            mock_ann.find.return_value = [announcement]
            
            response = announcements_client.get("/announcements")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1


class TestGetAllAnnouncementsEndpoint:
    """Test get all announcements endpoint"""
    
    def test_get_all_announcements(self, announcements_client, sample_teacher, sample_announcement):
        """Test getting all announcements"""
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            mock_ann.find.return_value = [sample_announcement]
            
            response = announcements_client.get(
                "/announcements/all",
                params={"teacher_username": "mrodriguez"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
    
    def test_get_all_announcements_no_auth(self, announcements_client):
        """Test getting all announcements without auth"""
        response = announcements_client.get("/announcements/all")
        
        assert response.status_code == 422


class TestCreateAnnouncementEndpoint:
    """Test create announcement endpoint"""
    
    def test_create_announcement_success(self, announcements_client, sample_teacher):
        """Test successful announcement creation"""
        future = (date.today() + timedelta(days=10)).isoformat()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            
            oid = ObjectId()
            mock_ann.insert_one.return_value = MagicMock(inserted_id=oid)
            mock_ann.find_one.return_value = {
                "_id": oid,
                "message": "New announcement",
                "expiration_date": future,
            }
            
            response = announcements_client.post(
                "/announcements",
                params={
                    "message": "New announcement",
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["message"] == "New announcement"
    
    def test_create_announcement_with_start_date(self, announcements_client, sample_teacher):
        """Test creating announcement with start_date"""
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=10)).isoformat()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            
            oid = ObjectId()
            mock_ann.insert_one.return_value = MagicMock(inserted_id=oid)
            mock_ann.find_one.return_value = {
                "_id": oid,
                "message": "Scheduled announcement",
                "start_date": today,
                "expiration_date": future,
            }
            
            response = announcements_client.post(
                "/announcements",
                params={
                    "message": "Scheduled announcement",
                    "start_date": today,
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 201
    
    def test_create_announcement_invalid_expiration_date(self, announcements_client, sample_teacher):
        """Test creating announcement with invalid expiration_date"""
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = announcements_client.post(
                "/announcements",
                params={
                    "message": "Test",
                    "expiration_date": "invalid-date",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 422
            assert "expiration_date must be a valid ISO date" in response.json()["detail"]
    
    def test_create_announcement_invalid_start_date(self, announcements_client, sample_teacher):
        """Test creating announcement with invalid start_date"""
        future = (date.today() + timedelta(days=10)).isoformat()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = announcements_client.post(
                "/announcements",
                params={
                    "message": "Test",
                    "start_date": "invalid-date",
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 422
            assert "start_date must be a valid ISO date" in response.json()["detail"]
    
    def test_create_announcement_start_after_expiration(self, announcements_client, sample_teacher):
        """Test creating announcement with start_date after expiration_date"""
        today = date.today().isoformat()
        past = (date.today() - timedelta(days=10)).isoformat()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = announcements_client.post(
                "/announcements",
                params={
                    "message": "Test",
                    "start_date": today,
                    "expiration_date": past,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 422
            assert "start_date must not be after" in response.json()["detail"]


class TestUpdateAnnouncementEndpoint:
    """Test update announcement endpoint"""
    
    def test_update_announcement_success(self, announcements_client, sample_teacher):
        """Test successful announcement update"""
        future = (date.today() + timedelta(days=10)).isoformat()
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            
            mock_result = MagicMock()
            mock_result.matched_count = 1
            mock_ann.update_one.return_value = mock_result
            mock_ann.find_one.return_value = {
                "_id": oid,
                "message": "Updated announcement",
                "expiration_date": future,
            }
            
            response = announcements_client.put(
                f"/announcements/{oid}",
                params={
                    "message": "Updated announcement",
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 200
    
    def test_update_announcement_with_start_date(self, announcements_client, sample_teacher):
        """Test updating announcement and setting start_date"""
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=10)).isoformat()
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            
            mock_result = MagicMock()
            mock_result.matched_count = 1
            mock_ann.update_one.return_value = mock_result
            mock_ann.find_one.return_value = {
                "_id": oid,
                "message": "Updated",
                "start_date": today,
                "expiration_date": future,
            }
            
            response = announcements_client.put(
                f"/announcements/{oid}",
                params={
                    "message": "Updated",
                    "start_date": today,
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 200
    
    def test_update_announcement_invalid_expiration_date(self, announcements_client, sample_teacher):
        """Test updating announcement with invalid expiration_date"""
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = announcements_client.put(
                f"/announcements/{oid}",
                params={
                    "message": "Test",
                    "expiration_date": "invalid-date",
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 422
            assert "expiration_date must be a valid ISO date" in response.json()["detail"]
    
    def test_update_announcement_invalid_start_date(self, announcements_client, sample_teacher):
        """Test updating announcement with invalid start_date"""
        future = (date.today() + timedelta(days=10)).isoformat()
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = announcements_client.put(
                f"/announcements/{oid}",
                params={
                    "message": "Test",
                    "start_date": "invalid-date",
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 422
            assert "start_date must be a valid ISO date" in response.json()["detail"]
    
    def test_update_announcement_start_after_expiration(self, announcements_client, sample_teacher):
        """Test updating announcement with start_date after expiration_date"""
        today = date.today().isoformat()
        past = (date.today() - timedelta(days=10)).isoformat()
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = announcements_client.put(
                f"/announcements/{oid}",
                params={
                    "message": "Test",
                    "start_date": today,
                    "expiration_date": past,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 422
            assert "start_date must not be after" in response.json()["detail"]
    
    def test_update_announcement_invalid_id(self, announcements_client, sample_teacher):
        """Test updating announcement with invalid ID"""
        future = (date.today() + timedelta(days=10)).isoformat()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = announcements_client.put(
                "/announcements/invalid-id",
                params={
                    "message": "Test",
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 404
    
    def test_update_announcement_not_found(self, announcements_client, sample_teacher):
        """Test updating non-existent announcement"""
        future = (date.today() + timedelta(days=10)).isoformat()
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            
            mock_result = MagicMock()
            mock_result.matched_count = 0
            mock_ann.update_one.return_value = mock_result
            
            response = announcements_client.put(
                f"/announcements/{oid}",
                params={
                    "message": "Test",
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 404
    
    def test_update_announcement_clear_start_date(self, announcements_client, sample_teacher):
        """Test updating announcement and clearing start_date"""
        future = (date.today() + timedelta(days=10)).isoformat()
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            
            mock_result = MagicMock()
            mock_result.matched_count = 1
            mock_ann.update_one.return_value = mock_result
            mock_ann.find_one.return_value = {
                "_id": oid,
                "message": "Updated",
                "expiration_date": future,
            }
            
            response = announcements_client.put(
                f"/announcements/{oid}",
                params={
                    "message": "Updated",
                    "expiration_date": future,
                    "teacher_username": "mrodriguez"
                }
            )
            
            assert response.status_code == 200
            # Verify unset was called
            assert mock_ann.update_one.call_count >= 1


class TestDeleteAnnouncementEndpoint:
    """Test delete announcement endpoint"""
    
    def test_delete_announcement_success(self, announcements_client, sample_teacher):
        """Test successful announcement deletion"""
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            
            mock_result = MagicMock()
            mock_result.deleted_count = 1
            mock_ann.delete_one.return_value = mock_result
            
            response = announcements_client.delete(
                f"/announcements/{oid}",
                params={"teacher_username": "mrodriguez"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "deleted successfully" in data["message"]
    
    def test_delete_announcement_invalid_id(self, announcements_client, sample_teacher):
        """Test deleting announcement with invalid ID"""
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers:
            mock_teachers.find_one.return_value = sample_teacher
            
            response = announcements_client.delete(
                "/announcements/invalid-id",
                params={"teacher_username": "mrodriguez"}
            )
            
            assert response.status_code == 404
    
    def test_delete_announcement_not_found(self, announcements_client, sample_teacher):
        """Test deleting non-existent announcement"""
        oid = ObjectId()
        
        with patch('src.backend.routers.announcements.teachers_collection') as mock_teachers, \
             patch('src.backend.routers.announcements.announcements_collection') as mock_ann:
            
            mock_teachers.find_one.return_value = sample_teacher
            
            mock_result = MagicMock()
            mock_result.deleted_count = 0
            mock_ann.delete_one.return_value = mock_result
            
            response = announcements_client.delete(
                f"/announcements/{oid}",
                params={"teacher_username": "mrodriguez"}
            )
            
            assert response.status_code == 404
