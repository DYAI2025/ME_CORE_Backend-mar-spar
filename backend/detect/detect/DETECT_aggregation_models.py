"""Datenmodelle für die Zeitreihen-Aggregation."""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from enum import Enum

import pandas as pd


class AggregationPeriod(str, Enum):
    """Verfügbare Aggregations-Zeiträume."""
    
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class TimeSeriesPoint(BaseModel):
    """Ein einzelner Punkt in einer Zeitreihe."""
    
    timestamp: datetime = Field(..., description="Zeitpunkt")
    period_start: datetime = Field(..., description="Start des Aggregationszeitraums")
    period_end: datetime = Field(..., description="Ende des Aggregationszeitraums")
    
    values: Dict[str, float] = Field(
        default_factory=dict,
        description="Werte für verschiedene Metriken"
    )
    
    counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Anzahlen (z.B. Marker-Counts)"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Zusätzliche Metadaten"
    )
    
    @validator('period_end')
    def validate_period(cls, v, values):
        """Stelle sicher, dass period_end nach period_start liegt."""
        if 'period_start' in values and v <= values['period_start']:
            raise ValueError('period_end muss nach period_start liegen')
        return v


class TimeSeriesData(BaseModel):
    """Container für Zeitreihen-Daten."""
    
    series_id: str = Field(..., description="Eindeutige ID der Zeitreihe")
    name: str = Field(..., description="Name der Zeitreihe")
    metric_type: str = Field(..., description="Art der Metrik (score, count, etc.)")
    
    period: AggregationPeriod = Field(..., description="Aggregationszeitraum")
    
    data_points: List[TimeSeriesPoint] = Field(
        default_factory=list,
        description="Die eigentlichen Datenpunkte"
    )
    
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistische Zusammenfassung"
    )
    
    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert die Zeitreihe in einen Pandas DataFrame."""
        if not self.data_points:
            return pd.DataFrame()
        
        records = []
        for point in self.data_points:
            record = {
                'timestamp': point.timestamp,
                'period_start': point.period_start,
                'period_end': point.period_end
            }
            record.update(point.values)
            record.update({f"{k}_count": v for k, v in point.counts.items()})
            records.append(record)
        
        df = pd.DataFrame(records)
        df.set_index('timestamp', inplace=True)
        return df
    
    def get_trend(self, metric: str) -> Optional[str]:
        """Berechnet den Trend für eine bestimmte Metrik."""
        if len(self.data_points) < 2:
            return None
        
        values = [p.values.get(metric, 0) for p in self.data_points]
        if not values:
            return None
        
        # Einfache Trendberechnung
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half > first_half * 1.1:
            return "increasing"
        elif second_half < first_half * 0.9:
            return "decreasing"
        else:
            return "stable"


class AggregationConfig(BaseModel):
    """Konfiguration für die Zeitreihen-Aggregation."""
    
    period: AggregationPeriod = Field(
        default=AggregationPeriod.DAILY,
        description="Standard-Aggregationszeitraum"
    )
    
    custom_period_hours: Optional[int] = Field(
        None,
        description="Stunden für custom period"
    )
    
    metrics_to_aggregate: List[str] = Field(
        default_factory=lambda: [
            "manipulation_index",
            "relationship_health",
            "fraud_probability",
            "marker_count"
        ],
        description="Zu aggregierende Metriken"
    )
    
    aggregation_functions: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "default": ["mean", "min", "max", "sum", "count"],
            "scores": ["mean", "min", "max", "std"],
            "counts": ["sum", "mean"]
        },
        description="Aggregationsfunktionen pro Metrik-Typ"
    )
    
    include_zero_periods: bool = Field(
        default=True,
        description="Ob Zeiträume ohne Daten inkludiert werden sollen"
    )
    
    smooth_data: bool = Field(
        default=False,
        description="Ob Daten geglättet werden sollen"
    )
    
    smoothing_window: int = Field(
        default=3,
        description="Fenster für Glättung"
    )


class HeatmapData(BaseModel):
    """Daten für Heatmap-Visualisierung."""
    
    title: str = Field(..., description="Titel der Heatmap")
    
    x_labels: List[str] = Field(
        ...,
        description="X-Achsen-Labels (z.B. Zeiträume)"
    )
    
    y_labels: List[str] = Field(
        ...,
        description="Y-Achsen-Labels (z.B. Marker-Kategorien)"
    )
    
    values: List[List[float]] = Field(
        ...,
        description="2D-Array der Werte"
    )
    
    color_scale: str = Field(
        default="RdYlGn",
        description="Farbskala für Heatmap"
    )
    
    annotations: Optional[List[List[str]]] = Field(
        None,
        description="Text-Annotationen für Zellen"
    )
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComparisonData(BaseModel):
    """Daten für Zeitreihen-Vergleiche."""
    
    comparison_type: str = Field(
        ...,
        description="Art des Vergleichs (period, speaker, category)"
    )
    
    series: List[TimeSeriesData] = Field(
        ...,
        description="Zu vergleichende Zeitreihen"
    )
    
    baseline_index: Optional[int] = Field(
        None,
        description="Index der Baseline-Serie"
    )
    
    differences: Optional[Dict[str, List[float]]] = Field(
        None,
        description="Berechnete Differenzen"
    )
    
    correlation_matrix: Optional[List[List[float]]] = Field(
        None,
        description="Korrelationsmatrix zwischen Serien"
    )


class AggregationResult(BaseModel):
    """Gesamtergebnis der Zeitreihen-Aggregation."""
    
    time_series: Dict[str, TimeSeriesData] = Field(
        default_factory=dict,
        description="Aggregierte Zeitreihen pro Metrik"
    )
    
    heatmaps: Dict[str, HeatmapData] = Field(
        default_factory=dict,
        description="Generierte Heatmap-Daten"
    )
    
    comparisons: List[ComparisonData] = Field(
        default_factory=list,
        description="Zeitreihen-Vergleiche"
    )
    
    summary_statistics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Zusammenfassende Statistiken"
    )
    
    export_data: Optional[pd.DataFrame] = Field(
        None,
        description="Exportierbare Daten als DataFrame"
    )
    
    processing_time: float = Field(0.0)
    
    class Config:
        """Pydantic Konfiguration."""
        arbitrary_types_allowed = True  # Für pandas DataFrame
    
    def to_csv(self, filepath: str):
        """Exportiert die Daten als CSV."""
        if self.export_data is not None:
            self.export_data.to_csv(filepath)
        else:
            # Erstelle DataFrame aus time_series
            dfs = []
            for metric, series in self.time_series.items():
                df = series.to_dataframe()
                df.columns = [f"{metric}_{col}" if col not in ['period_start', 'period_end'] 
                             else col for col in df.columns]
                dfs.append(df)
            
            if dfs:
                combined_df = pd.concat(dfs, axis=1)
                combined_df.to_csv(filepath)
    
    def to_json(self, filepath: str):
        """Exportiert die Daten als JSON."""
        import json
        
        # Konvertiere zu serialisierbarem Format
        data = {
            'time_series': {
                name: {
                    'series_id': ts.series_id,
                    'name': ts.name,
                    'metric_type': ts.metric_type,
                    'period': ts.period.value,
                    'data_points': [
                        {
                            'timestamp': point.timestamp.isoformat(),
                            'period_start': point.period_start.isoformat(),
                            'period_end': point.period_end.isoformat(),
                            'values': point.values,
                            'counts': point.counts
                        }
                        for point in ts.data_points
                    ],
                    'statistics': ts.statistics
                }
                for name, ts in self.time_series.items()
            },
            'summary_statistics': self.summary_statistics,
            'processing_time': self.processing_time
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)