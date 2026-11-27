import pandas as pd
import numpy as np
from common import wrap_angle_90

NOSE = 0
L_EYE = 2
R_EYE = 5
L_SHOULDER = 11
R_SHOULDER = 12
L_WRIST = 15
R_WRIST = 16
L_HIP = 23
R_HIP = 24


def shoulder_span(lm):
    d = lm[:, L_SHOULDER, :2] - lm[:, R_SHOULDER, :2]
    return np.sqrt((d ** 2).sum(axis=1))


def shoulder_center(lm):
    return (lm[:, L_SHOULDER, :2] + lm[:, R_SHOULDER, :2]) / 2.0


def hip_center(lm):
    return (lm[:, L_HIP, :2] + lm[:, R_HIP, :2]) / 2.0


def eye_center(lm):
    return (lm[:, L_EYE, :2] + lm[:, R_EYE, :2]) / 2.0


def shoulder_tilt_deg(lm):
    d = lm[:, L_SHOULDER, :2] - lm[:, R_SHOULDER, :2]
    ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    return wrap_angle_90(ang)


def head_tilt_deg(lm):
    d = lm[:, L_EYE, :2] - lm[:, R_EYE, :2]
    ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    return wrap_angle_90(ang)


def torso_lean_deg(lm):
    v = shoulder_center(lm) - hip_center(lm)
    return np.degrees(np.arctan2(v[:, 0], -v[:, 1]))


def hips_visible(lm, thr):
    v = np.minimum(lm[:, L_HIP, 3], lm[:, R_HIP, 3])
    return v >= thr


def upper_body_frame_features(lm):
    span = shoulder_span(lm)
    sc = shoulder_center(lm)
    ec = eye_center(lm)
    eye_dist = np.sqrt(((lm[:, L_EYE, :2] - lm[:, R_EYE, :2]) ** 2).sum(axis=1))
    sy = np.abs(lm[:, L_SHOULDER, 1] - lm[:, R_SHOULDER, 1])
    out = {
        "eye_shoulder_y_ratio": (ec[:, 1] - sc[:, 1]) / span,
        "shoulder_y_diff": sy,
        "nose_eye_center_offset_x": lm[:, NOSE, 0] - ec[:, 0],
        "shoulder_span": span,
        "eye_distance": eye_dist,
        "head_tilt_angle": head_tilt_deg(lm),
        "eye_distance_ratio": eye_dist / span,
        "shoulder_slope": sy,
    }
    return out


def frame_feature_matrix(lm, names):
    feats = upper_body_frame_features(lm)
    return np.column_stack([feats[n] for n in names])


def segment_features(t, lm, detected, hip_ok, expected_frames, cfg):
    n_frames = int(detected.sum())
    duration = float(t[-1] - t[0]) if len(t) > 1 else 0.0
    rate = n_frames / expected_frames if expected_frames > 0 else 0.0
    res = {
        "n_frames": n_frames,
        "detection_rate": float(rate),
    }
    names = cfg["video_feature_names"]
    for n in names:
        res[n] = np.nan
    if n_frames < 2:
        return res
    d = detected
    td = t[d]
    lmd = lm[d]
    span = shoulder_span(lmd)
    span_mean = float(np.nanmean(span))
    sc = shoulder_center(lmd)
    sc_norm = sc / span_mean
    res["shoulder_instability"] = float(np.sqrt(np.var(sc_norm[:, 0]) + np.var(sc_norm[:, 1])))
    res["shoulder_tilt_deg"] = float(np.mean(np.abs(shoulder_tilt_deg(lmd))))
    dt = np.diff(td)
    ok = dt > 0
    if ok.any():
        step = np.sqrt((np.diff(sc_norm, axis=0) ** 2).sum(axis=1))
        gap_ok = ok & (dt <= 3.0 / cfg["analysis_fps"])
        if gap_ok.any():
            res["movement_speed"] = float(np.mean(step[gap_ok] / dt[gap_ok]))
    nose_y = lmd[:, NOSE, 1]
    res["head_height_ratio"] = float(np.mean((sc[:, 1] - nose_y) / span))
    hd = hip_ok[d]
    if hd.mean() >= cfg["hip_visible_fraction_min"]:
        res["torso_lean_deg"] = float(np.mean(np.abs(torso_lean_deg(lmd[hd]))))
    return res


def make_delta_table(feat, cfg):
    names = cfg["video_feature_names"]
    rows = []
    for pid, g in feat.groupby("participant", sort=False):
        rel = g[g["segment"] == "relaxed"]
        if rel.empty:
            continue
        rel = rel.iloc[0]
        for _, r in g[g["segment"] != "relaxed"].iterrows():
            row = {
                "participant": pid,
                "segment": r["segment"],
                "usable": bool(r["usable"]) and bool(rel["usable"]),
                "duration_s": r["duration_s"],
            }
            for n in names:
                row["d_" + n] = r[n] - rel[n]
            row["module_version"] = cfg["module_version"]
            rows.append(row)
    return pd.DataFrame(rows)
