#!/usr/bin/env python3
"""
Simple test of Nook Engine
"""

import os
import sys
from pathlib import Path

# Add module path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test module imports"""
    print("🧪 Testing imports...")
    
    try:
        from nook_engine import NookEngine
        print("✅ NookEngine imported successfully")
        
        from nook_engine.transcriber import WhisperTranscriber
        print("✅ WhisperTranscriber imported successfully")
        
        from nook_engine.diarizer import SpeakerDiarizer
        print("✅ SpeakerDiarizer imported successfully")
        
        from nook_engine.audio_processor import AudioProcessor
        print("✅ AudioProcessor imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_initialization():
    """Test engine initialization"""
    print("\n🚀 Testing initialization...")
    
    try:
        from nook_engine import NookEngine
        
        # Create engine
        engine = NookEngine(
            model_size="base.en",
            device="cpu",
            language="en"
        )
        
        print("✅ Engine created successfully")
        
        # Try to initialize (may take time)
        print("⏳ Initializing...")
        success = engine.initialize()
        
        if success:
            print("✅ Initialization successful")
            
            # Show information
            info = engine.get_model_info()
            print("📊 Model information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("⚠️  Initialization failed (possibly no models)")
        
        # Cleanup
        engine.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_audio_devices():
    """Test audio device detection"""
    print("\n🎤 Testing audio devices...")
    
    try:
        from nook_engine.audio_processor import AudioProcessor
        
        processor = AudioProcessor()
        
        if processor.initialize():
            devices = processor.get_audio_devices()
            
            if devices:
                print(f"✅ Found {len(devices)} audio devices:")
                for device in devices[:3]:  # Show first 3
                    print(f"  [{device['id']}] {device['name']}")
                    print(f"      Inputs: {device['max_inputs']}, Outputs: {device['max_outputs']}")
            else:
                print("⚠️  No audio devices found")
            
            processor.cleanup()
            return True
        else:
            print("⚠️  Audio processor not initialized")
            return False
            
    except Exception as e:
        print(f"❌ Audio device test error: {e}")
        return False

def test_file_processing():
    """Test file processing (if whisper.cpp is available)"""
    print("\n📁 Testing file processing...")
    
    # Check for whisper.cpp
    whisper_paths = [
        "./whisper.cpp/build/bin/whisper-cli",
        "./whisper.cpp/build/bin/whisper",
        "./whisper.cpp/main"
    ]
    
    whisper_found = any(os.path.exists(path) for path in whisper_paths)
    
    if whisper_found:
        print("✅ whisper.cpp found")
        
        # Check for models
        models_dir = "./whisper.cpp/models"
        if os.path.exists(models_dir):
            models = [f for f in os.listdir(models_dir) if f.endswith('.bin')]
            if models:
                print(f"✅ Found {len(models)} models:")
                for model in models[:3]:
                    print(f"  - {model}")
                
                # Try to process file
                audio_file = "reference_user.wav"
                if os.path.exists(audio_file):
                    print(f"🎵 Testing processing of {audio_file}...")
                    
                    try:
                        from nook_engine import NookEngine
                        
                        engine = NookEngine(
                            model_size="base.en"
                        )
                        
                        if engine.initialize():
                            print("✅ Engine initialized")
                            
                            # Transcribe
                            result = engine.transcribe_audio(audio_file, "json")
                            if result:
                                print("✅ Transcription successful")
                                print(f"📝 Segments: {len(result.get('segments', []))}")
                            else:
                                print("⚠️  Transcription failed")
                            
                            engine.cleanup()
                        else:
                            print("⚠️  Initialization failed")
                            
                    except Exception as e:
                        print(f"❌ Processing error: {e}")
                else:
                    print(f"⚠️  File {audio_file} not found")
            else:
                print("⚠️  Models not found")
        else:
            print("⚠️  Models directory not found")
    else:
        print("⚠️  whisper.cpp not found")
        print("   Install whisper.cpp for full testing")
    
    return True

def main():
    """Main testing function"""
    print("🧪 Nook Engine - Testing")
    print("=" * 40)
    
    tests = [
        ("Module imports", test_imports),
        ("Initialization", test_initialization),
        ("Audio devices", test_audio_devices),
        ("File processing", test_file_processing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Critical error in test '{test_name}': {e}")
            results.append((test_name, False))
    
    # Results
    print("\n📊 Test results:")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed successfully!")
    elif passed > total // 2:
        print("⚠️  Most tests passed, but there are issues")
    else:
        print("❌ Many tests failed, check installation")
    
    print("\n💡 Recommendations:")
    if passed < total:
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check for whisper.cpp and models")
        print("3. Make sure audio devices are available")
    else:
        print("1. Nook Engine is ready to use!")
        print("2. Run: python example_usage.py")
        print("3. Read documentation in README.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Testing stopped by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
