"""
Main Spark NLP Service for MarkerEngine
Provides REST API for NLP processing and marker detection
"""
import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyspark.sql import SparkSession
from .udfs import create_marker_udfs
from .spark_nlp_service import SparkNlpService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MarkerEngine Spark NLP Service",
    description="Distributed NLP processing with marker detection",
    version="1.0.0"
)

# Global Spark session
spark: SparkSession = None
marker_udfs = None
nlp_service = None


class AnalyzeRequest(BaseModel):
    """Request model for text analysis"""
    text: str
    options: Dict[str, Any] = {}


class AnalyzeResponse(BaseModel):
    """Response model for text analysis"""
    tokens: List[str]
    pos_tags: List[Dict[str, str]]
    entities: List[Dict[str, Any]]
    markers: List[str]
    score: float


@app.on_event("startup")
async def startup_event():
    """Initialize Spark session and UDFs on startup"""
    global spark, marker_udfs, nlp_service
    
    logger.info("Starting Spark NLP Service...")
    
    # Create Spark session
    spark = SparkSession.builder \
        .appName("MarkerEngine-SparkNLP") \
        .config("spark.jars.packages", "com.johnsnowlabs.nlp:spark-nlp_2.12:5.1.4") \
        .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "4g")) \
        .config("spark.executor.memory", os.getenv("SPARK_EXECUTOR_MEMORY", "2g")) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()
    
    # Initialize UDFs
    marker_udfs = create_marker_udfs(spark)
    
    # Initialize NLP service
    nlp_service = SparkNlpService(spark)
    nlp_service.initialize()
    
    logger.info("Spark NLP Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up Spark session on shutdown"""
    global spark
    
    if spark:
        spark.stop()
        logger.info("Spark session stopped")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if spark and spark.sparkContext._jsc.sc().isStopped():
        raise HTTPException(status_code=503, detail="Spark context is stopped")
    
    return {
        "status": "healthy",
        "spark_version": spark.version if spark else "N/A",
        "nlp_service": "initialized" if nlp_service else "not initialized"
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """
    Analyze text using Spark NLP pipeline
    
    Args:
        request: Text analysis request
        
    Returns:
        Analysis results with NLP annotations and markers
    """
    if not nlp_service:
        raise HTTPException(status_code=503, detail="NLP service not initialized")
    
    try:
        # Create DataFrame from text
        df = spark.createDataFrame([(request.text,)], ["text"])
        
        # Apply NLP pipeline
        nlp_result = nlp_service.process_dataframe(df)
        
        # Apply marker detection UDFs
        result_df = nlp_result \
            .withColumn("markers", marker_udfs.detect_markers_udf("text")) \
            .withColumn("score", marker_udfs.score_markers_udf("markers"))
        
        # Collect results
        row = result_df.collect()[0]
        
        # Extract NLP annotations
        tokens = row["tokens"] if "tokens" in row else []
        pos_tags = [{"token": t, "pos": p} for t, p in zip(
            row.get("tokens", []), 
            row.get("pos", [])
        )]
        
        entities = []
        if "entities" in row:
            for entity in row["entities"]:
                entities.append({
                    "text": entity.result,
                    "type": entity.metadata.get("entity", "UNKNOWN"),
                    "start": entity.begin,
                    "end": entity.end
                })
        
        return AnalyzeResponse(
            tokens=tokens,
            pos_tags=pos_tags,
            entities=entities,
            markers=row["markers"],
            score=row["score"]
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/batch-analyze")
async def batch_analyze(texts: List[str]):
    """
    Analyze multiple texts in batch
    
    Args:
        texts: List of texts to analyze
        
    Returns:
        List of analysis results
    """
    if not nlp_service:
        raise HTTPException(status_code=503, detail="NLP service not initialized")
    
    try:
        # Create DataFrame from texts
        df = spark.createDataFrame([(t,) for t in texts], ["text"])
        
        # Apply NLP pipeline
        nlp_result = nlp_service.process_dataframe(df)
        
        # Apply marker detection UDFs
        result_df = nlp_result \
            .withColumn("markers", marker_udfs.detect_markers_udf("text")) \
            .withColumn("score", marker_udfs.score_markers_udf("markers"))
        
        # Collect and format results
        results = []
        for row in result_df.collect():
            results.append({
                "text": row["text"],
                "markers": row["markers"],
                "score": row["score"],
                "token_count": len(row.get("tokens", []))
            })
        
        return {"results": results, "count": len(results)}
        
    except Exception as e:
        logger.error(f"Batch analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)