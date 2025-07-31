import os
import importlib.util
import logging
from ..database import db
from ..config import settings
from typing import List, Dict, Any

detector_collection = db["detectors"]

async def run_analysis(text: str, schema_id: str) -> List[Dict[str, Any]]:
    recognized_markers = []
    
    # Hier könnte man den schema_id nutzen, um Detektoren zu filtern
    detectors = await detector_collection.find().to_list(length=None)

    for detector in detectors:
        file_path = os.path.join(settings.DETECTOR_PATH, detector.get("file_path", ""))
        module_name = detector.get("id")

        if not os.path.exists(file_path):
            logging.warning(f"Detector file not found: {file_path}")
            continue

        try:
            # Dynamically load the detector module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            detector_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(detector_module)

            # Assume each detector has a 'detect' function
            if hasattr(detector_module, "detect"):
                result = detector_module.detect(text)
                if result:
                    recognized_markers.append({
                        "detector_id": detector["_id"],
                        "fired_marker": detector.get("fires_marker")
                    })
        except Exception as e:
            logging.error(f"Error executing detector {module_name}: {e}")
            
    return recognized_markers