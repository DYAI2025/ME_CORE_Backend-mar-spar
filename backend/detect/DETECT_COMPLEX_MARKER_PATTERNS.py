import re
from collections import defaultdict

# ==============================================================================
# DEFINITION DER MUSTER FÜR KOMPLEXE METAMARKER
# Diese Muster basieren auf den zuvor generierten 20 Beispielen für jeden Marker.
# ==============================================================================

COMPLEX_MARKER_PATTERNS = {
    "REACTIVE_CONTROL_SPIRAL": [
        r"\b(ich bin (im moment|einfach) zu .* für dich)\b",
        r"\b(vielleicht sollte ich mich .* zurückziehen)\b",
        r"\b(mach dir keine sorgen um mich)\b",
        r"\b(ist mein problem, nicht deins)\b",
        r"\b(bin es gewohnt .* allein zu sein)\b",
        r"\b(will dem erfolg ja nicht im weg stehen)\b",
        r"\b(will keine große sache draus machen)\b",
        r"\b(tu einfach, was dich glücklich macht)\b",
        r"\b(ich bin die komplizierte)\b",
        r"\b(entschuldigung für die eigene existenz|entschuldige dass ich so bin)\b"
    ],
    "LIE_CONCEALMENT_MARKER": [
        r"\b(nicht so wichtig|nichts besonderes|nichts von belang)\b",
        r"\b(lange geschichte für einen anderen tag)\b",
        r"\b(warum ist das (jetzt|so) wichtig|warum willst du das wissen)\b",
        r"\b(nicht mehr (ganz )?sicher, wie das war)\b",
        r"\b(thema wechseln|nicht darüber sprechen)\b",
        r"\b(das ist kompliziert|du würdest es nicht verstehen)\b",
        r"\b(geht dich nichts an|meine privatsphäre)\b",
        r"\b(du verhörst mich|fühl mich wie im verhör)\b",
        r"\b(verwechselst da was)\b",
        r"\b(erledigt\. punkt\.)\b"
    ],
    "SEMANTISCHER_NEBEL": [
        # Sucht nach einer Häufung von abstrahierenden oder pseudo-intellektuellen Begriffen
        r"\b(konstrukt|dynamik|metaebene|struktur|energetische signatur|projektion)\b",
        r"\b(algorithisch|schleife|phänomen|ontologisch|archetypisch|binäre antwort)\b",
        r"\b(spektrum|osmotisch|systemisch|dialektik|resonanzraum|ambiguität)\b",
        r"\b(manifestiert sich|mitschwingt|konstellation|re-kalibrierung)\b"
    ],
    "DRAMA_TRIANGLE_MARKER": {
        # Dieser Marker wird erkannt, wenn Muster aus mind. 2 unterschiedlichen Rollen gefunden werden.
        "VERFOLGER": [
            r"\b(schon wieder du|wegen dir|deine schuld|typisch du)\b",
            r"\b(du bist das problem|unfähig|egoistisch|rücksichtslos)\b",
            r"\b(hör auf zu jammern|reiß dich zusammen)\b",
            r"\b(ich habs dir doch gesagt)\b"
        ],
        "OPFER": [
            r"\b(immer ich|warum immer mir|niemand (hilft|versteht) mir)\b",
            r"\b(ich bin (am ende|überfordert|zu schwach|die last))\b",
            r"\b(ich opfere mich auf|bekomme nur undankbarkeit)\b",
            r"\b(ich bin der sündenbock|kann nichts dafür)\b"
        ],
        "RETTER": [
            r"\b(lass mich das machen|ich regel das schon)\b",
            r"\b(komm her, du arme|ich helfe dir)\b",
            r"\b(ich rette dich|ich bügle das wieder aus)\b",
            r"\b(ohne mich geht es nicht|jemand muss es ja machen)\b"
        ]
    }
}

# ==============================================================================
# ANALYSEFUNKTIONEN
# ==============================================================================

