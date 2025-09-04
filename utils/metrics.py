"""
Metrics collection for the NFG Analytics Orchestrator.
Used to track API calls, performance, and other metrics.
"""
import time
import logging
from typing import Dict, Any, List, Optional
import threading
import json

logger = logging.getLogger(__name__)

class Metrics:
    """Simple metrics collection for the NFG Analytics Orchestrator"""
    
    # Class-level storage for metrics
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one metrics instance"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Metrics, cls).__new__(cls)
                cls._instance._metrics = {
                    "llm_calls": 0,
                    "llm_tokens_in": 0,
                    "llm_tokens_out": 0,
                    "llm_latency": [],
                    "llm_errors": 0,
                    "calls_by_model": {},
                    "query_count": 0,
                    "cache_hits": 0,
                    "cache_misses": 0
                }
                cls._instance._start_time = time.time()
            return cls._instance
    
    def record_llm_call(self, model: str, tokens_in: int = 0, 
                      tokens_out: int = 0, latency_ms: float = 0, 
                      error: bool = False) -> None:
        """Record metrics for an LLM API call"""
        with self._lock:
            self._metrics["llm_calls"] += 1
            self._metrics["llm_tokens_in"] += tokens_in
            self._metrics["llm_tokens_out"] += tokens_out
            self._metrics["llm_latency"].append(latency_ms)
            
            if error:
                self._metrics["llm_errors"] += 1
            
            # Track by model
            if model not in self._metrics["calls_by_model"]:
                self._metrics["calls_by_model"][model] = 0
            self._metrics["calls_by_model"][model] += 1
    

    def track_api_call(self, model: str, prompt: str, result: str, duration: float) -> None:
        """Track metrics for an API call - compatible with LLMProvider usage"""
        # Estimate token counts based on string lengths (very rough)
        tokens_in = len(prompt) // 4  # Rough estimate
        tokens_out = len(result) // 4  # Rough estimate
        latency_ms = duration * 1000  # Convert to milliseconds
        
        # Record using the standard method
        self.record_llm_call(model, tokens_in, tokens_out, latency_ms)
        
        # Track calls by model
        if model not in self._metrics["calls_by_model"]:
            self._metrics["calls_by_model"][model] = 0
        self._metrics["calls_by_model"][model] += 1
    def record_query(self, cache_hit: bool = False) -> None:
        """Record a user query"""
        with self._lock:
            self._metrics["query_count"] += 1
            if cache_hit:
                self._metrics["cache_hits"] += 1
            else:
                self._metrics["cache_misses"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get a copy of the current metrics"""
        with self._lock:
            metrics = self._metrics.copy()
            
            # Calculate derived metrics
            uptime_seconds = time.time() - self._start_time
            metrics["uptime_seconds"] = uptime_seconds
            
            # Calculate averages
            if metrics["llm_latency"]:
                metrics["avg_latency_ms"] = sum(metrics["llm_latency"]) / len(metrics["llm_latency"])
            else:
                metrics["avg_latency_ms"] = 0
                
            if metrics["llm_calls"] > 0:
                metrics["error_rate"] = metrics["llm_errors"] / metrics["llm_calls"]
            else:
                metrics["error_rate"] = 0
                
            # Calculate cache hit rate
            if (metrics["cache_hits"] + metrics["cache_misses"]) > 0:
                metrics["cache_hit_rate"] = metrics["cache_hits"] / (metrics["cache_hits"] + metrics["cache_misses"])
            else:
                metrics["cache_hit_rate"] = 0
                
            return metrics
    
    def log_metrics(self) -> None:
        """Log the current metrics"""
        metrics = self.get_metrics()
        logger.info(f"Current metrics: {json.dumps(metrics)}")
    
    def reset(self) -> None:
        """Reset metrics (mainly for testing)"""
        with self._lock:
            self._metrics = {
                "llm_calls": 0,
                "llm_tokens_in": 0,
                "llm_tokens_out": 0,
                "llm_latency": [],
                "llm_errors": 0,
                "calls_by_model": {},
                "query_count": 0,
                "cache_hits": 0,
                "cache_misses": 0
            }
            self._start_time = time.time()
