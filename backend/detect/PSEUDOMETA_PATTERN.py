import re

PSEUDOMETA_PATTERN_PATTERNS = [
    r"(metaebene|kommunikationsmatrix|semantik|axiome|double-bind|projektionen|beziehungsebene|interaktionsmuster|wir reden aneinander vorbei|das ist kein inhaltliches, sondern ein beziehungsproblem|unsere begrifflichkeiten klären|wir analysieren nur|symptom für ein strukturelles problem|die art, wie wir streiten, ist ein spiegel|sprachliche ebene|supervision für kommunikation|wir sprechen unterschiedliche sprachen der liebe)",
    r"(wir sollten nicht über den müll reden, sondern über das symbol dahinter|das eigentliche thema ist größer|soziologisch hochinteressant|wir sind beide nur schauspieler in einem drama|strukturproblem, kein gefühlsproblem)"
]

def detect_pseudometa_pattern(text):
    for pattern in PSEUDOMETA_PATTERN_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
