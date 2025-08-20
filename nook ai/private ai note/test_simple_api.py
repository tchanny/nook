"""
Simple API Test
Test the SimpleNookEngine API functionality
"""

import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from nook_engine import (
    create_mobile_engine,
    create_high_quality_engine,
    create_fast_engine
)


def test_mobile_engine():
    """Test mobile-optimized engine"""
    print("📱 Testing Mobile Engine...")
    
    try:
        # Create engine
        engine = create_mobile_engine()
        print("✅ Mobile engine created")
        
        # Initialize
        if not engine.initialize():
            print("❌ Failed to initialize")
            return False
        
        print("✅ Mobile engine initialized")
        
        # Get status
        status = engine.get_status()
        print(f"📊 Status: {status}")
        
        # Test basic functionality
        print("🔧 Testing basic functionality...")
        
        # Cleanup
        engine.cleanup()
        print("✅ Mobile engine test completed")
        return True
        
    except Exception as e:
        print(f"❌ Mobile engine test error: {e}")
        return False


def test_high_quality_engine():
    """Test high-quality engine"""
    print("\n🎯 Testing High Quality Engine...")
    
    try:
        # Create engine
        engine = create_high_quality_engine()
        print("✅ High quality engine created")
        
        # Initialize
        if not engine.initialize():
            print("❌ Failed to initialize")
            return False
        
        print("✅ High quality engine initialized")
        
        # Get status
        status = engine.get_status()
        print(f"📊 Status: {status}")
        
        # Cleanup
        engine.cleanup()
        print("✅ High quality engine test completed")
        return True
        
    except Exception as e:
        print(f"❌ High quality engine test error: {e}")
        return False


def test_fast_engine():
    """Test fast engine"""
    print("\n⚡ Testing Fast Engine...")
    
    try:
        # Create engine
        engine = create_fast_engine()
        print("✅ Fast engine created")
        
        # Initialize
        if not engine.initialize():
            print("❌ Failed to initialize")
            return False
        
        print("✅ Fast engine initialized")
        
        # Get status
        status = engine.get_status()
        print(f"📊 Status: {status}")
        
        # Cleanup
        engine.cleanup()
        print("✅ Fast engine test completed")
        return True
        
    except Exception as e:
        print(f"❌ Fast engine test error: {e}")
        return False


def test_quick_start():
    """Test quick start function"""
    print("\n🚀 Testing Quick Start...")
    
    try:
        from nook_engine import quick_start
        
        engine = quick_start()
        if engine:
            print("✅ Quick start successful")
            engine.cleanup()
            return True
        else:
            print("❌ Quick start failed")
            return False
            
    except Exception as e:
        print(f"❌ Quick start test error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Simple API Test Suite")
    print("=" * 40)
    
    tests = [
        ("Mobile Engine", test_mobile_engine),
        ("High Quality Engine", test_high_quality_engine),
        ("Fast Engine", test_fast_engine),
        ("Quick Start", test_quick_start)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*40)
    print("📊 TEST SUMMARY")
    print("="*40)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Simple API tests passed!")
    else:
        print(f"⚠️  {total - passed} tests failed.")
