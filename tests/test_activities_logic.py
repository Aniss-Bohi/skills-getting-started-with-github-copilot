"""
Unit tests for application business logic.

Tests the core validation and logic:
- Activity validation (checking if activity exists)
- Participant list management
- Duplicate signup prevention
- Participant limit enforcement
"""

import pytest


class TestActivityValidation:
    """Tests for activity existence validation"""
    
    def test_valid_activity_exists_in_database(self, client):
        """Test that valid activities exist in the database"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activity_data_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
    
    def test_participants_list_is_always_a_list(self, client):
        """Test that participants field is always a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)
    
    def test_max_participants_is_positive_integer(self, client):
        """Test that max_participants is a positive integer"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0


class TestParticipantManagement:
    """Tests for participant list management and validation"""
    
    def test_initial_participants_count_is_correct(self, client):
        """Test that initial participant counts match expected values"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club starts with 2 participants
        assert len(data["Chess Club"]["participants"]) == 2
        
        # Basketball Club starts with 1 participant
        assert len(data["Basketball Club"]["participants"]) == 1
    
    def test_participant_count_increases_after_signup(self, client, sample_email):
        """Test that participant count increases after signup"""
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        # Sign up
        client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email}
        )
        
        # Get new count
        response2 = client.get("/activities")
        new_count = len(response2.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count + 1
    
    def test_participant_count_decreases_after_removal(self, client):
        """Test that participant count decreases after removal"""
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        # Remove a participant
        client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        
        # Get new count
        response2 = client.get("/activities")
        new_count = len(response2.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count - 1
    
    def test_email_in_participant_list_preserved_correctly(self, client, sample_email):
        """Test that email is preserved correctly when added to participants"""
        # Sign up with sample email
        client.post(
            "/activities/Programming Class/signup",
            params={"email": sample_email}
        )
        
        # Verify exact email is in list
        response = client.get("/activities")
        data = response.json()
        assert sample_email in data["Programming Class"]["participants"]


class TestDuplicateSignupPrevention:
    """Tests for duplicate signup prevention logic"""
    
    def test_cannot_signup_if_already_participant(self, client):
        """Test that already-signed-up students cannot sign up again"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
    
    def test_duplicate_signup_error_message_is_informative(self, client):
        """Test that duplicate signup error has clear message"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "daniel@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower() or "duplicate" in data["detail"].lower()
    
    def test_signup_is_idempotent_in_terms_of_validation(self, client, sample_email):
        """Test the idempotent nature of our duplicate check"""
        # First signup succeeds
        response1 = client.post(
            "/activities/Art Club/signup",
            params={"email": sample_email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email fails consistently
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": sample_email}
        )
        assert response2.status_code == 400
        
        # Third attempt also fails - consistent error
        response3 = client.post(
            "/activities/Art Club/signup",
            params={"email": sample_email}
        )
        assert response3.status_code == 400


class TestParticipantLimitLogic:
    """Tests for enforcing participant limits."""
    
    def test_can_view_max_participants_for_activity(self, client):
        """Test that we can retrieve max_participants value"""
        response = client.get("/activities")
        data = response.json()
        
        chess_max = data["Chess Club"]["max_participants"]
        assert chess_max == 12
    
    def test_current_participants_do_not_exceed_limit(self, client):
        """Test that current participants never exceed max_participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            current_count = len(activity_data["participants"])
            max_count = activity_data["max_participants"]
            assert current_count <= max_count
    
    def test_activity_with_most_capacity_is_gym_class(self, client):
        """Test capacity of Gym Class (should have max 30)"""
        response = client.get("/activities")
        data = response.json()
        
        assert data["Gym Class"]["max_participants"] == 30
        assert len(data["Gym Class"]["participants"]) == 2
    
    def test_activity_with_least_capacity_is_chess_or_debate(self, client):
        """Test that Chess Club and Debate Team both have capacity of 12"""
        response = client.get("/activities")
        data = response.json()
        
        assert data["Chess Club"]["max_participants"] == 12
        assert data["Debate Team"]["max_participants"] == 12


class TestErrorHandling:
    """Tests for proper error handling and status codes"""
    
    def test_activity_not_found_returns_404(self, client):
        """Test that nonexistent activity returns 404 on signup"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@example.com"}
        )
        assert response.status_code == 404
    
    def test_participant_not_found_returns_404_on_delete(self, client):
        """Test that nonexistent participant returns 404 on delete"""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "nonexistent@example.com"}
        )
        assert response.status_code == 404
    
    def test_error_responses_contain_detail_field(self, client):
        """Test that error responses have detail field with message"""
        response = client.post(
            "/activities/Nonexistent/signup",
            params={"email": "test@example.com"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
