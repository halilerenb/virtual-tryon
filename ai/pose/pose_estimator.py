import cv2
import numpy as np
from pathlib import Path
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

LANDMARK_NAMES = [
    "NOSE", "LEFT_EYE_INNER", "LEFT_EYE", "LEFT_EYE_OUTER",
    "RIGHT_EYE_INNER", "RIGHT_EYE", "RIGHT_EYE_OUTER",
    "LEFT_EAR", "RIGHT_EAR", "MOUTH_LEFT", "MOUTH_RIGHT",
    "LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW",
    "LEFT_WRIST", "RIGHT_WRIST", "LEFT_PINKY", "RIGHT_PINKY",
    "LEFT_INDEX", "RIGHT_INDEX", "LEFT_THUMB", "RIGHT_THUMB",
    "LEFT_HIP", "RIGHT_HIP", "LEFT_KNEE", "RIGHT_KNEE",
    "LEFT_ANKLE", "RIGHT_ANKLE", "LEFT_HEEL", "RIGHT_HEEL",
    "LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX"
]

import os
MODEL_PATH = Path(os.environ.get("POSE_MODEL_PATH", "data/models/pose_landmarker.task"))

def extract_keypoints(image_path: str) -> dict:
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Görsel bulunamadı: {image_path}")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model bulunamadı: {MODEL_PATH}")

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Görsel okunamadı: {image_path}")

    h, w = image.shape[:2]
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=image_rgb
    )

    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        output_segmentation_masks=False,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp_image)

    if not result.pose_landmarks or len(result.pose_landmarks) == 0:
        return {
            "success": False,
            "error": "Vücut tespiti yapılamadı",
            "keypoints": []
        }

    keypoints = []
    for idx, landmark in enumerate(result.pose_landmarks[0]):
        name = LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"POINT_{idx}"
        keypoints.append({
            "id": idx,
            "name": name,
            "x": round(landmark.x * w),
            "y": round(landmark.y * h),
            "x_norm": round(landmark.x, 4),
            "y_norm": round(landmark.y, 4),
            "z": round(landmark.z, 4),
            "visibility": round(landmark.visibility, 4)
        })

    return {
        "success": True,
        "image_size": {"width": w, "height": h},
        "keypoints": keypoints
    }


def get_body_measurements_from_keypoints(keypoints: list) -> dict:
    kp_dict = {kp["name"]: kp for kp in keypoints}
    measurements = {}

    if "LEFT_SHOULDER" in kp_dict and "RIGHT_SHOULDER" in kp_dict:
        ls = kp_dict["LEFT_SHOULDER"]
        rs = kp_dict["RIGHT_SHOULDER"]
        measurements["shoulder_width_px"] = abs(ls["x"] - rs["x"])

    if "LEFT_HIP" in kp_dict and "RIGHT_HIP" in kp_dict:
        lh = kp_dict["LEFT_HIP"]
        rh = kp_dict["RIGHT_HIP"]
        measurements["hip_width_px"] = abs(lh["x"] - rh["x"])

    if "LEFT_SHOULDER" in kp_dict and "LEFT_HIP" in kp_dict:
        ls = kp_dict["LEFT_SHOULDER"]
        lh = kp_dict["LEFT_HIP"]
        measurements["torso_height_px"] = abs(ls["y"] - lh["y"])

    return measurements


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = extract_keypoints(sys.argv[1])
        if result["success"]:
            print(f"✓ {len(result['keypoints'])} keypoint tespit edildi")
            print(f"  Görsel boyutu: {result['image_size']}")
            measurements = get_body_measurements_from_keypoints(result["keypoints"])
            print(f"  Ölçümler: {measurements}")
            for kp in result["keypoints"][:5]:
                print(f"  {kp['name']}: ({kp['x']}, {kp['y']})")
        else:
            print(f"✗ Hata: {result['error']}")
    else:
        print("Kullanım: python pose_estimator.py <görsel_yolu>")