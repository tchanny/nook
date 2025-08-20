"""
Nook Engine - Privacy-First Speech Recognition Engine
Local transcription and speaker diarization with real-time capabilities
"""

from .core import NookEngine
from .simple_api import SimpleNookEngine, create_mobile_engine, create_high_quality_engine, create_fast_engine
from .websocket_api import WebSocketTranscriptionServer, create_websocket_server, start_websocket_server
from .ios_integration import IOSIntegrationEngine, create_ios_engine, create_macos_engine

# Core classes
__all__ = [
    # Main engine
    "NookEngine",
    
    # Simple API for embedding
    "SimpleNookEngine",
    "create_mobile_engine",
    "create_high_quality_engine", 
    "create_fast_engine",
    
    # WebSocket API
    "WebSocketTranscriptionServer",
    "create_websocket_server",
    "start_websocket_server",
    
    # iOS/macOS integration
    "IOSIntegrationEngine",
    "create_ios_engine",
    "create_macos_engine",
]

# Version info
__version__ = "1.0.0"
__author__ = "Nook AI Team"
__description__ = "Privacy-first speech recognition engine for local transcription and speaker diarization"

# Quick start functions
def quick_start():
    """Quick start with mobile-optimized engine"""
    engine = create_mobile_engine()
    if engine.initialize():
        print("✅ Nook Engine ready!")
        return engine
    else:
        print("❌ Failed to initialize")
        return None

def start_websocket_demo(host="localhost", port=8765):
    """Start WebSocket demo server"""
    server = start_websocket_server(host, port)
    print(f"🚀 WebSocket server started on ws://{host}:{port}")
    print("Connect with a WebSocket client to test real-time transcription")
    return server

def start_ios_demo(temp_dir="/tmp/nook_engine"):
    """Start iOS integration demo"""
    engine = create_ios_engine(temp_dir=temp_dir)
    if engine.initialize():
        print("✅ iOS Integration Engine ready!")
        print(f"📁 Communication files in: {temp_dir}")
        print("📱 Send commands via command.json file")
        return engine
    else:
        print("❌ Failed to initialize")
        return None
