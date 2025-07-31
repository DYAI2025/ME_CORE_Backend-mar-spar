"""
CAL_BASELINE_PROFILE.py
Concrete baseline generator for:

• mean / stdev of speaker_valence
• average tokens per message
• emoji rate

Outputs JSON compatible with SCR / PROF modules.
"""

import re, json, argparse, statistics, datetime
from pathlib import Path

EMOJI_RE = re.compile(r"\p{Emoji}", re.UNICODE)

def analyse(messages):
    vals, tokens, emojis = [], [], 0
    for m in messages:
        txt = m.get("text", "")
        if "speaker_valence" in m:
            vals.append(m["speaker_valence"])
        tokens.append(len(txt.split()))
        emojis += len(EMOJI_RE.findall(txt))

    baseline = {
        "speaker_valence": {
            "mean": statistics.mean(vals) if vals else 0,
            "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0
        },
        "avg_tokens": statistics.mean(tokens) if tokens else 0,
        "emoji_rate": emojis / max(len(messages), 1),
        "generated_at": datetime.datetime.utcnow().isoformat()
    }
    return baseline

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chat", required=True, help="chat.json")
    ap.add_argument("--out",  required=True, help="baseline.json")
    a = ap.parse_args()

    data = json.loads(Path(a.chat).read_text(encoding="utf-8"))
    baseline = analyse(data["messages"])
    Path(a.out).write_text(json.dumps(baseline, indent=2))
    print("✅ baseline saved:", a.out)

if __name__ == "__main__":
    main()
