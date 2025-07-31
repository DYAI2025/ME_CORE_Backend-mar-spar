"""
MarkerService for semantic marker detection.
Supports two-phase detection: initial scan and contextual rescan.
"""
from ..database import db
from ..models.marker import Marker
from ..models.analysis_context import AnalysisContext
from .activation_rules_engine import ActivationRulesEngine
from typing import List, Dict, Any, Optional, Set
from bson import ObjectId
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)
marker_collection = db["markers"]


class MarkerService:
    """Service for semantic marker analysis with two-phase processing"""
    
    def __init__(self):
        self.marker_cache: Dict[str, Marker] = {}
        self.rules_engine = ActivationRulesEngine()
        
    async def initial_scan(
        self, 
        text: str, 
        schema_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: Fast scan for atomic (A_) and signal (S_) markers.
        
        Args:
            text: The text to analyze
            schema_id: Optional schema filter
            
        Returns:
            List of detected markers
        """
        detected_markers = []
        
        # Build query for A_ and S_ markers
        query = {"_id": {"$regex": "^(A_|S_)"}}
        if schema_id:
            query["schema_id"] = schema_id
        
        # Load markers from database
        a_s_markers = await marker_collection.find(query).to_list(None)
        
        for marker_data in a_s_markers:
            try:
                marker = Marker(**marker_data)
                self.marker_cache[marker.id] = marker
                
                # Check if marker is detected in text
                if self._detect_marker(marker, text):
                    detected_markers.append({
                        "marker_id": marker.id,
                        "marker_type": marker.id.split("_")[0],
                        "frame": marker.frame.model_dump(),
                        "detected_at": datetime.now().isoformat(),
                        "confidence": self._calculate_confidence(marker, text),
                        "detection_phase": "initial",
                        "examples_matched": self._get_matched_examples(marker, text)
                    })
                    
            except Exception as e:
                logger.error(f"Error processing marker {marker_data.get('_id')}: {str(e)}")
                continue
        
        logger.info(f"Initial scan found {len(detected_markers)} markers")
        return detected_markers
    
    async def contextual_rescan(self, context: AnalysisContext) -> List[Dict[str, Any]]:
        """
        Phase 2: Intelligent scan for composed (C_) and meta-marker (MM_) markers
        using NLP enrichment data. Checks for complex activation rules.
        
        Args:
            context: AnalysisContext with NLP enrichment and initial markers
            
        Returns:
            List of newly detected/activated complex markers
        """
        activated_markers = []
        
        # Build activation candidates from initial scan
        activation_candidates = {
            m["marker_id"] for m in context.detected_markers 
            if m["marker_id"].startswith("S_")
        }
        
        # Build query for C_ and MM_ markers
        query = {"_id": {"$regex": "^(C_|MM_)"}}
        if context.schema_id:
            query["schema_id"] = context.schema_id
        
        # Load complex markers from database
        complex_markers = await marker_collection.find(query).to_list(None)
        
        for marker_data in complex_markers:
            try:
                marker = Marker(**marker_data)
                self.marker_cache[marker.id] = marker
                
                # Check if complex marker can be activated using rules engine
                activation_result = self.rules_engine.check_activation(
                    marker, context, set(m["marker_id"] for m in context.detected_markers)
                )
                
                if activation_result["activated"]:
                    activated_markers.append({
                        "marker_id": marker.id,
                        "marker_type": marker.id.split("_")[0],
                        "frame": marker.frame.model_dump(),
                        "activated_at": datetime.now().isoformat(),
                        "components": activation_result["components"],
                        "activation_rule": marker.activation,
                        "scoring": marker.scoring,
                        "confidence": activation_result["confidence"],
                        "detection_phase": "contextual",
                        "nlp_enhanced": activation_result.get("nlp_enhanced", False)
                    })
                    
            except Exception as e:
                logger.error(f"Error processing complex marker {marker_data.get('_id')}: {str(e)}")
                continue
        
        logger.info(f"Contextual rescan activated {len(activated_markers)} complex markers")
        return activated_markers
    
    def _detect_marker(self, marker: Marker, text: str) -> bool:
        """Check if a marker is detected in the text"""
        # Check examples
        for example in marker.examples:
            if example.lower() in text.lower():
                return True
        
        # Check patterns if available
        if marker.pattern:
            patterns = marker.pattern if isinstance(marker.pattern, list) else [marker.pattern]
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        
        # Check frame signals
        if marker.frame and marker.frame.signal:
            signals = marker.frame.signal if isinstance(marker.frame.signal, list) else [marker.frame.signal]
            for signal in signals:
                if signal.lower() in text.lower():
                    return True
        
        return False
    
    def _calculate_confidence(self, marker: Marker, text: str) -> float:
        """Calculate confidence score for marker detection"""
        confidence = 0.0
        match_count = 0
        
        # Check examples
        for example in marker.examples:
            if example.lower() in text.lower():
                match_count += 1
        
        if match_count > 0:
            confidence = min(1.0, match_count * 0.3)
        
        # Boost confidence if pattern matches
        if marker.pattern and confidence < 1.0:
            patterns = marker.pattern if isinstance(marker.pattern, list) else [marker.pattern]
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    confidence = min(1.0, confidence + 0.4)
        
        return confidence
    
    def _get_matched_examples(self, marker: Marker, text: str) -> List[str]:
        """Get list of examples that matched in the text"""
        matched = []
        for example in marker.examples:
            if example.lower() in text.lower():
                matched.append(example)
        return matched
    
    def _check_complex_activation(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        activation_candidates: Set[str]
    ) -> Dict[str, Any]:
        """
        Check complex activation rules for composed markers.
        Uses NLP enrichment data when available for sophisticated reasoning.
        
        Returns:
            Dict with activation status, confidence, and components
        """
        result = {
            "activated": False,
            "confidence": 0.0,
            "components": [],
            "nlp_enhanced": False
        }
        
        if not marker.composed_of:
            return result
        
        # Get detected marker IDs from context
        detected_ids = {m["marker_id"] for m in context.detected_markers}
        
        # Check activation rules
        if marker.activation:
            activation_type = marker.activation.get("type", "ALL")
            
            if activation_type == "ALL":
                # All components must be detected
                if all(comp in detected_ids for comp in marker.composed_of):
                    result["activated"] = True
                    result["components"] = marker.composed_of
                    result["confidence"] = 0.8
                    
            elif activation_type == "ANY":
                # At least one component must be detected
                found_components = [comp for comp in marker.composed_of if comp in detected_ids]
                if found_components:
                    result["activated"] = True
                    result["components"] = found_components
                    result["confidence"] = 0.6 + (0.2 * len(found_components) / len(marker.composed_of))
                    
            elif activation_type == "ANY_N":
                # At least N components must be detected
                n = marker.activation.get("count", 2)
                found_components = [comp for comp in marker.composed_of if comp in detected_ids]
                if len(found_components) >= n:
                    result["activated"] = True
                    result["components"] = found_components
                    result["confidence"] = 0.7 + (0.3 * len(found_components) / len(marker.composed_of))
        
        else:
            # Default: all components must be detected
            if all(comp in detected_ids for comp in marker.composed_of):
                result["activated"] = True
                result["components"] = marker.composed_of
                result["confidence"] = 0.75
        
        # Apply NLP-based enhancements if available
        if result["activated"] and context.tokens:
            result = self._apply_nlp_enhancements(marker, context, result)
        
        return result
    
    def _apply_nlp_enhancements(
        self, 
        marker: Marker, 
        context: AnalysisContext, 
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply NLP-based enhancements to activation decisions.
        Can adjust confidence based on linguistic features.
        """
        try:
            # Example: Boost confidence if key tokens are in proximity
            if context.tokens and len(context.tokens) > 0:
                result["nlp_enhanced"] = True
                
                # Check for temporal markers
                temporal_words = {"zuerst", "dann", "danach", "später", "gleichzeitig"}
                temporal_count = sum(1 for token in context.tokens if token.lower() in temporal_words)
                
                if temporal_count > 0 and marker.activation and marker.activation.get("temporal"):
                    # Boost confidence for temporal markers when temporal words are present
                    result["confidence"] = min(1.0, result["confidence"] + 0.1)
                
                # Check for negation near components
                negation_words = {"nicht", "kein", "keine", "niemals", "nie"}
                has_negation = any(token.lower() in negation_words for token in context.tokens)
                
                if has_negation:
                    # Reduce confidence if negation is present
                    result["confidence"] = max(0.3, result["confidence"] - 0.2)
                
        except Exception as e:
            logger.warning(f"Error in NLP enhancement: {str(e)}")
            # Continue with original result
        
        return result


# Keep existing standalone functions for backward compatibility
async def create_marker(marker_data: Marker) -> Marker:
    marker_dict = marker_data.model_dump(by_alias=True)
    await marker_collection.insert_one(marker_dict)
    return marker_data

async def list_markers(skip: int = 0, limit: int = 100) -> List[Marker]:
    markers = await marker_collection.find().skip(skip).limit(limit).to_list(limit)
    return [Marker(**m) for m in markers]

async def get_marker(marker_id: str) -> Marker | None:
    marker = await marker_collection.find_one({"_id": marker_id})
    if marker:
        return Marker(**marker)
    return None