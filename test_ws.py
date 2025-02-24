import asyncio
import websockets


async def listen():
    uri = "ws://127.0.0.1:8000/ws/orders"  # Corrected WebSocket URL
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print(f"Received: {message}")


asyncio.run(listen())

"""
if successful, this script will print the messages received from the WebSocket server.

for example:
    Received: New Order Created: MSFT at 3984.21 (sell)
    Received: New Order Created: AAPL at 3442.68 (sell)
"""
