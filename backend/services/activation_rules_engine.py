"""
Advanced Activation Rules Engine for MarkerEngine.
Implements complex activation patterns including temporal, sentiment, and proximity rules.
"""
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
from ..models.analysis_context import AnalysisContext
from ..models.marker import Marker

logger = logging.getLogger(__name__)


class ActivationRulesEngine:
    """
    Sophisticated rule engine for complex marker activation.
    Supports temporal sequences, sentiment alignment, proximity detection, and more.
    """
    
    def __init__(self):
        self.rule_handlers = {
            "ALL": self._check_all_rule,
            "ANY": self._check_any_rule,
            "ANY_N": self._check_any_n_rule,
            "TEMPORAL": self._check_temporal_rule,
            "SENTIMENT": self._check_sentiment_rule,
            "PROXIMITY": self._check_proximity_rule,
            "NEGATION": self._check_negation_rule,
            "PATTERN": self._check_pattern_rule,
            "COMPOSITE": self._check_composite_rule
        }
    
    def check_activation(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_marker_ids: Set[str]
    ) -> Dict[str, Any]:
        """
        Check if a complex marker should be activated based on its rules.
        
        Args:
            marker: The marker to check
            context: Analysis context with NLP data
            detected_marker_ids: Set of already detected marker IDs
            
        Returns:
            Dict with activation status, confidence, and details
        """
        result = {
            "activated": False,
            "confidence": 0.0,
            "components": [],
            "details": {},
            "rule_type": None,
            "nlp_enhanced": False
        }
        
        if not marker.activation or not marker.composed_of:
            # Default rule: ALL components must be present
            return self._check_all_rule(marker, context, detected_marker_ids)
        
        # Get rule type
        rule_type = marker.activation.get("type", "ALL").upper()
        result["rule_type"] = rule_type
        
        # Check if we have a handler for this rule type
        if rule_type in self.rule_handlers:
            handler_result = self.rule_handlers[rule_type](
                marker, context, detected_marker_ids
            )
            result.update(handler_result)
        else:
            logger.warning(f"Unknown activation rule type: {rule_type}")
            # Fall back to ALL rule
            result.update(self._check_all_rule(marker, context, detected_marker_ids))
        
        # Apply NLP enhancements if available and marker is activated
        if result["activated"] and context.tokens:
            result = self._apply_nlp_enhancements(marker, context, result)
        
        return result
    
    def _check_all_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """All components must be detected."""
        found_components = [
            comp for comp in marker.composed_of 
            if comp in detected_ids
        ]
        
        activated = len(found_components) == len(marker.composed_of)
        
        return {
            "activated": activated,
            "confidence": 0.9 if activated else 0.0,
            "components": found_components,
            "details": {
                "required": len(marker.composed_of),
                "found": len(found_components),
                "missing": list(set(marker.composed_of) - set(found_components))
            }
        }
    
    def _check_any_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """At least one component must be detected."""
        found_components = [
            comp for comp in marker.composed_of 
            if comp in detected_ids
        ]
        
        activated = len(found_components) > 0
        
        # Confidence based on how many components were found
        confidence = 0.0
        if activated:
            confidence = 0.5 + (0.4 * len(found_components) / len(marker.composed_of))
        
        return {
            "activated": activated,
            "confidence": confidence,
            "components": found_components,
            "details": {
                "required": "at least 1",
                "found": len(found_components),
                "total_possible": len(marker.composed_of)
            }
        }
    
    def _check_any_n_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """At least N components must be detected."""
        n = marker.activation.get("count", 2)
        found_components = [
            comp for comp in marker.composed_of 
            if comp in detected_ids
        ]
        
        activated = len(found_components) >= n
        
        # Confidence scales with how many beyond N were found
        confidence = 0.0
        if activated:
            excess = len(found_components) - n
            confidence = 0.7 + (0.3 * excess / max(1, len(marker.composed_of) - n))
        
        return {
            "activated": activated,
            "confidence": min(1.0, confidence),
            "components": found_components,
            "details": {
                "required": f"at least {n}",
                "found": len(found_components),
                "threshold": n
            }
        }
    
    def _check_temporal_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """Components must appear in temporal sequence."""
        window = marker.activation.get("window", 10)  # Token window
        strict_order = marker.activation.get("strict_order", False)
        
        # Find positions of components in the text
        component_positions = self._find_component_positions(
            marker.composed_of, context, detected_ids
        )
        
        if not component_positions:
            return {
                "activated": False,
                "confidence": 0.0,
                "components": [],
                "details": {"reason": "No components found in text"}
            }
        
        # Check temporal constraints
        if strict_order:
            # Components must appear in exact order
            activated, confidence = self._check_strict_temporal_order(
                marker.composed_of, component_positions, window
            )
        else:
            # Components must appear within window
            activated, confidence = self._check_temporal_proximity(
                component_positions, window
            )
        
        found_components = list(component_positions.keys())
        
        return {
            "activated": activated,
            "confidence": confidence,
            "components": found_components,
            "details": {
                "window": window,
                "strict_order": strict_order,
                "positions": component_positions,
                "temporal_pattern": "sequential" if strict_order else "proximity"
            },
            "nlp_enhanced": True
        }
    
    def _check_sentiment_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """Components must have aligned sentiment."""
        alignment = marker.activation.get("alignment", "consistent")
        min_confidence = marker.activation.get("min_confidence", 0.6)
        
        found_components = [
            comp for comp in marker.composed_of 
            if comp in detected_ids
        ]
        
        if not found_components or not context.sentiment_scores:
            # Fall back to basic ALL rule if no sentiment data
            return self._check_all_rule(marker, context, detected_ids)
        
        # Get sentiment around components
        component_sentiments = self._get_component_sentiments(
            found_components, context
        )
        
        # Check sentiment alignment
        if alignment == "consistent":
            activated, confidence = self._check_consistent_sentiment(
                component_sentiments, min_confidence
            )
        elif alignment == "contrasting":
            activated, confidence = self._check_contrasting_sentiment(
                component_sentiments, min_confidence
            )
        else:
            activated = len(found_components) == len(marker.composed_of)
            confidence = 0.7
        
        return {
            "activated": activated,
            "confidence": confidence,
            "components": found_components,
            "details": {
                "sentiment_alignment": alignment,
                "component_sentiments": component_sentiments,
                "overall_sentiment": context.sentiment_scores
            },
            "nlp_enhanced": True
        }
    
    def _check_proximity_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """Components must appear within proximity window."""
        max_distance = marker.activation.get("max_distance", 20)  # tokens
        
        found_components = [
            comp for comp in marker.composed_of 
            if comp in detected_ids
        ]
        
        if len(found_components) < 2:
            return {
                "activated": False,
                "confidence": 0.0,
                "components": found_components,
                "details": {"reason": "Need at least 2 components for proximity check"}
            }
        
        # Find positions and calculate distances
        positions = self._find_component_positions(
            found_components, context, detected_ids
        )
        
        if not positions:
            return self._check_all_rule(marker, context, detected_ids)
        
        # Calculate maximum distance between any two components
        max_actual_distance = self._calculate_max_distance(positions)
        
        activated = max_actual_distance <= max_distance
        
        # Confidence decreases with distance
        confidence = 0.0
        if activated:
            confidence = 0.9 - (0.4 * max_actual_distance / max_distance)
        
        return {
            "activated": activated,
            "confidence": max(0.5, confidence),
            "components": found_components,
            "details": {
                "max_allowed_distance": max_distance,
                "actual_max_distance": max_actual_distance,
                "component_positions": positions
            },
            "nlp_enhanced": True
        }
    
    def _check_negation_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """Check for negation context around components."""
        negation_window = marker.activation.get("negation_window", 3)
        allow_negation = marker.activation.get("allow_negation", False)
        
        found_components = [
            comp for comp in marker.composed_of 
            if comp in detected_ids
        ]
        
        if not found_components:
            return {
                "activated": False,
                "confidence": 0.0,
                "components": [],
                "details": {"reason": "No components found"}
            }
        
        # Check for negation
        has_negation = self._detect_negation_context(
            found_components, context, negation_window
        )
        
        # Activation depends on negation settings
        if allow_negation:
            activated = len(found_components) == len(marker.composed_of)
            confidence = 0.7 if has_negation else 0.9
        else:
            activated = len(found_components) == len(marker.composed_of) and not has_negation
            confidence = 0.9 if activated else 0.0
        
        return {
            "activated": activated,
            "confidence": confidence,
            "components": found_components,
            "details": {
                "negation_detected": has_negation,
                "allow_negation": allow_negation,
                "negation_window": negation_window
            },
            "nlp_enhanced": True
        }
    
    def _check_pattern_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """Check for specific linguistic patterns."""
        pattern_type = marker.activation.get("pattern", "conjunction")
        
        # Implement various pattern checks
        if pattern_type == "conjunction":
            return self._check_conjunction_pattern(marker, context, detected_ids)
        elif pattern_type == "cause_effect":
            return self._check_cause_effect_pattern(marker, context, detected_ids)
        else:
            # Unknown pattern, fall back
            return self._check_all_rule(marker, context, detected_ids)
    
    def _check_composite_rule(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """Composite rule combining multiple rule types."""
        rules = marker.activation.get("rules", [])
        operator = marker.activation.get("operator", "AND")  # AND/OR
        
        results = []
        for rule in rules:
            # Create temporary marker with single rule
            temp_activation = {"type": rule["type"], **rule}
            temp_marker = Marker(
                **{**marker.dict(), "activation": temp_activation}
            )
            
            # Check individual rule
            rule_result = self.check_activation(
                temp_marker, context, detected_ids
            )
            results.append(rule_result)
        
        # Combine results based on operator
        if operator == "AND":
            activated = all(r["activated"] for r in results)
            confidence = min(r["confidence"] for r in results) if results else 0.0
        else:  # OR
            activated = any(r["activated"] for r in results)
            confidence = max(r["confidence"] for r in results) if results else 0.0
        
        # Collect all components
        all_components = []
        for r in results:
            all_components.extend(r.get("components", []))
        components = list(set(all_components))
        
        return {
            "activated": activated,
            "confidence": confidence,
            "components": components,
            "details": {
                "composite_operator": operator,
                "rule_results": results
            },
            "nlp_enhanced": True
        }
    
    # Helper methods
    
    def _find_component_positions(
        self, 
        components: List[str], 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, List[int]]:
        """Find token positions where components are detected."""
        positions = defaultdict(list)
        
        if not context.tokens:
            return dict(positions)
        
        # For each detected marker in context
        for marker in context.detected_markers:
            if marker["marker_id"] in components:
                # Try to find marker text in tokens
                marker_text = marker.get("examples_matched", [])
                if marker_text:
                    for text in marker_text:
                        # Find positions of this text in tokens
                        text_tokens = text.lower().split()
                        for i in range(len(context.tokens) - len(text_tokens) + 1):
                            if all(
                                context.tokens[i+j].lower() == text_tokens[j]
                                for j in range(len(text_tokens))
                            ):
                                positions[marker["marker_id"]].append(i)
        
        return dict(positions)
    
    def _check_strict_temporal_order(
        self, 
        components: List[str], 
        positions: Dict[str, List[int]], 
        window: int
    ) -> Tuple[bool, float]:
        """Check if components appear in strict order within window."""
        # Get first position of each component
        first_positions = []
        for comp in components:
            if comp in positions and positions[comp]:
                first_positions.append(min(positions[comp]))
            else:
                return False, 0.0
        
        # Check if positions are in order
        if first_positions != sorted(first_positions):
            return False, 0.0
        
        # Check if all within window
        for i in range(1, len(first_positions)):
            if first_positions[i] - first_positions[i-1] > window:
                return False, 0.0
        
        # Calculate confidence based on how compact the sequence is
        total_span = first_positions[-1] - first_positions[0]
        confidence = 0.9 - (0.3 * total_span / (window * len(components)))
        
        return True, max(0.6, confidence)
    
    def _check_temporal_proximity(
        self, 
        positions: Dict[str, List[int]], 
        window: int
    ) -> Tuple[bool, float]:
        """Check if components appear within proximity window."""
        all_positions = []
        for pos_list in positions.values():
            all_positions.extend(pos_list)
        
        if len(all_positions) < 2:
            return False, 0.0
        
        all_positions.sort()
        
        # Check maximum gap
        max_gap = max(
            all_positions[i+1] - all_positions[i] 
            for i in range(len(all_positions)-1)
        )
        
        if max_gap > window:
            return False, 0.0
        
        # Confidence based on average gap
        avg_gap = (all_positions[-1] - all_positions[0]) / max(1, len(all_positions) - 1)
        confidence = 0.9 - (0.4 * avg_gap / window)
        
        return True, max(0.5, confidence)
    
    def _calculate_max_distance(self, positions: Dict[str, List[int]]) -> int:
        """Calculate maximum distance between any two components."""
        all_positions = []
        for pos_list in positions.values():
            all_positions.extend(pos_list)
        
        if len(all_positions) < 2:
            return 0
        
        return max(all_positions) - min(all_positions)
    
    def _get_component_sentiments(
        self, 
        components: List[str], 
        context: AnalysisContext
    ) -> Dict[str, Dict[str, float]]:
        """Get sentiment scores around each component."""
        # This is a simplified implementation
        # In production, would analyze sentiment in component context
        sentiments = {}
        
        for comp in components:
            # Use overall sentiment as approximation
            sentiments[comp] = context.sentiment_scores or {
                "positive": 0.33,
                "negative": 0.33,
                "neutral": 0.34
            }
        
        return sentiments
    
    def _check_consistent_sentiment(
        self, 
        sentiments: Dict[str, Dict[str, float]], 
        min_confidence: float
    ) -> Tuple[bool, float]:
        """Check if sentiments are consistent across components."""
        if not sentiments:
            return False, 0.0
        
        # Find dominant sentiment for each component
        dominant_sentiments = []
        for comp, sent_scores in sentiments.items():
            dominant = max(sent_scores.items(), key=lambda x: x[1])
            dominant_sentiments.append(dominant)
        
        # Check if all have same dominant sentiment
        sentiment_types = set(s[0] for s in dominant_sentiments)
        if len(sentiment_types) == 1:
            # All consistent
            avg_confidence = sum(s[1] for s in dominant_sentiments) / len(dominant_sentiments)
            return avg_confidence >= min_confidence, avg_confidence
        
        return False, 0.0
    
    def _check_contrasting_sentiment(
        self, 
        sentiments: Dict[str, Dict[str, float]], 
        min_confidence: float
    ) -> Tuple[bool, float]:
        """Check if sentiments contrast between components."""
        if len(sentiments) < 2:
            return False, 0.0
        
        # Check for positive-negative contrast
        has_positive = any(
            s.get("positive", 0) > min_confidence 
            for s in sentiments.values()
        )
        has_negative = any(
            s.get("negative", 0) > min_confidence 
            for s in sentiments.values()
        )
        
        if has_positive and has_negative:
            # Calculate confidence based on contrast strength
            max_pos = max(s.get("positive", 0) for s in sentiments.values())
            max_neg = max(s.get("negative", 0) for s in sentiments.values())
            confidence = (max_pos + max_neg) / 2
            return True, confidence
        
        return False, 0.0
    
    def _detect_negation_context(
        self, 
        components: List[str], 
        context: AnalysisContext,
        window: int
    ) -> bool:
        """Detect if components appear in negation context."""
        if not context.tokens:
            return False
        
        negation_words = {"nicht", "kein", "keine", "niemals", "nie", "nirgends", "niemand"}
        
        # Find component positions
        positions = self._find_component_positions(components, context, set(components))
        
        # Check for negation near each component
        for comp_positions in positions.values():
            for pos in comp_positions:
                # Check tokens within window
                start = max(0, pos - window)
                end = min(len(context.tokens), pos + window + 1)
                
                window_tokens = context.tokens[start:end]
                if any(token.lower() in negation_words for token in window_tokens):
                    return True
        
        return False
    
    def _check_conjunction_pattern(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """Check for conjunction pattern between components."""
        conjunctions = {"aber", "jedoch", "trotzdem", "dennoch", "obwohl", "allerdings"}
        
        found_components = [
            comp for comp in marker.composed_of 
            if comp in detected_ids
        ]
        
        if len(found_components) < 2:
            return {
                "activated": False,
                "confidence": 0.0,
                "components": found_components,
                "details": {"reason": "Need at least 2 components for conjunction pattern"}
            }
        
        # Check for conjunctions between components
        positions = self._find_component_positions(found_components, context, detected_ids)
        
        has_conjunction = False
        conjunction_found = None
        
        if len(positions) >= 2 and context.tokens:
            # Get position ranges
            pos_ranges = []
            for comp, pos_list in positions.items():
                if pos_list:
                    pos_ranges.append((min(pos_list), max(pos_list), comp))
            
            pos_ranges.sort()
            
            # Check for conjunctions between consecutive components
            for i in range(len(pos_ranges) - 1):
                start = pos_ranges[i][1]
                end = pos_ranges[i+1][0]
                
                between_tokens = context.tokens[start:end]
                for token in between_tokens:
                    if token.lower() in conjunctions:
                        has_conjunction = True
                        conjunction_found = token
                        break
        
        activated = len(found_components) == len(marker.composed_of) and has_conjunction
        confidence = 0.95 if activated else 0.0
        
        return {
            "activated": activated,
            "confidence": confidence,
            "components": found_components,
            "details": {
                "pattern": "conjunction",
                "conjunction_found": conjunction_found,
                "has_conjunction": has_conjunction
            },
            "nlp_enhanced": True
        }
    
    def _check_cause_effect_pattern(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        detected_ids: Set[str]
    ) -> Dict[str, Any]:
        """Check for cause-effect pattern between components."""
        cause_indicators = {"weil", "da", "denn", "deshalb", "daher", "deswegen"}
        
        # Similar implementation to conjunction pattern
        # but looking for causal connectors
        # ... (implementation similar to conjunction pattern)
        
        # Placeholder return
        return self._check_all_rule(marker, context, detected_ids)
    
    def _apply_nlp_enhancements(
        self, 
        marker: Marker, 
        context: AnalysisContext,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply additional NLP-based adjustments to activation confidence."""
        if not context.tokens:
            return result
        
        original_confidence = result["confidence"]
        adjustments = []
        
        # Check for question context
        if context.tokens and context.tokens[-1] == "?":
            result["confidence"] *= 0.9
            adjustments.append(("question_context", -0.1))
        
        # Check for uncertainty markers
        uncertainty_markers = {"vielleicht", "möglicherweise", "eventuell", "vermutlich"}
        if any(token.lower() in uncertainty_markers for token in context.tokens):
            result["confidence"] *= 0.85
            adjustments.append(("uncertainty_markers", -0.15))
        
        # Check for emphasis markers
        emphasis_markers = {"wirklich", "tatsächlich", "definitiv", "sicherlich"}
        if any(token.lower() in emphasis_markers for token in context.tokens):
            result["confidence"] = min(1.0, result["confidence"] * 1.1)
            adjustments.append(("emphasis_markers", +0.1))
        
        # Add adjustment details
        result["details"]["nlp_adjustments"] = {
            "original_confidence": original_confidence,
            "final_confidence": result["confidence"],
            "adjustments": adjustments
        }
        
        result["nlp_enhanced"] = True
        
        return result