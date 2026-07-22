"""
Shared fixtures and configuration for tests
"""
import pytest
from unittest.mock import MagicMock, patch
from bson import ObjectId


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB collections"""
    with patch('src.backend.database.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        
        # Mock collections
        activities_collection = MagicMock()
        teachers_collection = MagicMock()
        announcements_collection = MagicMock()
        
        mock_db.__getitem__.side_effect = lambda name: {
            'activities': activities_collection,
            'teachers': teachers_collection,
            'announcements': announcements_collection,
        }[name]
        
        yield {
            'client': mock_client,
            'db': mock_db,
            'activities': activities_collection,
            'teachers': teachers_collection,
            'announcements': announcements_collection,
        }


@pytest.fixture
def mock_password_hasher():
    """Mock Argon2 password hasher"""
    with patch('src.backend.database.PasswordHasher') as mock_hasher:
        hasher_instance = MagicMock()
        mock_hasher.return_value = hasher_instance
        hasher_instance.hash.return_value = '$argon2id$v=19$m=65540,t=3,p=4$...'
        hasher_instance.verify.return_value = None  # No exception means success
        yield hasher_instance


@pytest.fixture
def fastapi_client():
    """Create a test client for FastAPI app"""
    from fastapi.testclient import TestClient
    from src.app import app
    return TestClient(app)


@pytest.fixture
def sample_teacher():
    """Sample teacher data"""
    return {
        "_id": "mrodriguez",
        "username": "mrodriguez",
        "display_name": "Ms. Rodriguez",
        "password": "$argon2id$v=19$m=65540,t=3,p=4$...",
        "role": "teacher"
    }


@pytest.fixture
def sample_activity():
    """Sample activity data"""
    return {
        "_id": "Chess Club",
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
        "schedule_details": {
            "days": ["Monday", "Friday"],
            "start_time": "15:15",
            "end_time": "16:45"
        },
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    }


@pytest.fixture
def sample_announcement():
    """Sample announcement data"""
    return {
        "_id": ObjectId(),
        "message": "🎉 Activity registration is now open!",
        "expiration_date": "2026-09-30",
        "start_date": "2026-07-22"
    }
