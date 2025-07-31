from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union

class Frame(BaseModel):
    signal: Union[str, List[str]]
    concept: str
    pragmatics: str
    narrative: str

class Marker(BaseModel):
    id: str = Field(..., alias="_id")
    frame: Frame
    examples: List[str] = Field(..., min_length=1)
    pattern: Union[str, List[str], None] = None
    composed_of: Union[List[str], None] = None
    detect_class: Union[str, None] = None
    activation: Union[Dict[str, Any], None] = None
    scoring: Union[Dict[str, Any], None] = None
    tags: Union[List[str], None] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "C_RELATIONAL_DESTABILIZATION_LOOP",
                "frame": {
                    "signal": ["Nähe/Distanz-Kontraste"],
                    "concept": "Bindungsambivalenz",
                    "pragmatics": "Destabilisierung",
                    "narrative": "loop"
                },
                "composed_of": ["S_AMBIVALENT_ATTACHMENT_SPEECH", "S_SOFT_WITHDRAWAL"],
                "activation": {"rule": "ANY 2 IN 48h"},
                "scoring": {"base": 2.0, "weight": 1.6},
                "examples": ["Ich vermisse dich … aber ich brauche Abstand."],
                "tags": ["beziehung", "ambivalenz", "loop"]
            }
        }