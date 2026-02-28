# Build a simple LED cue JSON by waypoint index ranges
import json, sys

if __name__ == "__main__":
    # Usage: python make_led_cues.py 0:25:#00A3FF:solid 26:60:#FF006E:blink cues.json
    *ranges, out = sys.argv[1:]
    cues = []
    for spec in ranges:
        a,b,color,mode = spec.split(":")
        cues.append({"from":int(a), "to":int(b), "color":color, "mode":mode})
    doc = {"global_defaults":{"mode":"solid","color":"#FFFFFF","brightness":0.5}, "cues":cues}
    with open(out,"w") as f:
        json.dump(doc,f,indent=2)
    print(f"Wrote LED cues to {out}")
