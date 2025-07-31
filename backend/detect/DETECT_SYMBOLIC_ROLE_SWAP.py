import re

# Hinweis: Für sehr gute Erkennung ggf. Named Entity Recognition/Spacy etc. nutzen.
# Hier: Typische Muster für übertragene Objekte/Projektionen.
SYMBOLIC_ROLE_SWAP_PATTERNS = [
    r"(pflanze|haustier|hund|katze|fisch|socke|tasse|baum|navi|auto|akku|rad|gerät|kopfhörer|blume|radio|projekt|tür|fenster|wlan|handy|gerät|dokument|puzzleteil|ast|fahrrad|bank|sessel)",
    r"(funktioniert nicht|springt nicht an|bleibt stehen|eiert|schwimmt im kreis|geht kaputt|quietscht|reagiert nicht|leiser|verliert die balance|scheitert|einsam|geht leer aus|wird nie voll|ist nie synchron)",
    r"(als ob|wie wenn|genau wie|typisch für|kommt mir vor wie|es ist wie|fühlt sich an wie)"
]

def detect_symbolic_role_swap(text):
    for pattern in SYMBOLIC_ROLE_SWAP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
