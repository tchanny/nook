"""
iOS/macOS Integration Example
Demonstrates how to use Nook Engine from Swift applications
"""

import time
import json
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from nook_engine import create_ios_engine, create_macos_engine


def ios_integration_demo():
    """Demo of iOS integration capabilities"""
    print("📱 iOS Integration Demo")
    print("=" * 50)
    
    # Create iOS-optimized engine
    engine = create_ios_engine(
        model_size="tiny.en",
        optimize_for_mobile=True,
        temp_dir="/tmp/nook_engine_demo"
    )
    
    print(f"🔧 Engine created with temp dir: {engine.temp_dir}")
    
    # Initialize
    if not engine.initialize():
        print("❌ Failed to initialize engine")
        return
    
    print("✅ Engine initialized and ready for iOS app")
    print("\n📋 Available communication files:")
    print(f"   Status: {engine.status_file}")
    print(f"   Commands: {engine.command_file}")
    print(f"   Results: {engine.result_file}")
    print(f"   Stream: {engine.stream_file}")
    
    print("\n🔄 Engine is now monitoring for commands...")
    print("📱 iOS app can send commands via command.json file")
    
    # Simulate iOS app commands
    print("\n🧪 Simulating iOS app commands...")
    
    # Command 1: Get status
    print("\n1️⃣ Getting status...")
    command = {"type": "get_status"}
    with open(engine.command_file, 'w') as f:
        json.dump(command, f)
    
    time.sleep(0.5)  # Wait for processing
    
    if os.path.exists(engine.result_file):
        with open(engine.result_file, 'r') as f:
            result = json.load(f)
        print(f"   Result: {result['message']}")
    
    # Command 2: Start listening
    print("\n2️⃣ Starting listening...")
    command = {
        "type": "start_listening",
        "output_file": "demo_transcription.json",
        "enable_diarization": True,
        "partial_updates": True,
        "update_interval": 1.0
    }
    with open(engine.command_file, 'w') as f:
        json.dump(command, f)
    
    time.sleep(1)  # Wait for processing
    
    if os.path.exists(engine.result_file):
        with open(engine.result_file, 'r') as f:
            result = json.load(f)
        print(f"   Result: {result['message']}")
    
    if result.get('success'):
        print("   🎤 Listening started! Speak into microphone...")
        print("   📝 Real-time transcription will appear in stream file")
        
        # Let it run for a few seconds
        time.sleep(5)
        
        # Command 3: Stop listening
        print("\n3️⃣ Stopping listening...")
        command = {"type": "stop_listening"}
        with open(engine.command_file, 'w') as f:
            json.dump(command, f)
        
        time.sleep(1)  # Wait for processing
        
        if os.path.exists(engine.result_file):
            with open(engine.result_file, 'r') as f:
                result = json.load(f)
            print(f"   Result: {result['message']}")
            
            if 'results' in result:
                print(f"   📊 Final results: {len(result['results'].get('segments', []))} segments")
    
    # Command 4: Cleanup
    print("\n4️⃣ Cleaning up...")
    command = {"type": "cleanup"}
    with open(engine.command_file, 'w') as f:
        json.dump(command, f)
    
    time.sleep(1)  # Wait for processing
    
    print("✅ Demo completed!")
    print("\n💡 This demonstrates how iOS app can:")
    print("   - Send commands via JSON files")
    print("   - Read results and status")
    print("   - Get real-time transcription updates")
    print("   - Control engine lifecycle")


def macos_integration_demo():
    """Demo of macOS integration capabilities"""
    print("\n🖥️  macOS Integration Demo")
    print("=" * 50)
    
    # Create macOS-optimized engine
    engine = create_macos_engine(
        model_size="base.en",
        optimize_for_mobile=False,
        temp_dir="/tmp/nook_engine_macos_demo"
    )
    
    print(f"🔧 Engine created with temp dir: {engine.temp_dir}")
    
    # Initialize
    if not engine.initialize():
        print("❌ Failed to initialize engine")
        return
    
    print("✅ Engine initialized and ready for macOS app")
    
    # Simulate file transcription
    print("\n🧪 Simulating file transcription...")
    
    # Check if we have a test audio file
    test_audio = "test_audio.wav"
    if os.path.exists(test_audio):
        print(f"🎵 Transcribing: {test_audio}")
        
        command = {
            "type": "transcribe_file",
            "audio_file": test_audio,
            "enable_diarization": True,
            "output_format": "json"
        }
        
        with open(engine.command_file, 'w') as f:
            json.dump(command, f)
        
        time.sleep(2)  # Wait for processing
        
        if os.path.exists(engine.result_file):
            with open(engine.result_file, 'r') as f:
                result = json.load(f)
            print(f"   Result: {result['message']}")
            
            if result.get('success') and 'result' in result:
                transcript = result['result']
                print(f"   📝 Transcription completed!")
                print(f"   🎯 Segments: {len(transcript.get('segments', []))}")
                print(f"   👥 Speakers: {len(transcript.get('speakers', []))}")
    else:
        print(f"⚠️  Test audio file not found: {test_audio}")
        print("   Create a test_audio.wav file to test transcription")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    command = {"type": "cleanup"}
    with open(engine.command_file, 'w') as f:
        json.dump(command, f)
    
    time.sleep(1)
    print("✅ macOS demo completed!")


