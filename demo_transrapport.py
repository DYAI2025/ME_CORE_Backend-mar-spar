#!/usr/bin/env python3
"""
TransRapport Desktop MVP Demo

Demonstrates the real-time marker detection system with simulated audio.
"""

import asyncio
import websockets
import json
import time
import random
import numpy as np
from typing import Dict, Any

class AudioSimulator:
    """Simulates audio data for demonstration"""
    
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 0.5):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
    def generate_chunk(self, emotion_type: str = "neutral") -> bytes:
        """Generate simulated audio chunk with different emotional characteristics"""
        
        # Base frequency and amplitude parameters based on emotion
        if emotion_type == "anxious":
            base_freq = 220  # Higher pitch for anxiety
            amplitude = 0.6  # Higher amplitude
            noise_level = 0.3
        elif emotion_type == "avoidant":
            base_freq = 120  # Lower pitch
            amplitude = 0.2  # Lower amplitude
            noise_level = 0.1
        elif emotion_type == "secure":
            base_freq = 150  # Balanced pitch
            amplitude = 0.4  # Balanced amplitude
            noise_level = 0.15
        else:  # neutral
            base_freq = 140
            amplitude = 0.3
            noise_level = 0.2
        
        # Generate time array
        t = np.linspace(0, self.chunk_duration, self.chunk_size)
        
        # Generate base tone with some frequency modulation
        freq_modulation = 1 + 0.1 * np.sin(2 * np.pi * 2 * t)  # 2 Hz modulation
        signal = amplitude * np.sin(2 * np.pi * base_freq * freq_modulation * t)
        
        # Add harmonics for more realistic sound
        signal += 0.3 * amplitude * np.sin(2 * np.pi * base_freq * 2 * freq_modulation * t)
        signal += 0.2 * amplitude * np.sin(2 * np.pi * base_freq * 3 * freq_modulation * t)
        
        # Add noise
        noise = noise_level * np.random.normal(0, 1, len(signal))
        signal += noise
        
        # Apply some amplitude modulation (speech-like)
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 5 * t)  # 5 Hz envelope
        signal *= envelope
        
        # Convert to int16
        signal = np.clip(signal, -1, 1)
        audio_data = (signal * 32767).astype(np.int16)
        
        return audio_data.tobytes()

