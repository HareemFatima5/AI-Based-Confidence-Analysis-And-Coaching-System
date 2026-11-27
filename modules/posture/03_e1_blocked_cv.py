import json
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import KFold
from common import (load_config, load_confidetect, prepare_dataset, out_dir, write_run_info,
                    bootstrap_ci, blocked_folds, majority_baseline_pred)

cfg = load_config()
df = prepare_dataset(cfg, load_confidetect(cfg))
out = out_dir(cfg)
y = df[cfg["target"]].values
labels = sorted(np.unique(y))
e1 = cfg["e1"]


def macro_f1(a, b):
    return f1_score(a, b, average="macro", labels=labels, zero_division=0)


def make_rf():
    return RandomForestClassifier(
        n_estimators=e1["rf_trees"],
        min_samples_leaf=e1["rf_min_samples_leaf"],
        class_weight="balanced",
        n_jobs=-1,
        random_state=cfg["seed"],
    )


def cv_predict(X, y, folds):
    pred = np.empty(len(y), dtype=object)
    for tr, te in folds:
        m = make_rf()
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    return pred


rows = []
confusions = {}
base_pred = majority_baseline_pred(y)
base_f1 = macro_f1(y, base_pred)
base_lo, base_hi = bootstrap_ci(macro_f1, y, base_pred, e1["n_bootstrap"], e1["ci"], cfg["seed"])

for set_name, cols in cfg["feature_sets"].items():
    X = df[cols].values.astype(float)
    for scheme in ["blocked", "shuffled"]:
        if scheme == "blocked":
            folds = list(blocked_folds(len(y), e1["n_blocks"]))
        else:
            folds = list(KFold(n_splits=e1["n_blocks"], shuffle=True, random_state=cfg["seed"]).split(X))
        pred = cv_predict(X, y, folds)
        f1 = macro_f1(y, pred)
        lo, hi = bootstrap_ci(macro_f1, y, pred, e1["n_bootstrap"], e1["ci"], cfg["seed"])
        bacc = balanced_accuracy_score(y, pred)
        yb = (y == "Confident")
        pb = (pred == "Confident")
        f1_bin = f1_score(yb, pb, average="macro", zero_division=0)
        rows.append({
            "dataset": "ConfiDetect",
            "feature_set": set_name,
            "n_features": len(cols),
            "cv": scheme,
            "n_folds": e1["n_blocks"],
            "macro_f1": f1,
            "ci_low": lo,
            "ci_high": hi,
            "balanced_accuracy": bacc,
            "binary_confident_vs_rest_macro_f1": f1_bin,
            "majority_macro_f1": base_f1,
            "majority_ci_low": base_lo,
            "majority_ci_high": base_hi,
            "beats_majority": bool(lo > base_hi),
            "status": "feasibility only",
        })
        confusions[f"{set_name}_{scheme}"] = {
            "labels": labels,
            "matrix": confusion_matrix(y, pred, labels=labels).tolist(),
        }
        print(f"{set_name:10s} {scheme:9s} macro-F1 {f1:.3f} ({lo:.3f} to {hi:.3f})  majority {base_f1:.3f}")

res = pd.DataFrame(rows)
res.to_csv(os.path.join(out, "e1_confidetect.csv"), index=False)
with open(os.path.join(out, "e1_confusion_matrices.json"), "w") as f:
    json.dump(confusions, f, indent=2)
write_run_info(cfg, out, {"script": "03_e1_blocked_cv.py", "n_rows": int(len(y))})
