from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import uuid
from pathlib import Path
import sys
import os

project_root = Path(__file__).parents[4]
MODEL_PATH = project_root / "data" / "models" / "pose_landmarker.task"
os.environ["POSE_MODEL_PATH"] = str(MODEL_PATH)
sys.path.insert(0, str(project_root))

from ai.pose.pose_estimator import extract_keypoints, get_body_measurements_from_keypoints
from ai.segmentation.segmentor import segment_garment
from ai.segmentation.size_recommender import recommend_size

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

UPLOAD_DIR = Path("data/uploads")
OUTPUT_DIR = Path("data/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/pose")
async def pose_estimation(file: UploadFile = File(...)):
    """
    Kullanıcı fotoğrafından vücut keypoint'lerini çıkarır.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Sadece görsel dosyaları kabul edilir")

    file_id = str(uuid.uuid4())[:8]
    suffix = Path(file.filename).suffix
    save_path = UPLOAD_DIR / f"pose_{file_id}{suffix}"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = extract_keypoints(str(save_path))
        if not result["success"]:
            raise HTTPException(status_code=422, detail=result["error"])

        measurements = get_body_measurements_from_keypoints(result["keypoints"])

        return JSONResponse({
            "success": True,
            "file_id": file_id,
            "image_size": result["image_size"],
            "keypoint_count": len(result["keypoints"]),
            "keypoints": result["keypoints"],
            "measurements": measurements
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment")
async def segmentation(file: UploadFile = File(...)):
    """
    Kıyafet görselinden arka planı kaldırır ve maske oluşturur.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Sadece görsel dosyaları kabul edilir")

    file_id = str(uuid.uuid4())[:8]
    suffix = Path(file.filename).suffix
    save_path = UPLOAD_DIR / f"garment_{file_id}{suffix}"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = segment_garment(str(save_path), str(OUTPUT_DIR))
        if not result["success"]:
            raise HTTPException(status_code=422, detail=result["error"])

        return JSONResponse({
            "success": True,
            "file_id": file_id,
            "image_size": result["image_size"],
            "mask_coverage_percent": result["mask_coverage_percent"],
            "no_bg_path": result["no_bg_path"],
            "mask_path": result["mask_path"]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/size-recommend")
async def size_recommendation(
    chest: float,
    waist: float,
    hip: float,
    height: float = None,
    weight: float = None,
    gender: str = "unisex"
):
    """
    Kullanıcı ölçülerine göre beden tavsiyesi yapar.
    """
    try:
        result = recommend_size(
            chest=chest,
            waist=waist,
            hip=hip,
            height=height,
            weight=weight,
            gender=gender
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))