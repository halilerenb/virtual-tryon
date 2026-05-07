from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import shutil
import uuid
from pathlib import Path
import sys
import os
import httpx
import base64

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

COLAB_API_URL = "https://banshee-portal-various.ngrok-free.dev"


@router.post("/pose")
async def pose_estimation(file: UploadFile = File(...)):
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


class ScrapeRequest(BaseModel):
    product_url: str


@router.post("/scrape")
async def scrape_product(request: ScrapeRequest):
    try:
        from ai.scraper.product_scraper import scrape_product_variants
        result = await scrape_product_variants(request.product_url)
        if not result["success"]:
            raise HTTPException(status_code=422, detail=result["error"])
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/virtual-tryon")
async def virtual_tryon(
    person_file: UploadFile = File(...),
    garment_file: UploadFile = File(...),
    mask_type: str = "upper"
):
    try:
        person_bytes = await person_file.read()
        garment_bytes = await garment_file.read()

        person_b64 = base64.b64encode(person_bytes).decode()
        garment_b64 = base64.b64encode(garment_bytes).decode()

        async with httpx.AsyncClient(timeout=300) as client:
            res = await client.post(
                f"{COLAB_API_URL}/tryon",
                json={
                    "person_image": person_b64,
                    "garment_image": garment_b64,
                    "mask_type": mask_type
                }
            )

        data = res.json()

        if not data["success"]:
            raise HTTPException(status_code=500, detail=data["error"])

        result_bytes = base64.b64decode(data["result_image"])
        file_id = str(uuid.uuid4())[:8]
        result_path = OUTPUT_DIR / f"tryon_{file_id}.jpg"

        with open(result_path, "wb") as f:
            f.write(result_bytes)

        return JSONResponse({
            "success": True,
            "result_path": str(result_path),
            "file_id": file_id
        })

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Model zaman aşımına uğradı")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tryon-result/{file_id}")
async def get_tryon_result(file_id: str):
    """Try-on sonuç görselini döndürür."""
    result_path = OUTPUT_DIR / f"tryon_{file_id}.jpg"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Sonuç bulunamadı")
    return FileResponse(str(result_path), media_type="image/jpeg")