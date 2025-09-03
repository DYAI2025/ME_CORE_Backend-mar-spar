#!/usr/bin/env python3
"""
Test script for TransRapport Desktop MVP WebSocket functionality

Tests the /ws/events endpoint for real-time marker events
"""

import asyncio
import websockets
import json
import time
from typing import Dict, Any

async def test_events_websocket():
    """Test the events WebSocket endpoint"""
    uri = "ws://127.0.0.1:8710/api/dashboard/ws/events"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to events WebSocket")
            
            # Send ping
            await websocket.send(json.dumps({
                "type": "ping",
                "timestamp": time.time()
            }))
            
            # Subscribe to events
            await websocket.send(json.dumps({
                "type": "subscribe",
                "event_types": ["marker_detected", "audio_chunk_processed"]
            }))
            
            print("Listening for events... (press Ctrl+C to stop)")
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    print(f"Received: {data.get('type', 'unknown')} - {data}")
                    
                except asyncio.TimeoutError:
                    print("No events received in last 5 seconds")
                    # Send ping to keep connection alive
                    await websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": time.time()
                    }))
                    
    except ConnectionRefused:
        print("✗ Connection refused - is the server running on port 8710?")
        print("  Run 'make run' to start the server")
    except Exception as e:
        print(f"✗ Error: {e}")

async def test_audio_websocket():
    """Test the audio WebSocket endpoint"""
    uri = "ws://127.0.0.1:8710/api/dashboard/ws/audio"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to audio WebSocket")
            
            # Send audio config
            await websocket.send(json.dumps({
                "type": "audio_config",
                "config": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "format": "int16",
                    "chunk_size": 1024
                }
            }))
            
            # Send sample audio chunk
            sample_audio_data = "00110011" * 128  # Fake audio data
            await websocket.send(json.dumps({
                "type": "audio_chunk",
                "timestamp": time.time(),
                "data": sample_audio_data,
                "size": len(sample_audio_data)
            }))
            
            print("Sample audio data sent")
            
    except ConnectionRefused:
        print("✗ Connection refused - is the server running on port 8710?")
        print("  Run 'make run' to start the server")
    except Exception as e:
        print(f"✗ Error: {e}")

async def test_dashboard_websocket():
    """Test the dashboard WebSocket endpoint"""
    uri = "ws://127.0.0.1:8710/api/dashboard/ws"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to dashboard WebSocket")
            
            # Send ping
            await websocket.send(json.dumps({
                "type": "ping"
            }))
            
            # Wait for pong
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            
            if data.get("type") == "pong":
                print("✓ Ping/pong successful")
            else:
                print(f"Unexpected response: {data}")
                
    except ConnectionRefused:
        print("✗ Connection refused - is the server running on port 8710?")
        print("  Run 'make run' to start the server")
    except Exception as e:
        print(f"✗ Error: {e}")

async def main():
    """Run all WebSocket tests"""
    print("TransRapport Desktop MVP WebSocket Tests")
    print("=" * 40)
    
    # Test dashboard WebSocket
    print("\n1. Testing dashboard WebSocket...")
    await test_dashboard_websocket()
    
    # Test events WebSocket  
    print("\n2. Testing events WebSocket...")
    await test_events_websocket()
    
    # Test audio WebSocket
    print("\n3. Testing audio WebSocket...")
    await test_audio_websocket()
    
    print("\nTests completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTests interrupted by user")