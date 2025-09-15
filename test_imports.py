#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""

def test_imports():
    """Test all critical imports."""
    try:
        print("Testing imports...")
        
        # Test app module imports
        import app
        print("✅ app module imported successfully")
        
        import app.models
        print("✅ app.models imported successfully")
        
        import app.agents
        print("✅ app.agents imported successfully")
        
        import app.memory
        print("✅ app.memory imported successfully")
        
        import app.providers
        print("✅ app.providers imported successfully")
        
        import app.services
        print("✅ app.services imported successfully")
        
        import app.tools
        print("✅ app.tools imported successfully")
        
        # Test task executor imports
        import task_executor_agent
        print("✅ task_executor_agent imported successfully")
        
        import task_executor_agent.models
        print("✅ task_executor_agent.models imported successfully")
        
        import task_executor_agent.agent
        print("✅ task_executor_agent.agent imported successfully")
        
        import task_executor_agent.api
        print("✅ task_executor_agent.api imported successfully")
        
        import task_executor_agent.tools
        print("✅ task_executor_agent.tools imported successfully")
        
        # Test main application
        from app.server import create_app
        print("✅ app.server.create_app imported successfully")
        
        print("\n🎉 All imports successful! The module structure is correct.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
