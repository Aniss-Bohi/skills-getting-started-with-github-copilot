"""
Pytest configuration and shared fixtures for FastAPI tests.

This module provides:
- test_app: FastAPI app instance for testing
- client: TestClient configured for testing the app
- reset_app_state: Fixture that resets app state between tests
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to Python path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def test_app():
    """Provide a FastAPI app instance for testing."""
    return app


@pytest.fixture
def client(test_app):
    """Provide a TestClient for making requests to the app."""
    return TestClient(test_app)


@pytest.fixture(autouse=True)
def reset_app_state():
    """
    Reset the in-memory activities database to initial state before each test.
    
    This fixture uses autouse=True to run before every test automatically,
    ensuring test isolation and preventing test pollution.
    """
    # Save the initial state before any test runs
    initial_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Learn and play competitive basketball",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Soccer Team": {
            "description": "Join the school soccer team and compete in matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": ["alex@mergington.edu", "chris@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore painting, drawing, and other visual arts",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in plays and theatrical productions",
            "schedule": "Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["sophia@mergington.edu", "lucas@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and argumentation skills",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 12,
            "participants": ["andrew@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["ryan@mergington.edu", "mia@mergington.edu"]
        }
    }
    
    # Clear current state and restore initial state
    activities.clear()
    for activity_name, activity_data in initial_activities.items():
        # Create a deep copy to avoid reference issues
        activities[activity_name] = {
            "description": activity_data["description"],
            "schedule": activity_data["schedule"],
            "max_participants": activity_data["max_participants"],
            "participants": activity_data["participants"].copy()
        }
    
    yield  # Run the test
    
    # Clean up after test (not strictly necessary but good practice)
    activities.clear()


@pytest.fixture
def sample_email():
    """Provide a sample email for testing."""
    return "test_student@mergington.edu"


@pytest.fixture
def existing_activity():
    """Provide an existing activity name for testing."""
    return "Chess Club"


@pytest.fixture
def nonexistent_activity():
    """Provide a nonexistent activity name for testing."""
    return "Nonexistent Activity"
