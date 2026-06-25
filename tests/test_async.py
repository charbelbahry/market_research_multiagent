import pytest
import asyncio
from httpx import ASGITransport, AsyncClient
import time

from app.main import app
from app.config import get_settings

from app.core.mock_engine import MockEngine

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("USE_REAL_CREW", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake_key")
    get_settings.cache_clear()
    
    # Monkeypatch the real CrewEngine.analyze to simulate a blocking workload
    def fake_analyze(self, idea: str):
        time.sleep(1)  # Simulates a slow, blocking LLM call
        return MockEngine().analyze(idea)
        
    monkeypatch.setattr("app.core.crew_engine.CrewEngine.analyze", fake_analyze)

@pytest.mark.asyncio
async def test_concurrent_analyze():
    # Send 5 concurrent requests to the mock engine.
    # The mock engine has a `time.sleep(1)` inside it to simulate latency.
    # If the endpoint is blocking, 5 requests will take > 5 seconds.
    # If the endpoint is truly async and non-blocking, it will take ~1 second.
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_time = time.time()
        
        # Fire 5 requests simultaneously
        tasks = []
        for i in range(5):
            tasks.append(
                client.post("/analyze", json={"idea": f"Test idea number {i} to prove async"})
            )
            
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should be successful
        for response in responses:
            assert response.status_code == 200
            
        # Total time should be significantly less than 5 * 1s (mock engine delay)
        # We'll assert it took less than 3 seconds total.
        assert total_time < 3.0

@pytest.mark.asyncio
async def test_timeout_fallback(monkeypatch):
    # Temporarily force timeout to 0.5s but sleep for 2s to guarantee a timeout
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "1")
    get_settings.cache_clear()
    
    def extremely_slow_analyze(self, idea: str):
        time.sleep(2)
        return MockEngine().analyze(idea)
        
    monkeypatch.setattr("app.core.crew_engine.CrewEngine.analyze", extremely_slow_analyze)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/analyze", json={"idea": "Testing timeouts with graceful degradation"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["report"]["engine"] == "mock"
        assert data["meta"]["degraded"] is True
