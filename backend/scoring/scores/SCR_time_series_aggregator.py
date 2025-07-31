"""Time Series Aggregator für die Aggregation von Scores und Marker-Daten über Zeit."""

import logging
import time
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np

from .aggregation_models import (
    AggregationConfig, AggregationPeriod, AggregationResult,
    TimeSeriesData, TimeSeriesPoint, HeatmapData, ComparisonData
)
from ..scoring.score_models import ChunkScore, ScoreType
from ..matcher.marker_models import MarkerMatch, MarkerCategory

logger = logging.getLogger(__name__)


class TimeSeriesAggregator:
    """Aggregiert Scores und Marker-Daten über verschiedene Zeitfenster."""
    
    def __init__(self, config: Optional[AggregationConfig] = None):
        self.config = config or AggregationConfig()
    
    def aggregate_data(
        self,
        chunk_scores: List[ChunkScore],
        marker_matches: List[MarkerMatch],
        period: Optional[AggregationPeriod] = None
    ) -> AggregationResult:
        """Hauptmethode zur Aggregation von Daten.
        
        Args:
            chunk_scores: Liste von Chunk-Scores
            marker_matches: Liste von Marker-Matches
            period: Aggregationszeitraum (überschreibt config)
            
        Returns:
            AggregationResult mit allen aggregierten Daten
        """
        start_time = time.time()
        result = AggregationResult()
        
        # Verwende spezifizierten oder konfigurierten Zeitraum
        agg_period = period or self.config.period
        
        try:
            # Aggregiere Scores
            score_series = self._aggregate_scores(chunk_scores, agg_period)
            result.time_series.update(score_series)
            
            # Aggregiere Marker-Counts
            marker_series = self._aggregate_markers(marker_matches, agg_period)
            result.time_series.update(marker_series)
            
            # Erstelle Heatmaps
            result.heatmaps = self._create_heatmaps(
                chunk_scores,
                marker_matches,
                agg_period
            )
            
            # Erstelle Vergleiche
            result.comparisons = self._create_comparisons(result.time_series)
            
            # Berechne Summary Statistics
            result.summary_statistics = self._calculate_summary_stats(result.time_series)
            
            # Erstelle Export DataFrame
            result.export_data = self._create_export_dataframe(result.time_series)
            
        except Exception as e:
            logger.error(f"Fehler bei Aggregation: {e}")
            raise
        
        result.processing_time = time.time() - start_time
        logger.info(f"Aggregation abgeschlossen in {result.processing_time:.2f}s")
        
        return result
    
    def _aggregate_scores(
        self,
        chunk_scores: List[ChunkScore],
        period: AggregationPeriod
    ) -> Dict[str, TimeSeriesData]:
        """Aggregiert Chunk-Scores über Zeit."""
        series_dict = {}
        
        # Gruppiere Scores nach Typ
        scores_by_type = defaultdict(list)
        for score in chunk_scores:
            if score.timestamp:
                scores_by_type[score.score_type.value].append(score)
        
        # Erstelle Zeitreihe für jeden Score-Typ
        for score_type, scores in scores_by_type.items():
            if not scores:
                continue
            
            # Sortiere nach Zeit
            sorted_scores = sorted(scores, key=lambda s: s.timestamp)
            
            # Bestimme Zeitbereich
            start_time = sorted_scores[0].timestamp
            end_time = sorted_scores[-1].timestamp
            
            # Erstelle Zeitfenster
            time_windows = self._create_time_windows(start_time, end_time, period)
            
            # Aggregiere in Zeitfenster
            data_points = []
            for window_start, window_end in time_windows:
                window_scores = [
                    s for s in sorted_scores
                    if window_start <= s.timestamp < window_end
                ]
                
                if window_scores or self.config.include_zero_periods:
                    point = self._create_score_point(
                        window_scores,
                        window_start,
                        window_end,
                        score_type
                    )
                    data_points.append(point)
            
            # Glätte Daten wenn gewünscht
            if self.config.smooth_data and len(data_points) > self.config.smoothing_window:
                data_points = self._smooth_data_points(data_points, score_type)
            
            # Erstelle TimeSeriesData
            series = TimeSeriesData(
                series_id=f"scores_{score_type}",
                name=f"{score_type.replace('_', ' ').title()} Scores",
                metric_type="score",
                period=period,
                data_points=data_points,
                statistics=self._calculate_series_statistics(data_points, score_type)
            )
            
            series_dict[f"scores_{score_type}"] = series
        
        return series_dict
    
    def _aggregate_markers(
        self,
        marker_matches: List[MarkerMatch],
        period: AggregationPeriod
    ) -> Dict[str, TimeSeriesData]:
        """Aggregiert Marker-Matches über Zeit."""
        series_dict = {}
        
        # Filtere Matches mit Timestamps
        timed_matches = [m for m in marker_matches if m.timestamp]
        if not timed_matches:
            return series_dict
        
        # Sortiere nach Zeit
        sorted_matches = sorted(timed_matches, key=lambda m: m.timestamp)
        
        # Zeitbereich
        start_time = sorted_matches[0].timestamp
        end_time = sorted_matches[-1].timestamp
        
        # Zeitfenster
        time_windows = self._create_time_windows(start_time, end_time, period)
        
        # Aggregiere Marker-Counts gesamt
        total_points = []
        category_series = defaultdict(list)
        
        for window_start, window_end in time_windows:
            window_matches = [
                m for m in sorted_matches
                if window_start <= m.timestamp < window_end
            ]
            
            # Gesamt-Counts
            total_point = TimeSeriesPoint(
                timestamp=window_start,
                period_start=window_start,
                period_end=window_end,
                values={"marker_count": len(window_matches)},
                counts={"total": len(window_matches)}
            )
            
            # Counts nach Kategorie
            category_counts = defaultdict(int)
            for match in window_matches:
                category_counts[match.category.value] += 1
            
            total_point.counts.update(category_counts)
            total_points.append(total_point)
            
            # Separate Serien pro Kategorie
            for category in MarkerCategory:
                cat_count = category_counts.get(category.value, 0)
                cat_point = TimeSeriesPoint(
                    timestamp=window_start,
                    period_start=window_start,
                    period_end=window_end,
                    values={"count": cat_count},
                    counts={category.value: cat_count}
                )
                category_series[category.value].append(cat_point)
        
        # Erstelle Gesamt-Serie
        series_dict["markers_total"] = TimeSeriesData(
            series_id="markers_total",
            name="Total Marker Count",
            metric_type="count",
            period=period,
            data_points=total_points,
            statistics=self._calculate_series_statistics(total_points, "marker_count")
        )
        
        # Erstelle Kategorie-Serien
        for category, points in category_series.items():
            series_dict[f"markers_{category}"] = TimeSeriesData(
                series_id=f"markers_{category}",
                name=f"{category.replace('_', ' ').title()} Markers",
                metric_type="count",
                period=period,
                data_points=points,
                statistics=self._calculate_series_statistics(points, "count")
            )
        
        return series_dict
    
    def _create_time_windows(
        self,
        start: datetime,
        end: datetime,
        period: AggregationPeriod
    ) -> List[Tuple[datetime, datetime]]:
        """Erstellt Zeitfenster für Aggregation."""
        windows = []
        current = start
        
        while current < end:
            if period == AggregationPeriod.HOURLY:
                window_end = current + timedelta(hours=1)
            elif period == AggregationPeriod.DAILY:
                window_end = current + timedelta(days=1)
            elif period == AggregationPeriod.WEEKLY:
                window_end = current + timedelta(weeks=1)
            elif period == AggregationPeriod.MONTHLY:
                # Nächster Monat
                if current.month == 12:
                    window_end = current.replace(year=current.year + 1, month=1)
                else:
                    window_end = current.replace(month=current.month + 1)
            elif period == AggregationPeriod.QUARTERLY:
                # Nächstes Quartal
                quarter = (current.month - 1) // 3
                if quarter == 3:
                    window_end = current.replace(year=current.year + 1, month=1)
                else:
                    window_end = current.replace(month=(quarter + 1) * 3 + 1)
            elif period == AggregationPeriod.YEARLY:
                window_end = current.replace(year=current.year + 1)
            elif period == AggregationPeriod.CUSTOM:
                hours = self.config.custom_period_hours or 24
                window_end = current + timedelta(hours=hours)
            else:
                window_end = current + timedelta(days=1)
            
            windows.append((current, window_end))
            current = window_end
        
        return windows
    
    def _create_score_point(
        self,
        scores: List[ChunkScore],
        start: datetime,
        end: datetime,
        score_type: str
    ) -> TimeSeriesPoint:
        """Erstellt einen aggregierten Score-Punkt."""
        point = TimeSeriesPoint(
            timestamp=start,
            period_start=start,
            period_end=end
        )
        
        if scores:
            values = [s.normalized_score for s in scores]
            point.values = {
                "mean": np.mean(values),
                "min": min(values),
                "max": max(values),
                "std": np.std(values) if len(values) > 1 else 0,
                "median": np.median(values)
            }
            point.counts = {
                "chunk_count": len(scores),
                "confidence_avg": np.mean([s.confidence for s in scores])
            }
        else:
            # Keine Daten für diesen Zeitraum
            point.values = {
                "mean": 0,
                "min": 0,
                "max": 0,
                "std": 0,
                "median": 0
            }
            point.counts = {"chunk_count": 0}
        
        return point
    
    def _smooth_data_points(
        self,
        points: List[TimeSeriesPoint],
        metric: str
    ) -> List[TimeSeriesPoint]:
        """Glättet Datenpunkte mit Moving Average."""
        if len(points) <= self.config.smoothing_window:
            return points
        
        # Extrahiere Werte
        values = [p.values.get("mean", 0) for p in points]
        
        # Berechne Moving Average
        smoothed = []
        window = self.config.smoothing_window
        
        for i in range(len(values)):
            start_idx = max(0, i - window // 2)
            end_idx = min(len(values), i + window // 2 + 1)
            window_values = values[start_idx:end_idx]
            smoothed.append(np.mean(window_values))
        
        # Update Points
        for i, point in enumerate(points):
            point.values["mean_smoothed"] = smoothed[i]
        
        return points
    
    def _create_heatmaps(
        self,
        chunk_scores: List[ChunkScore],
        marker_matches: List[MarkerMatch],
        period: AggregationPeriod
    ) -> Dict[str, HeatmapData]:
        """Erstellt Heatmap-Daten."""
        heatmaps = {}
        
        # Marker-Kategorie Heatmap über Zeit
        category_heatmap = self._create_category_timeline_heatmap(
            marker_matches,
            period
        )
        if category_heatmap:
            heatmaps["marker_categories"] = category_heatmap
        
        # Score-Vergleich Heatmap
        score_heatmap = self._create_score_comparison_heatmap(
            chunk_scores,
            period
        )
        if score_heatmap:
            heatmaps["score_comparison"] = score_heatmap
        
        return heatmaps
    
    def _create_category_timeline_heatmap(
        self,
        matches: List[MarkerMatch],
        period: AggregationPeriod
    ) -> Optional[HeatmapData]:
        """Erstellt Heatmap für Marker-Kategorien über Zeit."""
        timed_matches = [m for m in matches if m.timestamp]
        if not timed_matches:
            return None
        
        # Zeitfenster
        start = min(m.timestamp for m in timed_matches)
        end = max(m.timestamp for m in timed_matches)
        windows = self._create_time_windows(start, end, period)
        
        # Matrix aufbauen
        categories = list(MarkerCategory)
        matrix = []
        x_labels = []
        
        for window_start, window_end in windows:
            window_matches = [
                m for m in timed_matches
                if window_start <= m.timestamp < window_end
            ]
            
            # Zähle pro Kategorie
            row = []
            for category in categories:
                count = sum(1 for m in window_matches if m.category == category)
                row.append(count)
            
            matrix.append(row)
            x_labels.append(window_start.strftime("%Y-%m-%d %H:%M"))
        
        # Transponiere für bessere Darstellung
        matrix = list(map(list, zip(*matrix)))
        
        return HeatmapData(
            title="Marker Categories Over Time",
            x_labels=x_labels,
            y_labels=[cat.value for cat in categories],
            values=matrix,
            color_scale="YlOrRd"
        )
    
    def _create_score_comparison_heatmap(
        self,
        chunk_scores: List[ChunkScore],
        period: AggregationPeriod
    ) -> Optional[HeatmapData]:
        """Erstellt Heatmap für Score-Vergleiche."""
        if not chunk_scores:
            return None
        
        # Gruppiere nach Score-Typ und Speaker
        score_matrix = defaultdict(lambda: defaultdict(list))
        
        for score in chunk_scores:
            if score.timestamp:
                speaker = score.metadata.get("speaker", "Unknown")
                score_matrix[score.score_type.value][speaker].append(score.normalized_score)
        
        if not score_matrix:
            return None
        
        # Erstelle Matrix
        score_types = list(score_matrix.keys())
        speakers = list(set(speaker for scores in score_matrix.values() for speaker in scores))
        
        matrix = []
        for score_type in score_types:
            row = []
            for speaker in speakers:
                scores = score_matrix[score_type].get(speaker, [])
                avg_score = np.mean(scores) if scores else 0
                row.append(avg_score)
            matrix.append(row)
        
        return HeatmapData(
            title="Average Scores by Type and Speaker",
            x_labels=speakers,
            y_labels=score_types,
            values=matrix,
            color_scale="RdYlGn_r"  # Reversed: Red=bad, Green=good
        )
    
    def _create_comparisons(
        self,
        time_series: Dict[str, TimeSeriesData]
    ) -> List[ComparisonData]:
        """Erstellt Vergleiche zwischen Zeitreihen."""
        comparisons = []
        
        # Vergleiche Score-Typen
        score_series = [
            ts for name, ts in time_series.items()
            if name.startswith("scores_")
        ]
        
        if len(score_series) > 1:
            comparison = ComparisonData(
                comparison_type="score_types",
                series=score_series
            )
            
            # Berechne Korrelationen
            if len(score_series[0].data_points) > 3:
                correlation_matrix = self._calculate_correlations(score_series)
                comparison.correlation_matrix = correlation_matrix
            
            comparisons.append(comparison)
        
        return comparisons
    
    def _calculate_correlations(
        self,
        series_list: List[TimeSeriesData]
    ) -> List[List[float]]:
        """Berechnet Korrelationsmatrix zwischen Zeitreihen."""
        # Extrahiere Werte
        value_arrays = []
        for series in series_list:
            values = [p.values.get("mean", 0) for p in series.data_points]
            value_arrays.append(values)
        
        # Berechne Korrelationen
        n = len(value_arrays)
        corr_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if len(value_arrays[i]) == len(value_arrays[j]):
                    corr = np.corrcoef(value_arrays[i], value_arrays[j])[0, 1]
                    corr_matrix[i][j] = float(corr) if not np.isnan(corr) else 0.0
                else:
                    corr_matrix[i][j] = 0.0
        
        return corr_matrix
    
    def _calculate_series_statistics(
        self,
        points: List[TimeSeriesPoint],
        main_metric: str
    ) -> Dict[str, Any]:
        """Berechnet Statistiken für eine Zeitreihe."""
        if not points:
            return {}
        
        # Extrahiere Hauptmetrik
        if main_metric in ["marker_count", "count"]:
            values = [p.values.get(main_metric, p.values.get("count", 0)) for p in points]
        else:
            values = [p.values.get("mean", 0) for p in points]
        
        non_zero_values = [v for v in values if v > 0]
        
        stats = {
            "total_periods": len(points),
            "non_zero_periods": len(non_zero_values),
            "average": np.mean(values) if values else 0,
            "std_dev": np.std(values) if len(values) > 1 else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "sum": sum(values) if values else 0
        }
        
        # Trend
        if len(values) > 2:
            first_third = np.mean(values[:len(values)//3])
            last_third = np.mean(values[-len(values)//3:])
            if last_third > first_third * 1.1:
                stats["trend"] = "increasing"
            elif last_third < first_third * 0.9:
                stats["trend"] = "decreasing"
            else:
                stats["trend"] = "stable"
        
        return stats
    
    def _calculate_summary_stats(
        self,
        time_series: Dict[str, TimeSeriesData]
    ) -> Dict[str, Dict[str, float]]:
        """Berechnet zusammenfassende Statistiken."""
        summary = {}
        
        for name, series in time_series.items():
            if series.statistics:
                summary[name] = {
                    "average": series.statistics.get("average", 0),
                    "trend": series.statistics.get("trend", "unknown"),
                    "periods": series.statistics.get("total_periods", 0),
                    "active_periods": series.statistics.get("non_zero_periods", 0)
                }
        
        return summary
    
    def _create_export_dataframe(
        self,
        time_series: Dict[str, TimeSeriesData]
    ) -> pd.DataFrame:
        """Erstellt DataFrame für Export."""
        if not time_series:
            return pd.DataFrame()
        
        # Sammle alle Datenpunkte
        all_data = []
        
        for series_name, series in time_series.items():
            for point in series.data_points:
                row = {
                    'timestamp': point.timestamp,
                    'period_start': point.period_start,
                    'period_end': point.period_end,
                    'series': series_name,
                    'metric_type': series.metric_type
                }
                
                # Füge Werte hinzu
                for key, value in point.values.items():
                    row[f"{series_name}_{key}"] = value
                
                # Füge Counts hinzu
                for key, count in point.counts.items():
                    row[f"{series_name}_{key}_count"] = count
                
                all_data.append(row)
        
        df = pd.DataFrame(all_data)
        
        # Pivotiere für bessere Darstellung
        if not df.empty:
            # Gruppiere nach Timestamp
            pivot_data = {}
            for _, row in df.iterrows():
                ts = row['timestamp']
                if ts not in pivot_data:
                    pivot_data[ts] = {'timestamp': ts}
                
                # Kopiere relevante Werte
                for col in row.index:
                    if col not in ['timestamp', 'period_start', 'period_end', 'series', 'metric_type']:
                        pivot_data[ts][col] = row[col]
            
            df = pd.DataFrame(list(pivot_data.values()))
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
        
        return df