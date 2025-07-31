"""
Unit tests for Spark UDFs
"""
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import ArrayType, StringType, DoubleType
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from udfs import MarkerUDFs


@pytest.fixture(scope="session")
def spark():
    """Create Spark session for tests"""
    spark = SparkSession.builder \
        .appName("MarkerUDF-Tests") \
        .master("local[2]") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()
    
    yield spark
    spark.stop()


@pytest.fixture
def marker_udfs(spark):
    """Create MarkerUDFs instance with test data"""
    # Mock broadcast data
    detect_registry = {
        "A_TEST": {
            "type": "keyword",
            "keywords": ["test", "prüfung"]
        },
        "S_POSITIVE": {
            "type": "pattern",
            "pattern": r"\b(gut|toll|super)\b"
        }
    }
    
    markers = {
        "A_TEST": {
            "type": "A",
            "confidence": 0.9
        },
        "S_POSITIVE": {
            "type": "S",
            "confidence": 0.85
        }
    }
    
    scoring_profile = {
        "weights": {
            "A": 1.0,
            "S": 1.2,
            "C": 1.5,
            "MM": 2.0
        }
    }
    
    # Create UDFs instance
    udfs = MarkerUDFs(spark)
    
    # Override broadcast variables
    udfs.broadcast_detect = spark.sparkContext.broadcast(detect_registry)
    udfs.broadcast_markers = spark.sparkContext.broadcast(markers)
    udfs.broadcast_scoring = spark.sparkContext.broadcast(scoring_profile)
    
    # Register UDFs
    udfs._register_udfs()
    
    return udfs


def test_detect_markers_empty_text(marker_udfs):
    """Test marker detection with empty text"""
    result = marker_udfs.detect_markers("")
    assert result == []
    
    result = marker_udfs.detect_markers(None)
    assert result == []


def test_detect_markers_keyword(marker_udfs):
    """Test keyword-based marker detection"""
    text = "Dies ist ein Test der Marker-Erkennung"
    result = marker_udfs.detect_markers(text)
    assert "A_TEST" in result
    
    text = "Die Prüfung war erfolgreich"
    result = marker_udfs.detect_markers(text)
    assert "A_TEST" in result


def test_detect_markers_pattern(marker_udfs):
    """Test pattern-based marker detection"""
    text = "Das ist wirklich gut gemacht!"
    result = marker_udfs.detect_markers(text)
    assert "S_POSITIVE" in result
    
    text = "Super Arbeit, toll!"
    result = marker_udfs.detect_markers(text)
    assert "S_POSITIVE" in result


def test_score_markers_empty(marker_udfs):
    """Test scoring with empty marker list"""
    result = marker_udfs.score_markers([])
    assert result == 0.0


def test_score_markers_single(marker_udfs):
    """Test scoring with single marker"""
    result = marker_udfs.score_markers(["A_TEST"])
    assert result == pytest.approx(0.9, rel=1e-2)  # confidence * weight


def test_score_markers_multiple(marker_udfs):
    """Test scoring with multiple markers"""
    result = marker_udfs.score_markers(["A_TEST", "S_POSITIVE"])
    
    # Calculate expected score
    # A_TEST: 0.9 * 1.0 = 0.9
    # S_POSITIVE: 0.85 * 1.2 = 1.02
    # Total: (0.9 + 1.02) / (1.0 + 1.2) = 0.872
    expected = 0.872
    
    assert result == pytest.approx(expected, rel=1e-2)


def test_udf_integration(spark, marker_udfs):
    """Test UDFs with Spark DataFrame"""
    # Create test DataFrame
    data = [
        ("Dies ist ein Test",),
        ("Das Ergebnis ist super gut",),
        ("Keine Marker hier",),
    ]
    df = spark.createDataFrame(data, ["text"])
    
    # Apply UDFs
    result_df = df \
        .withColumn("markers", marker_udfs.detect_markers_udf("text")) \
        .withColumn("score", marker_udfs.score_markers_udf("markers"))
    
    # Collect results
    results = result_df.collect()
    
    # Verify first row
    assert "A_TEST" in results[0]["markers"]
    assert results[0]["score"] > 0
    
    # Verify second row
    assert "S_POSITIVE" in results[1]["markers"]
    assert results[1]["score"] > 0
    
    # Verify third row
    assert len(results[2]["markers"]) == 0
    assert results[2]["score"] == 0.0