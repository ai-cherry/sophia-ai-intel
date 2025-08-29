"""
End-to-end tests for complete user journeys
"""

import pytest
from playwright.sync_api import Page, expect
import time


class TestUserJourney:
    """Test complete user workflows"""
    
    @pytest.mark.e2e
    def test_new_user_onboarding(self, page: Page):
        """Test new user onboarding flow"""
        # Navigate to application
        page.goto("http://localhost:3000")
        
        # Check landing page
        expect(page).to_have_title("Sophia AI Intelligence")
        
        # Start chat
        chat_input = page.locator('input[placeholder*="Type your message"]')
        expect(chat_input).to_be_visible()
        
        # Send first message
        chat_input.fill("Hello, I'm new here")
        page.keyboard.press("Enter")
        
        # Wait for response
        response = page.locator('.assistant-message').first
        expect(response).to_be_visible(timeout=10000)
        
        # Verify welcome message
        expect(response).to_contain_text(["Welcome", "Hello", "Hi"])
    
    @pytest.mark.e2e
    def test_research_to_implementation_flow(self, page: Page):
        """Test complete research to code implementation flow"""
        page.goto("http://localhost:3000")
        
        # Research phase
        chat_input = page.locator('input[placeholder*="Type your message"]')
        chat_input.fill("Research the best practices for implementing authentication in Next.js")
        page.keyboard.press("Enter")
        
        # Wait for research response
        page.wait_for_selector('.assistant-message', timeout=15000)
        
        # Request implementation
        chat_input.fill("Now implement a basic authentication system based on these practices")
        page.keyboard.press("Enter")
        
        # Wait for code generation
        code_block = page.locator('pre code').first
        expect(code_block).to_be_visible(timeout=20000)
        
        # Verify code contains expected patterns
        code_content = code_block.inner_text()
        assert any(keyword in code_content for keyword in ['auth', 'login', 'user', 'session'])
    
    @pytest.mark.e2e
    def test_swarm_visualization(self, page: Page):
        """Test swarm visualization and interaction"""
        page.goto("http://localhost:3000/swarm-monitor")
        
        # Wait for visualization to load
        viz_container = page.locator('[data-testid="swarm-visualization"]')
        expect(viz_container).to_be_visible(timeout=5000)
        
        # Check for swarm nodes
        swarm_nodes = page.locator('[data-testid^="swarm-"]')
        expect(swarm_nodes).to_have_count(3, timeout=5000)
        
        # Click on a swarm to see details
        first_swarm = swarm_nodes.first
        first_swarm.click()
        
        # Check details panel
        details = page.locator('[data-testid="swarm-details"]')
        expect(details).to_be_visible()
        expect(details).to_contain_text("agents")
    
    @pytest.mark.e2e
    def test_error_recovery(self, page: Page):
        """Test application error handling and recovery"""
        page.goto("http://localhost:3000")
        
        # Trigger an error by sending malformed input
        chat_input = page.locator('input[placeholder*="Type your message"]')
        
        # Send very long message to trigger potential issues
        long_message = "x" * 10000
        chat_input.fill(long_message)
        page.keyboard.press("Enter")
        
        # Application should handle gracefully
        error_message = page.locator('.error-message')
        if error_message.is_visible():
            expect(error_message).to_contain_text(["error", "try again", "issue"])
        
        # Should still be functional
        chat_input.fill("Hello")
        page.keyboard.press("Enter")
        
        response = page.locator('.assistant-message').last
        expect(response).to_be_visible(timeout=10000)
    
    @pytest.mark.e2e
    def test_session_persistence(self, page: Page, context):
        """Test session persistence across page reloads"""
        page.goto("http://localhost:3000")
        
        # Send a message
        chat_input = page.locator('input[placeholder*="Type your message"]')
        chat_input.fill("Remember that my favorite color is blue")
        page.keyboard.press("Enter")
        
        # Wait for response
        page.wait_for_selector('.assistant-message', timeout=10000)
        
        # Reload page
        page.reload()
        
        # Check conversation history is preserved
        messages = page.locator('.message')
        expect(messages).to_have_count(2, timeout=5000)  # User + Assistant
        
        # Test memory recall
        chat_input.fill("What's my favorite color?")
        page.keyboard.press("Enter")
        
        response = page.locator('.assistant-message').last
        expect(response).to_contain_text("blue", timeout=10000)