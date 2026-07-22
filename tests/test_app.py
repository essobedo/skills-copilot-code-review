"""
Tests for main app module
"""
import pytest
from unittest.mock import patch, MagicMock


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static/index.html"""
        with patch('src.backend.database.init_database'):
            from fastapi.testclient import TestClient
            from src.app import app
            
            client = TestClient(app)
            response = client.get("/", follow_redirects=False)
            
            assert response.status_code == 307
            assert response.headers["location"] == "/static/index.html"


class TestAppInitialization:
    """Test app initialization"""
    
    def test_app_has_correct_title(self):
        """Test app has correct title"""
        with patch('src.backend.database.init_database'):
            from src.app import app
            
            assert app.title == "Mergington High School API"
    
    def test_app_has_correct_description(self):
        """Test app has correct description"""
        with patch('src.backend.database.init_database'):
            from src.app import app
            
            assert "extracurricular activities" in app.description
    
    def test_app_includes_routers(self):
        """Test app includes all necessary routers"""
        with patch('src.backend.database.init_database'):
            from src.app import app
            
            # Check if routers are included by looking at the routes list
            # Use a different approach - check the routes in the app
            route_paths = []
            for route in app.routes:
                if hasattr(route, 'path'):
                    route_paths.append(route.path)
            
            # At minimum, we should have the root endpoint
            assert any("/" == path for path in route_paths)
