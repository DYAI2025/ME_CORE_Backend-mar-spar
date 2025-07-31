"""
LLM Bridge for narrative interpretation of marker analysis results
Primary: Moonshot.ai Kimi K2 128k
Fallback: OpenAI GPT-4
"""

import os
import httpx
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class MarkerInterpretation(BaseModel):
    """Model for marker interpretation request"""
    markers: List[Dict[str, Any]]
    schema_name: str
    detected_count: int
    total_score: float = 0.0


class LLMResponse(BaseModel):
    """Model for LLM interpretation response"""
    interpretation: str
    model_used: str
    processing_time: float
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class LLMBridge:
    """Bridge to external LLMs for narrative interpretation"""
    
    def __init__(self):
        # Load API keys from environment
        self.kimi_api_key = os.getenv("KIMI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # API endpoints
        self.kimi_endpoint = "https://api.moonshot.cn/v1/chat/completions"
        self.openai_endpoint = "https://api.openai.com/v1/chat/completions"
        
        # Validate API keys
        if not self.kimi_api_key:
            logger.warning("KIMI_API_KEY not found in environment")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not found in environment")
    
    def _create_interpretation_prompt(self, marker_data: MarkerInterpretation) -> str:
        """Create prompt for LLM interpretation"""
        prompt = f"""Du bist ein Experte für psycholinguistische Analyse. Deine Aufgabe ist es, die von der MarkerEngine erkannten semantischen Marker in eine verständliche, narrative Interpretation zu übersetzen.

WICHTIG: Du analysierst NICHT den Originaltext. Du interpretierst ausschließlich die bereits erkannten Marker und ihre Bedeutung.

Analyseschema: {marker_data.schema_name}
Anzahl erkannter Marker: {marker_data.detected_count}
Gesamtscore: {marker_data.total_score:.2f}

Erkannte Marker:
"""
        
        for marker in marker_data.markers:
            prompt += f"\n- {marker.get('id', 'Unknown')}: {marker.get('frame', {}).get('concept', 'Unknown concept')}"
            if 'scoring' in marker:
                prompt += f" (Score: {marker['scoring'].get('base', 1.0) * marker['scoring'].get('weight', 1.0):.2f})"
        
        prompt += """

Bitte erstelle eine kohärente, gut formulierte Interpretation dieser Marker-Konstellation. 
Erkläre:
1. Was diese Marker-Kombination über die Kommunikationsdynamik aussagt
2. Welche psychologischen oder relationalen Muster erkennbar sind
3. Mögliche Bedeutungen im Kontext

Formuliere die Interpretation in einem empathischen, nicht-wertenden Ton. 
Die Interpretation sollte 150-300 Wörter umfassen."""
        
        return prompt
    
    async def _call_kimi_api(self, prompt: str) -> Optional[str]:
        """Call Moonshot Kimi K2 API"""
        if not self.kimi_api_key:
            logger.error("Kimi API key not configured")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.kimi_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "moonshot-v1-128k",
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Experte für psycholinguistische Analyse und narrative Interpretation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.kimi_endpoint,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Kimi API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Kimi API exception: {e}")
            return None
    
    async def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI GPT-4 API as fallback"""
        if not self.openai_api_key:
            logger.error("OpenAI API key not configured")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Experte für psycholinguistische Analyse und narrative Interpretation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.openai_endpoint,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"OpenAI API exception: {e}")
            return None
    
    async def generate_interpretation(self, marker_data: MarkerInterpretation) -> LLMResponse:
        """Generate interpretation using LLM with fallback logic"""
        start_time = asyncio.get_event_loop().time()
        
        # Create prompt
        prompt = self._create_interpretation_prompt(marker_data)
        
        # Try primary LLM (Kimi)
        logger.info("Attempting interpretation with Kimi K2...")
        interpretation = await self._call_kimi_api(prompt)
        model_used = "moonshot-v1-128k"
        
        # Fallback to GPT-4 if Kimi fails
        if not interpretation:
            logger.info("Falling back to GPT-4...")
            interpretation = await self._call_openai_api(prompt)
            model_used = "gpt-4"
        
        # Final fallback if both fail
        if not interpretation:
            logger.error("Both LLM APIs failed, using default interpretation")
            interpretation = self._create_default_interpretation(marker_data)
            model_used = "default"
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return LLMResponse(
            interpretation=interpretation,
            model_used=model_used,
            processing_time=processing_time
        )
    
    def _create_default_interpretation(self, marker_data: MarkerInterpretation) -> str:
        """Create a basic interpretation when LLM APIs fail"""
        return f"""Die Analyse hat {marker_data.detected_count} bedeutsame Marker in Ihrem Text identifiziert. 
Diese Marker weisen auf spezifische Kommunikationsmuster und psychologische Dynamiken hin. 
Eine detaillierte Interpretation konnte aufgrund technischer Einschränkungen nicht erstellt werden. 
Die erkannten Strukturen können jedoch wichtige Hinweise auf die zugrundeliegenden Beziehungsdynamiken geben."""


# Singleton instance
llm_bridge = LLMBridge()