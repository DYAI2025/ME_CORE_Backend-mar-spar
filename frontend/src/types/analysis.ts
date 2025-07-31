export interface AnalysisRequest {
  text: string;
  schema_id: string;
}

export interface AnalysisResponse {
  markers: DetectedMarker[];
  interpretation: string;
  model_used?: string;
  processing_time?: number;
  marker_count: number;
  total_score: number;
}

export interface DetectedMarker {
  id: string;
  frame: {
    signal: string | string[];
    concept: string;
    pragmatics: string;
    narrative: string;
  };
  scoring?: {
    base: number;
    weight: number;
  };
  position?: {
    start: number;
    end: number;
  };
  context?: string;
}

export interface AnalysisSchema {
  id: string;
  name: string;
  description?: string;
  version?: string;
  marker_count?: number;
}