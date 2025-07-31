"""
Performance and load tests using Locust.
Run with: locust -f backend/tests/performance/test_load.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between, events
import random
import time
import json


class MarkerEngineUser(HttpUser):
    """Simulates a user interacting with the MarkerEngine API."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts."""
        # Check health endpoint first
        response = self.client.get("/healthz")
        if response.status_code != 200:
            print(f"Health check failed: {response.status_code}")
    
    @task(5)
    def analyze_text(self):
        """Most common task - analyze text for markers."""
        test_texts = [
            "Der Patient zeigt deutliche Anzeichen von AMBIVALENZ.",
            "Es besteht eine ausgeprägte RESONANZ zwischen den Beteiligten.",
            "Die FAMILIENDYNAMIK ist von komplexen Mustern geprägt.",
            "Wir beobachten eine Form der CO-REGULATION im System.",
            "Der REAKTIVE KONTROLLSPIRALE zeigt sich in verschiedenen Situationen.",
        ]
        
        request_data = {
            "text": random.choice(test_texts),
            "language": "de",
            "options": {
                "include_metadata": True,
                "confidence_threshold": random.uniform(0.6, 0.9)
            }
        }
        
        with self.client.post(
            "/api/v1/analyze",
            json=request_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "markers" not in data:
                    response.failure("Missing markers in response")
                else:
                    # Track custom metrics
                    marker_count = len(data["markers"])
                    response.request_meta["marker_count"] = marker_count
            elif response.status_code == 429:
                response.success()  # Rate limiting is expected
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(3)
    def get_markers(self):
        """Get list of available markers."""
        with self.client.get(
            "/api/v1/markers",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                markers = response.json()
                if not isinstance(markers, list):
                    response.failure("Expected list of markers")
            else:
                response.failure(f"Failed to get markers: {response.status_code}")
    
    @task(2)
    def get_specific_marker(self):
        """Get details of a specific marker."""
        # First get list of markers
        response = self.client.get("/api/v1/markers")
        if response.status_code == 200 and response.json():
            markers = response.json()
            if markers:
                marker_id = random.choice(markers)["id"]
                self.client.get(f"/api/v1/markers/{marker_id}")
    
    @task(1)
    def get_metrics(self):
        """Get system metrics - less frequent task."""
        self.client.get("/api/v1/metrics")
    
    @task(1)
    def get_dashboard(self):
        """Get dashboard data - aggregated view."""
        self.client.get("/api/v1/dashboard")


class AdvancedMarkerEngineUser(HttpUser):
    """Advanced user scenarios with complex workflows."""
    
    wait_time = between(2, 5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_markers = []
    
    @task(3)
    def complete_analysis_workflow(self):
        """Complete workflow: analyze -> review markers -> get details."""
        # Step 1: Analyze text
        analysis_response = self.client.post(
            "/api/v1/analyze",
            json={
                "text": "Complex text with multiple markers for testing.",
                "language": "de"
            }
        )
        
        if analysis_response.status_code == 200:
            markers = analysis_response.json().get("markers", [])
            
            # Step 2: Get details for each marker
            for marker in markers[:3]:  # Limit to 3 to avoid overload
                self.client.get(f"/api/v1/markers/{marker['id']}")
    
    @task(1)
    def create_and_manage_marker(self):
        """Create, update, and delete marker lifecycle."""
        # Create
        create_response = self.client.post(
            "/api/v1/markers",
            json={
                "name": f"PERF_TEST_MARKER_{int(time.time())}",
                "category": "performance_test",
                "confidence": 0.85,
                "description": "Performance test marker"
            }
        )
        
        if create_response.status_code == 201:
            marker_id = create_response.json()["id"]
            self.created_markers.append(marker_id)
            
            # Update
            self.client.patch(
                f"/api/v1/markers/{marker_id}",
                json={"confidence": 0.90}
            )
            
            # Delete (50% chance to keep some markers)
            if random.random() > 0.5:
                self.client.delete(f"/api/v1/markers/{marker_id}")
                self.created_markers.remove(marker_id)
    
    @task(2)
    def burst_analysis(self):
        """Simulate burst of analysis requests."""
        for _ in range(random.randint(3, 7)):
            self.client.post(
                "/api/v1/analyze",
                json={
                    "text": f"Burst test {time.time()}",
                    "language": "de"
                }
            )
            time.sleep(0.1)  # Small delay between burst requests


# Custom event handlers for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, **kwargs):
    """Track custom metrics per request."""
    if hasattr(response, 'request_meta') and 'marker_count' in response.request_meta:
        # Could send to monitoring system
        marker_count = response.request_meta['marker_count']
        print(f"Markers found: {marker_count}")


# Standalone execution for debugging
if __name__ == "__main__":
    from locust.env import Environment
    from locust.stats import StatsCSVFileWriter
    
    # Setup Environment
    env = Environment(user_classes=[MarkerEngineUser, AdvancedMarkerEngineUser])
    env.create_local_runner()
    
    # Start test
    env.runner.start(10, spawn_rate=2)  # 10 users, 2 per second
    
    # Run for 60 seconds
    time.sleep(60)
    
    # Stop
    env.runner.quit()
    
    # Print statistics
    print("\nTest Results:")
    print(f"Total requests: {env.stats.total.num_requests}")
    print(f"Failed requests: {env.stats.total.num_failures}")
    print(f"Median response time: {env.stats.total.median_response_time}ms")
    print(f"95th percentile: {env.stats.total.get_response_time_percentile(0.95)}ms")