def swift_integration_guide():
    """Show Swift integration code examples"""
    print("\n📱 Swift Integration Guide")
    print("=" * 50)
    
    swift_code = '''
// Swift + PythonKit integration example

import Foundation
import PythonKit

class NookEngineManager: ObservableObject {
    @Published var isListening = false
    @Published var transcription = ""
    @Published var speakers: [String] = []
    
    private let engine: PythonObject
    private let tempDir = "/tmp/nook_engine"
    private var statusTimer: Timer?
    
    init() {
        // Initialize Python
        Python.initialize()
        
        // Import Nook Engine
        let nookEngine = Python.import("nook_engine")
        self.engine = nookEngine.create_ios_engine(
            model_size: "tiny.en",
            optimize_for_mobile: true,
            temp_dir: tempDir
        )
        
        // Initialize engine
        if engine.initialize() == true {
            print("✅ Nook Engine initialized")
            startStatusMonitoring()
        } else {
            print("❌ Failed to initialize Nook Engine")
        }
    }
    
    func startListening() {
        // Send command via JSON file
        let command = [
            "type": "start_listening",
            "enable_diarization": true
        ]
        
        sendCommand(command)
    }
    
    func stopListening() {
        let command = ["type": "stop_listening"]
        sendCommand(command)
    }
    
    private func sendCommand(_ command: [String: Any]) {
        let commandFile = "\(tempDir)/command.json"
        
        do {
            let data = try JSONSerialization.data(withJSONObject: command)
            try data.write(to: URL(fileURLWithPath: commandFile))
        } catch {
            print("Error sending command: \(error)")
        }
    }
    
    private func startStatusMonitoring() {
        statusTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in
            self.checkStatus()
            self.checkStream()
        }
    }
    
    private func checkStatus() {
        let statusFile = "\(tempDir)/status.json"
        guard let data = try? Data(contentsOf: URL(fileURLWithPath: statusFile)) else { return }
        
        do {
            let status = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            DispatchQueue.main.async {
                self.isListening = status?["is_listening"] as? Bool ?? false
            }
        } catch {
            print("Error reading status: \(error)")
        }
    }
    
    private func checkStream() {
        let streamFile = "\(tempDir)/stream.jsonl"
        guard let data = try? Data(contentsOf: URL(fileURLWithPath: streamFile)) else { return }
        
        guard let content = String(data: data, encoding: .utf8) else { return }
        let lines = content.components(separatedBy: .newlines).filter { !$0.isEmpty }
        
        if let lastLine = lines.last {
            do {
                let update = try JSONSerialization.jsonObject(with: Data(lastLine.utf8)) as? [String: Any]
                DispatchQueue.main.async {
                    self.transcription = update?["text"] as? String ?? ""
                }
            } catch {
                print("Error parsing stream: \(error)")
            }
        }
    }
    
    deinit {
        statusTimer?.invalidate()
        let command = ["type": "cleanup"]
        sendCommand(command)
    }
}
'''
    
    print("📝 Copy this Swift code to integrate Nook Engine:")
    print(swift_code)
    
    print("\n🔧 Key integration points:")
    print("   1. Use PythonKit to import nook_engine")
    print("   2. Create engine instance with create_ios_engine()")
    print("   3. Send commands via JSON files")
    print("   4. Monitor status and stream files")
    print("   5. Handle real-time updates in SwiftUI")


if __name__ == "__main__":
    print("🚀 Nook Engine iOS/macOS Integration Examples")
    print("=" * 60)
    
    try:
        # iOS integration demo
        ios_integration_demo()
        
        # macOS integration demo
        macos_integration_demo()
        
        # Swift integration guide
        swift_integration_guide()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    print("\n🎯 Next steps:")
    print("   1. Integrate with your Swift/SwiftUI app")
    print("   2. Customize the communication protocol")
    print("   3. Add error handling and retry logic")
    print("   4. Optimize for your specific use case")
