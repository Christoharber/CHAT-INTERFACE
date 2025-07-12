from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import httpx
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class ChatMessage(BaseModel):
    message: str
    model: Optional[str] = "llama3.2:latest"
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str
    model: str
    done: bool

class ChatHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    response: str
    model: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Ollama integration endpoints
@api_router.get("/ollama/models")
async def get_ollama_models():
    """Get available Ollama models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch models from Ollama")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Ollama is not running. Please start Ollama on localhost:11434")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Ollama: {str(e)}")

@api_router.post("/ollama/chat")
async def chat_with_ollama(chat_request: ChatMessage):
    """Chat with Ollama model"""
    try:
        # Save message to database
        chat_history = ChatHistory(
            message=chat_request.message,
            response="",  # Will be filled after response
            model=chat_request.model or "llama3.2:latest"
        )
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": chat_request.model or "llama3.2:latest",
                "prompt": chat_request.message,
                "stream": False
            }
            
            response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                chat_response = ChatResponse(
                    response=result.get("response", ""),
                    model=result.get("model", chat_request.model or "llama3.2:latest"),
                    done=result.get("done", True)
                )
                
                # Update chat history with response
                chat_history.response = chat_response.response
                await db.chat_history.insert_one(chat_history.dict())
                
                return chat_response
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get response from Ollama")
                
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Ollama is not running. Please start Ollama on localhost:11434")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

async def generate_streaming_response(model: str, prompt: str):
    """Generate streaming response from Ollama"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True
            }
            
            async with client.stream('POST', f"{OLLAMA_URL}/api/generate", json=payload) as response:
                if response.status_code == 200:
                    full_response = ""
                    async for chunk in response.aiter_lines():
                        if chunk:
                            try:
                                data = json.loads(chunk)
                                if "response" in data:
                                    full_response += data["response"]
                                    yield f"data: {json.dumps({'response': data['response'], 'done': data.get('done', False)})}\n\n"
                                if data.get("done", False):
                                    # Save to database when done
                                    chat_history = ChatHistory(
                                        message=prompt,
                                        response=full_response,
                                        model=model
                                    )
                                    await db.chat_history.insert_one(chat_history.dict())
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    yield f"data: {json.dumps({'error': 'Failed to get response from Ollama'})}\n\n"
    except httpx.ConnectError:
        yield f"data: {json.dumps({'error': 'Ollama is not running. Please start Ollama on localhost:11434'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': f'Error communicating with Ollama: {str(e)}'})}\n\n"

@api_router.post("/ollama/chat/stream")
async def stream_chat_with_ollama(chat_request: ChatMessage):
    """Stream chat with Ollama model"""
    return StreamingResponse(
        generate_streaming_response(
            chat_request.model or "llama3.2:latest",
            chat_request.message
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@api_router.get("/ollama/health")
async def check_ollama_health():
    """Check if Ollama is running and accessible"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                models = response.json()
                return {
                    "status": "healthy",
                    "models_available": len(models.get("models", [])),
                    "models": models.get("models", [])
                }
            else:
                return {"status": "unhealthy", "error": "Ollama responded with error"}
    except httpx.ConnectError:
        return {"status": "offline", "error": "Ollama is not running on localhost:11434"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@api_router.get("/chat/history")
async def get_chat_history():
    """Get chat history from database"""
    try:
        history = await db.chat_history.find().sort("timestamp", -1).limit(50).to_list(50)
        return [ChatHistory(**chat) for chat in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()