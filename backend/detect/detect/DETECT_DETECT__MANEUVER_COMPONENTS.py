import re

# ==============================================================================
# DEFINITION DER SEMANTISCHEN KOMPONENTEN
# Diese "Zutaten" machen das Hinhaltemanöver aus.
# ==============================================================================

MANEUVER_COMPONENTS = {
    "ZUSTIMMUNG_VORDERGRÜNDIG": [
        r"\b(ja klar|unbedingt|auf jeden fall|klingt super|gerne|tolle idee|wäre schön)\b"
    ],
    "VERANTWORTUNGS_VERSCHIEBUNG": [
        r"\b(du entscheidest|such du aus|was meinst du denn|was willst du denn|meld du dich|überrasch mich|wie du magst)\b"
    ],
    "VAGE_ZEITPLANUNG": [
        r"\b(mal schauen|später|irgendwann|bald|demnächst|bei Gelegenheit|im Auge behalten|eher spontan|lose anpeilen)\b"
    ],
    "ENTHUSIASTISCHE_UNVERBINDLICHKEIT": [
        r"\b(freu mich schon|unbedingt|riesig|total gern|auf jeden Fall)\b"
        # Dieser Marker wird stark, wenn er mit einer der anderen Komponenten kombiniert wird.
    ]
}

# ==============================================================================
# ANALYSEFUNKTION
# ==============================================================================

def detect_ambivalent_stalling(text: str) -> dict:
    """
    Analysiert einen Text semantisch auf das "Ambivalente Hinhaltemanöver".

    Die Funktion prüft, ob mehrere Komponenten des Manövers im Text vorkommen,
    um eine hohe Treffsicherheit zu gewährleisten.

    Args:
        text: Der zu analysierende Text (z.B. eine Chat-Nachricht, eine Aussage).

    Returns:
        Ein Dictionary mit dem Analyseergebnis.
    """
    found_components = set()
    
    # Durchsuche den Text nach jeder Komponente des Manövers
    for component_name, patterns in MANEUVER_COMPONENTS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_components.add(component_name)
                break  # Ein Treffer pro Komponente reicht

    score = len(found_components)
    is_detected = score >= 2  # Marker wird als erkannt gewertet, wenn mind. 2 Komponenten zutreffen

    analysis = {
        "marker_id": "AMBIVALENT_STALLING_MANEUVER",
        "is_detected": is_detected,
        "confidence_score": score / len(MANEUVER_COMPONENTS),
        "found_components": list(found_components)
    }

    if is_detected:
        explanation = "Die Aussage enthält mehrere Signale für ein Hinhaltemanöver. "
        if "ZUSTIMMUNG_VORDERGRÜNDIG" in found_components and "VERANTWORTUNGS_VERSCHIEBUNG" in found_components:
            explanation += "Einer scheinbaren Zustimmung folgt eine sofortige Rückgabe der Verantwortung."
        elif "ZUSTIMMUNG_VORDERGRÜNDIG" in found_components and "VAGE_ZEITPLANUNG" in found_components:
            explanation += "Eine positive Reaktion wird mit einer unverbindlichen Zeitangabe kombiniert, um eine konkrete Festlegung zu vermeiden."
        else:
            explanation += "Durch die Kombination verschiedener vager Elemente wird eine klare Zusage vermieden."
        analysis["explanation"] = explanation

    return analysis

# ==============================================================================
# DEMONSTRATION / ANWENDUNGSBEISPIEL
# ==============================================================================

if __name__ == "__main__":
    
    test_cases = [
        # Klassischer Fall: Zustimmung + Verantwortungs-Verschiebung
        "Ja klar, super Idee! Was schwebt dir denn so vor?",
        # Klassischer Fall: Zustimmung + vage Zeitplanung
        "Uhm, ja, unbedingt. Lass uns das mal im Auge behalten und dann eher spontan schauen.",
        # Subtiler Fall: Enthusiasmus + Verantwortungs-Verschiebung
        "Auf jeden Fall! Freu mich schon riesig. Melde dich einfach, wenn du losfährst!",
        # Nur eine Komponente -> sollte nicht erkannt werden
        "Vielleicht könnten wir ins Kino gehen.",
        # Eindeutige Zusage -> sollte nicht erkannt werden
        "Ja, lass uns am Samstag um 19 Uhr ins Kino gehen. Ich buche die Karten.",
        # Komplexerer Fall
        "Ich würde total gern mitkommen! Ich muss nur mal schauen, wie lange ich arbeiten muss. Sag du doch mal, wann es dir am besten passen würde."
    ]

    print("--- Semantische Analyse auf Hinhaltemanöver ---\n")

    for i, text in enumerate(test_cases):
        result = detect_ambivalent_stalling(text)
        print(f"Testfall #{i+1}: \"{text}\"")
        if result["is_detected"]:
            print(f"  ▶️ Marker erkannt: JA")
            print(f"  ▶️ Erklärung: {result.get('explanation', 'N/A')}")
            print(f"  ▶️ Gefundene Komponenten: {result['found_components']}")
        else:
            print(f"  ▶️ Marker erkannt: NEIN (Nur {len(result['found_components'])}/2 Komponenten gefunden)")
        print("-" * 50)