import json
import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from common import (load_config, load_confidetect, prepare_dataset, out_dir, model_dir, write_run_info,
                    blocked_folds, majority_baseline_pred)

cfg = load_config()
df = prepare_dataset(cfg, load_confidetect(cfg))
mdir = model_dir(cfg)
odir = out_dir(cfg)

set_name = cfg["deployed_feature_set"]
cols = cfg["feature_sets"][set_name]
X = df[cols].values.astype(float)
y = df[cfg["target"]].values
labels = sorted(np.unique(y))

model = RandomForestClassifier(
    n_estimators=cfg["e1"]["rf_trees"],
    min_samples_leaf=cfg["e1"]["rf_min_samples_leaf"],
    class_weight="balanced",
    n_jobs=-1,
    random_state=cfg["seed"],
)
model.fit(X, y)
joblib.dump(model, os.path.join(mdir, "model.joblib"))

e1_path = os.path.join(odir, "e1_confidetect.csv")
metrics = {"status": "feasibility only", "feature_set": set_name, "n_features": len(cols)}
if os.path.exists(e1_path):
    e1 = pd.read_csv(e1_path)
    row = e1[(e1["feature_set"] == set_name) & (e1["cv"] == "blocked")].iloc[0]
    metrics.update({
        "blocked_cv_macro_f1": float(row["macro_f1"]),
        "blocked_cv_ci_low": float(row["ci_low"]),
        "blocked_cv_ci_high": float(row["ci_high"]),
        "majority_macro_f1": float(row["majority_macro_f1"]),
    })
else:
    folds = list(blocked_folds(len(y), cfg["e1"]["n_blocks"]))
    pred = np.empty(len(y), dtype=object)
    for tr, te in folds:
        m = RandomForestClassifier(n_estimators=cfg["e1"]["rf_trees"], class_weight="balanced", n_jobs=-1, random_state=cfg["seed"])
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    metrics["blocked_cv_macro_f1"] = float(f1_score(y, pred, average="macro", labels=labels))
    metrics["majority_macro_f1"] = float(f1_score(y, majority_baseline_pred(y), average="macro", labels=labels))
with open(os.path.join(mdir, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)

importances = pd.Series(model.feature_importances_, index=cols).sort_values(ascending=False)
importances.to_csv(os.path.join(mdir, "feature_importances.csv"), header=["importance"])

meta = {
    "name": cfg["module_version"],
    "model_type": "RandomForestClassifier",
    "feature_set": set_name,
    "features": cols,
    "classes": [str(c) for c in model.classes_],
    "output": "probability of Confident",
    "positive_class": "Confident",
    "trained_on": "ConfiDetect posture table",
    "n_training_rows": int(len(y)),
    "wrap_head_tilt": cfg["wrap_head_tilt"],
    "seed": cfg["seed"],
    "use": "feasibility only, never used to judge the final system",
}
with open(os.path.join(mdir, "model_meta.json"), "w") as f:
    json.dump(meta, f, indent=2)

with open(os.path.join(mdir, "config_used.json"), "w") as f:
    json.dump(cfg, f, indent=2)

card = f"""# {cfg['module_version']} model card

Model: random forest, {cfg['e1']['rf_trees']} trees, balanced class weights, seed {cfg['seed']}.
Training data: ConfiDetect posture table, {len(y)} rows ({', '.join(f'{k} {v}' for k, v in pd.Series(y).value_counts().items())}).
Features ({len(cols)}): {', '.join(cols)}.
Output: probability of the Confident class, averaged per segment to give posture_prob.

Evaluation: blocked {cfg['e1']['n_blocks']}-fold cross-validation, macro-F1 {metrics.get('blocked_cv_macro_f1', float('nan')):.3f} against {metrics.get('majority_macro_f1', float('nan')):.3f} for the majority class.

Limits:
- ConfiDetect labels were assigned by rules on posture cues, so the model largely learns those rules.
- The dataset has no person identifiers, so folds are blocks of consecutive rows.
- The upper_body set is used on our videos because arms, wrists and hips are not visible in head-to-mid-chest framing.
- ConfiDetect Neutral is a rule-based posture pattern and is not the same as the Neutral class from our raters.
- Output is feasibility evidence only and is never used to judge the final system.
"""
with open(os.path.join(mdir, "model_card.md"), "w") as f:
    f.write(card)

write_run_info(cfg, mdir, {"script": "04_train_posture_model.py"})
print(json.dumps(metrics, indent=2))
print(importances)
