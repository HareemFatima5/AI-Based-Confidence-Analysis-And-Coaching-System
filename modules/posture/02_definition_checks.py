import json
import os
import numpy as np
import pandas as pd
from common import load_config, load_confidetect, out_dir, write_run_info

cfg = load_config()
df = load_confidetect(cfg)
out = out_dir(cfg)

checks = []


def record(name, expr, resid, tol, exact):
    resid = np.asarray(resid, dtype=float)
    mae = float(np.nanmean(np.abs(resid)))
    mx = float(np.nanmax(np.abs(resid)))
    frac = float(np.nanmean(np.abs(resid) <= tol))
    checks.append({
        "identity": name,
        "expression": expr,
        "tolerance": tol,
        "mean_abs_error": mae,
        "max_abs_error": mx,
        "share_within_tolerance": frac,
        "holds": bool(frac >= 0.999) if exact else None,
        "holds_approximately": bool(frac >= 0.9),
        "expected": "exact" if exact else "approximate",
    })


record("body_lean_x", "shoulder_center_x - hip_center_x", df["body_lean_x"] - (df["shoulder_center_x"] - df["hip_center_x"]), 1e-5, True)
record("shoulder_slope", "shoulder_y_diff", df["shoulder_slope"] - df["shoulder_y_diff"], 1e-5, True)
record("eye_distance_ratio", "eye_distance / shoulder_span", df["eye_distance_ratio"] - df["eye_distance"] / df["shoulder_span"], 1e-5, True)
spine_pred = 90.0 + np.degrees(np.arctan2(df["body_lean_x"], df["hip_shoulder_y_diff"]))
record("spine_angle", "90 + degrees(atan2(body_lean_x, hip_shoulder_y_diff))", df["spine_angle"] - spine_pred, 0.05, True)
record("wrist_shoulder_ratio", "wrist_distance_x / shoulder_span", df["wrist_shoulder_ratio"] - df["wrist_distance_x"] / df["shoulder_span"], 0.02, False)

res = pd.DataFrame(checks)
res.to_csv(os.path.join(out, "confidetect_definition_checks.csv"), index=False)

tilt = df["head_tilt_angle"]
tilt_summary = {
    "share_abs_above_90": float((tilt.abs() > 90).mean()),
    "head_direction_for_abs_above_90": df.loc[tilt.abs() > 90, "head_direction"].value_counts().to_dict(),
    "head_direction_for_abs_below_90": df.loc[tilt.abs() <= 90, "head_direction"].value_counts().to_dict(),
}
with open(os.path.join(out, "confidetect_head_tilt_check.json"), "w") as f:
    json.dump(tilt_summary, f, indent=2)

frames = []
for col in ["head_direction", "arm_position", "posture", "confidence_label"]:
    g = df.groupby(col)[cfg["numeric_columns"]].agg(["min", "max"])
    g.columns = ["_".join(c) for c in g.columns]
    g = g.reset_index().rename(columns={col: "level"})
    g.insert(0, "column", col)
    frames.append(g)
pd.concat(frames, ignore_index=True).to_csv(os.path.join(out, "confidetect_label_rule_ranges.csv"), index=False)

write_run_info(cfg, out, {"script": "02_definition_checks.py"})
print(res.to_string(index=False))
print(json.dumps(tilt_summary, indent=2))
