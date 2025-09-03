#!/usr/bin/env python3
"""
Audio Capture and WebSocket Sender for TransRapport Desktop MVP

This module provides cross-platform audio capture using sounddevice or PyAudio
and streams audio data via WebSocket to the backend for real-time processing.

Supports:
- macOS and Windows audio capture
- Real-time WebSocket streaming
- Configurable audio parameters
- Automatic device detection
- Recording path creation (fixes Wave_write AttributeError)
"""

import asyncio
import websockets
import json
import logging
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import argparse

# Audio library imports with fallback
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

# Data processing
import numpy as np
import wave
import io

# Configuration
DEFAULT_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "chunk_size": 1024,
    "format": "int16",
    "device": None,
    "websocket_url": "ws://127.0.0.1:8710/ws/audio",
    "recording_path": "./recordings",
    "buffer_size": 4096,
    "compression": False
}

class AudioCaptureError(Exception):
    """Audio capture related errors"""
    pass

class AudioCapture:
    """Cross-platform audio capture with WebSocket streaming"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.logger = logging.getLogger(__name__)
        self.is_recording = False
        self.websocket = None
        self.audio_buffer = []
        self.library = None
        
        # Recording path setup (fixes Wave_write AttributeError)
        self.recording_path = Path(self.config["recording_path"])
        self.recording_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize audio library
        self._initialize_audio_library()
        
    def _initialize_audio_library(self):
        """Initialize the best available audio library"""
        if SOUNDDEVICE_AVAILABLE:
            self.library = "sounddevice"
            self.logger.info("Using sounddevice for audio capture")
        elif PYAUDIO_AVAILABLE:
            self.library = "pyaudio"
            self.logger.info("Using PyAudio for audio capture")
        else:
            raise AudioCaptureError(
                "No audio library available. Please install sounddevice or pyaudio:\n"
                "pip install sounddevice\n"
                "# or\n"
                "pip install pyaudio"
            )
    
    def list_devices(self) -> Dict[str, Any]:
        """List available audio input devices"""
        devices = {"input_devices": []}
        
        if self.library == "sounddevice":
            device_list = sd.query_devices()
            for i, device in enumerate(device_list):
                if device['max_input_channels'] > 0:
                    devices["input_devices"].append({
                        "index": i,
                        "name": device['name'],
                        "channels": device['max_input_channels'],
                        "sample_rate": device['default_samplerate']
                    })
        
        elif self.library == "pyaudio":
            pa = pyaudio.PyAudio()
            for i in range(pa.get_device_count()):
                device = pa.get_device_info_by_index(i)
                if device['maxInputChannels'] > 0:
                    devices["input_devices"].append({
                        "index": i,
                        "name": device['name'],
                        "channels": device['maxInputChannels'],
                        "sample_rate": device['defaultSampleRate']
                    })
            pa.terminate()
        
        return devices
    
    def get_device_info(self, device_index: Optional[int] = None) -> Dict[str, Any]:
        """Get information about a specific device or default device"""
        if self.library == "sounddevice":
            if device_index is not None:
                device = sd.query_devices(device_index)
            else:
                device = sd.query_devices(kind='input')
            
            return {
                "index": device_index,
                "name": device['name'],
                "channels": device['max_input_channels'],
                "sample_rate": device['default_samplerate']
            }
        
        elif self.library == "pyaudio":
            pa = pyaudio.PyAudio()
            if device_index is not None:
                device = pa.get_device_info_by_index(device_index)
            else:
                device = pa.get_default_input_device_info()
            pa.terminate()
            
            return {
                "index": device_index or device['index'],
                "name": device['name'],
                "channels": device['maxInputChannels'],
                "sample_rate": device['defaultSampleRate']
            }
    
    async def connect_websocket(self, url: Optional[str] = None):
        """Connect to WebSocket server"""
        url = url or self.config["websocket_url"]
        try:
            self.websocket = await websockets.connect(url)
            self.logger.info(f"Connected to WebSocket: {url}")
            
            # Send initial configuration
            await self.websocket.send(json.dumps({
                "type": "audio_config",
                "config": {
                    "sample_rate": self.config["sample_rate"],
                    "channels": self.config["channels"],
                    "format": self.config["format"],
                    "chunk_size": self.config["chunk_size"]
                }
            }))
            
        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket: {e}")
            raise AudioCaptureError(f"WebSocket connection failed: {e}")
    
    async def disconnect_websocket(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.logger.info("Disconnected from WebSocket")
    
    def _audio_callback_sounddevice(self, indata, frames, time, status):
        """Callback for sounddevice audio capture"""
        if status:
            self.logger.warning(f"Audio callback status: {status}")
        
        if self.is_recording:
            # Convert to int16 if needed
            if self.config["format"] == "int16":
                audio_data = (indata * 32767).astype(np.int16)
            else:
                audio_data = indata
            
            # Add to buffer for WebSocket streaming
            self.audio_buffer.append(audio_data.tobytes())
    
    def _audio_callback_pyaudio(self, in_data, frame_count, time_info, status):
        """Callback for PyAudio audio capture"""
        if self.is_recording:
            self.audio_buffer.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    async def _stream_audio_data(self):
        """Stream audio data via WebSocket"""
        while self.is_recording and self.websocket:
            if self.audio_buffer:
                # Get audio chunks from buffer
                chunks_to_send = self.audio_buffer[:10]  # Send up to 10 chunks at once
                self.audio_buffer = self.audio_buffer[10:]
                
                if chunks_to_send:
                    try:
                        # Combine chunks
                        combined_data = b''.join(chunks_to_send)
                        
                        # Send audio data
                        await self.websocket.send(json.dumps({
                            "type": "audio_chunk",
                            "timestamp": time.time(),
                            "data": combined_data.hex(),  # Send as hex string
                            "size": len(combined_data)
                        }))
                        
                    except Exception as e:
                        self.logger.error(f"Failed to send audio data: {e}")
            
            await asyncio.sleep(0.01)  # 10ms intervals
    
    async def start_recording(self, duration: Optional[float] = None, 
                             save_to_file: bool = False) -> str:
        """Start audio recording and WebSocket streaming"""
        if self.is_recording:
            raise AudioCaptureError("Recording already in progress")
        
        self.is_recording = True
        self.audio_buffer = []
        
        # Generate recording filename if saving
        recording_file = None
        if save_to_file:
            timestamp = int(time.time())
            recording_file = self.recording_path / f"recording_{timestamp}.wav"
        
        try:
            if self.library == "sounddevice":
                await self._start_recording_sounddevice(duration, recording_file)
            elif self.library == "pyaudio":
                await self._start_recording_pyaudio(duration, recording_file)
            
        except Exception as e:
            self.is_recording = False
            raise AudioCaptureError(f"Recording failed: {e}")
        
        return str(recording_file) if recording_file else "streaming"
    
    async def _start_recording_sounddevice(self, duration: Optional[float], 
                                          recording_file: Optional[Path]):
        """Start recording with sounddevice"""
        device_info = self.get_device_info(self.config["device"])
        self.logger.info(f"Recording with device: {device_info['name']}")
        
        # Start WebSocket streaming task
        streaming_task = asyncio.create_task(self._stream_audio_data())
        
        try:
            with sd.InputStream(
                samplerate=self.config["sample_rate"],
                channels=self.config["channels"],
                device=self.config["device"],
                blocksize=self.config["chunk_size"],
                callback=self._audio_callback_sounddevice
            ):
                self.logger.info("Recording started...")
                
                if duration:
                    await asyncio.sleep(duration)
                else:
                    # Record until stopped
                    while self.is_recording:
                        await asyncio.sleep(0.1)
                        
        finally:
            streaming_task.cancel()
            try:
                await streaming_task
            except asyncio.CancelledError:
                pass
    
    async def _start_recording_pyaudio(self, duration: Optional[float], 
                                      recording_file: Optional[Path]):
        """Start recording with PyAudio"""
        device_info = self.get_device_info(self.config["device"])
        self.logger.info(f"Recording with device: {device_info['name']}")
        
        # Audio format mapping
        format_map = {
            "int16": pyaudio.paInt16,
            "int32": pyaudio.paInt32,
            "float32": pyaudio.paFloat32
        }
        
        pa = pyaudio.PyAudio()
        
        # Start WebSocket streaming task
        streaming_task = asyncio.create_task(self._stream_audio_data())
        
        try:
            stream = pa.open(
                format=format_map.get(self.config["format"], pyaudio.paInt16),
                channels=self.config["channels"],
                rate=self.config["sample_rate"],
                input=True,
                input_device_index=self.config["device"],
                frames_per_buffer=self.config["chunk_size"],
                stream_callback=self._audio_callback_pyaudio
            )
            
            stream.start_stream()
            self.logger.info("Recording started...")
            
            if duration:
                await asyncio.sleep(duration)
            else:
                # Record until stopped
                while self.is_recording:
                    await asyncio.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            
        finally:
            pa.terminate()
            streaming_task.cancel()
            try:
                await streaming_task
            except asyncio.CancelledError:
                pass
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        self.logger.info("Recording stopped")
    
    async def run_interactive(self):
        """Run in interactive mode with user controls"""
        print("TransRapport Audio Capture")
        print("=" * 30)
        
        # List available devices
        devices = self.list_devices()
        print("\nAvailable input devices:")
        for device in devices["input_devices"]:
            print(f"  {device['index']}: {device['name']} "
                  f"({device['channels']} channels, {device['sample_rate']} Hz)")
        
        # Device selection
        device_index = input(f"\nSelect device (Enter for default): ").strip()
        if device_index:
            self.config["device"] = int(device_index)
        
        # Connect to WebSocket
        print(f"\nConnecting to WebSocket: {self.config['websocket_url']}")
        try:
            await self.connect_websocket()
            print("✓ WebSocket connected")
        except Exception as e:
            print(f"✗ WebSocket connection failed: {e}")
            return
        
        # Start recording
        print("\nPress Enter to start recording, 'q' to quit...")
        while True:
            try:
                cmd = input().strip().lower()
                if cmd == 'q':
                    break
                elif cmd == '' and not self.is_recording:
                    print("Recording started. Press Enter to stop...")
                    await self.start_recording()
                elif cmd == '' and self.is_recording:
                    self.stop_recording()
                    print("Recording stopped. Press Enter to start again, 'q' to quit...")
            except KeyboardInterrupt:
                break
        
        # Cleanup
        self.stop_recording()
        await self.disconnect_websocket()
        print("Goodbye!")

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="TransRapport Audio Capture")
    parser.add_argument("--websocket-url", default=DEFAULT_CONFIG["websocket_url"],
                       help="WebSocket server URL")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_CONFIG["sample_rate"],
                       help="Audio sample rate")
    parser.add_argument("--channels", type=int, default=DEFAULT_CONFIG["channels"],
                       help="Number of audio channels")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CONFIG["chunk_size"],
                       help="Audio chunk size")
    parser.add_argument("--device", type=int, help="Audio device index")
    parser.add_argument("--duration", type=float, help="Recording duration in seconds")
    parser.add_argument("--list-devices", action="store_true",
                       help="List available audio devices")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Log level")
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    # Create configuration from args
    config = {
        "websocket_url": args.websocket_url,
        "sample_rate": args.sample_rate,
        "channels": args.channels,
        "chunk_size": args.chunk_size,
        "device": args.device
    }
    
    # Initialize audio capture
    try:
        capture = AudioCapture(config)
    except AudioCaptureError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # List devices if requested
    if args.list_devices:
        devices = capture.list_devices()
        print("Available input devices:")
        for device in devices["input_devices"]:
            print(f"  {device['index']}: {device['name']} "
                  f"({device['channels']} channels, {device['sample_rate']} Hz)")
        return
    
    # Run in interactive mode
    await capture.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())