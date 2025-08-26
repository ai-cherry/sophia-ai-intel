#!/usr/bin/env python3
"""
Basic import test for ClientHealthTeam
"""

import sys
import os

def test_basic_import():
    """Test basic Python import"""
    try:
        print("🔍 Testing basic Python import...")

        # Add the specific directory to Python path
        client_health_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'services',
            'agno-teams',
            'src',
            'business',
            'client_health'
        )

        print(f"   📁 Adding path: {client_health_path}")
        sys.path.insert(0, client_health_path)

        # Try to import the module directly
        import client_health_team_clean

        print("✅ Successfully imported client_health_team_clean")

        # Check if we can create the class
        team_class = getattr(client_health_team_clean, 'ClientHealthTeam', None)
        if team_class:
            print("✅ ClientHealthTeam class found")
            return True
        else:
            print("❌ ClientHealthTeam class not found")
            return False

    except ImportError as e:
        print(f"❌ Import failed: {e}")

        # Try to see what's in the directory
        try:
            import os
            client_health_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                'services',
                'agno-teams',
                'src',
                'business',
                'client_health'
            )

            if os.path.exists(client_health_path):
                print(f"   📁 Directory exists: {client_health_path}")
                files = os.listdir(client_health_path)
                print(f"   📄 Files: {files}")

                if 'client_health_team_clean.py' in files:
                    print("   ✅ client_health_team_clean.py exists")

                    # Try to read the file to see if there are syntax errors
                    with open(os.path.join(client_health_path, 'client_health_team_clean.py'), 'r') as f:
                        content = f.read()
                        print(f"   📏 File length: {len(content)} characters")

                        # Check for basic syntax issues
                        if 'class ClientHealthTeam' in content:
                            print("   ✅ Contains ClientHealthTeam class definition")
                        else:
                            print("   ❌ Missing ClientHealthTeam class definition")

                        if 'def __init__' in content:
                            print("   ✅ Contains __init__ method")
                        else:
                            print("   ❌ Missing __init__ method")

                else:
                    print("   ❌ client_health_team_clean.py not found")

            else:
                print(f"   ❌ Directory does not exist: {client_health_path}")

        except Exception as e2:
            print(f"❌ Error checking directory: {e2}")

        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_syntax_only():
    """Test just the Python syntax without imports"""
    try:
        print("🔍 Testing Python syntax only...")

        client_health_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'services',
            'agno-teams',
            'src',
            'business',
            'client_health',
            'client_health_team_clean.py'
        )

        if os.path.exists(client_health_path):
            print(f"   📁 File exists: {client_health_path}")

            # Try to compile the file to check syntax
            with open(client_health_path, 'r') as f:
                source_code = f.read()

            compile(source_code, client_health_path, 'exec')
            print("✅ Python syntax is valid")
            return True
        else:
            print(f"   ❌ File does not exist: {client_health_path}")
            return False

    except SyntaxError as e:
        print(f"❌ Syntax error found: {e}")
        print(f"   📍 Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error testing syntax: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Basic Import Tests\n")

    tests = [
        ("Syntax Check", test_syntax_only),
        ("Import Test", test_basic_import)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 Running: {test_name}")
        print('='*50)

        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")

    print(f"\n{'='*50}")
    print("📊 TEST RESULTS SUMMARY")
    print('='*50)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - ClientHealthTeam syntax and basic structure are valid!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - check errors above")
        if passed > 0:
            print("   ✅ At least syntax is valid - import issues may be path-related")
        else:
            print("   ❌ Both syntax and import failed - critical issues found")