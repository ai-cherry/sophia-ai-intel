"""
Unit tests for the Model Router component
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json


class TestModelRouter:
    """Test suite for ModelRouter functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock routing configuration"""
        return {
            "scout": {
                "models": ["gpt-4", "claude-3", "mixtral"],
                "fanout": 3,
                "temperature": 0.7
            },
            "coder": {
                "models": ["deepseek-coder", "codellama"],
                "temperature": 0.3
            },
            "judge": {
                "models": ["gpt-5", "claude-opus"],
                "temperature": 0.1
            }
        }
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_scout_fanout_distributes_to_multiple_models(self):
        """Test that scout fanout correctly distributes queries to multiple models"""
        from services.model_router import ModelRouter
        
        router = ModelRouter()
        
        with patch.object(router, '_call_model', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"response": "test response", "model": "test"}
            
            result = await router.scout_fanout(
                message="Test query",
                context={"session_id": "test-123"}
            )
            
            assert "scouts" in result
            assert len(result["scouts"]) >= 2
            assert mock_call.call_count >= 2
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_judge_decision_detects_contradictions(self):
        """Test that judge correctly identifies contradictions in scout responses"""
        from services.model_router import ModelRouter
        
        router = ModelRouter()
        
        scout_responses = [
            {
                "model": "gpt-4",
                "response": "The answer is definitely A",
                "confidence": 0.9
            },
            {
                "model": "claude-3", 
                "response": "The answer is clearly B, not A",
                "confidence": 0.85
            }
        ]
        
        with patch.object(router, '_call_judge', new_callable=AsyncMock) as mock_judge:
            mock_judge.return_value = {
                "verdict": "contradiction_detected",
                "resolution": "Further analysis needed",
                "confidence": 0.6
            }
            
            result = await router.judge_decision(scout_responses)
            
            assert result["contradiction_detected"] == True
            assert "resolution" in result
            assert result["confidence"] < 0.7  # Lower confidence due to contradiction
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_coder_cascade_with_retry(self):
        """Test coder cascade with retry logic on failure"""
        from services.model_router import ModelRouter
        
        router = ModelRouter()
        
        with patch.object(router, '_call_model', new_callable=AsyncMock) as mock_call:
            # First call fails, second succeeds
            mock_call.side_effect = [
                Exception("Model unavailable"),
                {"code": "def test(): pass", "language": "python"}
            ]
            
            result = await router.coder_cascade(
                task="Write a test function",
                context={}
            )
            
            assert result["success"] == True
            assert "code" in result
            assert mock_call.call_count == 2
    
    @pytest.mark.unit
    def test_routing_policy_validation(self):
        """Test that routing policies are properly validated"""
        from services.model_router import validate_routing_policy
        
        valid_policy = {
            "routes": [
                {
                    "pattern": "research",
                    "models": ["gpt-4"],
                    "strategy": "fanout"
                }
            ]
        }
        
        invalid_policy = {
            "routes": [
                {
                    "pattern": "research"
                    # Missing required fields
                }
            ]
        }
        
        assert validate_routing_policy(valid_policy) == True
        assert validate_routing_policy(invalid_policy) == False
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_model_fallback_chain(self):
        """Test fallback chain when primary models are unavailable"""
        from services.model_router import ModelRouter
        
        router = ModelRouter()
        
        with patch.object(router, '_call_model', new_callable=AsyncMock) as mock_call:
            # First two calls fail, third succeeds
            mock_call.side_effect = [
                Exception("GPT-5 unavailable"),
                Exception("Claude Opus unavailable"),
                {"response": "Fallback response from GPT-4"}
            ]
            
            result = await router.execute_with_fallback(
                message="Test message",
                preferred_models=["gpt-5", "claude-opus", "gpt-4"]
            )
            
            assert result["success"] == True
            assert result["model_used"] == "gpt-4"
            assert mock_call.call_count == 3
    
    @pytest.mark.unit
    def test_calculate_agreement_score(self):
        """Test agreement score calculation between multiple responses"""
        from services.helpers.scoring import agreement_score
        
        # High agreement
        responses1 = [
            ["claim1", "claim2", "claim3"],
            ["claim1", "claim2", "claim3"],
            ["claim1", "claim2", "claim4"]
        ]
        score1 = agreement_score(responses1)
        assert score1 > 0.7
        
        # Low agreement
        responses2 = [
            ["claim1", "claim2"],
            ["claim3", "claim4"],
            ["claim5", "claim6"]
        ]
        score2 = agreement_score(responses2)
        assert score2 < 0.3
        
        # Perfect agreement
        responses3 = [
            ["claim1", "claim2"],
            ["claim1", "claim2"],
            ["claim1", "claim2"]
        ]
        score3 = agreement_score(responses3)
        assert score3 == 1.0