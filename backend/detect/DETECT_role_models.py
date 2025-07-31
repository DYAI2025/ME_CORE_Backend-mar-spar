"""Datenmodelle für Rollen- und Attribut-Tracking."""

from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..matcher.marker_models import MarkerCategory


class AttributeType(str, Enum):
    """Typen von Personen