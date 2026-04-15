"""
Integration tests for FastAPI endpoints using TestClient.

Tests all four endpoints:
- GET / (redirect to static files)
- GET /activities (get all activities)
- POST /activities/{activity_name}/signup (sign up for activity)
- DELETE /activities/{activity_name}/participants (remove from activity)
"""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"
    
    def test_root_follows_redirect(self, client):
        """Test that following the redirect returns status 200"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_all_activities_returns_expected_structure(self, client):
        """Test that activities have the expected structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check we have all 9 activities
        assert len(data) == 9
        
        # Check that Chess Club exists with proper structure
        assert "Chess Club" in data
        chess = data["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess
        assert isinstance(chess["participants"], list)
    
    def test_get_all_activities_has_all_expected_activities(self, client):
        """Test that all 9 expected activities are present"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Club", "Soccer Team", "Art Club",
            "Drama Club", "Debate Team", "Science Club"
        ]
        
        for activity in expected_activities:
            assert activity in data
    
    def test_get_activities_preserves_state(self, client, sample_email):
        """Test that multiple GET requests return consistent state"""
        response1 = client.get("/activities")
        data1 = response1.json()
        
        response2 = client.get("/activities")
        data2 = response2.json()
        
        assert data1 == data2


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, sample_email):
        """Test successful signup for an activity"""
        response = client.post(
            f"/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client, sample_email):
        """Test that signup actually adds the participant to the activity"""
        # Sign up
        client.post(
            f"/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert sample_email in data["Chess Club"]["participants"]
    
    def test_signup_to_nonexistent_activity_returns_404(self, client, sample_email, nonexistent_activity):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_duplicate_signup_returns_400(self, client, existing_activity):
        """Test that signing up twice for the same activity returns 400"""
        # First signup
        response1 = client.post(
            f"/activities/{existing_activity}/signup",
            params={"email": "michael@mergington.edu"}  # Already signed up
        )
        assert response1.status_code == 400
        data = response1.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_to_different_activities(self, client, sample_email):
        """Test that same student can sign up for multiple different activities"""
        # Sign up for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity (different)
        response2 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": sample_email}
        )
        assert response2.status_code == 200
        
        # Verify both signups succeeded
        response = client.get("/activities")
        data = response.json()
        assert sample_email in data["Chess Club"]["participants"]
        assert sample_email in data["Basketball Club"]["participants"]
    
    def test_signup_without_email_parameter(self, client):
        """Test that signup without email parameter fails"""
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_signup_with_empty_email(self, client):
        """Test signup with empty email string"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        assert response.status_code == 200 or response.status_code == 400
        # Note: Behavior depends on validation implementation
    
    def test_signup_multiple_students_same_activity(self, client):
        """Test that multiple different students can sign up for same activity"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(
            "/activities/Art Club/signup",
            params={"email": email1}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": email2}
        )
        assert response2.status_code == 200
        
        # Both should be in the activity
        response = client.get("/activities")
        data = response.json()
        assert email1 in data["Art Club"]["participants"]
        assert email2 in data["Art Club"]["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""
    
    def test_remove_existing_participant_succeeds(self, client):
        """Test removing an existing participant from an activity"""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
    
    def test_remove_participant_actually_removes(self, client):
        """Test that participant is actually removed from activity"""
        # Remove
        client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        
        # Verify removal
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
    
    def test_remove_from_nonexistent_activity_returns_404(self, client, nonexistent_activity):
        """Test removing from nonexistent activity returns 404"""
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants",
            params={"email": "some@email.com"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_remove_nonexistent_participant_returns_404(self, client, existing_activity):
        """Test removing nonexistent participant returns 404"""
        response = client.delete(
            f"/activities/{existing_activity}/participants",
            params={"email": "nonexistent@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]
    
    def test_remove_without_email_parameter(self, client):
        """Test that remove without email parameter fails"""
        response = client.delete("/activities/Chess Club/participants")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_remove_then_readd_same_participant(self, client):
        """Test that removed participant can be re-added"""
        # Remove
        response1 = client.delete(
            "/activities/Art Club/participants",
            params={"email": "isabella@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Re-add (should succeed since they're no longer signed up)
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": "isabella@mergington.edu"}
        )
        assert response2.status_code == 200
    
    def test_remove_multiple_participants(self, client):
        """Test removing multiple participants from same activity"""
        email1 = "michael@mergington.edu"
        email2 = "daniel@mergington.edu"
        
        response1 = client.delete(
            "/activities/Chess Club/participants",
            params={"email": email1}
        )
        assert response1.status_code == 200
        
        response2 = client.delete(
            "/activities/Chess Club/participants",
            params={"email": email2}
        )
        assert response2.status_code == 200
        
        # Verify both are removed
        response = client.get("/activities")
        data = response.json()
        assert email1 not in data["Chess Club"]["participants"]
        assert email2 not in data["Chess Club"]["participants"]
