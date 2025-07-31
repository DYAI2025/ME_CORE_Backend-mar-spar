import re

CO_REGULATION_COLLAPSE_PATTERNS = [
    r"(ich kann nicht mehr|du auch nicht mehr|wir kommen nicht weiter|ich gebe auf|es ist alles gesagt|das gespräch ist beendet|wir schweigen uns an|lass mich einfach in ruhe|ich kapituliere|genug|wir haben uns festgefahren|jeder macht seins|es macht alles nur schlimmer|ich klinke mich aus|keine kraft mehr|wie mit einer wand reden)",
    r"(wir verletzen uns nur noch|wir drehen uns im kreis|es bleibt nur noch rückzug|wir sind beide raus|kommunikation (bricht|abgebrochen)|beide geben auf|nur noch schweigen|gegenseitiger rückzug|es gibt nichts mehr zu sagen|du gewinnst)"
]

def detect_co_regulation_collapse(text):
    for pattern in CO_REGULATION_COLLAPSE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
