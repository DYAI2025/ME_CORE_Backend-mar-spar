import re

REACTIVE_CONTROL_SPIRAL_PATTERNS = [
    r"(du hast angefangen|nein, du hast angefangen|du willst stur sein|ich kann sturer sein|jedes mal, wenn ich|toll, weil du eingeschnappt bist, bin ich jetzt auch eingeschnappt|ich gehe erst einen schritt, wenn du einen gehst|ich senke meinen ton erst, wenn du deinen senkst|ich schreie durch die tür|du manipulierst|nein, du zwingst mich dazu|wenn du provozierst, kann ich für nichts garantieren|du willst es auf die harte tour|solange du dich nicht entschuldigst, entschuldige ich mich auch nicht|kontrolle behalten|es endet erst, wenn einer aufgibt)",
    r"(du willst ehrlich sein, okay, hier ist die ehrliche meinung|du bist das problem|du willst immer das letzte wort|ich hab dir zehnmal geschrieben|ich ignoriere jetzt mal deine anrufe|jeder deiner vorwürfe gibt mir nur mehr munition)"
]

def detect_reactive_control_spiral(text):
    for pattern in REACTIVE_CONTROL_SPIRAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
