"""
Quick WebSocket test client
Connects to the telemetry stream and prints packets
"""

import asyncio
import websockets
import json


async def test_websocket():
    """Connect to WebSocket and print telemetry"""
    uri = "ws://localhost:8000/ws/telemetry"
    
    print("Connecting to telemetry stream...")
    print(f"URI: {uri}")
    print("-" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            print("-" * 60)
            
            # Receive and print 10 packets
            for i in range(10):
                message = await websocket.recv()
                data = json.loads(message)
                
                # Print formatted telemetry
                if "flight_state_name" in data:
                    print(f"Packet #{i+1}:")
                    print(f"  Time: {data['timestamp_ms']}ms")
                    print(f"  State: {data['flight_state_name']}")
                    print(f"  Altitude: {data['altitude_m']:.2f}m")
                    print(f"  Velocity: {data['velocity_ms']:.2f}m/s")
                    print(f"  GPS: ({data['gps_lat']:.6f}, {data['gps_lon']:.6f})")
                    print("-" * 60)
                else:
                    print(f"Message: {data}")
            
            print("✅ Test complete! Received 10 packets successfully.")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
