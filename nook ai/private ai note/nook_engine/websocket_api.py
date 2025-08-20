"""
WebSocket API for real-time transcription updates
Enables integration with web interfaces and real-time applications
"""

import asyncio
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Set
from websockets.server import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

from .simple_api import SimpleNookEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketTranscriptionServer:
    """
    WebSocket server for real-time transcription updates
    
    Features:
    - Real-time transcription streaming
    - Multiple client support
    - Speaker diarization updates
    - Error handling and reconnection
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        engine: Optional[SimpleNookEngine] = None
    ):
        """
        Initialize WebSocket server
        
        Args:
            host: Server host
            port: Server port
            engine: Pre-configured engine instance
        """
        self.host = host
        self.port = port
        self.engine = engine or create_mobile_engine()
        
        # WebSocket state
        self.clients: Set[WebSocketServerProtocol] = set()
        self.is_running = False
        self.server = None
        
        # Transcription state
        self.is_listening = False
        self.current_session = None
        
        # Callbacks
        self.on_client_connect: Optional[Callable] = None
        self.on_client_disconnect: Optional[Callable] = None
        self.on_transcription_start: Optional[Callable] = None
        self.on_transcription_stop: Optional[Callable] = None
    
    async def start_server(self):
        """Start WebSocket server"""
        try:
            logger.info(f"🚀 Starting WebSocket server on {self.host}:{self.port}")
            
            # Initialize engine
            if not self.engine.is_initialized:
                if not self.engine.initialize():
                    logger.error("❌ Failed to initialize engine")
                    return
            
            # Start server
            self.server = await serve(
                self._handle_client,
                self.host,
                self.port
            )
            
            self.is_running = True
            logger.info(f"✅ WebSocket server started on ws://{self.host}:{self.port}")
            
            # Keep server running
            await asyncio.Future()  # Run forever
            
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.is_running = False
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connection"""
        try:
            # Add client
            self.clients.add(websocket)
            client_id = id(websocket)
            
            logger.info(f"🔌 New client connected: {client_id}")
            
            if self.on_client_connect:
                self.on_client_connect(client_id)
            
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Nook Engine WebSocket API",
                "client_id": client_id,
                "status": self.engine.get_status()
            }))
            
            # Handle client messages
            async for message in websocket:
                await self._process_client_message(websocket, message)
                
        except ConnectionClosed:
            logger.info(f"🔌 Client disconnected: {id(websocket)}")
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            # Remove client
            self.clients.discard(websocket)
            if self.on_client_disconnect:
                self.on_client_disconnect(id(websocket))
    
    async def _process_client_message(self, websocket: WebSocketServerProtocol, message: str):
        """Process message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "start_listening":
                await self._handle_start_listening(websocket, data)
            elif msg_type == "stop_listening":
                await self._handle_stop_listening(websocket, data)
            elif msg_type == "transcribe_file":
                await self._handle_transcribe_file(websocket, data)
            elif msg_type == "get_status":
                await self._handle_get_status(websocket, data)
            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong", "timestamp": time.time()}))
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON message"
            }))
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Processing error: {e}"
            }))
    
    async def _handle_start_listening(self, websocket: WebSocketServerProtocol, data: Dict):
        """Handle start listening request"""
        try:
            if self.is_listening:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Already listening"
                }))
                return
            
            # Configure callbacks for real-time updates
            self.engine.set_callbacks(
                on_transcription_update=self._on_transcription_update,
                on_speaker_change=self._on_speaker_change,
                on_error=self._on_error
            )
            
            # Start listening
            output_file = data.get("output_file", "live_transcription.json")
            success = self.engine.start_listening(
                output_file=output_file,
                enable_diarization=data.get("enable_diarization", True),
                partial_updates=data.get("partial_updates", True),
                update_interval=data.get("update_interval", 1.0)
            )
            
            if success:
                self.is_listening = True
                self.current_session = {
                    "start_time": time.time(),
                    "output_file": output_file,
                    "client": websocket
                }
                
                await websocket.send(json.dumps({
                    "type": "listening_started",
                    "message": "Real-time listening started",
                    "output_file": output_file
                }))
                
                if self.on_transcription_start:
                    self.on_transcription_start()
                    
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Failed to start listening"
                }))
                
        except Exception as e:
            logger.error(f"Start listening error: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Start listening failed: {e}"
            }))
    
    async def _handle_stop_listening(self, websocket: WebSocketServerProtocol, data: Dict):
        """Handle stop listening request"""
        try:
            if not self.is_listening:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Not currently listening"
                }))
                return
            
            # Stop listening
            results = self.engine.stop_listening()
            self.is_listening = False
            
            # Send final results
            await websocket.send(json.dumps({
                "type": "listening_stopped",
                "message": "Real-time listening stopped",
                "results": results
            }))
            
            if self.on_transcription_stop:
                self.on_transcription_stop()
                
        except Exception as e:
            logger.error(f"Stop listening error: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Stop listening failed: {e}"
            }))
    
    async def _handle_transcribe_file(self, websocket: WebSocketServerProtocol, data: Dict):
        """Handle file transcription request"""
        try:
            audio_file = data.get("audio_file")
            if not audio_file:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "audio_file is required"
                }))
                return
            
            # Send progress update
            await websocket.send(json.dumps({
                "type": "transcription_progress",
                "message": "Starting transcription...",
                "audio_file": audio_file
            }))
            
            # Transcribe file
            result = self.engine.transcribe_file(
                audio_file=audio_file,
                enable_diarization=data.get("enable_diarization", True),
                output_format=data.get("output_format", "json")
            )
            
            if result:
                await websocket.send(json.dumps({
                    "type": "transcription_complete",
                    "message": "Transcription completed",
                    "audio_file": audio_file,
                    "result": result
                }))
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Transcription failed"
                }))
                
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"File transcription failed: {e}"
            }))
    
    async def _handle_get_status(self, websocket: WebSocketServerProtocol, data: Dict):
        """Handle status request"""
        try:
            status = self.engine.get_status()
            status.update({
                "websocket_server": {
                    "is_running": self.is_running,
                    "clients_count": len(self.clients),
                    "is_listening": self.is_listening
                }
            })
            
            await websocket.send(json.dumps({
                "type": "status",
                "status": status
            }))
            
        except Exception as e:
            logger.error(f"Status error: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Status failed: {e}"
            }))
    
    def _on_transcription_update(self, update: Dict):
        """Handle transcription update from engine"""
        asyncio.create_task(self._broadcast_transcription_update(update))
    
    def _on_speaker_change(self, speaker: str):
        """Handle speaker change from engine"""
        asyncio.create_task(self._broadcast_speaker_change(speaker))
    
    def _on_error(self, error: str):
        """Handle error from engine"""
        asyncio.create_task(self._broadcast_error(error))
    
    async def _broadcast_transcription_update(self, update: Dict):
        """Broadcast transcription update to all clients"""
        if not self.clients:
            return
        
        message = json.dumps({
            "type": "transcription_update",
            "update": update,
            "timestamp": time.time()
        })
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    async def _broadcast_speaker_change(self, speaker: str):
        """Broadcast speaker change to all clients"""
        if not self.clients:
            return
        
        message = json.dumps({
            "type": "speaker_change",
            "speaker": speaker,
            "timestamp": time.time()
        })
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Speaker change broadcast error: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    async def _broadcast_error(self, error: str):
        """Broadcast error to all clients"""
        if not self.clients:
            return
        
        message = json.dumps({
            "type": "error",
            "message": error,
            "timestamp": time.time()
        })
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcast error: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    def stop_server(self):
        """Stop WebSocket server"""
        try:
            if self.is_listening:
                self.engine.stop_listening()
            
            if self.server:
                self.server.close()
                self.is_running = False
            
            logger.info("🛑 WebSocket server stopped")
            
        except Exception as e:
            logger.error(f"Stop server error: {e}")
    
    def get_server_status(self) -> Dict:
        """Get server status"""
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "clients_count": len(self.clients),
            "is_listening": self.is_listening,
            "engine_status": self.engine.get_status() if self.engine else None
        }


# Convenience functions
def create_websocket_server(
    host: str = "localhost",
    port: int = 8765,
    engine: Optional[SimpleNookEngine] = None
) -> WebSocketTranscriptionServer:
    """Create a WebSocket server instance"""
    return WebSocketTranscriptionServer(host, port, engine)


def start_websocket_server(
    host: str = "localhost",
    port: int = 8765,
    engine: Optional[SimpleNookEngine] = None
):
    """Start WebSocket server in a separate thread"""
    server = create_websocket_server(host, port, engine)
    
    def run_server():
        asyncio.run(server.start_server())
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    return server


# Import from simple_api
from .simple_api import create_mobile_engine
