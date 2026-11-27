import json
import os
import numpy as np
import pandas as pd
from common import load_config, out_dir, write_run_info
from features import make_delta_table

cfg = load_config()
out = out_dir(cfg)
feat = pd.read_csv(os.path.join(out, "posture_features.csv"))
delta = make_delta_table(feat, cfg)
delta.to_csv(os.path.join(out, "posture_delta.csv"), index=False)

names = cfg["video_feature_names"]
failures = []
checked = 0
for _, d in delta.iterrows():
    g = feat[feat["participant"] == d["participant"]]
    rel = g[g["segment"] == "relaxed"].iloc[0]
    seg = g[g["segment"] == d["segment"]].iloc[0]
    for n in names:
        a = seg[n] - rel[n]
        b = d["d_" + n]
        if np.isnan(a) and np.isnan(b):
            continue
        checked += 1
        if not np.isclose(a, b, atol=1e-12):
            failures.append({"participant": d["participant"], "segment": d["segment"], "feature": n})

counts = feat.groupby("participant")["segment"].nunique()
result = {
    "delta_rows": int(len(delta)),
    "values_checked": checked,
    "identity_failures": failures,
    "identity_holds": len(failures) == 0,
    "participants_without_5_segments": counts[counts != 5].index.tolist(),
    "usable_delta_rows": int(delta["usable"].sum()),
}
with open(os.path.join(out, "delta_identity_check.json"), "w") as f:
    json.dump(result, f, indent=2)
write_run_info(cfg, out, {"script": "08_make_deltas.py"})
print(json.dumps(result, indent=2))
