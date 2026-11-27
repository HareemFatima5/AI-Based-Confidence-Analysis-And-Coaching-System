import argparse
import glob
import json
import os
import joblib
import numpy as np
import pandas as pd
from common import load_config, resolve, out_dir, model_dir, write_run_info
from extract import detect_video, frame_table, build_segment_rows, shoulders_ok
from features import frame_feature_matrix

ap = argparse.ArgumentParser()
ap.add_argument("--participants", nargs="*", default=None)
ap.add_argument("--videos", default=None)
ap.add_argument("--segments", default=None)
ap.add_argument("--gpu", action="store_true")
ap.add_argument("--force", action="store_true")
ap.add_argument("--max-seconds", type=float, default=None)
args = ap.parse_args()

cfg = load_config()
out = out_dir(cfg)
cache = out_dir(cfg, "cache")
frames_dir = out_dir(cfg, "frames")
vdir = args.videos or resolve(cfg, cfg["paths"]["videos"])
seg_path = args.segments or resolve(cfg, cfg["paths"]["segments"])
seg = pd.read_csv(seg_path)

model = None
feature_names = None
mpath = os.path.join(model_dir(cfg), "model.joblib")
if os.path.exists(mpath):
    model = joblib.load(mpath)
    with open(os.path.join(model_dir(cfg), "model_meta.json")) as f:
        feature_names = json.load(f)["features"]
else:
    print("posture_v0.1 not found, posture_prob will be empty")

participants = args.participants or list(dict.fromkeys(seg["participant"]))


def find_video(pid, kind):
    hits = sorted(glob.glob(os.path.join(vdir, f"{pid}_{kind}.*")))
    return hits[0] if hits else None


all_rows = []
for pid in participants:
    pseg = seg[seg["participant"] == pid]
    for kind in ["relaxed", "interview"]:
        vp = find_video(pid, kind)
        if vp is None:
            print(f"missing video {pid}_{kind}")
            continue
        cp = os.path.join(cache, f"{pid}_{kind}.npz")
        if os.path.exists(cp) and not args.force and args.max_seconds is None:
            z = np.load(cp, allow_pickle=True)
            times, lms, det, meta = z["times"], z["lms"], z["det"], json.loads(str(z["meta"]))
        else:
            times, lms, det, meta = detect_video(vp, cfg, use_gpu=args.gpu, max_seconds=args.max_seconds)
            if args.max_seconds is None:
                np.savez_compressed(cp, times=times, lms=lms, det=det, meta=json.dumps(meta))
        ft = frame_table(pid, kind, times, lms, det, cfg)
        if feature_names is not None and len(times):
            use = det & shoulders_ok(lms, cfg["hip_visibility_threshold"]) if len(times) else det
            mat = np.full((len(times), len(feature_names)), np.nan)
            if use.any():
                mat[use] = frame_feature_matrix(lms[use], feature_names)
            for k, n in enumerate(feature_names):
                ft[n] = mat[:, k]
        ft.to_csv(os.path.join(frames_dir, f"{pid}_{kind}_frames.csv"), index=False)
        rows = build_segment_rows(pid, kind, times, lms, det, meta, pseg, cfg, model, feature_names)
        all_rows.extend(rows)
        print(pid, kind, len(times), "frames", meta["duration_s"], "s")

cols = ["participant", "segment", "usable", "duration_s", "n_frames", "detection_rate", "short",
        "shoulder_instability", "shoulder_tilt_deg", "torso_lean_deg", "movement_speed",
        "head_height_ratio", "posture_prob", "module_version", "note"]
feat = pd.DataFrame(all_rows, columns=cols)
order = {n: i for i, n in enumerate(cfg["segment_names"])}
feat["_o"] = feat["segment"].map(order)
feat = feat.sort_values(["participant", "_o"]).drop(columns="_o")
feat.to_csv(os.path.join(out, "posture_features.csv"), index=False)
write_run_info(cfg, out, {"script": "07_extract_features.py", "participants": participants, "gpu_delegate": args.gpu})
print(feat.to_string(index=False))