class TransRapportDemo:
    """Main demonstration class"""
    
    def __init__(self):
        self.audio_simulator = AudioSimulator()
        self.websocket_url = "ws://127.0.0.1:8710"
        self.events_ws = None
        self.audio_ws = None
        self.running = False
        
    async def connect(self):
        """Connect to WebSocket endpoints"""
        try:
            print("Connecting to TransRapport Desktop MVP...")
            
            # Connect to events WebSocket
            events_url = f"{self.websocket_url}/api/dashboard/ws/events"
            self.events_ws = await websockets.connect(events_url)
            print(f"✓ Connected to events WebSocket: {events_url}")
            
            # Connect to audio WebSocket
            audio_url = f"{self.websocket_url}/api/dashboard/ws/audio"
            self.audio_ws = await websockets.connect(audio_url)
            print(f"✓ Connected to audio WebSocket: {audio_url}")
            
            # Send audio configuration
            await self.audio_ws.send(json.dumps({
                "type": "audio_config",
                "config": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "int16",
                    "chunk_size": 8000  # 0.5 seconds at 16kHz
                }
            }))
            print("✓ Audio configuration sent")
            
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            print("Make sure the server is running: make run")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket endpoints"""
        if self.events_ws:
            await self.events_ws.close()
        if self.audio_ws:
            await self.audio_ws.close()
        print("Disconnected from WebSockets")
    
    async def listen_for_events(self):
        """Listen for marker events"""
        if not self.events_ws:
            return
            
        print("\n📡 Listening for marker events...")
        try:
            while self.running:
                message = await asyncio.wait_for(self.events_ws.recv(), timeout=1.0)
                event = json.loads(message)
                
                # Display event
                self.display_event(event)
                
        except asyncio.TimeoutError:
            pass  # Continue listening
        except Exception as e:
            print(f"Event listening error: {e}")
    
    def display_event(self, event: Dict[str, Any]):
        """Display a marker event"""
        event_type = event.get("type", "unknown")
        marker_id = event.get("marker_id", "unknown")
        category = event.get("category", "unknown")
        confidence = event.get("confidence", 0.0)
        
        # Format confidence as percentage
        confidence_pct = f"{confidence * 100:.1f}%"
        
        # Color coding for categories
        color_map = {
            "ATO": "🔴",      # Red for attachment
            "SEM": "🔵",      # Blue for semantic
            "CLU": "🟡",      # Yellow for clustering
            "INTUITION": "🟣", # Purple for intuition
            "SYSTEM": "⚙️"    # Gear for system
        }
        
        icon = color_map.get(category, "⚪")
        
        if event_type == "marker_detected":
            print(f"{icon} {category} | {marker_id} ({confidence_pct})")
            
            # Show prosody features if available
            prosody = event.get("prosody_features")
            if prosody:
                f0 = prosody.get("f0", 0)
                rms = prosody.get("rms", 0)
                print(f"   Prosody: F0={f0:.1f}Hz, RMS={rms:.3f}")
            
            # Show metadata if available
            metadata = event.get("metadata")
            if metadata:
                if "attachment_style" in metadata:
                    style = metadata["attachment_style"]
                    indicators = ", ".join(metadata.get("indicators", []))
                    print(f"   Attachment: {style} ({indicators})")
                elif "pattern_type" in metadata:
                    pattern = metadata["pattern_type"]
                    note = metadata.get("therapeutic_note", "")
                    print(f"   Pattern: {pattern} - {note}")
        
        elif event_type == "audio_chunk_processed":
            markers_detected = event.get("metadata", {}).get("markers_detected", 0)
            if markers_detected > 0:
                print(f"⚙️  Audio processed: {markers_detected} markers detected")
        
        elif event_type in ["ato_heuristic", "sem_gating", "clu_windowing", "intuition_signal"]:
            print(f"{icon} {event_type.upper()} | {marker_id} ({confidence_pct})")
    
    async def simulate_conversation(self):
        """Simulate a conversation with different emotional states"""
        if not self.audio_ws:
            return
            
        print("\n🎤 Starting conversation simulation...")
        print("Simulating different emotional states:")
        
        # Conversation scenario
        scenarios = [
            ("neutral", 3, "Starting conversation (neutral)"),
            ("secure", 4, "Discussing positive memories (secure attachment)"),
            ("anxious", 5, "Talking about relationship concerns (anxious)"),
            ("neutral", 2, "Transition period"),
            ("avoidant", 4, "Discussing difficult topics (avoidant)"),
            ("secure", 3, "Resolution phase (secure)"),
            ("neutral", 2, "Ending conversation")
        ]
        
        for emotion_type, duration, description in scenarios:
            print(f"\n{description} - {duration}s")
            
            # Send audio chunks for this emotional state
            chunks_to_send = int(duration / 0.5)  # 0.5s per chunk
            
            for i in range(chunks_to_send):
                if not self.running:
                    break
                    
                # Generate audio chunk
                audio_data = self.audio_simulator.generate_chunk(emotion_type)
                
                # Send via WebSocket
                await self.audio_ws.send(json.dumps({
                    "type": "audio_chunk",
                    "timestamp": time.time(),
                    "data": audio_data.hex(),
                    "size": len(audio_data)
                }))
                
                # Wait for next chunk
                await asyncio.sleep(0.5)
                
                # Show progress
                if i % 2 == 0:  # Every second
                    print(".", end="", flush=True)
            
            print()  # New line after each scenario
    
    async def run_demo(self):
        """Run the complete demonstration"""
        print("TransRapport Desktop MVP - Real-time Marker Detection Demo")
        print("=" * 60)
        
        # Connect to server
        if not await self.connect():
            return
        
        self.running = True
        
        try:
            # Start event listener
            event_task = asyncio.create_task(self.listen_for_events())
            
            # Wait a moment for connection to stabilize
            await asyncio.sleep(1)
            
            # Run conversation simulation
            await self.simulate_conversation()
            
            # Keep listening for a moment to catch final events
            print("\n⏳ Waiting for final events...")
            await asyncio.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user")
        
        finally:
            self.running = False
            
            # Cancel event task
            if 'event_task' in locals():
                event_task.cancel()
                try:
                    await event_task
                except asyncio.CancelledError:
                    pass
            
            await self.disconnect()
            print("\nDemo completed!")

async def main():
    """Main entry point"""
    demo = TransRapportDemo()
    await demo.run_demo()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo stopped.")