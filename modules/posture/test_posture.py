import numpy as np
import pandas as pd
import pytest
from common import load_config, wrap_angle_90, cohens_kappa, blocked_folds
from features import (segment_features, shoulder_tilt_deg, torso_lean_deg, upper_body_frame_features,
                      make_delta_table, L_SHOULDER, R_SHOULDER, L_HIP, R_HIP, NOSE, L_EYE, R_EYE)
from extract import build_segment_rows

cfg = load_config()
FPS = cfg["analysis_fps"]


def base_landmarks(n, hips=True):
    lm = np.zeros((n, 33, 4))
    lm[:, :, 3] = 1.0
    lm[:, L_SHOULDER, :2] = [0.6, 0.5]
    lm[:, R_SHOULDER, :2] = [0.4, 0.5]
    lm[:, NOSE, :2] = [0.5, 0.3]
    lm[:, L_EYE, :2] = [0.54, 0.28]
    lm[:, R_EYE, :2] = [0.46, 0.28]
    lm[:, L_HIP, :2] = [0.58, 0.9]
    lm[:, R_HIP, :2] = [0.42, 0.9]
    if not hips:
        lm[:, L_HIP, 3] = 0.0
        lm[:, R_HIP, 3] = 0.0
    return lm


def seg(lm, detected=None, expected=None):
    n = len(lm)
    t = np.arange(n) / FPS
    det = np.ones(n, dtype=bool) if detected is None else detected
    hip = np.minimum(lm[:, L_HIP, 3], lm[:, R_HIP, 3]) >= cfg["hip_visibility_threshold"]
    return segment_features(t, lm, det, hip, expected or n, cfg)


def test_wrap_angle():
    assert wrap_angle_90(176.0) == pytest.approx(-4.0)
    assert wrap_angle_90(-179.0) == pytest.approx(1.0)
    assert wrap_angle_90(45.0) == pytest.approx(45.0)
    assert wrap_angle_90(90.0) == pytest.approx(-90.0)


def test_shoulder_tilt_known():
    lm = base_landmarks(50)
    lm[:, L_SHOULDER, 1] = 0.5 + 0.2 * np.tan(np.radians(10))
    assert np.allclose(shoulder_tilt_deg(lm), 10.0, atol=1e-6)
    assert seg(lm)["shoulder_tilt_deg"] == pytest.approx(10.0, abs=1e-6)


def test_shoulder_tilt_swapped_sides_wraps():
    lm = base_landmarks(50)
    lm[:, L_SHOULDER, :2] = [0.4, 0.5]
    lm[:, R_SHOULDER, :2] = [0.6, 0.5 + 0.2 * np.tan(np.radians(10))]
    assert seg(lm)["shoulder_tilt_deg"] == pytest.approx(10.0, abs=1e-6)


def test_level_shoulders_zero_tilt_zero_instability():
    res = seg(base_landmarks(60))
    assert res["shoulder_tilt_deg"] == pytest.approx(0.0, abs=1e-9)
    assert res["shoulder_instability"] == pytest.approx(0.0, abs=1e-9)
    assert res["movement_speed"] == pytest.approx(0.0, abs=1e-9)


def test_movement_speed_known():
    n = 60
    lm = base_landmarks(n)
    shift = 0.02 * np.arange(n)
    for idx in (L_SHOULDER, R_SHOULDER, NOSE, L_EYE, R_EYE, L_HIP, R_HIP):
        lm[:, idx, 0] += shift
    res = seg(lm)
    expected = 0.02 * FPS / 0.2
    assert res["movement_speed"] == pytest.approx(expected, rel=1e-6)


def test_head_height_ratio_known():
    res = seg(base_landmarks(40))
    assert res["head_height_ratio"] == pytest.approx((0.5 - 0.3) / 0.2, rel=1e-6)


