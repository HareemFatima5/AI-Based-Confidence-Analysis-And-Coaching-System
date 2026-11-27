import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from common import load_config, load_confidetect, prepare_dataset, out_dir, write_run_info

cfg = load_config()
raw = load_confidetect(cfg)
df = prepare_dataset(cfg, raw)
out = out_dir(cfg)

num = cfg["numeric_columns"]
cat = cfg["categorical_columns"] + [cfg["target"]]

report = {
    "n_rows": int(len(raw)),
    "n_columns": int(raw.shape[1]),
    "missing_total": int(raw.isna().sum().sum()),
    "duplicate_rows": int(raw.duplicated().sum()),
    "class_counts": raw[cfg["target"]].value_counts().to_dict(),
    "class_share": raw[cfg["target"]].value_counts(normalize=True).round(4).to_dict(),
    "categorical_levels": {c: raw[c].value_counts().to_dict() for c in cat},
}
with open(os.path.join(out, "confidetect_audit.json"), "w") as f:
    json.dump(report, f, indent=2)

ranges = raw[num].describe().T[["min", "max", "mean", "std"]]
ranges.to_csv(os.path.join(out, "confidetect_ranges.csv"))

ranges_wrapped = df[num].describe().T[["min", "max", "mean", "std"]]
ranges_wrapped.to_csv(os.path.join(out, "confidetect_ranges_wrapped.csv"))

by_class = df.groupby(cfg["target"])[num].mean().T
by_class.to_csv(os.path.join(out, "confidetect_feature_means_by_class.csv"))

run_lengths = (raw[cfg["target"]] != raw[cfg["target"]].shift()).cumsum()
runs = raw.groupby(run_lengths)[cfg["target"]].agg(["first", "size"])
runs.columns = ["label", "length"]
runs.to_csv(os.path.join(out, "confidetect_label_runs.csv"), index=False)

lag1 = {}
for c in num:
    s = raw[c]
    lag1[c] = float(s.autocorr(lag=1))
pd.Series(lag1, name="lag1_autocorr").to_csv(os.path.join(out, "confidetect_lag1_autocorr.csv"))

fig, ax = plt.subplots(figsize=(6, 4))
raw[cfg["target"]].value_counts().plot(kind="bar", ax=ax)
ax.set_ylabel("rows")
fig.tight_layout()
fig.savefig(os.path.join(out, "confidetect_class_counts.png"), dpi=150)
plt.close(fig)

fig, axes = plt.subplots(4, 4, figsize=(16, 12))
for ax, c in zip(axes.ravel(), num):
    for lab, g in df.groupby(cfg["target"]):
        ax.hist(g[c].dropna(), bins=40, alpha=0.5, label=lab)
    ax.set_title(c, fontsize=9)
axes.ravel()[0].legend()
for ax in axes.ravel()[len(num):]:
    ax.axis("off")
fig.tight_layout()
fig.savefig(os.path.join(out, "confidetect_feature_histograms.png"), dpi=120)
plt.close(fig)

corr = df[num].corr()
corr.to_csv(os.path.join(out, "confidetect_feature_correlations.csv"))
fig, ax = plt.subplots(figsize=(9, 8))
im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="coolwarm")
ax.set_xticks(range(len(num)))
ax.set_yticks(range(len(num)))
ax.set_xticklabels(num, rotation=90, fontsize=7)
ax.set_yticklabels(num, fontsize=7)
fig.colorbar(im)
fig.tight_layout()
fig.savefig(os.path.join(out, "confidetect_feature_correlations.png"), dpi=150)
plt.close(fig)

write_run_info(cfg, out, {"script": "01_audit_confidetect.py"})
print(json.dumps(report, indent=2))
print(runs.groupby("label")["length"].describe())
