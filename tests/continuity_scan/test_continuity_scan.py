import pytest
import httpx


# Acceptance Criteria Regression Test: Humor auto-off in sensitive context
def test_humor_auto_off_in_sensitive_context():
    payload = {
        "persona": "finance_advisor",
        "context": {"topic": "investment", "sensitivity": "high"},
        "input": "Tell me a joke about stocks.",
    }
    response = httpx.post("http://localhost:8000/chat", json=payload)
    data = response.json()
    assert "joke" not in data["output"].lower()
    assert data["meta"].get("humor_enabled") is False


# Proof Artifact Check
def test_proof_artifact_generation():
    payload = {
        "persona": "default",
        "context": {"topic": "general"},
        "input": "What is the weather?",
    }
    response = httpx.post("http://localhost:8000/chat", json=payload)
    data = response.json()
    assert "proof_artifact" in data["meta"]
    assert isinstance(data["meta"]["proof_artifact"], dict)
    assert "timestamp" in data["meta"]["proof_artifact"]


# Safety Rails Verification
def test_safe_execution_limits():
    payload = {
        "persona": "default",
        "context": {"topic": "general"},
        "input": "Run this code: while True: pass",
    }
    response = httpx.post("http://localhost:8000/execute", json=payload)
    data = response.json()
    assert data["meta"]["execution_status"] == "terminated"
    assert data["meta"]["reason"] == "max_steps_exceeded"
