"""
Childhood Attachment Detector & Analysis Schema
================================================
This single Python module provides **both**:
1.  A detector skeleton (`ChildhoodAttachmentDetector`) that follows the 5‑Phasen‑Flow you described.
2.  An embedded YAML string (`SCHEMA_YAML`) that can be written out or loaded via the existing
    `schema_loader` util to register the analysis‑schema in your pipeline.

Feel free to split this file later; it is kept together here to obey the
single‑file canvas rule.
"""

from __future__ import annotations
import math
from collections import defaultdict, deque
from statistics import mean, pstdev
from typing import List, Dict, Deque, Tuple, Any

# ---------------------------------------------------------------------------
# Helper data structures (adjust to match your real Marker/Detector framework)
# ---------------------------------------------------------------------------

class Marker:
    """Lightweight marker placeholder."""

    def __init__(self, marker_id: str, position: int, count: int = 1):
        self.id = marker_id
        self.position = position  # token offset in full conversation
        self.count = count

    def to_dict(self) -> Dict[str, Any]:
        return {"marker": self.id, "pos": self.position, "count": self.count}


# Mapping der vier Atomic‑Typen → Listen existierender Marker‑IDs
ATOMIC_CHILDHOOD_MARKERS: Dict[str, List[str]] = {
    "positive": ["CH_POSITIVE_NOSTALGIA", "CH_PLAYFUL_MEMORY"],
    "negative": ["CH_NEGLECT", "CH_TRAUMA_MENTION"],
    "self_reliant": ["CH_EARLY_AUTONOMY"],
    "unvorhersehbar": ["CH_CHAOTIC_FAMILY"],
}

# Trigger‑Schwelle für Drift (Phase ③)
DRIFT_THRESHOLD = 0.25  # ≥ 25 % Abweichung von Baseline‑Quote


class ChildhoodAttachmentDetector:
    """Detector implementing Baseline → Drift → Cluster → Meta pipeline."""

    def __init__(
        self,
        baseline_tokens: int = 1000,
        baseline_msgs: int = 30,
        drift_window_tokens: int = 200,
    ) -> None:
        self.baseline_tokens = baseline_tokens
        self.baseline_msgs = baseline_msgs
        self.drift_window_tokens = drift_window_tokens

        # state
        self._token_counter: int = 0
        self._msg_counter: int = 0
        self._baseline_counts: Dict[str, int] = defaultdict(int)
        self._baseline_completed: bool = False

        # sliding window for drift detection: deque of (token_count, marker_type)
        self._drift_window: Deque[Tuple[int, str]] = deque()
        self._drift_counts: Dict[str, int] = defaultdict(int)

        # rolling window for cluster aggregation (Phase ④)
        self._cluster_window_msgs: Deque[str] = deque(maxlen=15)

        # attachment style votes across chunks (Phase ⑤)
        self._active_clusters: List[str] = []

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def ingest_message(self, tokens: List[str], detected_markers: List[Marker]) -> List[Marker]:
        """Call once per incoming chat message.

        Returns list of *newly* triggered semantic/cluster/meta markers.
        """
        n_tokens = len(tokens)
        self._token_counter += n_tokens
        self._msg_counter += 1

        triggered: List[Marker] = []

        # --------------------------------------------------------------
        # Phase ① + ② – Baseline collection until thresholds reached
        # --------------------------------------------------------------
        if not self._baseline_completed:
            self._update_counts(self._baseline_counts, detected_markers)
            if (
                self._token_counter >= self.baseline_tokens
                or self._msg_counter >= self.baseline_msgs
            ):
                self._baseline_completed = True
                # After baseline complete → compute z‑scores & attach style cluster
                z_scores = self._calculate_z_scores(self._baseline_counts)
                style_cluster = self._classify_attachment_style(z_scores)
                triggered.append(Marker(style_cluster, self._token_counter))
                self._active_clusters.append(style_cluster)
            return triggered  # no drift detection before baseline is fixed

        # --------------------------------------------------------------
        # Phase ③ – Drift detection (sliding window by token)
        # --------------------------------------------------------------
        self._update_counts(self._drift_counts, detected_markers)
        self._drift_window.extend((self._token_counter, m_type) for m_type in self._marker_types(detected_markers))
        # prune window
        while self._drift_window and (self._token_counter - self._drift_window[0][0]) > self.drift_window_tokens:
            _, old_type = self._drift_window.popleft()
            self._drift_counts[old_type] -= 1

        drift_triggered = self._check_drift()
        if drift_triggered:
            triggered.append(Marker("S_CHILDHOOD_DRIFT", self._token_counter))

        # --------------------------------------------------------------
        # Phase ④ – Cluster aggregation (15 message window)
        # --------------------------------------------------------------
        cluster_marker = self._update_cluster_window(drift_triggered)
        if cluster_marker:
            triggered.append(Marker(cluster_marker, self._token_counter))
            self._active_clusters.append(cluster_marker)

        # --------------------------------------------------------------
        # Phase ⑤ – Meta condensation
        # --------------------------------------------------------------
        if len(self._active_clusters) >= 2:
            triggered.append(Marker("MM_ATTACHMENT_PROFILE", self._token_counter))
            # reset to avoid spamming every message
            self._active_clusters = []

        return triggered

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_counts(self, counter: Dict[str, int], markers: List[Marker]) -> None:
        for m_type in self._marker_types(markers):
            counter[m_type] += 1

    def _marker_types(self, markers: List[Marker]) -> List[str]:
        """Map concrete marker‑IDs to their atomic childhood type label."""
        types: List[str] = []
        for mk in markers:
            for t, lst in ATOMIC_CHILDHOOD_MARKERS.items():
                if mk.id in lst:
                    types.append(t)
        return types

    # -------------------- Phase ② helpers -----------------------------

    def _calculate_z_scores(self, counts: Dict[str, int]) -> Dict[str, float]:
        values = list(counts.values())
        mu = mean(values)
        sigma = pstdev(values) or 1.0
        return {k: (v - mu) / sigma for k, v in counts.items()}

    def _classify_attachment_style(self, z_scores: Dict[str, float]) -> str:
        """Very naive rule‑based classifier (replace with ML model)."""
        if z_scores.get("positive", 0) >= 1.0 and z_scores.get("negative", 0) < 0:
            return "C_ATTACHMENT_STYLE_SECURE"
        if z_scores.get("self_reliant", 0) >= 1.0:
            return "C_ATTACHMENT_STYLE_AVOIDANT"
        if z_scores.get("negative", 0) >= 1.0:
            return "C_ATTACHMENT_STYLE_ANXIOUS"
        return "C_ATTACHMENT_STYLE_MIXED"

    # -------------------- Phase ③ helpers -----------------------------

    def _check_drift(self) -> bool:
        total_baseline = sum(self._baseline_counts.values()) or 1
        total_window = sum(self._drift_counts.values()) or 1
        # compare relative frequencies
        for t in ATOMIC_CHILDHOOD_MARKERS.keys():
            base_q = self._baseline_counts[t] / total_baseline
            win_q = self._drift_counts[t] / total_window
            if abs(win_q - base_q) >= DRIFT_THRESHOLD:
                return True
        return False

    # -------------------- Phase ④ helpers -----------------------------

    def _update_cluster_window(self, new_drift: bool) -> str | None:
        self._cluster_window_msgs.append("DRIFT" if new_drift else "-")
        # simplistic aggregation: if at least 1 DRIFT in window, assume insecure style
        if "DRIFT" in self._cluster_window_msgs:
            return "C_ATTACHMENT_STYLE_INSECURE"
        return None


