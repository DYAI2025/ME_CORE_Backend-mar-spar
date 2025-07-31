"""
PYTHON_MARKER - Semantic Marker
Sehr grobe Heuristik: je mehr Self-Disclosure-Marker, desto höher.
"""

import re

class PYTHON_MARKER:
    """
    Sehr grobe Heuristik: je mehr Self-Disclosure-Marker, desto höher.
    """
    
    examples = [
    ]
    
    patterns = [
        re.compile(r"(muster.*wird.*ergänzt)", re.IGNORECASE)
    ]
    
    semantic_grabber_id = "AUTO_GENERATED"
    
    def match(self, text):
        """Prüft ob der Text zum Marker passt"""
        for pattern in self.patterns:
            if pattern.search(text):
                return True
        return False
