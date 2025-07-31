import re

RESONANCE_PATTERNS = [
    r"(ich verstehe dich|ich sehe dich|ich fühle mit dir|wow, das eröffnet mir eine neue perspektive|das kenne ich auch|mir geht es genauso|ich urteile nicht|ich höre dir zu|danke, dass du das sagst|du sprichst mir aus der seele|ich fühle mich verbunden|du gibst mir neue einsicht|das ergibt sinn|genau das ist der punkt|ich bin froh, dass du es aussprichst|deine worte berühren mich|du bist nicht allein damit|ich kann zu 100 prozent nachfühlen)",
    r"(das fühlt sich so wahr an|ich muss dir nicht mal zustimmen, aber ich verstehe dich|ich kann dir keine lösung geben, aber ich bin da|die energie hat sich gerade verändert|du bist wirklich gesehen)"
]

def detect_resonance(text):
    for pattern in RESONANCE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
