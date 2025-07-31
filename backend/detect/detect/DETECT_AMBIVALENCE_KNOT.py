import re

AMBIVALENCE_KNOT_PATTERNS = [
    r"(ich will .* aber|unbedingt .* aber|hilf mir .* aber lass|komm her .* aber lass mich|ich brauche dich .* aber|bleib .* aber|geh .* aber|ich liebe dich .* aber|ich hasse es .* aber|ich freue mich .* aber)",
    r"(kann nicht mit dir .* kann nicht ohne dich|will ehrlich sein .* kann es aber nicht|möchte dich sehen .* habe angst davor|nähe .* aber brauche abstand|will teilen .* aber nicht alles|ich bin froh .* aber es wäre besser, wenn du gehst|ich habe die entscheidung getroffen zu gehen .* aber kann die tür nicht zumachen)",
    r"(bitte komm .* aber erwarte nicht|melde dich .* aber nicht jetzt|ich ersticke .* aber du sollst nicht gehen|ich vertraue dir .* aber misstraue trotzdem)"
]

def detect_ambivalence_knot(text):
    for pattern in AMBIVALENCE_KNOT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return True
    return False
