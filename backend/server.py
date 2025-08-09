from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import socketio
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import asyncio
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Socket.IO setup
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Data Models
class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: str  # batsman, bowler, all-rounder, wicket-keeper
    base_price: float  # in lakhs
    country: str
    rating: int  # 1-5 stars
    stats: Dict[str, Any] = {}

class Team(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    owner_id: str
    budget: float = 8000.0  # 80 crores in lakhs
    players: List[str] = []  # player IDs
    
class Room(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    host_id: str
    teams: List[Team] = []
    current_player_index: int = 0
    auction_state: str = "waiting"  # waiting, active, completed
    current_bid: float = 0
    current_bidder: str = ""
    timer_end: Optional[datetime] = None
    players_pool: List[str] = []  # player IDs for auction
    sold_players: List[str] = []

# Initialize cricket players database
async def init_players_db():
    existing_count = await db.players.count_documents({})
    if existing_count > 0:
        return
    
    # Create 200 cricket players
    players_data = []
    
    # Indian Players
    indian_players = [
        ("Virat Kohli", "batsman", 1500, 5), ("Rohit Sharma", "batsman", 1400, 5),
        ("KL Rahul", "wicket-keeper", 1100, 4), ("Hardik Pandya", "all-rounder", 1500, 5),
        ("Jasprit Bumrah", "bowler", 1200, 5), ("Mohammed Shami", "bowler", 900, 4),
        ("Ravindra Jadeja", "all-rounder", 1600, 5), ("Rishabh Pant", "wicket-keeper", 1600, 5),
        ("Shubman Gill", "batsman", 800, 4), ("Yuzvendra Chahal", "bowler", 600, 4),
        ("Bhuvneshwar Kumar", "bowler", 400, 3), ("Ishan Kishan", "wicket-keeper", 1520, 4),
        ("Shreyas Iyer", "batsman", 1225, 4), ("Suryakumar Yadav", "batsman", 800, 4),
        ("Washington Sundar", "all-rounder", 325, 3), ("Axar Patel", "all-rounder", 900, 4),
        ("Mohammed Siraj", "bowler", 600, 4), ("Kuldeep Yadav", "bowler", 200, 3),
        ("Deepak Chahar", "bowler", 1400, 3), ("Sanju Samson", "wicket-keeper", 1400, 4),
        ("Prithvi Shaw", "batsman", 750, 3), ("Mayank Agarwal", "batsman", 1200, 3),
        ("Shikhar Dhawan", "batsman", 850, 4), ("Dinesh Karthik", "wicket-keeper", 550, 3),
        ("Krunal Pandya", "all-rounder", 850, 3), ("Rahul Chahar", "bowler", 525, 3),
    ]
    
    # International Players
    international_players = [
        ("Jos Buttler", "wicket-keeper", 1000, 5, "England"), ("Ben Stokes", "all-rounder", 1650, 5, "England"),
        ("Jason Roy", "batsman", 200, 4, "England"), ("Liam Livingstone", "all-rounder", 1150, 4, "England"),
        ("Jonny Bairstow", "wicket-keeper", 675, 4, "England"), ("Sam Curran", "all-rounder", 1850, 4, "England"),
        ("David Warner", "batsman", 650, 5, "Australia"), ("Steve Smith", "batsman", 220, 5, "Australia"),
        ("Glenn Maxwell", "all-rounder", 1100, 4, "Australia"), ("Pat Cummins", "bowler", 750, 5, "Australia"),
        ("Mitchell Starc", "bowler", 2475, 5, "Australia"), ("Josh Hazlewood", "bowler", 175, 4, "Australia"),
        ("Marcus Stoinis", "all-rounder", 900, 3, "Australia"), ("Aaron Finch", "batsman", 150, 4, "Australia"),
        ("Kane Williamson", "batsman", 200, 5, "New Zealand"), ("Trent Boult", "bowler", 800, 4, "New Zealand"),
        ("Mitchell Santner", "all-rounder", 200, 3, "New Zealand"), ("Tim Southee", "bowler", 150, 4, "New Zealand"),
        ("Quinton de Kock", "wicket-keeper", 675, 4, "South Africa"), ("Kagiso Rabada", "bowler", 950, 5, "South Africa"),
        ("Anrich Nortje", "bowler", 650, 4, "South Africa"), ("Aiden Markram", "batsman", 200, 4, "South Africa"),
        ("Babar Azam", "batsman", 200, 5, "Pakistan"), ("Shaheen Afridi", "bowler", 800, 5, "Pakistan"),
        ("Mohammad Rizwan", "wicket-keeper", 200, 4, "Pakistan"), ("Rashid Khan", "bowler", 1500, 5, "Afghanistan"),
    ]
    
    # Add more players to reach 200
    additional_players = []
    for i in range(150):
        roles = ["batsman", "bowler", "all-rounder", "wicket-keeper"]
        countries = ["India", "England", "Australia", "South Africa", "New Zealand", "Pakistan", "West Indies", "Sri Lanka", "Bangladesh", "Afghanistan"]
        
        additional_players.append((
            f"Player {i+1}",
            random.choice(roles),
            random.randint(20, 800),
            random.randint(2, 4),
            random.choice(countries)
        ))
    
    # Create player objects
    for name, role, price, rating in indian_players:
        player = Player(
            name=name,
            role=role,
            base_price=price,
            country="India",
            rating=rating
        )
        players_data.append(player.dict())
    
    for name, role, price, rating, country in international_players:
        player = Player(
            name=name,
            role=role,
            base_price=price,
            country=country,
            rating=rating
        )
        players_data.append(player.dict())
    
    for name, role, price, rating, country in additional_players:
        player = Player(
            name=name,
            role=role,
            base_price=price,
            country=country,
            rating=rating
        )
        players_data.append(player.dict())
    
    await db.players.insert_many(players_data)

# Socket.IO Events
@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@sio.event
async def join_room(sid, data):
    room_code = data.get('room_code')
    team_name = data.get('team_name')
    
    # Find room by code
    room_data = await db.rooms.find_one({"code": room_code})
    if not room_data:
        await sio.emit('error', {'message': 'Room not found'}, to=sid)
        return
    
    room = Room(**room_data)
    
    # Check if room is full
    if len(room.teams) >= 8:
        await sio.emit('error', {'message': 'Room is full'}, to=sid)
        return
    
    # Create new team
    team = Team(name=team_name, owner_id=sid)
    room.teams.append(team)
    
    # Update room in database
    await db.rooms.update_one(
        {"code": room_code},
        {"$set": {"teams": [team.dict() for team in room.teams]}}
    )
    
    # Join socket room
    await sio.enter_room(sid, room_code)
    
    # Notify all users in room
    await sio.emit('team_joined', {
        'team': team.dict(),
        'total_teams': len(room.teams)
    }, room=room_code)

@sio.event
async def place_bid(sid, data):
    room_code = data.get('room_code')
    bid_amount = data.get('bid_amount')
    
    room_data = await db.rooms.find_one({"code": room_code})
    if not room_data:
        return
    
    room = Room(**room_data)
    
    # Validate bid
    if bid_amount <= room.current_bid:
        await sio.emit('error', {'message': 'Bid must be higher than current bid'}, to=sid)
        return
    
    # Find team by owner_id
    team = next((t for t in room.teams if t.owner_id == sid), None)
    if not team:
        return
    
    # Check budget
    if bid_amount > team.budget:
        await sio.emit('error', {'message': 'Insufficient budget'}, to=sid)
        return
    
    # Update bid
    room.current_bid = bid_amount
    room.current_bidder = sid
    room.timer_end = datetime.utcnow() + timedelta(seconds=30)
    
    # Update in database
    await db.rooms.update_one(
        {"code": room_code},
        {"$set": {
            "current_bid": room.current_bid,
            "current_bidder": room.current_bidder,
            "timer_end": room.timer_end
        }}
    )
    
    # Broadcast bid to all users in room
    await sio.emit('new_bid', {
        'bid_amount': bid_amount,
        'bidder_team': team.name,
        'timer_end': room.timer_end.isoformat()
    }, room=room_code)

# API Routes
@api_router.post("/room/create")
async def create_room():
    # Generate 6-digit code
    code = str(random.randint(100000, 999999))
    
    # Get all players for auction
    all_players = await db.players.find().to_list(1000)
    player_ids = [player["id"] for player in all_players]
    
    room = Room(
        code=code,
        host_id="",
        players_pool=player_ids
    )
    
    await db.rooms.insert_one(room.dict())
    
    return {"room_code": code}

@api_router.get("/room/{room_code}")
async def get_room(room_code: str):
    room_data = await db.rooms.find_one({"code": room_code})
    if not room_data:
        return {"error": "Room not found"}
    
    return room_data

@api_router.get("/players")
async def get_players():
    players = await db.players.find().to_list(1000)
    return players

@api_router.post("/room/{room_code}/start")
async def start_auction(room_code: str):
    room_data = await db.rooms.find_one({"code": room_code})
    if not room_data:
        return {"error": "Room not found"}
    
    # Start auction
    await db.rooms.update_one(
        {"code": room_code},
        {"$set": {"auction_state": "active"}}
    )
    
    # Get first player
    players = await db.players.find().to_list(1000)
    if players:
        first_player = players[0]
        await sio.emit('auction_started', {
            'current_player': first_player,
            'current_bid': first_player['base_price']
        }, room=room_code)
    
    return {"message": "Auction started"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_players_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Don't mount socket app at root - it conflicts with FastAPI routes
# Instead, we'll use the socket_app directly as the main app