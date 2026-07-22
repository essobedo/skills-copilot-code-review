"""
Tests for database module
"""
import pytest
from unittest.mock import patch, MagicMock
from argon2 import exceptions as argon2_exceptions


class TestHashPassword:
    """Test password hashing"""
    
    def test_hash_password(self, mock_password_hasher):
        """Test hash_password returns a hashed password"""
        with patch('src.backend.database.PasswordHasher') as mock_hasher_class:
            hasher_instance = MagicMock()
            mock_hasher_class.return_value = hasher_instance
            hasher_instance.hash.return_value = 'hashed_password_value'
            
            from src.backend.database import hash_password
            result = hash_password("test_password")
            
            assert result == 'hashed_password_value'
            hasher_instance.hash.assert_called_once_with("test_password")


class TestVerifyPassword:
    """Test password verification"""
    
    def test_verify_password_success(self):
        """Test verify_password returns True for matching password"""
        with patch('src.backend.database.PasswordHasher') as mock_hasher_class:
            hasher_instance = MagicMock()
            mock_hasher_class.return_value = hasher_instance
            hasher_instance.verify.return_value = None  # No exception = success
            
            from src.backend.database import verify_password
            result = verify_password("hashed_pwd", "plain_pwd")
            
            assert result is True
    
    def test_verify_password_mismatch(self):
        """Test verify_password returns False for mismatched password"""
        with patch('src.backend.database.PasswordHasher') as mock_hasher_class:
            hasher_instance = MagicMock()
            mock_hasher_class.return_value = hasher_instance
            hasher_instance.verify.side_effect = argon2_exceptions.VerifyMismatchError()
            
            from src.backend.database import verify_password
            result = verify_password("hashed_pwd", "wrong_pwd")
            
            assert result is False
    
    def test_verify_password_exception(self):
        """Test verify_password returns False for other exceptions"""
        with patch('src.backend.database.PasswordHasher') as mock_hasher_class:
            hasher_instance = MagicMock()
            mock_hasher_class.return_value = hasher_instance
            hasher_instance.verify.side_effect = Exception("Invalid hash")
            
            from src.backend.database import verify_password
            result = verify_password("invalid_hash", "plain_pwd")
            
            assert result is False


class TestInitDatabase:
    """Test database initialization"""
    
    def test_init_database_empty(self):
        """Test init_database populates empty database"""
        with patch('src.backend.database.activities_collection') as mock_activities, \
             patch('src.backend.database.teachers_collection') as mock_teachers, \
             patch('src.backend.database.announcements_collection') as mock_announcements:
            
            # All collections are empty
            mock_activities.count_documents.return_value = 0
            mock_teachers.count_documents.return_value = 0
            mock_announcements.count_documents.return_value = 0
            
            from src.backend.database import init_database
            init_database()
            
            # Verify collections were populated
            assert mock_activities.insert_one.called
            assert mock_teachers.insert_one.called
            assert mock_announcements.insert_one.called
    
    def test_init_database_already_populated(self):
        """Test init_database doesn't override existing data"""
        with patch('src.backend.database.activities_collection') as mock_activities, \
             patch('src.backend.database.teachers_collection') as mock_teachers, \
             patch('src.backend.database.announcements_collection') as mock_announcements:
            
            # All collections already have data
            mock_activities.count_documents.return_value = 1
            mock_teachers.count_documents.return_value = 1
            mock_announcements.count_documents.return_value = 1
            
            from src.backend.database import init_database
            init_database()
            
            # Verify collections were not modified
            mock_activities.insert_one.assert_not_called()
            mock_teachers.insert_one.assert_not_called()
            mock_announcements.insert_one.assert_not_called()
    
    def test_init_database_partial_population(self):
        """Test init_database populates only empty collections"""
        with patch('src.backend.database.activities_collection') as mock_activities, \
             patch('src.backend.database.teachers_collection') as mock_teachers, \
             patch('src.backend.database.announcements_collection') as mock_announcements:
            
            # Activities and teachers exist, announcements don't
            mock_activities.count_documents.return_value = 1
            mock_teachers.count_documents.return_value = 1
            mock_announcements.count_documents.return_value = 0
            
            from src.backend.database import init_database
            init_database()
            
            # Verify only announcements were populated
            mock_activities.insert_one.assert_not_called()
            mock_teachers.insert_one.assert_not_called()
            assert mock_announcements.insert_one.called
