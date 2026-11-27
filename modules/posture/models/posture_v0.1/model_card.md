# posture_v0.1 model card

Model: random forest, 300 trees, balanced class weights, seed 42.
Training data: ConfiDetect posture table, 5949 rows (Confident 3132, Neutral 1662, Low 1155).
Features (8): eye_shoulder_y_ratio, shoulder_y_diff, nose_eye_center_offset_x, shoulder_span, eye_distance, head_tilt_angle, eye_distance_ratio, shoulder_slope.
Output: probability of the Confident class, averaged per segment to give posture_prob.

Evaluation: blocked 10-fold cross-validation, macro-F1 0.674 against 0.230 for the majority class.

Limits:
- ConfiDetect labels were assigned by rules on posture cues, so the model largely learns those rules.
- The dataset has no person identifiers, so folds are blocks of consecutive rows.
- The upper_body set is used on our videos because arms, wrists and hips are not visible in head-to-mid-chest framing.
- ConfiDetect Neutral is a rule-based posture pattern and is not the same as the Neutral class from our raters.
- Output is feasibility evidence only and is never used to judge the final system.
