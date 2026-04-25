import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import io

def remove_background(image_path: str, output_path: str = None) -> dict:
    """
    Verilen görselden arka planı kaldırır.
    Kıyafet görselleri için kullanılır.
    """
    try:
        from rembg import remove
    except ImportError:
        return {
            "success": False,
            "error": "rembg kütüphanesi bulunamadı"
        }

    image_path = Path(image_path)
    if not image_path.exists():
        return {
            "success": False,
            "error": f"Görsel bulunamadı: {image_path}"
        }

    # Görseli oku
    with open(image_path, "rb") as f:
        input_data = f.read()

    # Arka planı kaldır
    print("Arka plan kaldırılıyor...")
    output_data = remove(input_data)

    # PIL Image olarak aç
    result_image = Image.open(io.BytesIO(output_data)).convert("RGBA")

    # Kaydet
    if output_path is None:
        output_path = image_path.parent / f"{image_path.stem}_no_bg.png"
    else:
        output_path = Path(output_path)

    result_image.save(str(output_path), "PNG")

    # Maske oluştur (alpha kanalından)
    alpha = np.array(result_image)[:, :, 3]
    mask = (alpha > 128).astype(np.uint8) * 255

    w, h = result_image.size

    return {
        "success": True,
        "output_path": str(output_path),
        "image_size": {"width": w, "height": h},
        "mask_coverage": round(np.sum(mask > 0) / (w * h) * 100, 2)
    }


def segment_garment(image_path: str, output_dir: str = "data/outputs") -> dict:
    """
    Kıyafet görselini segmente eder:
    - Arka planı kaldırır
    - Maske oluşturur
    - Sonuçları kaydeder
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_path = Path(image_path)
    stem = image_path.stem

    no_bg_path = output_dir / f"{stem}_no_bg.png"
    mask_path = output_dir / f"{stem}_mask.png"

    # Arka planı kaldır
    result = remove_background(str(image_path), str(no_bg_path))

    if not result["success"]:
        return result

    # Maskeyi ayrıca kaydet
    from PIL import Image
    img = Image.open(str(no_bg_path)).convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    mask = (alpha > 128).astype(np.uint8) * 255
    mask_img = Image.fromarray(mask)
    mask_img.save(str(mask_path))

    return {
        "success": True,
        "no_bg_path": str(no_bg_path),
        "mask_path": str(mask_path),
        "image_size": result["image_size"],
        "mask_coverage_percent": result["mask_coverage"]
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"Segmentasyon başlıyor: {image_path}")
        result = segment_garment(image_path)
        if result["success"]:
            print(f"✓ Segmentasyon tamamlandı")
            print(f"  Arka plansız görsel: {result['no_bg_path']}")
            print(f"  Maske: {result['mask_path']}")
            print(f"  Kapsama oranı: %{result['mask_coverage_percent']}")
        else:
            print(f"✗ Hata: {result['error']}")
    else:
        print("Kullanım: python segmentor.py <görsel_yolu>")