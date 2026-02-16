"""
Tests for the FastAPI Mergington High School Activities application.
"""

import pytest
from fastapi import status
from src.app import activities


class TestActivitiesAPI:
    """Test class for activities API endpoints."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        # Should redirect to static files
        assert "index.html" in str(response.url) or response.history

    def test_get_activities(self, client, reset_activities):
        """Test getting all activities."""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # Should have 9 activities
        
        # Check that Chess Club exists with expected structure
        assert "Chess Club" in data
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        # Test signing up a new student for Chess Club
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]
        
        # Verify the student was added to the activity
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity."""
        response = client.post(
            "/activities/Non-existent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test signing up a student who is already registered."""
        # Try to sign up michael@mergington.edu for Chess Club (already registered)
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"]

    def test_signup_url_encoding(self, client, reset_activities):
        """Test signup with URL encoded activity names and emails."""
        # Test with spaces in activity name and special characters in email
        response = client.post(
            "/activities/Programming%20Class/signup?email=test%2Bstudent@mergington.edu"
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Check that the email was properly decoded and added
        assert "test+student@mergington.edu" in activities["Programming Class"]["participants"]

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        # Unregister michael@mergington.edu from Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "message" in result
        assert "michael@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]
        
        # Verify the student was removed from the activity
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregistration from non-existent activity."""
        response = client.delete(
            "/activities/Non-existent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]

    def test_unregister_student_not_registered(self, client, reset_activities):
        """Test unregistering a student who is not registered for the activity."""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        result = response.json()
        assert "detail" in result
        assert "not signed up" in result["detail"]

    def test_unregister_url_encoding(self, client, reset_activities):
        """Test unregistration with URL encoded activity names and emails."""
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=emma@mergington.edu"
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the student was removed
        assert "emma@mergington.edu" not in activities["Programming Class"]["participants"]

    def test_multiple_operations_sequence(self, client, reset_activities):
        """Test a sequence of signup and unregister operations."""
        activity_name = "Art Workshop"
        test_email = "sequence.test@mergington.edu"
        
        # First, sign up the student
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        assert signup_response.status_code == status.HTTP_200_OK
        assert test_email in activities[activity_name]["participants"]
        
        # Then, unregister the student
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={test_email}"
        )
        assert unregister_response.status_code == status.HTTP_200_OK
        assert test_email not in activities[activity_name]["participants"]
        
        # Try to unregister again (should fail)
        unregister_again_response = client.delete(
            f"/activities/{activity_name}/unregister?email={test_email}"
        )
        assert unregister_again_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_activity_data_persistence(self, client, reset_activities):
        """Test that activity data persists between requests."""
        # Sign up a student
        client.post("/activities/Drama Club/signup?email=persistence.test@mergington.edu")
        
        # Get activities and verify the student is there
        response = client.get("/activities")
        data = response.json()
        assert "persistence.test@mergington.edu" in data["Drama Club"]["participants"]
        
        # Make another request and verify data persists
        response = client.get("/activities")
        data = response.json()
        assert "persistence.test@mergington.edu" in data["Drama Club"]["participants"]

    def test_max_participants_constraint(self, client, reset_activities):
        """Test that activities respect max_participants constraint indirectly."""
        # This test verifies we can access max_participants field
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "max_participants" in activity_data
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0
            assert len(activity_data["participants"]) <= activity_data["max_participants"]