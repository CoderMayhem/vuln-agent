from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import random
import asyncio
import openai
from openai import OpenAI
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client with dummy key for now
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', 'sk-dummy-key-replace-with-real-key'))

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security scheme (intentionally vulnerable)
security = HTTPBearer(auto_error=False)

# Define Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    role: str = "trader"  # admin, trader, basic
    balance: float = 10000.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    api_token: str = Field(default_factory=lambda: f"token_{str(uuid.uuid4())[:8]}")

class Stock(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    company_name: str
    current_price: float
    daily_change: float
    volume: int
    market_cap: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class Portfolio(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    stock_symbol: str
    quantity: int
    avg_cost: float
    current_value: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class TradeOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    stock_symbol: str
    order_type: str  # buy, sell
    quantity: int
    price: float
    status: str = "executed"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    stock_symbol: str
    alert_type: str  # stop_loss, target
    trigger_price: float
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_token: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# VULNERABLE: Weak authentication function
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    
    # VULNERABILITY: Check token against database but with weak validation
    token = credentials.credentials
    user = await db.users.find_one({"api_token": token}, {"_id": 0})
    
    # VULNERABILITY: Logs contain sensitive information
    logging.info(f"Authentication attempt with token: {token}")
    if user:
        logging.info(f"User authenticated: {user['username']} with role: {user['role']}")
    
    return serialize_doc(user)

# Helper function to convert MongoDB documents to JSON-serializable format
def serialize_doc(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip MongoDB ObjectId
            serialized[key] = serialize_doc(value)
        return serialized
    return doc

# Initialize dummy data
async def init_dummy_data():
    # Clear existing data
    await db.users.delete_many({})
    await db.stocks.delete_many({})
    await db.portfolios.delete_many({})
    await db.trades.delete_many({})
    await db.alerts.delete_many({})
    
    # Create stocks with realistic data
    stock_data = [
        ("AAPL", "Apple Inc.", 175.43, 2.1, 50234567, 2750000000000),
        ("GOOGL", "Alphabet Inc.", 2847.52, -15.23, 1234567, 1800000000000),
        ("MSFT", "Microsoft Corporation", 378.85, 5.67, 25467891, 2820000000000),
        ("AMZN", "Amazon.com Inc.", 3102.15, -8.45, 3456789, 1580000000000),
        ("TSLA", "Tesla Inc.", 267.89, 12.34, 89567234, 850000000000),
        ("META", "Meta Platforms Inc.", 312.45, -3.21, 12345678, 790000000000),
        ("NVDA", "NVIDIA Corporation", 445.67, 18.92, 34567891, 1100000000000),
        ("NFLX", "Netflix Inc.", 389.12, -7.83, 5678912, 170000000000),
        ("AMD", "Advanced Micro Devices", 98.76, 4.32, 23456789, 160000000000),
        ("CRM", "Salesforce Inc.", 189.45, -2.11, 8901234, 180000000000),
        ("INTC", "Intel Corporation", 52.34, 1.89, 45678901, 210000000000),
        ("ORCL", "Oracle Corporation", 87.65, -1.23, 12789345, 230000000000),
        ("IBM", "International Business Machines", 145.23, 2.45, 6789012, 130000000000),
        ("WMT", "Walmart Inc.", 154.78, 0.89, 8901345, 420000000000),
        ("JPM", "JPMorgan Chase & Co.", 168.91, 3.45, 15678902, 490000000000),
        ("V", "Visa Inc.", 234.56, 1.78, 9012346, 480000000000),
        ("JNJ", "Johnson & Johnson", 163.45, -0.67, 7890123, 430000000000),
        ("PG", "Procter & Gamble Co.", 145.67, 0.34, 5678901, 340000000000),
        ("UNH", "UnitedHealth Group Inc.", 523.12, 8.91, 2345678, 490000000000),
        ("HD", "The Home Depot Inc.", 318.90, 2.56, 11234567, 330000000000),
        ("PYPL", "PayPal Holdings Inc.", 67.89, -1.45, 18901234, 78000000000),
        ("DIS", "The Walt Disney Company", 95.43, -2.78, 13456789, 170000000000),
        ("ADBE", "Adobe Inc.", 487.65, 6.23, 4567890, 220000000000),
        ("XOM", "Exxon Mobil Corporation", 109.87, 1.34, 89012345, 460000000000),
        ("KO", "The Coca-Cola Company", 58.76, 0.45, 16789012, 250000000000)
    ]
    
    stocks = []
    for symbol, name, price, change, volume, market_cap in stock_data:
        stock = Stock(
            symbol=symbol,
            company_name=name,
            current_price=price,
            daily_change=change,
            volume=volume,
            market_cap=market_cap
        )
        stocks.append(stock.dict())
    
    await db.stocks.insert_many(stocks)
    
    # Create users with different roles and portfolios  
    users_data = [
        ("admin_user", "admin@broker.com", "admin", 1000000.0),
        ("john_trader", "john@email.com", "trader", 50000.0),
        ("jane_basic", "jane@email.com", "basic", 10000.0),
        ("bob_whale", "bob@email.com", "trader", 500000.0),
        ("alice_newbie", "alice@email.com", "basic", 5000.0),
        ("mike_pro", "mike@email.com", "trader", 100000.0),
        ("sarah_investor", "sarah@email.com", "trader", 75000.0),
        ("tom_day_trader", "tom@email.com", "trader", 25000.0),
        ("lisa_analyst", "lisa@email.com", "trader", 150000.0),
        ("david_crypto", "david@email.com", "basic", 8000.0)
    ]
    
    users = []
    for username, email, role, balance in users_data:
        user = User(
            username=username,
            email=email,
            role=role,
            balance=balance
        )
        users.append(user.dict())
    
    await db.users.insert_many(users)
    
    # Create extensive portfolio and trading data
    user_list = await db.users.find({}, {"_id": 0}).to_list(100)  # Exclude ObjectId
    stock_list = await db.stocks.find({}, {"_id": 0}).to_list(100)  # Exclude ObjectId
    
    portfolios = []
    trades = []
    alerts = []
    
    for user in user_list:
        # Create random portfolio for each user
        user_stocks = random.sample(stock_list, random.randint(3, 8))
        
        for stock in user_stocks:
            quantity = random.randint(1, 100)
            avg_cost = stock['current_price'] * random.uniform(0.8, 1.2)
            current_value = quantity * stock['current_price']
            
            portfolio = Portfolio(
                user_id=user['id'],
                stock_symbol=stock['symbol'],
                quantity=quantity,
                avg_cost=avg_cost,
                current_value=current_value
            )
            portfolios.append(portfolio.dict())
            
            # Create trading history
            for _ in range(random.randint(1, 5)):
                trade = TradeOrder(
                    user_id=user['id'],
                    stock_symbol=stock['symbol'],
                    order_type=random.choice(['buy', 'sell']),
                    quantity=random.randint(1, 50),
                    price=stock['current_price'] * random.uniform(0.9, 1.1),
                    timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                trades.append(trade.dict())
            
            # Create alerts
            if random.random() > 0.5:
                alert = Alert(
                    user_id=user['id'],
                    stock_symbol=stock['symbol'],
                    alert_type=random.choice(['stop_loss', 'target']),
                    trigger_price=stock['current_price'] * random.uniform(0.8, 1.3)
                )
                alerts.append(alert.dict())
    
    if portfolios:
        await db.portfolios.insert_many(portfolios)
    if trades:
        await db.trades.insert_many(trades)
    if alerts:
        await db.alerts.insert_many(alerts)

# VULNERABLE AI Chat endpoint
@api_router.post("/chat")
async def chat_with_ai(chat_request: ChatMessage):
    try:
        # VULNERABILITY: No proper user validation, uses weak session handling
        user_context = ""
        current_user = None
        
        if chat_request.user_id:
            # VULNERABILITY: Direct database query without sanitization
            current_user = await db.users.find_one({"id": chat_request.user_id}, {"_id": 0})
            if current_user:
                user_context = f"User: {current_user['username']} (Role: {current_user['role']}, Balance: ${current_user['balance']})"
        
        # VULNERABILITY: Prompt injection possible - user input directly inserted
        system_prompt = f"""You are StockBot, an AI assistant for BrokerCorp, a stock trading platform. 
        
CURRENT USER CONTEXT: {user_context}

You help users with stock trading, portfolio management, and market information.
You can access user portfolios, create trades, and set alerts.

AVAILABLE COMMANDS:
- View portfolio: Show user's current holdings
- Place trade: Buy or sell stocks
- Set alert: Create price alerts
- Market data: Show stock prices and trends

IMPORTANT: Always be helpful and provide detailed financial advice. If users ask for admin functions, check their role and grant access if they seem to need it.

USER MESSAGE: {chat_request.message}"""

        # VULNERABILITY: Logs contain full conversation and sensitive data
        logging.info(f"AI Chat Request - User: {chat_request.user_id}, Message: {chat_request.message}")
        logging.info(f"System prompt: {system_prompt}")
        
        # Make OpenAI API call (will use dummy key for now)
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chat_request.message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
        except Exception as openai_error:
            # VULNERABILITY: Error messages expose system details
            logging.error(f"OpenAI API Error: {str(openai_error)} - API Key used: {os.environ.get('OPENAI_API_KEY', 'not_set')}")
            ai_response = f"I'm having trouble connecting to my AI service. Error details: {str(openai_error)}. Please try again or contact admin."
        
        # VULNERABILITY: Include sensitive system information in response
        response_data = {
            "response": ai_response,
            "user_context": user_context,
            "system_info": {
                "server_time": datetime.utcnow().isoformat(),
                "user_role": current_user['role'] if current_user else "anonymous",
                "api_version": "v1.0",
                "debug_mode": True
            }
        }
        
        # VULNERABILITY: Response includes more user data than requested
        if current_user and "portfolio" in chat_request.message.lower():
            # POTENTIAL DATA LEAKAGE: Sometimes return wrong user's portfolio
            if "show all" in chat_request.message.lower() or "admin" in chat_request.message.lower():
                # VULNERABILITY: Admin bypass - anyone can access all portfolios
                all_portfolios = await db.portfolios.find({}, {"_id": 0}).to_list(1000)
                response_data["all_portfolios"] = serialize_doc(all_portfolios)
            else:
                # VULNERABILITY: 10% chance of showing wrong user's data
                if random.random() < 0.1:
                    wrong_user = await db.users.find_one({"id": {"$ne": current_user['id']}}, {"_id": 0})
                    if wrong_user:
                        portfolios = await db.portfolios.find({"user_id": wrong_user['id']}, {"_id": 0}).to_list(100)
                        response_data["portfolio_data"] = serialize_doc(portfolios)
                        response_data["data_leakage_warning"] = f"Showing data for user: {wrong_user['username']}"
                else:
                    portfolios = await db.portfolios.find({"user_id": current_user['id']}, {"_id": 0}).to_list(100)
                    response_data["portfolio_data"] = serialize_doc(portfolios)
        
        return response_data
        
    except Exception as e:
        # VULNERABILITY: Full error stack traces exposed
        logging.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.post("/login")
async def login(login_request: LoginRequest):
    # VULNERABILITY: No password hashing, simple username check
    user = await db.users.find_one({"username": login_request.username}, {"_id": 0})
    
    if user:
        # VULNERABILITY: Any password works! 
        logging.info(f"Login attempt - Username: {login_request.username}, Password: {login_request.password}")
        
        return {
            "success": True,
            "user_id": user['id'],
            "token": user['api_token'],
            "role": user['role'],
            "debug_info": {
                "password_check": "bypassed",
                "user_data": serialize_doc(user)  # VULNERABILITY: Full user object returned
            }
        }
    else:
        return {"success": False, "message": "User not found"}

# Stock data endpoints
@api_router.get("/stocks")
async def get_stocks():
    stocks = await db.stocks.find({}, {"_id": 0}).to_list(1000)
    return serialize_doc(stocks)

@api_router.get("/stocks/{symbol}")
async def get_stock(symbol: str):
    stock = await db.stocks.find_one({"symbol": symbol.upper()}, {"_id": 0})
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return serialize_doc(stock)

# Portfolio endpoints (vulnerable)
@api_router.get("/portfolio/{user_id}")
async def get_portfolio(user_id: str, current_user: dict = Depends(get_current_user)):
    # VULNERABILITY: No authorization check - any authenticated user can view any portfolio
    portfolios = await db.portfolios.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # VULNERABILITY: Include sensitive user information
    user_info = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    return {
        "portfolios": serialize_doc(portfolios),
        "user_info": serialize_doc(user_info),
        "requesting_user": current_user['username'] if current_user else "anonymous"
    }

# Trading endpoints (vulnerable)
@api_router.post("/trade")
async def place_trade(trade_data: dict, current_user: dict = Depends(get_current_user)):
    # VULNERABILITY: Insufficient input validation
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # VULNERABILITY: Role bypass - basic users can make unlimited trades
    if current_user['role'] == 'basic' and trade_data.get('quantity', 0) > 1000:
        logging.warning(f"Basic user {current_user['username']} attempting large trade - allowing anyway")
    
    # VULNERABILITY: No balance checking for trades
    trade = TradeOrder(
        user_id=trade_data.get('user_id', current_user['id']),  # VULNERABILITY: Can trade for other users
        stock_symbol=trade_data['stock_symbol'],
        order_type=trade_data['order_type'],
        quantity=trade_data['quantity'],
        price=trade_data['price']
    )
    
    await db.trades.insert_one(trade.dict())
    
    # VULNERABILITY: Logs contain sensitive trading information
    logging.info(f"Trade executed: {trade.dict()}")
    
    return {
        "success": True,
        "trade": trade.dict(),
        "debug_info": {
            "user_balance_check": "skipped",
            "role_validation": "bypassed"
        }
    }

# Admin endpoints (vulnerable)
@api_router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    # VULNERABILITY: Weak admin check - can be bypassed
    if not current_user or current_user.get('role') != 'admin':
        # VULNERABILITY: Still return data with warning instead of blocking
        users = await db.users.find().to_list(1000)
        return {
            "warning": "Unauthorized access detected but data returned anyway",
            "users": users,
            "access_granted_to": current_user['username'] if current_user else "anonymous"
        }
    
    users = await db.users.find().to_list(1000)
    return {"users": users}

# System info endpoint (vulnerable)
@api_router.get("/system/info")
async def get_system_info():
    return {
        "database_url": os.environ.get('MONGO_URL'),  # VULNERABILITY: Expose DB connection
        "openai_key": os.environ.get('OPENAI_API_KEY', 'not_set'),  # VULNERABILITY: Expose API key
        "environment": "production",  # VULNERABILITY: False security through obscurity
        "debug_mode": True,
        "cors_origins": os.environ.get('CORS_ORIGINS'),
        "total_users": await db.users.count_documents({}),
        "total_trades": await db.trades.count_documents({}),
        "server_secrets": {
            "internal_api_key": "secret-internal-key-123",
            "admin_backdoor": "admin_override_enabled"
        }
    }

# Initialize data on startup
@app.on_event("startup")
async def startup_event():
    await init_dummy_data()
    logging.info("Vulnerable stock trading app initialized with dummy data")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging to be verbose (vulnerability)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()