def analyze_text_for_complex_markers(text: str) -> dict:
    """
    Analysiert einen Text auf das Vorhandensein der vier komplexen Metamarker.

    Args:
        text: Der zu analysierende Text.

    Returns:
        Ein Dictionary, das die erkannten Marker und die gefundenen Treffer auflistet.
    """
    results = defaultdict(list)

    # --- Test für einfache Marker (Kontrollspirale, Lügen, Nebel) ---
    simple_markers_to_check = ["REACTIVE_CONTROL_SPIRAL", "LIE_CONCEALMENT_MARKER"]
    for marker_name in simple_markers_to_check:
        for pattern in COMPLEX_MARKER_PATTERNS[marker_name]:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                results[marker_name].append(match.group(0).strip())

    # --- Test für Semantischen Nebel (basierend auf Worthäufigkeit) ---
    fog_hits = []
    for pattern in COMPLEX_MARKER_PATTERNS["SEMANTISCHER_NEBEL"]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            fog_hits.append(match.group(0).strip())
    if len(fog_hits) >= 2:  # Wird als erkannt gewertet, wenn mind. 2 Nebel-Wörter vorkommen
        results["SEMANTISCHER_NEBEL"] = fog_hits
        
    # --- Spezieller Test für Dramadreieck (Rollen-Rotation) ---
    detected_roles = set()
    role_hits = []
    for role, patterns in COMPLEX_MARKER_PATTERNS["DRAMA_TRIANGLE_MARKER"].items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                detected_roles.add(role)
                role_hits.append(f"{role}: '{match.group(0).strip()}'")
    
    # Wird erkannt, wenn Muster aus mindestens zwei verschiedenen Rollen gefunden werden.
    if len(detected_roles) >= 2:
        results["DRAMA_TRIANGLE_MARKER"] = role_hits

    return dict(results)

# ==============================================================================
# DEMONSTRATION / ANWENDUNGSBEISPIEL
# ==============================================================================

if __name__ == "__main__":
    
    # --- Testfälle für jeden der vier Marker ---

    test_reactive_control = "Mach dir keine Sorgen um mich. Ich bin es gewohnt, allein zu sein. Ist mein Problem, nicht deins."
    
    test_drama_triangle = "Immer ich muss alles machen! (Opfer) Aber gut, ich helfe dir ja gerne. (Retter) Wenn du nur nicht so unfähig wärst! (Verfolger)"
    
    test_lie_concealment = "Warum willst du das jetzt wissen? Das ist nicht so wichtig. Lass uns bitte das Thema wechseln."
    
    test_semantic_fog = "Es geht hier nicht um Gefühle, sondern um die systemische Dynamik, die sich in unserer Interaktion manifestiert. Das ist ein komplexes Phänomen."

    print("--- STARTE ANALYSE FÜR KOMPLEXE METAMARKER ---\n")

    # --- Analyse durchführen und Ergebnisse ausgeben ---
    
    print("1. Test für: REACTIVE_CONTROL_SPIRAL")
    results1 = analyze_text_for_complex_markers(test_reactive_control)
    print(f"   Input: '{test_reactive_control}'")
    print(f"   Ergebnis: {results1}\n")

    print("-" * 50)
    
    print("2. Test für: DRAMA_TRIANGLE_MARKER")
    results2 = analyze_text_for_complex_markers(test_drama_triangle)
    print(f"   Input: '{test_drama_triangle}'")
    print(f"   Ergebnis: {results2}\n")
    
    print("-" * 50)
    
    print("3. Test für: LIE_CONCEALMENT_MARKER")
    results3 = analyze_text_for_complex_markers(test_lie_concealment)
    print(f"   Input: '{test_lie_concealment}'")
    print(f"   Ergebnis: {results3}\n")
    
    print("-" * 50)
    
    print("4. Test für: SEMANTISCHER_NEBEL")
    results4 = analyze_text_for_complex_markers(test_semantic_fog)
    print(f"   Input: '{test_semantic_fog}'")
    print(f"   Ergebnis: {results4}\n")