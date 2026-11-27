import argparse
import difflib
import glob
import json
import os
import re
import pandas as pd
from common import load_config, resolve, out_dir, write_run_info

ap = argparse.ArgumentParser()
ap.add_argument("--videos", default=None)
ap.add_argument("--participants", nargs="*", default=None)
ap.add_argument("--whisper-model", default="medium")
ap.add_argument("--language", default=None)
ap.add_argument("--min-score", type=float, default=0.5)
ap.add_argument("--cpu", action="store_true")
args = ap.parse_args()

cfg = load_config()
vdir = args.videos or resolve(cfg, cfg["paths"]["videos"])
out = out_dir(cfg)
os.makedirs(os.path.join(out, "transcripts"), exist_ok=True)

from faster_whisper import WhisperModel

device = "cpu" if args.cpu else "cuda"
compute = "int8" if args.cpu else "float16"
try:
    model = WhisperModel(args.whisper_model, device=device, compute_type=compute)
except Exception:
    model = WhisperModel(args.whisper_model, device="cpu", compute_type="int8")


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()


def best_window(segs, question, start_idx, max_len=4):
    q = norm(question)
    best = (0.0, None, None)
    for i in range(start_idx, len(segs)):
        text = ""
        for j in range(i, min(i + max_len, len(segs))):
            text = (text + " " + segs[j]["text"]).strip()
            score = difflib.SequenceMatcher(None, norm(text), q).ratio()
            if score > best[0]:
                best = (score, i, j)
    return best


files = sorted(glob.glob(os.path.join(vdir, "*_interview.*")))
if args.participants:
    files = [f for f in files if os.path.basename(f).split("_")[0] in args.participants]

rows = []
for f in files:
    pid = os.path.basename(f).split("_")[0]
    segments, info = model.transcribe(f, task="translate", language=args.language, vad_filter=True, beam_size=5)
    segs = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
    with open(os.path.join(out, "transcripts", f"{pid}_interview_translated.json"), "w") as fh:
        json.dump({"language": info.language, "duration": info.duration, "segments": segs}, fh, indent=1)
    duration = float(info.duration)
    found = {}
    cursor = 0
    for name in ["B1", "B2", "B3", "B4"]:
        score, i, j = best_window(segs, cfg["questions"][name], cursor)
        if i is not None and score >= args.min_score:
            found[name] = {"q_start": segs[i]["start"], "q_end": segs[j]["end"], "score": score}
            cursor = j + 1
        else:
            found[name] = None
    rows.append({"participant": pid, "segment": "relaxed", "start_s": 0.0, "end_s": "", "notes": "whole recording"})
    names = ["B1", "B2", "B3", "B4"]
    for k, name in enumerate(names):
        if found[name] is None:
            rows.append({"participant": pid, "segment": name, "start_s": "", "end_s": "", "notes": "question not found, set by hand"})
            continue
        start = found[name]["q_end"]
        nxt = None
        for n2 in names[k + 1:]:
            if found[n2] is not None:
                nxt = found[n2]["q_start"]
                break
        end = min(start + cfg["max_segment_s"], nxt if nxt is not None else duration, duration)
        rows.append({"participant": pid, "segment": name, "start_s": round(start, 2), "end_s": round(end, 2),
                     "notes": f"drafted, match {found[name]['score']:.2f}, check by hand"})

draft = pd.DataFrame(rows, columns=["participant", "segment", "start_s", "end_s", "notes"])
draft.to_csv(os.path.join(out, "segments_draft.csv"), index=False)
write_run_info(cfg, out, {"script": "06_draft_segments.py", "whisper_model": args.whisper_model})
print(draft.to_string(index=False))
