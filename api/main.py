"""
FastAPI app exposing POST /query endpoint for NFG analytics.
Dynamic implementation using LLM-driven pipeline.
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import time
import json
from typing import Dict, Any, Optional
import asyncio

from engine.pipeline import Pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NFG Analytics API",
    description="API for NFG (Networks–Fuels–Generation) energy analytics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DATA_FOLDER = os.getenv("DATA_FOLDER", "./data")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID", None)

# Initialize pipeline with OpenAI configuration
pipeline = Pipeline(csv_folder=DATA_FOLDER, api_key=OPENAI_API_KEY, model=OPENAI_MODEL)

# Request model
class QueryRequest:
    def __init__(self, text: str, stream: bool = False):
        self.text = text
        self.stream = stream

# Dependency to validate and extract request
async def get_query_request(request: Request) -> QueryRequest:
    try:
        data = await request.json()
        text = data.get("text", "")
        stream = data.get("stream", False)
        
        if not text:
            raise HTTPException(status_code=400, detail="Query text is required")
            
        return QueryRequest(text=text, stream=stream)
    except Exception as e:
        logger.error(f"Error parsing request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

@app.post("/query")
async def query_endpoint(query_request: QueryRequest = Depends(get_query_request)):
    """
    Process an NFG analytics query.
    
    Args:
        query_request: Request with query text and stream flag
        
    Returns:
        JSON response or streaming response
    """
    try:
        text = query_request.text
        stream = query_request.stream
        
        if stream:
            return StreamingResponse(
                stream_response(text),
                media_type="text/event-stream"
            )
        else:
            # Synchronous response
            result = pipeline.answer_query(text)
            return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

async def stream_response(text: str):
    """
    Stream response steps.
    
    Args:
        text: Query text
        
    Yields:
        SSE events with steps and final result
    """
    # Step 1: Parsing intent
    yield f"data: {json.dumps({'step': 'parsing_intent', 'message': 'Analyzing query...'})}\n\n"
    await asyncio.sleep(0.5)
    
    # Step 2: Getting equation
    yield f"data: {json.dumps({'step': 'getting_equation', 'message': 'Determining equation...'})}\n\n"
    await asyncio.sleep(0.5)
    
    # Step 3: Fetching data
    yield f"data: {json.dumps({'step': 'fetching_data', 'message': 'Fetching data...'})}\n\n"
    await asyncio.sleep(0.5)
    
    # Step 4: Calculate result
    yield f"data: {json.dumps({'step': 'calculating', 'message': 'Calculating result...'})}\n\n"
    await asyncio.sleep(0.5)
    
    # Get actual result
    result = pipeline.answer_query(text)
    
    # Step 5: Final result
    yield f"data: {json.dumps({'step': 'result', 'message': 'Complete', 'result': result})}\n\n"

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}
