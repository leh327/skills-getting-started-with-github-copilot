"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a known state before each test"""
    original_participants = {
        "Chess Club": ["michael@mergington.edu", "daniel@mergington.edu"],
        "Programming Class": ["emma@mergington.edu", "sophia@mergington.edu"],
        "Gym Class": ["john@mergington.edu", "olivia@mergington.edu"],
        "Soccer Team": ["liam@mergington.edu", "noah@mergington.edu"],
        "Track and Field": ["ava@mergington.edu", "mia@mergington.edu"],
        "Art Club": ["isabella@mergington.edu", "harper@mergington.edu"],
        "Drama Club": ["charlie@mergington.edu", "lucy@mergington.edu"],
        "Debate Team": ["ethan@mergington.edu", "olivia@mergington.edu"],
        "Science Olympiad": ["sophia@mergington.edu", "jack@mergington.edu"],
    }
    
    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"] = participants.copy()
    
    yield
    
    # Cleanup after test
    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"] = participants.copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test successful retrieval of all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all activities are returned
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        
    def test_get_activities_participants(self, client):
        """Test that participants are correctly listed"""
        response = client.get("/activities")
        data = response.json()
        
        chess_participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
        
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants
        
    def test_signup_duplicate_fails(self, client):
        """Test that signing up twice fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities_data = client.get("/activities").json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered michael@mergington.edu from Chess Club" in data["message"]
        
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants
        
    def test_unregister_not_registered_fails(self, client):
        """Test that unregistering someone not registered fails"""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
        
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister for non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_unregister_and_resign_up(self, client):
        """Test that a student can unregister and sign up again"""
        email = "flaky@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert email in client.get("/activities").json()["Chess Club"]["participants"]
        
        # Unregister
        client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert email not in client.get("/activities").json()["Chess Club"]["participants"]
        
        # Sign up again
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in client.get("/activities").json()["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