def test_torso_lean_known():
    lm = base_landmarks(40)
    dx = 0.4 * np.tan(np.radians(15))
    lm[:, L_SHOULDER, 0] += dx
    lm[:, R_SHOULDER, 0] += dx
    assert np.allclose(torso_lean_deg(lm), 15.0, atol=1e-6)
    assert seg(lm)["torso_lean_deg"] == pytest.approx(15.0, abs=1e-6)


def test_torso_lean_empty_when_hips_hidden():
    res = seg(base_landmarks(40, hips=False))
    assert np.isnan(res["torso_lean_deg"])
    assert not np.isnan(res["shoulder_tilt_deg"])


def test_detection_rate():
    n = 100
    det = np.zeros(n, dtype=bool)
    det[:50] = True
    res = seg(base_landmarks(n), detected=det, expected=n)
    assert res["detection_rate"] == pytest.approx(0.5)
    assert res["n_frames"] == 50


def test_upper_body_features_known():
    f = upper_body_frame_features(base_landmarks(5))
    assert f["shoulder_span"][0] == pytest.approx(0.2)
    assert f["eye_distance"][0] == pytest.approx(0.08)
    assert f["eye_distance_ratio"][0] == pytest.approx(0.4)
    assert f["eye_shoulder_y_ratio"][0] == pytest.approx((0.28 - 0.5) / 0.2)
    assert f["nose_eye_center_offset_x"][0] == pytest.approx(0.0)
    assert f["shoulder_y_diff"][0] == pytest.approx(0.0)
    assert np.allclose(f["shoulder_slope"], f["shoulder_y_diff"])
    assert f["head_tilt_angle"][0] == pytest.approx(0.0)


def test_segment_rows_flags_and_usability():
    n = 1200
    t = np.arange(n) / FPS
    lm = base_landmarks(n, hips=False)
    det = np.ones(n, dtype=bool)
    meta = {"duration_s": float(n / FPS), "fps": 30.0, "n_sampled": n}
    seg_df = pd.DataFrame([
        {"participant": "P01", "segment": "relaxed", "start_s": 0.0, "end_s": np.nan},
        {"participant": "P01", "segment": "B1", "start_s": 10.0, "end_s": 80.0},
        {"participant": "P01", "segment": "B2", "start_s": 85.0, "end_s": 95.0},
    ])
    rows = build_segment_rows("P01", "interview", t, lm, det, meta, seg_df, cfg)
    by = {r["segment"]: r for r in rows}
    assert "relaxed" not in by
    assert by["B1"]["usable"] and not by["B1"]["short"]
    assert "torso_lean_empty_hips_hidden" in by["B1"]["note"]
    assert by["B2"]["short"] and not by["B2"]["usable"]


def test_delta_identity_and_empty_propagation():
    names = cfg["video_feature_names"]
    rows = []
    for seg_name, v in [("relaxed", 1.0), ("B1", 3.0), ("B2", 0.5)]:
        r = {"participant": "P01", "segment": seg_name, "usable": True, "duration_s": 60.0}
        for n in names:
            r[n] = v
        rows.append(r)
    rows[2]["torso_lean_deg"] = np.nan
    d = make_delta_table(pd.DataFrame(rows), cfg)
    assert list(d["segment"]) == ["B1", "B2"]
    assert d.loc[0, "d_shoulder_tilt_deg"] == pytest.approx(2.0)
    assert d.loc[1, "d_shoulder_tilt_deg"] == pytest.approx(-0.5)
    assert np.isnan(d.loc[1, "d_torso_lean_deg"])


def test_blocked_folds_are_contiguous_and_disjoint():
    folds = list(blocked_folds(103, 10))
    seen = np.concatenate([te for _, te in folds])
    assert sorted(seen) == list(range(103))
    for tr, te in folds:
        assert np.all(np.diff(te) == 1)
        assert not set(tr) & set(te)


def test_kappa():
    a = np.array([1, 1, 0, 0, 1, 0])
    assert cohens_kappa(a, a) == pytest.approx(1.0)
    assert cohens_kappa(a, 1 - a) == pytest.approx(-1.0)
