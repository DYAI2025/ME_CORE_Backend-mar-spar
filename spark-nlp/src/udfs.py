"""
Spark UDFs for Marker Detection and Scoring
Integrates with backend marker logic via broadcast variables
"""
from typing import List, Dict, Any, Optional
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, StringType, DoubleType, StructType, StructField
import json
import logging

logger = logging.getLogger(__name__)


class MarkerUDFs:
    """Container for Marker-related Spark UDFs"""
    
    def __init__(self, spark: SparkSession):
        """Initialize UDFs with Spark session and broadcast variables"""
        self.spark = spark
        self._load_broadcast_data()
        self._register_udfs()
    
    def _load_broadcast_data(self):
        """Load and broadcast marker data and detect registry"""
        try:
            # Load DETECT registry
            with open('/app/backend/detect/DETECT_registry.json', 'r') as f:
                detect_registry = json.load(f)
            self.broadcast_detect = self.spark.sparkContext.broadcast(detect_registry)
            
            # Load marker definitions
            with open('/app/backend/markers/markers.json', 'r') as f:
                markers = json.load(f)
            self.broadcast_markers = self.spark.sparkContext.broadcast(markers)
            
            # Load scoring profiles
            with open('/app/backend/scoring/default_profile.json', 'r') as f:
                scoring_profile = json.load(f)
            self.broadcast_scoring = self.spark.sparkContext.broadcast(scoring_profile)
            
            logger.info("Successfully loaded and broadcast marker data")
            
        except Exception as e:
            logger.error(f"Failed to load broadcast data: {e}")
            raise
    
    def detect_markers(self, text: str) -> List[str]:
        """
        UDF to detect markers in text using broadcast registry
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected marker IDs
        """
        if not text:
            return []
        
        detected_markers = []
        detect_registry = self.broadcast_detect.value
        
        try:
            # Normalize text for detection
            text_lower = text.lower()
            
            # Check each detector in registry
            for marker_id, detector_config in detect_registry.items():
                if self._check_detector(text_lower, detector_config):
                    detected_markers.append(marker_id)
            
            logger.debug(f"Detected {len(detected_markers)} markers in text")
            
        except Exception as e:
            logger.error(f"Error in marker detection: {e}")
        
        return detected_markers
    
    def score_markers(self, marker_ids: List[str]) -> float:
        """
        UDF to calculate aggregate score for detected markers
        
        Args:
            marker_ids: List of marker IDs
            
        Returns:
            Aggregate score (0.0 - 1.0)
        """
        if not marker_ids:
            return 0.0
        
        scoring_profile = self.broadcast_scoring.value
        markers = self.broadcast_markers.value
        
        try:
            total_score = 0.0
            total_weight = 0.0
            
            for marker_id in marker_ids:
                # Get marker metadata
                marker = markers.get(marker_id, {})
                marker_type = marker.get('type', 'A')  # Default to Atomic
                
                # Get scoring weight for marker type
                weight = scoring_profile.get('weights', {}).get(marker_type, 1.0)
                
                # Get marker confidence (from detection or default)
                confidence = marker.get('confidence', 0.8)
                
                total_score += confidence * weight
                total_weight += weight
            
            # Calculate normalized score
            if total_weight > 0:
                final_score = min(total_score / total_weight, 1.0)
            else:
                final_score = 0.0
            
            logger.debug(f"Calculated score {final_score} for {len(marker_ids)} markers")
            return final_score
            
        except Exception as e:
            logger.error(f"Error in marker scoring: {e}")
            return 0.0
    
    def _check_detector(self, text: str, detector_config: Dict[str, Any]) -> bool:
        """Check if detector matches text"""
        detector_type = detector_config.get('type', 'keyword')
        
        if detector_type == 'keyword':
            keywords = detector_config.get('keywords', [])
            return any(keyword.lower() in text for keyword in keywords)
        
        elif detector_type == 'pattern':
            import re
            pattern = detector_config.get('pattern', '')
            try:
                return bool(re.search(pattern, text, re.IGNORECASE))
            except:
                return False
        
        elif detector_type == 'composite':
            # Simplified composite check
            required = detector_config.get('required', [])
            return all(marker.lower() in text for marker in required)
        
        return False
    
    def _register_udfs(self):
        """Register UDFs with Spark SQL"""
        # Register detect_markers UDF
        self.detect_markers_udf = udf(
            self.detect_markers,
            ArrayType(StringType())
        )
        self.spark.udf.register("detect_markers", self.detect_markers_udf)
        
        # Register score_markers UDF
        self.score_markers_udf = udf(
            self.score_markers,
            DoubleType()
        )
        self.spark.udf.register("score_markers", self.score_markers_udf)
        
        logger.info("Successfully registered Spark UDFs")
    
    def get_marker_details(self, marker_ids: List[str]) -> List[Dict[str, Any]]:
        """
        UDF to get detailed marker information
        
        Args:
            marker_ids: List of marker IDs
            
        Returns:
            List of marker details
        """
        markers = self.broadcast_markers.value
        details = []
        
        for marker_id in marker_ids:
            if marker_id in markers:
                marker_detail = {
                    'id': marker_id,
                    'type': markers[marker_id].get('type'),
                    'category': markers[marker_id].get('category'),
                    'confidence': markers[marker_id].get('confidence', 0.8)
                }
                details.append(marker_detail)
        
        return details


def create_marker_udfs(spark: SparkSession) -> MarkerUDFs:
    """Factory function to create MarkerUDFs instance"""
    return MarkerUDFs(spark)


# Example usage in Spark job
def process_dataframe_with_markers(spark: SparkSession, df):
    """
    Process a DataFrame with marker detection and scoring
    
    Args:
        spark: SparkSession instance
        df: Input DataFrame with 'text' column
        
    Returns:
        DataFrame with added 'markers' and 'score' columns
    """
    # Create and register UDFs
    marker_udfs = create_marker_udfs(spark)
    
    # Apply UDFs to DataFrame
    result_df = df \
        .withColumn("markers", marker_udfs.detect_markers_udf("text")) \
        .withColumn("score", marker_udfs.score_markers_udf("markers"))
    
    return result_df