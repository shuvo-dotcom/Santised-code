"""
FastAPI application for the NFG Analytics Orchestrator.
"""
import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the metrics collector
from utils.metrics import Metrics

# Import the pipeline
from engine.pipeline import Pipeline

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the app
app = FastAPI(
    title="NFG Analytics API",
    description="API for the Networks–Fuels–Generation (NFG) energy analytics system",
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

# Initialize metrics
metrics = Metrics()

# Initialize the pipeline
try:
    csv_folder = os.getenv("DATA_FOLDER", "./data")
    pipeline = Pipeline(csv_folder=csv_folder)
    logger.info(f"Pipeline initialized with data folder: {csv_folder}")
except Exception as e:
    logger.error(f"Failed to initialize pipeline: {str(e)}")
    pipeline = None

# Define request models
class QueryRequest(BaseModel):
    text: str
    stream: bool = False

# Define response models
class QueryResponse(BaseModel):
    result: Dict[str, Any]
    
class HealthResponse(BaseModel):
    status: str
    version: str
    metrics: Optional[Dict[str, Any]] = None

@app.get("/health", response_model=HealthResponse)
async def health():
    """Check the health of the API and return metrics"""
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "metrics": metrics.get_metrics()
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Execute a query against the NFG Analytics pipeline"""
    if pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    try:
        # Record the query
        metrics.record_query()
        
        # Execute the query
        result = pipeline.answer_query(request.text)
        
        return {"result": result}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")
