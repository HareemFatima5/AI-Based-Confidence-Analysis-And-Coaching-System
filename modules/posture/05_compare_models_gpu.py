import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, balanced_accuracy_score
from common import (load_config, load_confidetect, prepare_dataset, out_dir, write_run_info,
                    bootstrap_ci, blocked_folds)

cfg = load_config()
df = prepare_dataset(cfg, load_confidetect(cfg))
out = out_dir(cfg)
y_raw = df[cfg["target"]].values
classes = sorted(np.unique(y_raw))
y = np.array([classes.index(v) for v in y_raw])
e1 = cfg["e1"]

try:
    import torch
    has_torch = True
    cuda = torch.cuda.is_available()
except Exception:
    torch = None
    has_torch = False
    cuda = False

try:
    import xgboost as xgb
    has_xgb = True
except Exception:
    has_xgb = False

print("torch", has_torch, "cuda", cuda, "xgboost", has_xgb)


def macro_f1(a, b):
    return f1_score(a, b, average="macro", labels=list(range(len(classes))), zero_division=0)


class RF:
    name = "random_forest"

    def fit_predict(self, Xtr, ytr, Xte):
        m = RandomForestClassifier(n_estimators=e1["rf_trees"], class_weight="balanced", n_jobs=-1, random_state=cfg["seed"])
        m.fit(Xtr, ytr)
        return m.predict(Xte)


class XGB:
    name = "xgboost"

    def fit_predict(self, Xtr, ytr, Xte):
        counts = np.bincount(ytr, minlength=len(classes)).astype(float)
        w = (len(ytr) / (len(classes) * counts))[ytr]
        m = xgb.XGBClassifier(
            n_estimators=400,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            tree_method="hist",
            device="cuda" if cuda else "cpu",
            random_state=cfg["seed"],
            objective="multi:softprob",
            num_class=len(classes),
        )
        m.fit(Xtr, ytr, sample_weight=w)
        return m.predict(Xte)


class MLP:
    name = "mlp_torch"

    def fit_predict(self, Xtr, ytr, Xte):
        torch.manual_seed(cfg["seed"])
        dev = torch.device("cuda" if cuda else "cpu")
        mu = Xtr.mean(axis=0)
        sd = Xtr.std(axis=0) + 1e-8
        xt = torch.tensor((Xtr - mu) / sd, dtype=torch.float32, device=dev)
        yt = torch.tensor(ytr, dtype=torch.long, device=dev)
        xe = torch.tensor((Xte - mu) / sd, dtype=torch.float32, device=dev)
        counts = np.bincount(ytr, minlength=len(classes)).astype(float)
        cw = torch.tensor(len(ytr) / (len(classes) * counts), dtype=torch.float32, device=dev)
        net = torch.nn.Sequential(
            torch.nn.Linear(xt.shape[1], 128), torch.nn.ReLU(), torch.nn.Dropout(0.1),
            torch.nn.Linear(128, 64), torch.nn.ReLU(),
            torch.nn.Linear(64, len(classes)),
        ).to(dev)
        opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
        lossf = torch.nn.CrossEntropyLoss(weight=cw)
        n = xt.shape[0]
        g = torch.Generator(device="cpu").manual_seed(cfg["seed"])
        for ep in range(80):
            net.train()
            perm = torch.randperm(n, generator=g).to(dev)
            for i in range(0, n, 256):
                idx = perm[i:i + 256]
                opt.zero_grad()
                loss = lossf(net(xt[idx]), yt[idx])
                loss.backward()
                opt.step()
        net.eval()
        with torch.no_grad():
            return net(xe).argmax(dim=1).cpu().numpy()


models = [RF()]
if has_xgb:
    models.append(XGB())
if has_torch:
    models.append(MLP())

rows = []
for set_name in ["upper_body", "no_hip", "full"]:
    cols = cfg["feature_sets"][set_name]
    X = df[cols].values.astype(float)
    folds = list(blocked_folds(len(y), e1["n_blocks"]))
    for mdl in models:
        pred = np.empty(len(y), dtype=int)
        for tr, te in folds:
            pred[te] = mdl.fit_predict(X[tr], y[tr], X[te])
        f1 = macro_f1(y, pred)
        lo, hi = bootstrap_ci(macro_f1, y, pred, e1["n_bootstrap"], e1["ci"], cfg["seed"])
        rows.append({
            "feature_set": set_name,
            "model": mdl.name,
            "device": "cuda" if cuda and mdl.name != "random_forest" else "cpu",
            "macro_f1": f1,
            "ci_low": lo,
            "ci_high": hi,
            "balanced_accuracy": balanced_accuracy_score(y, pred),
            "cv": "blocked",
            "status": "feasibility only",
        })
        print(f"{set_name:10s} {mdl.name:14s} {f1:.3f} ({lo:.3f} to {hi:.3f})")

pd.DataFrame(rows).to_csv(os.path.join(out, "model_comparison_confidetect.csv"), index=False)
write_run_info(cfg, out, {"script": "05_compare_models_gpu.py", "cuda": cuda})
