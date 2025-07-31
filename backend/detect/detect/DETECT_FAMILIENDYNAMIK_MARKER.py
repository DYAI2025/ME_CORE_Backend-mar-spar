import re

FAMILIENDYNAMIK_PATTERNS = [
    r"(typisch für unsere familie|du bist das schwarze schaf|oma hat dich immer bevorzugt|beim erbe leer ausgegangen|du klingst wie mutter|in dieser familie|deine sturheit kommt von papa|geschichten von vor 20 jahren|ich bin immer der kleine bruder|friedensstifter in dieser familie|maßregelst mich vor meinen kindern|wir halten nur zusammen, weil wir müssen|hier wird erfolg misstrauisch beäugt|keiner redet tacheles|hinterrücks gelästert|nie 'ich liebe dich' gesagt|bei uns wurde nichts ausgesprochen|jede feier endet im streit|du behandelst mich wie 12|älteste bestimmt immer|keiner hört mir zu|das perfekte familienbild|du warst nie da, als ich dich gebraucht habe)"
]

def detect_family_dynamics(text):
    for pattern in FAMILIENDYNAMIK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
