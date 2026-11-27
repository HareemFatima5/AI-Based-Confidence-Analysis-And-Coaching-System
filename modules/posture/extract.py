import os
import urllib.request
import numpy as np
import pandas as pd
import cv2
from common import load_config, resolve
from features import segment_features, hips_visible, L_SHOULDER, R_SHOULDER, NOSE, frame_feature_matrix

SEGMENT_VIDEO = {"relaxed": "relaxed", "B1": "interview", "B2": "interview", "B3": "interview", "B4": "interview"}


def ensure_pose_model(cfg):
    path = resolve(cfg, cfg["pose_model_path"])
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(cfg["pose_model_url"], path)
    return path


def create_landmarker(cfg, use_gpu=False):
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
    delegate = mp_python.BaseOptions.Delegate.GPU if use_gpu else mp_python.BaseOptions.Delegate.CPU
    base = mp_python.BaseOptions(model_asset_path=ensure_pose_model(cfg), delegate=delegate)
    opts = vision.PoseLandmarkerOptions(
        base_options=base,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.PoseLandmarker.create_from_options(opts)


def detect_video(video_path, cfg, use_gpu=False, max_seconds=None):
    import mediapipe as mp
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps if total > 0 else 0.0
    step_s = 1.0 / cfg["analysis_fps"]
    landmarker = create_landmarker(cfg, use_gpu)
    times = []
    lms = []
    det = []
    next_t = 0.0
    idx = 0
    last_ts = -1
    while True:
        ok = cap.grab()
        if not ok:
            break
        t = idx / fps
        idx += 1
        if max_seconds is not None and t > max_seconds:
            break
        if t + 1e-9 < next_t:
            continue
        ok, frame = cap.retrieve()
        if not ok:
            continue
        next_t += step_s
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int(round(t * 1000))
        if ts <= last_ts:
            ts = last_ts + 1
        last_ts = ts
        res = landmarker.detect_for_video(img, ts)
        times.append(t)
        if res.pose_landmarks and len(res.pose_landmarks[0]) >= 33:
            arr = np.array([[p.x, p.y, p.z, p.visibility] for p in res.pose_landmarks[0]], dtype=float)
            lms.append(arr)
            det.append(True)
        else:
            lms.append(np.full((33, 4), np.nan))
            det.append(False)
    cap.release()
    landmarker.close()
    meta = {"fps": float(fps), "duration_s": float(max(duration, times[-1] if times else 0.0)), "n_sampled": len(times)}
    return np.array(times), np.array(lms), np.array(det), meta


def shoulders_ok(lm, thr=0.5):
    return np.minimum(lm[:, L_SHOULDER, 3], lm[:, R_SHOULDER, 3]) >= thr


def frame_table(participant, kind, times, lms, det, cfg):
    hip = np.zeros(len(times), dtype=bool)
    sh = np.zeros(len(times), dtype=bool)
    if len(times):
        valid = det
        hip[valid] = hips_visible(lms[valid], cfg["hip_visibility_threshold"])
        sh[valid] = shoulders_ok(lms[valid], cfg["hip_visibility_threshold"])
    return pd.DataFrame({
        "participant": participant,
        "video": kind,
        "t_s": times,
        "detected": det,
        "shoulders_visible": sh,
        "hips_visible": hip,
    })


def build_segment_rows(participant, kind, times, lms, det, meta, seg_df, cfg, model=None, feature_names=None):
    rows = []
    sh = np.zeros(len(times), dtype=bool)
    if len(times):
        sh[det] = shoulders_ok(lms[det], cfg["hip_visibility_threshold"])
    use = det & sh
    hip = np.zeros(len(times), dtype=bool)
    if len(times):
        hip[det] = hips_visible(lms[det], cfg["hip_visibility_threshold"])
    for _, s in seg_df.iterrows():
        name = s["segment"]
        if SEGMENT_VIDEO[name] != kind:
            continue
        if name == "relaxed":
            start, end = 0.0, meta["duration_s"]
        else:
            start = float(s["start_s"])
            end = meta["duration_s"] if pd.isna(s["end_s"]) else float(s["end_s"])
        mask = (times >= start) & (times < end)
        seg_dur = max(end - start, 0.0)
        expected = int(np.floor(seg_dur * cfg["analysis_fps"]))
        note = []
        if mask.sum() == 0:
            res = {n: np.nan for n in cfg["video_feature_names"]}
            res.update({"n_frames": 0, "detection_rate": 0.0})
            note.append("no_frames")
        else:
            res = segment_features(times[mask], lms[mask], use[mask], hip[mask], max(expected, 1), cfg)
        short = seg_dur < cfg["min_segment_s"]
        usable = (res["detection_rate"] >= cfg["detection_threshold"]) and not short
        if short:
            note.append("short")
        if res["detection_rate"] < cfg["detection_threshold"]:
            note.append("low_detection")
        if np.isnan(res.get("torso_lean_deg", np.nan)) and res["n_frames"] >= 2:
            note.append("torso_lean_empty_hips_hidden")
        prob = np.nan
        if model is not None and res["n_frames"] >= 2:
            X = frame_feature_matrix(lms[mask & use], feature_names)
            ok = np.isfinite(X).all(axis=1)
            if ok.any():
                prob = float(model.predict_proba(X[ok])[:, list(model.classes_).index("Confident")].mean())
        rows.append({
            "participant": participant,
            "segment": name,
            "usable": bool(usable),
            "duration_s": round(seg_dur, 3),
            "n_frames": res["n_frames"],
            "detection_rate": round(res["detection_rate"], 4),
            "short": bool(short),
            "shoulder_instability": res["shoulder_instability"],
            "shoulder_tilt_deg": res["shoulder_tilt_deg"],
            "torso_lean_deg": res["torso_lean_deg"],
            "movement_speed": res["movement_speed"],
            "head_height_ratio": res["head_height_ratio"],
            "posture_prob": prob,
            "module_version": cfg["module_version"],
            "note": ";".join(note),
        })
    return rows
