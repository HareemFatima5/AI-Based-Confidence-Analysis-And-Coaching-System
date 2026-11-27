import glob
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import load_config, resolve, out_dir, write_run_info, load_confidetect, prepare_dataset

cfg = load_config()
out = out_dir(cfg)
feat = pd.read_csv(os.path.join(out, "posture_features.csv"))

bad = feat[~feat["usable"].astype(bool)].copy()
bad["reason"] = bad["note"].fillna("")
bad[["participant", "segment", "duration_s", "n_frames", "detection_rate", "short", "reason"]].to_csv(
    os.path.join(out, "exclusions_posture.csv"), index=False)

summary = pd.DataFrame({
    "segments_total": [len(feat)],
    "segments_usable": [int(feat["usable"].sum())],
    "segments_excluded": [int((~feat["usable"].astype(bool)).sum())],
    "excluded_low_detection": [int(feat["note"].fillna("").str.contains("low_detection").sum())],
    "excluded_short": [int(feat["short"].sum())],
    "torso_lean_empty": [int(feat["note"].fillna("").str.contains("torso_lean_empty").sum())],
    "mean_detection_rate": [float(feat["detection_rate"].mean())],
})
summary.to_csv(os.path.join(out, "quality_summary_posture.csv"), index=False)

seg_path = resolve(cfg, cfg["paths"]["segments"])
seg = pd.read_csv(seg_path) if os.path.exists(seg_path) else None

plots = out_dir(cfg, "detection_plots")
frame_files = sorted(glob.glob(os.path.join(out, "frames", "*_frames.csv")))
all_frames = []
for fp in frame_files:
    fr = pd.read_csv(fp)
    all_frames.append(fr)
    pid = fr["participant"].iloc[0]
    kind = fr["video"].iloc[0]
    fig, ax = plt.subplots(figsize=(10, 2.5))
    win = max(int(cfg["analysis_fps"] * 5), 1)
    rate = fr["shoulders_visible"].astype(float).rolling(win, min_periods=1).mean()
    hip = fr["hips_visible"].astype(float).rolling(win, min_periods=1).mean()
    ax.plot(fr["t_s"], rate, label="upper body")
    ax.plot(fr["t_s"], hip, label="hips")
    ax.axhline(cfg["detection_threshold"], linestyle="--", color="gray")
    if seg is not None and kind == "interview":
        for _, s in seg[(seg["participant"] == pid) & (seg["segment"] != "relaxed")].iterrows():
            if pd.notna(s["start_s"]):
                ax.axvspan(s["start_s"], s["end_s"], alpha=0.15)
                ax.text(s["start_s"], 1.02, s["segment"], fontsize=8)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("seconds")
    ax.set_title(f"{pid} {kind}")
    ax.legend(loc="lower right", fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(plots, f"{pid}_{kind}_detection.png"), dpi=120)
    plt.close(fig)

if all_frames:
    frames = pd.concat(all_frames, ignore_index=True)
    ref = prepare_dataset(cfg, load_confidetect(cfg))
    cols = [c for c in cfg["feature_sets"][cfg["deployed_feature_set"]] if c in frames.columns]
    rows = []
    for c in cols:
        v = frames[c].dropna()
        lo, hi = ref[c].min(), ref[c].max()
        p1, p99 = ref[c].quantile(0.01), ref[c].quantile(0.99)
        rows.append({
            "feature": c,
            "video_frames": int(len(v)),
            "video_min": float(v.min()) if len(v) else np.nan,
            "video_max": float(v.max()) if len(v) else np.nan,
            "video_mean": float(v.mean()) if len(v) else np.nan,
            "confidetect_min": float(lo),
            "confidetect_max": float(hi),
            "share_inside_min_max": float(((v >= lo) & (v <= hi)).mean()) if len(v) else np.nan,
            "share_inside_p1_p99": float(((v >= p1) & (v <= p99)).mean()) if len(v) else np.nan,
        })
    pd.DataFrame(rows).to_csv(os.path.join(out, "range_check_posture.csv"), index=False)

write_run_info(cfg, out, {"script": "09_quality_report.py"})
print(summary.to_string(index=False))
