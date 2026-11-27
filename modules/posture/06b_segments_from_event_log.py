import argparse
import os
import pandas as pd
from common import load_config, resolve

ap = argparse.ArgumentParser()
ap.add_argument("--events", required=True)
ap.add_argument("--out", default=None)
ap.add_argument("--durations", default=None)
args = ap.parse_args()

cfg = load_config()
ev = pd.read_csv(args.events)
durations = {}
if args.durations:
    d = pd.read_csv(args.durations)
    durations = dict(zip(d["participant"], d["duration_interview_s"]))

rows = []
for pid, g in ev.groupby("participant", sort=False):
    rows.append({"participant": pid, "segment": "relaxed", "start_s": 0.0, "end_s": "", "notes": "whole recording"})
    for k in range(1, 5):
        name = f"B{k}"
        gq = g[g["question"] == k]
        qend = gq.loc[gq["event"] == "question_end", "t_s"]
        if qend.empty:
            rows.append({"participant": pid, "segment": name, "start_s": "", "end_s": "", "notes": "missing question_end"})
            continue
        start = float(qend.iloc[0])
        limits = [start + cfg["max_segment_s"]]
        done = gq.loc[gq["event"] == "done_click", "t_s"]
        if not done.empty:
            limits.append(float(done.iloc[0]))
        nxt = g[(g["question"] == k + 1) & (g["event"] == "question_start")]["t_s"]
        if not nxt.empty:
            limits.append(float(nxt.iloc[0]))
        if pid in durations:
            limits.append(float(durations[pid]))
        rows.append({"participant": pid, "segment": name, "start_s": round(start, 2), "end_s": round(min(limits), 2), "notes": "from app event log"})

seg = pd.DataFrame(rows, columns=["participant", "segment", "start_s", "end_s", "notes"])
dest = args.out or resolve(cfg, cfg["paths"]["segments"])
os.makedirs(os.path.dirname(dest), exist_ok=True)
seg.to_csv(dest, index=False)
print(seg.to_string(index=False))
