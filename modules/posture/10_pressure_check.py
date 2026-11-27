import os
import numpy as np
import pandas as pd
from scipy import stats
from common import load_config, out_dir, write_run_info, bootstrap_ci

cfg = load_config()
out = out_dir(cfg)
feat = pd.read_csv(os.path.join(out, "posture_features.csv"))
feat["usable"] = feat["usable"].astype(bool)
names = cfg["video_feature_names"] + ["posture_prob"]

rows = []
for pid, g in feat.groupby("participant"):
    rel = g[(g["segment"] == "relaxed") & g["usable"]]
    itv = g[(g["segment"] != "relaxed") & g["usable"]]
    if rel.empty or len(itv) < 2:
        continue
    r = {"participant": pid, "n_usable_interview_segments": len(itv)}
    for n in names:
        r["relaxed_" + n] = rel[n].iloc[0]
        r["interview_" + n] = itv[n].mean()
    rows.append(r)
per = pd.DataFrame(rows)
per.to_csv(os.path.join(out, "pressure_check_per_participant.csv"), index=False)

res = []
for n in names:
    if per.empty:
        break
    a = per["relaxed_" + n]
    b = per["interview_" + n]
    ok = a.notna() & b.notna()
    a, b = a[ok].values, b[ok].values
    k = len(a)
    row = {"feature": n, "n_participants": k, "relaxed_mean": np.nan, "interview_mean": np.nan,
           "mean_diff": np.nan, "diff_ci_low": np.nan, "diff_ci_high": np.nan, "cohens_dz": np.nan,
           "wilcoxon_p": np.nan, "status": "preliminary"}
    if k >= 2:
        d = b - a
        row["relaxed_mean"] = float(a.mean())
        row["interview_mean"] = float(b.mean())
        row["mean_diff"] = float(d.mean())
        rng = np.random.default_rng(cfg["seed"])
        boots = np.array([d[rng.integers(0, k, k)].mean() for _ in range(2000)])
        row["diff_ci_low"], row["diff_ci_high"] = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
        if d.std(ddof=1) > 0:
            row["cohens_dz"] = float(d.mean() / d.std(ddof=1))
        if k >= 6 and np.any(d != 0):
            try:
                row["wilcoxon_p"] = float(stats.wilcoxon(d).pvalue)
            except Exception:
                pass
    res.append(row)
pd.DataFrame(res).to_csv(os.path.join(out, "pressure_check_posture.csv"), index=False)
write_run_info(cfg, out, {"script": "10_pressure_check.py", "n_participants": int(len(per))})
print(pd.DataFrame(res).to_string(index=False))
