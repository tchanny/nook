"""
WebSocket Client Example for Nook Engine
Test real-time transcription via WebSocket API
"""

import asyncio
import json
import websockets
import time
from typing import Dict, Optional


class NookEngineWebSocketClient:
    """WebSocket client for testing Nook Engine real-time API"""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.is_connected = False
        
        # State
        self.is_listening = False
        self.transcription_history = []
        self.speakers = []
        
        # Callbacks
        self.on_transcription_update = None
        self.on_speaker_change = None
        self.on_error = None
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            print(f"🔌 Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            print("✅ Connected to Nook Engine WebSocket API")
            
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            print("🔌 Disconnected from WebSocket API")
    
    async def _listen_for_messages(self):
        """Listen for incoming messages from server"""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            print(f"❌ Message listening error: {e}")
    
    async def _handle_message(self, message: str):
        """Handle incoming message from server"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "welcome":
                print(f"👋 {data.get('message', 'Welcome')}")
                print(f"   Client ID: {data.get('client_id')}")
                
            elif msg_type == "listening_started":
                print(f"🎤 {data.get('message', 'Listening started')}")
                self.is_listening = True
                
            elif msg_type == "listening_stopped":
                print(f"🛑 {data.get('message', 'Listening stopped')}")
                self.is_listening = False
                
                # Show final results
                if 'results' in data:
                    results = data['results']
                    print(f"📊 Final results:")
                    print(f"   Segments: {len(results.get('segments', []))}")
                    print(f"   Speakers: {len(results.get('speakers', []))}")
                    print(f"   Duration: {results.get('total_duration', 0):.1f}s")
                
            elif msg_type == "transcription_update":
                update = data.get("update", {})
                text = update.get("text", "")
                speaker = update.get("speaker", "Unknown")
                timestamp = update.get("timestamp", 0)
                
                # Add to history
                self.transcription_history.append({
                    "text": text,
                    "speaker": speaker,
                    "timestamp": timestamp
                })
                
                # Display update
                print(f"📝 [{speaker}] {text}")
                
                # Trigger callback
                if self.on_transcription_update:
                    self.on_transcription_update(update)
                
            elif msg_type == "speaker_change":
                speaker = data.get("speaker", "Unknown")
                print(f"👥 Speaker changed to: {speaker}")
                
                if speaker not in self.speakers:
                    self.speakers.append(speaker)
                
                # Trigger callback
                if self.on_speaker_change:
                    self.on_speaker_change(speaker)
                
            elif msg_type == "transcription_progress":
                print(f"🔄 {data.get('message', 'Progress')}")
                
            elif msg_type == "transcription_complete":
                print(f"✅ {data.get('message', 'Transcription complete')}")
                if 'result' in data:
                    result = data['result']
                    print(f"   Audio file: {data.get('audio_file')}")
                    print(f"   Segments: {len(result.get('segments', []))}")
                    print(f"   Speakers: {len(result.get('speakers', []))}")
                
            elif msg_type == "error":
                error_msg = data.get("message", "Unknown error")
                print(f"❌ Error: {error_msg}")
                
                # Trigger callback
                if self.on_error:
                    self.on_error(error_msg)
                
            elif msg_type == "pong":
                # Ping-pong for connection health
                pass
                
            else:
                print(f"❓ Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON message: {message}")
        except Exception as e:
            print(f"❌ Message handling error: {e}")
    
    async def send_command(self, command: Dict) -> bool:
        """Send command to server"""
        if not self.is_connected or not self.websocket:
            print("❌ Not connected to server")
            return False
        
        try:
            await self.websocket.send(json.dumps(command))
            return True
        except Exception as e:
            print(f"❌ Failed to send command: {e}")
            return False
    
    async def start_listening(
        self,
        output_file: str = "live_transcription.json",
        enable_diarization: bool = True,
        partial_updates: bool = True,
        update_interval: float = 1.0
    ) -> bool:
        """Start real-time listening"""
        command = {
            "type": "start_listening",
            "output_file": output_file,
            "enable_diarization": enable_diarization,
            "partial_updates": partial_updates,
            "update_interval": update_interval
        }
        
        return await self.send_command(command)
    
    async def stop_listening(self) -> bool:
        """Stop real-time listening"""
        command = {"type": "stop_listening"}
        return await self.send_command(command)
    
    async def transcribe_file(
        self,
        audio_file: str,
        enable_diarization: bool = True,
        output_format: str = "json"
    ) -> bool:
        """Transcribe an audio file"""
        command = {
            "type": "transcribe_file",
            "audio_file": audio_file,
            "enable_diarization": enable_diarization,
            "output_format": output_format
        }
        
        return await self.send_command(command)
    
    async def get_status(self) -> bool:
        """Get server status"""
        command = {"type": "get_status"}
        return await self.send_command(command)
    
    async def ping(self) -> bool:
        """Send ping to server"""
        command = {"type": "ping"}
        return await self.send_command(command)
    
    def get_transcription_summary(self) -> Dict:
        """Get summary of transcription session"""
        if not self.transcription_history:
            return {"message": "No transcription data"}
        
        total_words = sum(len(item["text"].split()) for item in self.transcription_history)
        unique_speakers = list(set(item["speaker"] for item in self.transcription_history))
        
        return {
            "total_segments": len(self.transcription_history),
            "total_words": total_words,
            "speakers": unique_speakers,
            "duration": time.time() - self.transcription_history[0]["timestamp"] if self.transcription_history else 0
        }


async def interactive_demo():
    """Interactive demo of WebSocket client"""
    print("🚀 Nook Engine WebSocket Client Demo")
    print("=" * 50)
    
    # Create client
    client = NookEngineWebSocketClient()
    
    # Set up callbacks
    def on_transcription(update):
        # Custom handling of transcription updates
        pass
    
    def on_speaker_change(speaker):
        print(f"🎭 New speaker detected: {speaker}")
    
    def on_error(error):
        print(f"🚨 Error occurred: {error}")
    
    client.on_transcription_update = on_transcription
    client.on_speaker_change = on_speaker_change
    client.on_error = on_error
    
    # Connect to server
    if not await client.connect():
        print("❌ Failed to connect. Make sure WebSocket server is running.")
        return
    
    try:
        print("\n📋 Available commands:")
        print("   1. start - Start real-time listening")
        print("   2. stop - Stop listening")
        print("   3. transcribe <file> - Transcribe audio file")
        print("   4. status - Get server status")
        print("   5. ping - Test connection")
        print("   6. summary - Show transcription summary")
        print("   7. quit - Exit demo")
        
        while True:
            try:
                command = input("\n🎯 Enter command: ").strip().lower()
                
                if command == "start":
                    print("🎤 Starting real-time listening...")
                    await client.start_listening()
                    
                elif command == "stop":
                    print("🛑 Stopping listening...")
                    await client.stop_listening()
                    
                elif command.startswith("transcribe "):
                    audio_file = command.split(" ", 1)[1]
                    print(f"🎵 Transcribing: {audio_file}")
                    await client.transcribe_file(audio_file)
                    
                elif command == "status":
                    print("📊 Getting server status...")
                    await client.get_status()
                    
                elif command == "ping":
                    print("🏓 Pinging server...")
                    await client.ping()
                    
                elif command == "summary":
                    summary = client.get_transcription_summary()
                    print("📊 Transcription Summary:")
                    for key, value in summary.items():
                        print(f"   {key}: {value}")
                    
                elif command == "quit":
                    print("👋 Goodbye!")
                    break
                    
                else:
                    print("❓ Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                print("\n⏹️  Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Command error: {e}")
    
    finally:
        # Cleanup
        await client.disconnect()


async def automated_demo():
    """Automated demo of WebSocket client"""
    print("🤖 Automated WebSocket Client Demo")
    print("=" * 50)
    
    # Create client
    client = NookEngineWebSocketClient()
    
    # Connect to server
    if not await client.connect():
        print("❌ Failed to connect. Make sure WebSocket server is running.")
        return
    
    try:
        print("🔄 Running automated demo...")
        
        # Get status
        print("\n1️⃣ Getting server status...")
        await client.get_status()
        await asyncio.sleep(1)
        
        # Start listening
        print("\n2️⃣ Starting real-time listening...")
        await client.start_listening()
        await asyncio.sleep(5)  # Listen for 5 seconds
        
        # Stop listening
        print("\n3️⃣ Stopping listening...")
        await client.stop_listening()
        await asyncio.sleep(1)
        
        # Show summary
        print("\n4️⃣ Transcription summary:")
        summary = client.get_transcription_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Automated demo completed!")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
    
    finally:
        # Cleanup
        await client.disconnect()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        # Run automated demo
        asyncio.run(automated_demo())
    else:
        # Run interactive demo
        asyncio.run(interactive_demo())
