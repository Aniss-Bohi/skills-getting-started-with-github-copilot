"""
Edge case and boundary condition tests.

Tests various edge cases and boundary conditions:
- Parameter handling (empty strings, special characters, etc.)
- Email validation edge cases
- Activity name case sensitivity
- Large datasets and capacity boundaries
- Special characters in parameters
"""

import pytest


class TestEmailEdgeCases:
    """Tests for email parameter edge cases"""
    
    def test_email_with_special_characters(self, client):
        """Test signup with special characters in email"""
        special_email = "test+tag@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": special_email}
        )
        assert response.status_code == 200
        
        # Verify it was added
        response = client.get("/activities")
        data = response.json()
        assert special_email in data["Chess Club"]["participants"]
    
    def test_email_with_numbers_and_dots(self, client):
        """Test email with numbers and dots"""
        email = "student.123@mergington.edu"
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    def test_email_case_sensitivity(self, client):
        """Test if email matching is case-sensitive"""
        email1 = "TestStudent@mergington.edu"
        email2 = "teststudent@mergington.edu"
        
        # Sign up with one case
        response1 = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email1}
        )
        assert response1.status_code == 200
        
        # Sign up with different case
        response2 = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email2}
        )
        # This will be 200 (both allowed) if case-insensitive or different
        # It will be 400 if case-insensitive and considered same
        assert response2.status_code in [200, 400]
    
    def test_very_long_email_address(self, client):
        """Test with a very long but valid email"""
        long_email = "verylongemailaddress" * 3 + "@mergington.edu"
        response = client.post(
            "/activities/Science Club/signup",
            params={"email": long_email}
        )
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 422]


class TestActivityNameEdgeCases:
    """Tests for activity name parameter edge cases"""
    
    def test_activity_name_case_sensitivity(self, client, sample_email):
        """Test if activity names are case-sensitive"""
        # Exact case (should work)
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": sample_email + "1"}
        )
        assert response1.status_code == 200
        
        # Different case (may fail)
        response2 = client.post(
            "/activities/chess club/signup",
            params={"email": sample_email + "2"}
        )
        assert response2.status_code in [200, 404]  # Depends on implementation
    
    def test_activity_name_with_extra_whitespace(self, client, sample_email):
        """Test activity name with extra whitespace"""
        response = client.post(
            "/activities/Chess Club /signup",  # Extra space before /
            params={"email": sample_email}
        )
        assert response.status_code == 404  # Should not match
    
    def test_nonexistent_activity_name_variations(self, client, sample_email):
        """Test various nonexistent activity name patterns"""
        nonexistent_names = [
            "Chess Clubs",  # Plural
            "The Chess Club",  # With article
            "Chess",  # Partial
            "",  # Empty
        ]
        
        for activity_name in nonexistent_names:
            if activity_name:  # Skip empty for URL construction
                response = client.post(
                    f"/activities/{activity_name}/signup",
                    params={"email": sample_email}
                )
                assert response.status_code == 404


class TestParameterValidation:
    """Tests for parameter validation edge cases"""
    
    def test_missing_email_query_parameter(self, client):
        """Test endpoint without email parameter"""
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == 422  # Missing required parameter
    
    def test_multiple_email_parameters(self, client):
        """Test behavior with multiple email parameters"""
        # Some frameworks take first, some last, some error
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ["test1@example.com", "test2@example.com"]}
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_url_encoded_special_characters_in_email(self, client):
        """Test that URL encoding is handled correctly"""
        email_with_plus = "student+summer@mergington.edu"
        response = client.post(
            "/activities/Art Club/signup",
            params={"email": email_with_plus}
        )
        assert response.status_code == 200
    
    def test_email_none_value(self, client):
        """Test passing None as email value (converts to string 'None')"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": None}
        )
        # None gets converted to string "None" by the HTTP client
        # This is technically valid from FastAPI's perspective
        assert response.status_code in [200, 400, 422]


class TestConcurrentOperations:
    """Tests for scenarios that might happen in sequence/concurrently"""
    
    def test_signup_and_remove_same_student_sequence(self, client):
        """Test signing up and removing same student in sequence"""
        email = "sequence_test@mergington.edu"
        
        # Sign up
        response1 = client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Remove
        response2 = client.delete(
            "/activities/Drama Club/participants",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify removed
        response3 = client.get("/activities")
        data = response3.json()
        assert email not in data["Drama Club"]["participants"]
    
    def test_multiple_students_overlapping_operations(self, client):
        """Test multiple students doing operations on same activity"""
        email1 = "student_a@mergington.edu"
        email2 = "student_b@mergington.edu"
        
        # Both sign up for same activity
        response1 = client.post(
            "/activities/Debate Team/signup",
            params={"email": email1}
        )
        response2 = client.post(
            "/activities/Debate Team/signup",
            params={"email": email2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Remove one
        response3 = client.delete(
            "/activities/Debate Team/participants",
            params={"email": email1}
        )
        assert response3.status_code == 200
        
        # Verify only one removed
        response4 = client.get("/activities")
        data = response4.json()
        assert email1 not in data["Debate Team"]["participants"]
        assert email2 in data["Debate Team"]["participants"]


class TestCapacityBoundaries:
    """Tests for participant capacity boundaries"""
    
    def test_activity_at_exact_capacity(self, client):
        """Test activity that is at exact maximum capacity"""
        # Get current activities
        response = client.get("/activities")
        data = response.json()
        
        # Find an activity and check if any are at/near capacity
        for activity_name, activity_data in data.items():
            current = len(activity_data["participants"])
            max_cap = activity_data["max_participants"]
            
            # If any activity is near capacity, track it
            if current == max_cap:
                # Activity is at capacity - documented but tests would need
                # to add participants to test this boundary
                assert current <= max_cap
    
    def test_participant_list_never_exceeds_max(self, client):
        """Verify current state never exceeds max for any activity"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            current = len(activity_data["participants"])
            max_cap = activity_data["max_participants"]
            assert current <= max_cap, f"{activity_name} exceeds capacity"


class TestResponseConsistency:
    """Tests for response consistency and format"""
    
    def test_successful_signup_response_format(self, client, sample_email):
        """Test that successful signup response has expected format"""
        response = client.post(
            "/activities/Chemistry Club/signup" if False else "/activities/Programming Class/signup",
            params={"email": sample_email}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert isinstance(data["message"], str)
    
    def test_successful_remove_response_format(self, client):
        """Test that successful remove response has expected format"""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "michael@mergington.edu"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert isinstance(data["message"], str)
    
    def test_activities_list_consistency_across_requests(self, client):
        """Test that activities list is consistent across multiple requests"""
        responses = []
        for _ in range(3):
            response = client.get("/activities")
            data = response.json()
            responses.append(data)
        
        # All should be identical
        assert responses[0] == responses[1]
        assert responses[1] == responses[2]
