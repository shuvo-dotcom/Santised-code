"""
FastAPI app exposing endpoints for NFG analytics with chat interface support.
Dynamic implementation using LLM-driven pipeline.
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Import from original codebase
import sys
sys.path.append('/app')
from engine.pipeline import Pipeline
from semantic.llm_provider import LLMProvider
from semantic.variable_catalog import VariableCatalog
from nfg_math.equations import EquationRegistry
from semantic.intent_parser import IntentParser
from data_io.csv_store import CSVStore

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NFG Analytics API",
    description="API for NFG (Networks–Fuels–Generation) energy analytics with chat interface",
    version="1.0.0"
)

# Add CORS support for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class QueryRequest(BaseModel):
    query: str

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    
class ChatHistoryRequest(BaseModel):
    messages: List[ChatMessage]
    new_message: str

# In-memory chat history store (replace with database in production)
chat_sessions = {}

# Initialize components on startup
@app.on_event("startup")
async def startup_event():
    # Get model from environment or use default
    model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    logger.info(f"Initializing NFG Analytics with model: {model_name}")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set. LLM functionality will be limited.")
    
    # Initialize components
    llm_provider = LLMProvider(model=model_name)
    
    var_cat = VariableCatalog()
    var_cat.llm_provider = llm_provider
    
    eq_reg = EquationRegistry({})  # Initialize with empty dict as required
    eq_reg.llm_provider = llm_provider
    
    int_par = IntentParser()
    int_par.llm_provider = llm_provider
    
    # Use the DATA_FOLDER environment variable for the CSVStore
    data_folder = os.getenv("DATA_FOLDER", "/app/data")
    csv_store = CSVStore(folder=data_folder)
    
    # Initialize pipeline
    app.state.pipeline = Pipeline(
        csv_folder=data_folder,
        api_key=os.getenv("OPENAI_API_KEY"),
        model=model_name
    )
    
    logger.info("NFG Analytics API initialized successfully")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Single query endpoint (original functionality)
@app.post("/query")
async def process_query(request: QueryRequest):
    if not hasattr(app.state, "pipeline"):
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    start_time = time.time()
    logger.info(f"Processing query: {request.query}")
    
    try:
        result = app.state.pipeline.answer_query(request.query)
        elapsed_time = time.time() - start_time
        logger.info(f"Query processed in {elapsed_time:.2f} seconds")
        
        # Add processing time to response
        result["processing_time"] = f"{elapsed_time:.2f}s"
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# Create a new chat session
@app.post("/chat/session")
async def create_chat_session():
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = []
    
    return {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "message": "Chat session created"
    }

# Get chat history for a session
@app.get("/chat/{session_id}")
async def get_chat_history(session_id: str):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return {
        "session_id": session_id,
        "messages": chat_sessions[session_id]
    }

# Send a message in a chat session
@app.post("/chat/{session_id}")
async def chat_message(session_id: str, request: QueryRequest):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    if not hasattr(app.state, "pipeline"):
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Process user message
    user_message = {
        "role": "user",
        "content": request.query,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add user message to history
    chat_sessions[session_id].append(user_message)
    
    try:
        # Process query
        start_time = time.time()
        logger.info(f"Processing chat query: {request.query}")
        
        result = app.state.pipeline.answer_query(request.query)
        elapsed_time = time.time() - start_time
        
        # Convert result to conversational format
        if result.get("result") is not None:
            metric = result.get("metric", "")
            value = result.get("result", "")
            unit = result.get("unit", "")
            method = result.get("method", "")
            
            response_content = f"The {metric} is {value} {unit}.\n\n"
            
            if method:
                response_content += f"I calculated this using the formula: {method}.\n\n"
                
            if result.get("inputs"):
                response_content += "The values used in the calculation were:\n"
                for var_name, var_value in result.get("inputs", {}).items():
                    response_content += f"- {var_name}: {var_value}\n"
            
            if result.get("notes"):
                response_content += f"\n{result.get('notes')}"
        else:
            # Error or no result
            response_content = "I couldn't calculate a result for your query. Please try rephrasing or provide more information."
        
        # Create assistant response
        assistant_message = {
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now().isoformat(),
            "raw_result": result  # Include raw result for frontend
        }
        
        # Add assistant message to history
        chat_sessions[session_id].append(assistant_message)
        
        return {
            "message": assistant_message,
            "session_id": session_id,
            "processing_time": f"{elapsed_time:.2f}s"
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        
        # Add error message to history
        error_message = {
            "role": "assistant",
            "content": f"Sorry, I encountered an error while processing your request: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "error": True
        }
        chat_sessions[session_id].append(error_message)
        
        return {
            "message": error_message,
            "session_id": session_id,
            "error": True
        }

# Delete a chat session
@app.delete("/chat/{session_id}")
async def delete_chat_session(session_id: str):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    del chat_sessions[session_id]
    return {"message": "Chat session deleted"}
