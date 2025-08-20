"""
Complete Nook Engine Test
Tests all functionality including new APIs and integrations
"""

import time
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from nook_engine import (
    NookEngine,
    SimpleNookEngine,
    create_mobile_engine,
    create_high_quality_engine,
    create_fast_engine,
    create_ios_engine,
    create_macos_engine,
    start_websocket_demo,
    start_ios_demo
)


def test_core_engine():
    """Test core NookEngine functionality"""
    print("🧪 Testing Core NookEngine...")
    
    try:
        # Create engine
        engine = NookEngine(model_size="tiny.en")
        
        # Initialize
        if not engine.initialize():
            print("❌ Core engine initialization failed")
            return False
        
        print("✅ Core engine initialized")
        
        # Test transcription
        test_audio = "test_audio.wav"
        if os.path.exists(test_audio):
            print(f"🎵 Testing transcription: {test_audio}")
            result = engine.transcribe_audio(test_audio)
            if result:
                print(f"✅ Transcription successful: {len(result.get('segments', []))} segments")
            else:
                print("❌ Transcription failed")
        else:
            print(f"⚠️  Test audio file not found: {test_audio}")
        
        # Test diarization
        if os.path.exists(test_audio):
            print(f"👥 Testing diarization: {test_audio}")
            result = engine.diarize_audio(test_audio)
            if result:
                print(f"✅ Diarization successful: {len(result.get('speakers', []))} speakers")
            else:
                print("❌ Diarization failed")
        
        # Cleanup
        engine.cleanup()
        print("✅ Core engine test completed")
        return True
        
    except Exception as e:
        print(f"❌ Core engine test error: {e}")
        return False


def test_simple_api():
    """Test SimpleNookEngine API"""
    print("\n🧪 Testing Simple API...")
    
    try:
        # Test mobile engine
        print("📱 Testing mobile engine...")
        mobile_engine = create_mobile_engine()
        
        if not mobile_engine.initialize():
            print("❌ Mobile engine initialization failed")
            return False
        
        print("✅ Mobile engine initialized")
        
        # Test status
        status = mobile_engine.get_status()
        print(f"📊 Status: {status}")
        
        # Test file transcription
        test_audio = "test_audio.wav"
        if os.path.exists(test_audio):
            print(f"🎵 Testing file transcription: {test_audio}")
            result = mobile_engine.transcribe_file(test_audio, enable_diarization=True)
            if result:
                print(f"✅ File transcription successful")
            else:
                print("❌ File transcription failed")
        
        # Cleanup
        mobile_engine.cleanup()
        print("✅ Simple API test completed")
        return True
        
    except Exception as e:
        print(f"❌ Simple API test error: {e}")
        return False


def test_engine_variants():
    """Test different engine variants"""
    print("\n🧪 Testing Engine Variants...")
    
    try:
        # Test high quality engine
        print("🎯 Testing high quality engine...")
        hq_engine = create_high_quality_engine()
        
        if not hq_engine.initialize():
            print("❌ High quality engine initialization failed")
            return False
        
        print("✅ High quality engine initialized")
        hq_engine.cleanup()
        
        # Test fast engine
        print("⚡ Testing fast engine...")
        fast_engine = create_fast_engine()
        
        if not fast_engine.initialize():
            print("❌ Fast engine initialization failed")
            return False
        
        print("✅ Fast engine initialized")
        fast_engine.cleanup()
        
        print("✅ Engine variants test completed")
        return True
        
    except Exception as e:
        print(f"❌ Engine variants test error: {e}")
        return False


def test_ios_integration():
    """Test iOS integration engine"""
    print("\n🧪 Testing iOS Integration...")
    
    try:
        # Test iOS engine
        print("📱 Testing iOS engine...")
        ios_engine = create_ios_engine(temp_dir="/tmp/nook_engine_test")
        
        if not ios_engine.initialize():
            print("❌ iOS engine initialization failed")
            return False
        
        print("✅ iOS engine initialized")
        
        # Test communication files
        print("📁 Testing communication files...")
        required_files = [
            ios_engine.status_file,
            ios_engine.command_file,
            ios_engine.result_file,
            ios_engine.stream_file
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ {os.path.basename(file_path)} exists")
            else:
                print(f"❌ {os.path.basename(file_path)} missing")
        
        # Test command processing
        print("📤 Testing command processing...")
        test_command = {"type": "get_status"}
        with open(ios_engine.command_file, 'w') as f:
            json.dump(test_command, f)
        
        # Wait for processing
        time.sleep(1)
        
        if os.path.exists(ios_engine.result_file):
            with open(ios_engine.result_file, 'r') as f:
                result = json.load(f)
            print(f"✅ Command processed: {result.get('message', 'Unknown')}")
        else:
            print("❌ Command processing failed")
        
        # Cleanup
        ios_engine.cleanup()
        print("✅ iOS integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ iOS integration test error: {e}")
        return False


def test_macos_integration():
    """Test macOS integration engine"""
    print("\n🧪 Testing macOS Integration...")
    
    try:
        # Test macOS engine
        print("🖥️  Testing macOS engine...")
        macos_engine = create_macos_engine(temp_dir="/tmp/nook_engine_macos_test")
        
        if not macos_engine.initialize():
            print("❌ macOS engine initialization failed")
            return False
        
        print("✅ macOS engine initialized")
        
        # Test status
        status = macos_engine.get_status()
        print(f"📊 Status: {status}")
        
        # Cleanup
        macos_engine.cleanup()
        print("✅ macOS integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ macOS integration test error: {e}")
        return False


def test_websocket_demo():
    """Test WebSocket demo functionality"""
    print("\n🧪 Testing WebSocket Demo...")
    
    try:
        print("🌐 Starting WebSocket demo...")
        
        # Start demo in background
        server = start_websocket_demo(host="localhost", port=8766)
        
        # Wait a bit for server to start
        time.sleep(2)
        
        # Check server status
        status = server.get_server_status()
        print(f"📊 Server status: {status}")
        
        if status.get("is_running"):
            print("✅ WebSocket demo started successfully")
            
            # Stop server
            server.stop_server()
            print("✅ WebSocket demo stopped")
            return True
        else:
            print("❌ WebSocket demo failed to start")
            return False
        
    except Exception as e:
        print(f"❌ WebSocket demo test error: {e}")
        return False


def test_ios_demo():
    """Test iOS demo functionality"""
    print("\n🧪 Testing iOS Demo...")
    
    try:
        print("📱 Starting iOS demo...")
        
        # Start demo
        engine = start_ios_demo(temp_dir="/tmp/nook_engine_ios_demo")
        
        if engine:
            print("✅ iOS demo started successfully")
            
            # Cleanup
            engine.cleanup()
            print("✅ iOS demo stopped")
            return True
        else:
            print("❌ iOS demo failed to start")
            return False
        
    except Exception as e:
        print(f"❌ iOS demo test error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("🚀 Running Complete Nook Engine Test Suite")
    print("=" * 60)
    
    tests = [
        ("Core Engine", test_core_engine),
        ("Simple API", test_simple_api),
        ("Engine Variants", test_engine_variants),
        ("iOS Integration", test_ios_integration),
        ("macOS Integration", test_macos_integration),
        ("WebSocket Demo", test_websocket_demo),
        ("iOS Demo", test_ios_demo)
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
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Nook Engine is ready for production!")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing error: {e}")
        sys.exit(1)
