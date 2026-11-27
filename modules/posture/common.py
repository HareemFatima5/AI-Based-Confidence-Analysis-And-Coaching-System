import json
import os
import subprocess
import sys
import datetime
import numpy as np
import pandas as pd
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))


def load_config(path=None):
    path = path or os.path.join(ROOT, "config.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def resolve(cfg, *parts):
    p = os.path.join(ROOT, *parts)
    return p


def out_dir(cfg, sub=None):
    d = resolve(cfg, cfg["paths"]["outputs"])
    if sub:
        d = os.path.join(d, sub)
    os.makedirs(d, exist_ok=True)
    return d


def model_dir(cfg):
    d = resolve(cfg, cfg["paths"]["models"])
    os.makedirs(d, exist_ok=True)
    return d


def wrap_angle_90(a):
    a = np.asarray(a, dtype=float)
    return (a + 90.0) % 180.0 - 90.0


def load_confidetect(cfg, path=None):
    local = path or resolve(cfg, cfg["dataset_local"])
    if os.path.exists(local):
        df = pd.read_csv(local)
    else:
        df = pd.read_csv(cfg["dataset_url"])
        os.makedirs(os.path.dirname(local), exist_ok=True)
        df.to_csv(local, index=False)
    return df


def prepare_dataset(cfg, df):
    df = df.copy()
    if cfg.get("wrap_head_tilt", True):
        df["head_tilt_angle"] = wrap_angle_90(df["head_tilt_angle"].values)
    return df


def git_commit():
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return "no-git"


def write_run_info(cfg, folder, extra=None):
    import sklearn
    info = {
        "code_commit": git_commit(),
        "config_version": cfg["config_version"],
        "module_version": cfg["module_version"],
        "date": datetime.datetime.now().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "seed": cfg["seed"],
    }
    if extra:
        info.update(extra)
    with open(os.path.join(folder, "run_info.json"), "w") as f:
        json.dump(info, f, indent=2)
    return info


def majority_baseline_pred(y):
    vals, counts = np.unique(y, return_counts=True)
    return np.full(len(y), vals[np.argmax(counts)], dtype=object)


def bootstrap_ci(metric_fn, y_true, y_pred, n_boot, ci, seed):
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n = len(y_true)
    vals = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        vals[i] = metric_fn(y_true[idx], y_pred[idx])
    lo = (1 - ci) / 2 * 100
    hi = (1 + ci) / 2 * 100
    return float(np.percentile(vals, lo)), float(np.percentile(vals, hi))


def blocked_folds(n, n_blocks):
    edges = np.linspace(0, n, n_blocks + 1).astype(int)
    for i in range(n_blocks):
        test = np.arange(edges[i], edges[i + 1])
        train = np.concatenate([np.arange(0, edges[i]), np.arange(edges[i + 1], n)])
        yield train, test


def cohens_kappa(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    labels = np.unique(np.concatenate([a, b]))
    po = np.mean(a == b)
    pe = sum(np.mean(a == l) * np.mean(b == l) for l in labels)
    if pe == 1:
        return 1.0
    return float((po - pe) / (1 - pe))
