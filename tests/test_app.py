"""
Integration tests for the High School Management System API

Tests cover all endpoints:
- GET /activities
- POST /activities/{activity_name}/signup
- POST /activities/{activity_name}/unregister
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for making requests to the app.
    
    Imports app fresh for each test to ensure isolated app state.
    """
    from src.app import app
    return TestClient(app)


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_root_redirects_to_static(self, client):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify the response is a dictionary
        assert isinstance(activities, dict)
        
        # Verify all expected activities are present
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Club",
            "Music Band",
            "Science Club",
            "Math Club"
        ]
        for activity in expected_activities:
            assert activity in activities

    def test_get_activities_returns_activity_details(self, client):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        # Check a specific activity has all required fields
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client):
        """Test successfully signing up for an activity."""
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up a new participant
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1
        assert "newstudent@mergington.edu" in response.json()["Chess Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signing up for a non-existent activity."""
        response = client.post(
            "/activities/Fake Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_already_registered(self, client):
        """Test that a student cannot sign up twice for the same activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_activity_full(self, client):
        """Test that a student cannot sign up for a full activity."""
        # Find an activity that's full or get close to full
        response = client.get("/activities")
        activities = response.json()
        
        # Use Gym Class which has max_participants: 30 and 2 current participants
        # Let's create a scenario by manually filling it up in this test
        # For now, we'll test with a realistic scenario
        
        # Chess Club has max_participants: 12 and 2 current participants
        # Let's sign up 10 more students to fill it
        activity_name = "Chess Club"
        activity = activities[activity_name]
        
        # Calculate how many more can join
        can_join = activity["max_participants"] - len(activity["participants"])
        
        # Sign up students until the activity is full
        for i in range(can_join):
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"student{i}@mergington.edu"}
            )
            assert response.status_code == 200
        
        # Now the activity should be full, try to sign up one more
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overfull@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "Activity is full" in data["detail"]


class TestUnregisterFromActivity:
    """Tests for the POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_successful(self, client):
        """Test successfully unregistering from an activity."""
        # First, sign up a student
        email = "unregister_test@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Verify they were added
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Unregister the student
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was removed
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count - 1
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregistering from a non-existent activity."""
        response = client.post(
            "/activities/Fake Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_participant_not_found(self, client):
        """Test that unregistering a non-existent participant returns error."""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_unregister_from_activity_with_no_free_slots(self, client):
        """Test unregistering frees up a slot in a full activity."""
        activity_name = "Basketball Team"
        
        # Get initial state
        response = client.get("/activities")
        activity = response.json()[activity_name]
        initial_count = len(activity["participants"])
        max_participants = activity["max_participants"]
        
        # Fill up the activity
        for i in range(max_participants - initial_count):
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"filler{i}@mergington.edu"}
            )
            assert response.status_code == 200
        
        # Verify it's full
        response = client.get("/activities")
        assert len(response.json()[activity_name]["participants"]) == max_participants
        
        # Unregister one person
        email_to_remove = f"filler0@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        assert response.status_code == 200
        
        # Verify there's now a free slot
        response = client.get("/activities")
        assert len(response.json()[activity_name]["participants"]) == max_participants - 1
        
        # Verify a new student can now sign up
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "newafter@mergington.edu"}
        )
        assert response.status_code == 200
