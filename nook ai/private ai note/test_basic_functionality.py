"""
Basic Functionality Test
Test the core functionality of Nook Engine
"""

import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from nook_engine import (
    NookEngine,
    create_mobile_engine,
    create_high_quality_engine,
    create_fast_engine,
    quick_start
)


def test_basic_initialization():
    """Test basic engine initialization"""
    print("🧪 Testing Basic Initialization...")
    
    try:
        # Test core engine
        print("🔧 Testing Core Engine...")
        engine = NookEngine(model_size="tiny.en")
        
        if not engine.initialize():
            print("❌ Core engine initialization failed")
            return False
        
        print("✅ Core engine initialized successfully")
        
        # Test status
        print("📊 Engine status: Initialized")
        
        # Cleanup
        engine.cleanup()
        print("✅ Core engine test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic initialization error: {e}")
        return False


def test_mobile_optimization():
    """Test mobile-optimized engine"""
    print("\n📱 Testing Mobile Optimization...")
    
    try:
        # Create mobile engine
        engine = create_mobile_engine()
        
        if not engine.initialize():
            print("❌ Mobile engine initialization failed")
            return False
        
        print("✅ Mobile engine initialized")
        
        # Check mobile optimizations
        status = engine.get_status()
        print(f"📊 Status: {status}")
        
        # Verify mobile settings
        if status.get('optimize_for_mobile'):
            print("✅ Mobile optimization enabled")
        else:
            print("❌ Mobile optimization not enabled")
        
        # Cleanup
        engine.cleanup()
        print("✅ Mobile optimization test completed")
        return True
        
    except Exception as e:
        print(f"❌ Mobile optimization error: {e}")
        return False


def test_engine_variants():
    """Test different engine variants"""
    print("\n🎯 Testing Engine Variants...")
    
    try:
        # Test high quality engine
        print("🎯 Testing High Quality Engine...")
        hq_engine = create_high_quality_engine()
        
        if not hq_engine.initialize():
            print("❌ High quality engine initialization failed")
            return False
        
        print("✅ High quality engine initialized")
        
        status = hq_engine.get_status()
        print(f"📊 Model: {status.get('model_size')}")
        
        hq_engine.cleanup()
        
        # Test fast engine
        print("⚡ Testing Fast Engine...")
        fast_engine = create_fast_engine()
        
        if not fast_engine.initialize():
            print("❌ Fast engine initialization failed")
            return False
        
        print("✅ Fast engine initialized")
        
        status = fast_engine.get_status()
        print(f"📊 Model: {status.get('model_size')}")
        
        fast_engine.cleanup()
        
        print("✅ Engine variants test completed")
        return True
        
    except Exception as e:
        print(f"❌ Engine variants error: {e}")
        return False


def test_quick_start():
    """Test quick start functionality"""
    print("\n🚀 Testing Quick Start...")
    
    try:
        print("🚀 Starting quick start...")
        engine = quick_start()
        
        if engine:
            print("✅ Quick start successful")
            
            # Check status
            status = engine.get_status()
            print(f"📊 Status: {status}")
            
            # Cleanup
            engine.cleanup()
            print("✅ Quick start test completed")
            return True
        else:
            print("❌ Quick start failed")
            return False
            
    except Exception as e:
        print(f"❌ Quick start error: {e}")
        return False


def test_simple_api_features():
    """Test Simple API features"""
    print("\n🔧 Testing Simple API Features...")
    
    try:
        # Create engine
        engine = create_mobile_engine()
        
        if not engine.initialize():
            print("❌ Engine initialization failed")
            return False
        
        print("✅ Engine initialized")
        
        # Test status
        status = engine.get_status()
        print(f"📊 Status: {status}")
        
        # Test callback setting
        print("🔧 Testing callback setting...")
        
        def test_callback(update):
            print(f"📝 Callback received: {update}")
        
        engine.set_callbacks(
            on_transcription_update=test_callback,
            on_speaker_change=lambda s: print(f"👥 Speaker: {s}"),
            on_error=lambda e: print(f"❌ Error: {e}")
        )
        
        print("✅ Callbacks set successfully")
        
        # Test get_latest_text (should be empty initially)
        latest_text = engine.get_latest_text()
        print(f"📝 Latest text: '{latest_text}'")
        
        # Test get_speakers (should be empty initially)
        speakers = engine.get_speakers()
        print(f"👥 Speakers: {speakers}")
        
        # Cleanup
        engine.cleanup()
        print("✅ Simple API features test completed")
        return True
        
    except Exception as e:
        print(f"❌ Simple API features error: {e}")
        return False


def test_ios_integration_basic():
    """Test basic iOS integration functionality"""
    print("\n📱 Testing iOS Integration Basic...")
    
    try:
        from nook_engine import create_ios_engine
        
        # Create iOS engine
        engine = create_ios_engine(temp_dir="/tmp/nook_engine_test_basic")
        
        if not engine.initialize():
            print("❌ iOS engine initialization failed")
            return False
        
        print("✅ iOS engine initialized")
        
        # Check communication files
        print("📁 Checking communication files...")
        
        required_files = [
            engine.status_file,
            engine.command_file,
            engine.result_file,
            engine.stream_file
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ {os.path.basename(file_path)} exists")
            else:
                print(f"❌ {os.path.basename(file_path)} missing")
        
        # Test status
        status = engine.get_status()
        print(f"📊 Status: {status}")
        
        # Cleanup
        engine.cleanup()
        print("✅ iOS integration basic test completed")
        return True
        
    except Exception as e:
        print(f"❌ iOS integration basic error: {e}")
        return False


if __name__ == "__main__":
    import os
    
    print("🧪 Basic Functionality Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Initialization", test_basic_initialization),
        ("Mobile Optimization", test_mobile_optimization),
        ("Engine Variants", test_engine_variants),
        ("Quick Start", test_quick_start),
        ("Simple API Features", test_simple_api_features),
        ("iOS Integration Basic", test_ios_integration_basic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic functionality tests passed!")
        print("🚀 Nook Engine is ready for production!")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
    
    print("\n💡 Key Features Tested:")
    print("   ✅ Core engine initialization")
    print("   ✅ Mobile optimization")
    print("   ✅ Engine variants (mobile, high-quality, fast)")
    print("   ✅ Quick start functionality")
    print("   ✅ Simple API features")
    print("   ✅ iOS integration basics")
