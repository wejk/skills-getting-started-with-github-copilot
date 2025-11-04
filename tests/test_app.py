from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 301  # Permanent redirect
    assert response.headers["location"] == "/static/index.html"

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) > 0
    
    # Check activity structure
    for activity_name, details in activities.items():
        assert isinstance(activity_name, str)
        assert isinstance(details, dict)
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)

def test_signup_for_activity():
    # Test successful signup
    response = client.post("/activities/Chess Club/signup?email=test@mergington.edu")
    assert response.status_code == 200
    assert response.json()["message"] == "Signed up test@mergington.edu for Chess Club"

    # Test duplicate signup
    response = client.post("/activities/Chess Club/signup?email=test@mergington.edu")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()

    # Test non-existent activity
    response = client.post("/activities/NonExistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unregister_participant():
    # First sign up a test participant
    email = "unregister_test@mergington.edu"
    activity = "Chess Club"
    client.post(f"/activities/{activity}/signup?email={email}")

    # Test successful unregistration
    response = client.delete(f"/activities/{activity}/participants/{email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity}"

    # Test unregistering non-registered participant
    response = client.delete(f"/activities/{activity}/participants/{email}")
    assert response.status_code == 404
    assert "not registered" in response.json()["detail"].lower()

    # Test unregistering from non-existent activity
    response = client.delete(f"/activities/NonExistentClub/participants/{email}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_max_participants():
    activity = "Chess Club"
    # Get current activity data
    response = client.get("/activities")
    activities = response.json()
    max_participants = activities[activity]["max_participants"]
    
    # Fill up the activity to maximum
    current_participants = len(activities[activity]["participants"])
    for i in range(current_participants, max_participants):
        email = f"test{i}@mergington.edu"
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
    
    # Try to add one more participant
    response = client.post(f"/activities/{activity}/signup?email=overflow@mergington.edu")
    assert response.status_code == 400
    assert "activity is full" in response.json()["detail"].lower()