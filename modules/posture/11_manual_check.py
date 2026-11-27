import argparse
import glob
import json
import os
import cv2
import numpy as np
import pandas as pd
from common import load_config, resolve, out_dir, write_run_info, cohens_kappa

ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["make-template", "score"])
ap.add_argument("--participants", nargs="*", default=None)
ap.add_argument("--videos", default=None)
ap.add_argument("--sheet", default=None)
args = ap.parse_args()

cfg = load_config()
out = out_dir(cfg)
mc = cfg["manual_check"]
sheet = args.sheet or os.path.join(out, "manual_check_sheet.csv")

if args.mode == "make-template":
    vdir = args.videos or resolve(cfg, cfg["paths"]["videos"])
    files = sorted(glob.glob(os.path.join(out, "frames", "*_interview_frames.csv")))
    pids = args.participants or [os.path.basename(f).split("_")[0] for f in files][:mc["n_recordings"]]
    rng = np.random.default_rng(cfg["seed"])
    img_dir = out_dir(cfg, "manual_check_frames")
    rows = []
    for pid in pids:
        fr = pd.read_csv(os.path.join(out, "frames", f"{pid}_interview_frames.csv"))
        idx = np.sort(rng.choice(len(fr), size=min(mc["n_samples_per_recording"], len(fr)), replace=False))
        vp = sorted(glob.glob(os.path.join(vdir, f"{pid}_interview.*")))[0]
        cap = cv2.VideoCapture(vp)
        for i in idx:
            r = fr.iloc[i]
            cap.set(cv2.CAP_PROP_POS_MSEC, float(r["t_s"]) * 1000.0)
            ok, frame = cap.read()
            name = f"{pid}_interview_{r['t_s']:.1f}.jpg"
            if ok:
                cv2.imwrite(os.path.join(img_dir, name), frame)
            rows.append({
                "participant": pid,
                "video": "interview",
                "t_s": r["t_s"],
                "image": name,
                "auto_body_visible": int(r["shoulders_visible"]),
                "auto_hips_visible": int(r["hips_visible"]),
                "manual_body_visible": "",
                "manual_hips_visible": "",
            })
        cap.release()
    pd.DataFrame(rows).to_csv(sheet, index=False)
    print("wrote", sheet, "and images in", img_dir)
else:
    s = pd.read_csv(sheet)
    s = s.dropna(subset=["manual_body_visible", "manual_hips_visible"])
    s["manual_body_visible"] = s["manual_body_visible"].astype(int)
    s["manual_hips_visible"] = s["manual_hips_visible"].astype(int)
    result = {"n_samples": int(len(s)), "participants": sorted(s["participant"].unique().tolist()), "status": "preliminary"}
    for key, auto, man in [("body", "auto_body_visible", "manual_body_visible"), ("hips", "auto_hips_visible", "manual_hips_visible")]:
        result[key] = {
            "agreement": float((s[auto] == s[man]).mean()),
            "kappa": cohens_kappa(s[auto].values, s[man].values),
            "auto_positive": int(s[auto].sum()),
            "manual_positive": int(s[man].sum()),
        }
    result["per_participant"] = {
        pid: {
            "body_agreement": float((g["auto_body_visible"] == g["manual_body_visible"]).mean()),
            "hips_agreement": float((g["auto_hips_visible"] == g["manual_hips_visible"]).mean()),
            "n": int(len(g)),
        } for pid, g in s.groupby("participant")
    }
    with open(os.path.join(out, "manual_check_result.json"), "w") as f:
        json.dump(result, f, indent=2)
    write_run_info(cfg, out, {"script": "11_manual_check.py"})
    print(json.dumps(result, indent=2))
