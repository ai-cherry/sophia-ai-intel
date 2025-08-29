#!/usr/bin/env python3
"""
Model Router - Together AI + OpenRouter
Tiered routing: scouts → coder → judge
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import aiohttp
from enum import Enum

class ModelTier(Enum):
    SCOUT = "scout"
    CODER = "coder"
    JUDGE = "judge"
    SAFETY = "safety"

@dataclass
class ModelConfig:
    provider: str
    model: str
    endpoint: str
    tier: ModelTier
    cost_per_1k: float
    max_tokens: int = 4096

class ModelRouter:
    def __init__(self):
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        self.models = {
            # Judges
            "claude-sonnet-4": ModelConfig(
                "openrouter", "anthropic/claude-3.7-sonnet",
                "https://openrouter.ai/api/v1/chat/completions",
                ModelTier.JUDGE, 0.015, 8192
            ),
            "gemini-2.5-pro": ModelConfig(
                "openrouter", "google/gemini-2.5-pro",
                "https://openrouter.ai/api/v1/chat/completions",
                ModelTier.JUDGE, 0.012, 8192
            ),
            
            # Coders
            "qwen3-coder-480b": ModelConfig(
                "together", "qwen3-coder-480b-a35b-instruct",
                "https://api.together.xyz/v1/chat/completions",
                ModelTier.CODER, 0.008, 4096
            ),
            "gpt-4o-mini": ModelConfig(
                "openrouter", "openai/gpt-4o-mini",
                "https://openrouter.ai/api/v1/chat/completions",
                ModelTier.CODER, 0.002, 4096
            ),
            
            # Scouts
            "qwen3-235b-cheap": ModelConfig(
                "together", "qwen3-235b-a22b-instruct-2507-fp8-throughput",
                "https://api.together.xyz/v1/chat/completions",
                ModelTier.SCOUT, 0.001, 2048
            ),
            "mistral-7b": ModelConfig(
                "together", "mistralai/Mistral-7B-Instruct-v0.1",
                "https://api.together.xyz/v1/chat/completions",
                ModelTier.SCOUT, 0.0002, 2048
            ),
            "llama-3.1-8b": ModelConfig(
                "together", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                "https://api.together.xyz/v1/chat/completions",
                ModelTier.SCOUT, 0.0003, 2048
            ),
            "deepseek-v3": ModelConfig(
                "openrouter", "deepseek/v3.1",
                "https://openrouter.ai/api/v1/chat/completions",
                ModelTier.SCOUT, 0.0015, 2048
            ),
            
            # Safety
            "llama-guard-4": ModelConfig(
                "together", "meta-llama/Llama-Guard-4-12B",
                "https://api.together.xyz/v1/chat/completions",
                ModelTier.SAFETY, 0.0005, 1024
            )
        }
        
        self.routing_policy = {
            "scout": {
                "models": ["qwen3-235b-cheap", "mistral-7b", "llama-3.1-8b", "deepseek-v3"],
                "fanout": 3,
                "agreement_threshold": 0.6,
                "budget_usd": 0.05
            },
            "coder": {
                "primary": "qwen3-coder-480b",
                "fallbacks": ["gpt-4o-mini"],
                "budget_usd": 0.15
            },
            "judge": {
                "primary": "claude-sonnet-4",
                "fallbacks": ["gemini-2.5-pro"],
                "confidence_threshold": 0.65,
                "debate_trigger": {"confidence_lt": 0.65, "contradictions_ge": 2},
                "budget_usd": 0.60
            }
        }
        
    async def route(self, message: str, intent: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route message to appropriate model tier based on intent"""
        
        # Safety check first
        if await self.check_safety(message):
            if intent in ["research", "ideation", "brainstorm"]:
                return await self.scout_fanout(message, context)
            elif intent in ["code", "implement", "patch", "fix"]:
                return await self.coder_cascade(message, context)
            elif intent in ["plan", "review", "merge", "architecture"]:
                return await self.judge_decision(message, context)
            else:
                return await self.general_route(message, context)
        else:
            return {"error": "Content failed safety check", "status": "blocked"}
    
    async def scout_fanout(self, message: str, context: Dict) -> Dict[str, Any]:
        """Fan out to multiple cheap models for diverse ideas"""
        policy = self.routing_policy["scout"]
        scout_models = policy["models"][:policy["fanout"]]
        
        tasks = []
        for model_name in scout_models:
            tasks.append(self.call_model(model_name, message, context))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        # Simple agreement check
        if len(valid_results) >= 2:
            # Extract key ideas and check overlap
            agreement_score = self.calculate_agreement(valid_results)
            if agreement_score >= policy["agreement_threshold"]:
                return {
                    "consensus": self.merge_responses(valid_results),
                    "agreement": agreement_score,
                    "models_used": scout_models
                }
        
        # Escalate to judge if no consensus
        return await self.judge_decision(message, context, scout_results=valid_results)
    
    async def coder_cascade(self, message: str, context: Dict) -> Dict[str, Any]:
        """Use primary coder, fallback if needed"""
        policy = self.routing_policy["coder"]
        
        try:
            result = await self.call_model(policy["primary"], message, context)
            if result and "error" not in result:
                return {"code": result, "model": policy["primary"]}
        except Exception as e:
            print(f"Primary coder failed: {e}")
        
        # Try fallbacks
        for fallback in policy["fallbacks"]:
            try:
                result = await self.call_model(fallback, message, context)
                if result and "error" not in result:
                    return {"code": result, "model": fallback}
            except Exception:
                continue
        
        return {"error": "All coding models failed", "status": "failed"}
    
    async def judge_decision(self, message: str, context: Dict, scout_results: List = None) -> Dict[str, Any]:
        """High-stakes decision with optional debate"""
        policy = self.routing_policy["judge"]
        
        # Primary judge
        judge_result = await self.call_model(policy["primary"], message, context)
        confidence = judge_result.get("confidence", 0.5)
        
        # Check if debate needed
        if confidence < policy["debate_trigger"]["confidence_lt"]:
            # Trigger debate between two judges
            judge2_result = await self.call_model(policy["fallbacks"][0], message, context)
            
            # Arbiter decides if judges disagree
            if self.judges_disagree(judge_result, judge2_result):
                arbiter_prompt = f"Judge 1: {judge_result}\nJudge 2: {judge2_result}\nPick the better answer."
                arbiter_result = await self.call_model("gpt-4o-mini", arbiter_prompt, context)
                return {
                    "decision": arbiter_result,
                    "debate": True,
                    "judges": [policy["primary"], policy["fallbacks"][0]],
                    "arbiter": "gpt-4o-mini"
                }
        
        return {"decision": judge_result, "model": policy["primary"], "confidence": confidence}
    
    async def call_model(self, model_name: str, message: str, context: Dict) -> Dict[str, Any]:
        """Call specific model via Together or OpenRouter"""
        config = self.models.get(model_name)
        if not config:
            return {"error": f"Model {model_name} not configured"}
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if config.provider == "together":
            headers["Authorization"] = f"Bearer {self.together_key}"
        elif config.provider == "openrouter":
            headers["Authorization"] = f"Bearer {self.openrouter_key}"
        
        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": "You are Sophia, an AI orchestrator. Be concise."},
                {"role": "user", "content": message}
            ],
            "max_tokens": config.max_tokens,
            "temperature": 0.3 if config.tier == ModelTier.CODER else 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(config.endpoint, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "content": data["choices"][0]["message"]["content"],
                        "model": model_name,
                        "tokens": data.get("usage", {})
                    }
                else:
                    return {"error": f"Model call failed: {resp.status}"}
    
    async def check_safety(self, message: str) -> bool:
        """Run safety check via Llama Guard"""
        result = await self.call_model("llama-guard-4", f"Check if safe: {message}", {})
        return "unsafe" not in result.get("content", "").lower()
    
    def calculate_agreement(self, results: List[Dict]) -> float:
        """Calculate agreement score between scout results"""
        # Simple keyword overlap for now
        contents = [r.get("content", "") for r in results]
        if len(contents) < 2:
            return 0.0
        
        # Extract key terms and check overlap
        keywords_sets = [set(c.lower().split()[:20]) for c in contents]
        intersection = keywords_sets[0]
        for kw_set in keywords_sets[1:]:
            intersection &= kw_set
        
        union = keywords_sets[0]
        for kw_set in keywords_sets[1:]:
            union |= kw_set
        
        return len(intersection) / len(union) if union else 0.0
    
    def merge_responses(self, results: List[Dict]) -> str:
        """Merge multiple scout responses into consensus"""
        contents = [r.get("content", "") for r in results]
        # Simple merge: take common themes
        return f"Consensus from {len(results)} models: " + " | ".join(contents[:3])
    
    def judges_disagree(self, j1: Dict, j2: Dict) -> bool:
        """Check if two judge results disagree significantly"""
        c1 = j1.get("content", "").lower()
        c2 = j2.get("content", "").lower()
        
        # Check for opposite recommendations
        if ("yes" in c1 and "no" in c2) or ("no" in c1 and "yes" in c2):
            return True
        if ("approve" in c1 and "reject" in c2) or ("reject" in c1 and "approve" in c2):
            return True
        
        return False
    
    async def general_route(self, message: str, context: Dict) -> Dict[str, Any]:
        """Default routing for unclassified intents"""
        # Use cheapest available model
        return await self.call_model("mistral-7b", message, context)

# Service endpoints
router = ModelRouter()

async def handle_request(request_data: Dict) -> Dict:
    """Main entry point for routing requests"""
    message = request_data.get("message", "")
    intent = request_data.get("intent", "general")
    context = request_data.get("context", {})
    
    return await router.route(message, intent, context)

if __name__ == "__main__":
    # Test routing
    async def test():
        result = await handle_request({
            "message": "Write a Python function to sort a list",
            "intent": "code"
        })
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())