# ---------------------------------------------------------------------------
# Embedded YAML schema describing the full analysis pipeline
# ---------------------------------------------------------------------------

SCHEMA_YAML = """
schema_version: "1.0"
analysis_type: "childhood_attachment_profile"
meta:
  generated_at: 2025-07-21
  author: detector_childhood_attachment.py

phases:
  - id: baseline_capture
    window:
      tokens: 1000
      messages: 30
    description: |
      Collect frequencies of childhood‑reference atomic markers as baseline.

  - id: profile_calculation
    z_score_threshold: 1.0
    classifier: AttachmentStyleRuleBased

  - id: drift_detection
    window_tokens: 200
    drift_threshold: 0.25
    semantic_marker: S_CHILDHOOD_DRIFT

  - id: cluster_aggregation
    window_messages: 15
    boolean_logic: "ANY"
    cluster_markers:
      secure: C_ATTACHMENT_STYLE_SECURE
      avoidant: C_ATTACHMENT_STYLE_AVOIDANT
      anxious: C_ATTACHMENT_STYLE_ANXIOUS
      insecure_mix: C_ATTACHMENT_STYLE_INSECURE

  - id: meta_condensation
    rule: ">= 2 CLUSTER markers active simultaneously"
    meta_marker: MM_ATTACHMENT_PROFILE

markers_in_scope:
  atomic:
    positive: [CH_POSITIVE_NOSTALGIA, CH_PLAYFUL_MEMORY]
    negative: [CH_NEGLECT, CH_TRAUMA_MENTION]
    self_reliant: [CH_EARLY_AUTONOMY]
    unvorhersehbar: [CH_CHAOTIC_FAMILY]

  semantic:
    - S_CHILDHOOD_DRIFT

  cluster:
    - C_ATTACHMENT_STYLE_SECURE
    - C_ATTACHMENT_STYLE_AVOIDANT
    - C_ATTACHMENT_STYLE_ANXIOUS
    - C_ATTACHMENT_STYLE_INSECURE

  meta:
    - MM_ATTACHMENT_PROFILE

accumulation_logic:
  baseline_to_profile:
    z_score: true
    classifier: AttachmentStyleRuleBased
  drift_trigger:
    compare_with: baseline
    metric: relative_frequency
    threshold: 0.25
  cluster_window:
    size_messages: 15
    logic: any
  meta_trigger:
    cluster_active_count: ">=2"

outputs:
  attachment_profile:
    anxious: 0.0
    avoidant: 0.0
    secure: 0.0
  drift_events: []
  meta_markers: []
"""

# ---------------------------------------------------------------------------
# Convenience write‑out helper (optional)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with open("childhood_attachment_schema.yaml", "w", encoding="utf-8") as fh:
        fh.write(SCHEMA_YAML)
    print("✅  Schema saved to childhood_attachment_schema.yaml")
