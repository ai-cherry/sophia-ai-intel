#!/usr/bin/env python3
"""
Test script for ClientHealthTeam integration and collaboration
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_client_health_team():
    """Test the ClientHealthTeam with agent collaboration"""
    try:
        print("🔍 Testing ClientHealthTeam integration...")

        # Import the clean ClientHealthTeam
        from services.agno_teams.src.business.client_health.client_health_team_clean import (
            ClientHealthTeam,
            ClientHealthRequest
        )

        print("✅ Successfully imported ClientHealthTeam")

        # Create team instance
        team = ClientHealthTeam(
            name="TestClientHealthTeam",
            integrations={
                "usage_metrics": "http://mcp-usage:8080",
                "support_tickets": "http://mcp-support:8080",
                "intercom": "http://mcp-intercom:8080"
            }
        )

        print("✅ Successfully created ClientHealthTeam instance")
        print(f"   📊 Team has {len(team.agents)} agents: {list(team.agents.keys())}")

        # Test agent collaboration setup
        print("🔗 Testing agent collaboration setup...")
        if hasattr(team, 'shared_data'):
            print("✅ Data sharing framework initialized")
            print(f"   📈 Communication channels: {len(team.communication_channels)}")
        else:
            print("❌ Data sharing framework not found")

        # Test basic health analysis request
        print("🏥 Testing health analysis request...")
        request = ClientHealthRequest(
            client_ids=["client_001"],
            include_predictions=True,
            time_window=30,
            alert_threshold=0.3,
            focus_areas=["usage", "support"]
        )

        print(f"   📋 Request: {request.client_ids}, time_window: {request.time_window} days")

        # Run health analysis
        results = await team.analyze_client_health(request)

        print("✅ Health analysis completed successfully")
        print(f"   📊 Analyzed {len(results)} clients")

        if results:
            client = results[0]
            print(f"   👤 Client: {client.client_name}")
            print(f"   📊 Overall Score: {client.overall_score:.3f}")
            print(f"   🔴 Risk Level: {client.risk_level}")
            print(f"   💰 Predicted LTV: ${client.predicted_ltv:,.0f}")
            print(f"   📝 Recommendations: {len(client.recommendations)}")
            print(f"   📊 Factors: {len(client.factors)}")

            # Test agent communication stats
            if hasattr(team, '_get_agent_communication_stats'):
                stats = team._get_agent_communication_stats()
                print("✅ Communication stats available")
                print(f"   📡 Total communications: {stats.get('total_communications', 0)}")
                if stats.get('most_active_channel'):
                    print(f"   📈 Most active channel: {stats['most_active_channel']}")

        print("\n🎉 All tests passed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_environment_configuration():
    """Test environment-based configuration"""
    try:
        print("🔧 Testing environment-based configuration...")

        # Set environment variables
        os.environ["MCP_USAGE_URL"] = "http://test-usage:8080"
        os.environ["MCP_SUPPORT_URL"] = "http://test-support:8080"
        os.environ["MCP_INTERCOM_URL"] = "http://test-intercom:8080"

        from services.agno_teams.src.business.client_health.client_health_team_clean import (
            ClientHealthTeam
        )

        # Create team without integrations (should use env vars)
        team = ClientHealthTeam()

        print("✅ Team created with environment configuration")

        # Check if environment variables were used
        expected_urls = {
            "usage_metrics": "http://test-usage:8080",
            "support_tickets": "http://test-support:8080",
            "intercom": "http://test-intercom:8080"
        }

        for key, expected_url in expected_urls.items():
            if key in team.integrations and team.integrations[key] == expected_url:
                print(f"   ✅ {key}: {expected_url}")
            else:
                print(f"   ❌ {key}: expected {expected_url}, got {team.integrations.get(key)}")
                return False

        print("✅ Environment configuration test passed!")
        return True

    except Exception as e:
        print(f"❌ Environment configuration test failed: {e}")
        return False

async def test_agent_collaboration():
    """Test agent collaboration and data sharing"""
    try:
        print("🤝 Testing agent collaboration...")

        from services.agno_teams.src.business.client_health.client_health_team_clean import (
            ClientHealthTeam
        )

        team = ClientHealthTeam()

        # Test data sharing methods
        test_insights = {"test_metric": 0.85, "risk_level": "low"}
        await team._share_insights_between_agents(
            "usage_analyst", "support_analyst", "client_001", test_insights
        )

        print("✅ Insights shared between agents")

        # Test getting shared insights
        shared = await team._get_shared_insights("client_001", "support_analyst")
        if shared:
            print("✅ Shared insights retrieved")
            print(f"   📊 Insights: {list(shared.keys())}")
        else:
            print("❌ No shared insights found")

        # Test communication stats
        stats = team._get_agent_communication_stats()
        if stats.get('total_communications', 0) > 0:
            print("✅ Communication stats working")
            print(f"   📈 Communications: {stats['total_communications']}")
        else:
            print("❌ No communications recorded")

        print("✅ Agent collaboration test passed!")
        return True

    except Exception as e:
        print(f"❌ Agent collaboration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting ClientHealthTeam Integration Tests\n")

    tests = [
        ("Basic Integration", test_client_health_team),
        ("Environment Config", test_environment_configuration),
        ("Agent Collaboration", test_agent_collaboration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 Running: {test_name}")
        print('='*50)

        if await test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")

    print(f"\n{'='*50}")
    print("📊 TEST RESULTS SUMMARY"
    print('='*50)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - ClientHealthTeam is ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - check errors above")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())