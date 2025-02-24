from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List
import sqlite3
import random

"""
To test in terminal:

curl -X POST "http://127.0.0.1:8000/orders" -H "accept: application/json" (for post)
"""

app = FastAPI()


# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the FastAPI Trade Orders API. Use /orders to create and fetch trade orders."
    }


# Database setup
def get_db():
    conn = sqlite3.connect("orders.db", check_same_thread=False)
    cursor = conn.cursor()

    # Ensure the table is only created if it does not already exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            price REAL,
            quantity INTEGER,
            order_type TEXT
        )
    """
    )
    conn.commit()
    return conn, cursor


# Order Model
class Order(BaseModel):
    symbol: str
    price: float
    quantity: int
    order_type: str  # buy/sell


# Function to generate random order
def generate_random_order():
    symbols = ["AAPL", "GOOGL", "AMZN", "TSLA", "MSFT"]
    order_types = ["buy", "sell"]
    return Order(
        symbol=random.choice(symbols),
        price=round(random.uniform(50, 5000), 2),
        quantity=random.randint(1, 100),
        order_type=random.choice(order_types),
    )


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# WebSocket Endpoint for real-time order updates
@app.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# POST /orders - Create a new order and broadcast it
@app.post("/orders", response_model=Order)
async def create_order():
    order = generate_random_order()
    conn, cursor = get_db()
    cursor.execute(
        "INSERT INTO orders (symbol, price, quantity, order_type) VALUES (?, ?, ?, ?)",
        (order.symbol, order.price, order.quantity, order.order_type),
    )
    conn.commit()
    conn.close()
    await manager.broadcast(
        f"New Order Created: {order.symbol} at {order.price} ({order.order_type})"
    )
    return order


# GET /orders - Get all orders
@app.get("/orders", response_model=List[Order])
def get_orders():
    conn, cursor = get_db()
    cursor.execute("SELECT symbol, price, quantity, order_type FROM orders")
    orders = [
        Order(symbol=row[0], price=row[1], quantity=row[2], order_type=row[3])
        for row in cursor.fetchall()
    ]
    conn.close()
    return orders
