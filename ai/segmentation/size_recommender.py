from pathlib import Path
import json


# Standart beden tabloları (cm cinsinden)
# Gerçek ürünlerde bu tablo ürün sayfasından çekilecek
DEFAULT_SIZE_CHARTS = {
    "unisex": {
        "XS": {"chest": (76, 84), "waist": (60, 68), "hip": (80, 88)},
        "S":  {"chest": (84, 92), "waist": (68, 76), "hip": (88, 96)},
        "M":  {"chest": (92, 100), "waist": (76, 84), "hip": (96, 104)},
        "L":  {"chest": (100, 108), "waist": (84, 92), "hip": (104, 112)},
        "XL": {"chest": (108, 116), "waist": (92, 100), "hip": (112, 120)},
        "XXL":{"chest": (116, 124), "waist": (100, 108), "hip": (120, 128)},
    },
    "women": {
        "XS": {"chest": (76, 82), "waist": (58, 64), "hip": (82, 88)},
        "S":  {"chest": (82, 88), "waist": (64, 70), "hip": (88, 94)},
        "M":  {"chest": (88, 94), "waist": (70, 76), "hip": (94, 100)},
        "L":  {"chest": (94, 100), "waist": (76, 82), "hip": (100, 106)},
        "XL": {"chest": (100, 106), "waist": (82, 88), "hip": (106, 112)},
        "XXL":{"chest": (106, 112), "waist": (88, 94), "hip": (112, 118)},
    },
    "men": {
        "XS": {"chest": (82, 88), "waist": (68, 74), "hip": (82, 88)},
        "S":  {"chest": (88, 96), "waist": (74, 80), "hip": (88, 94)},
        "M":  {"chest": (96, 104), "waist": (80, 86), "hip": (94, 100)},
        "L":  {"chest": (104, 112), "waist": (86, 92), "hip": (100, 106)},
        "XL": {"chest": (112, 120), "waist": (92, 98), "hip": (106, 112)},
        "XXL":{"chest": (120, 128), "waist": (98, 104), "hip": (112, 118)},
    }
}


def recommend_size(
    chest: float,
    waist: float,
    hip: float,
    height: float = None,
    weight: float = None,
    gender: str = "unisex",
    size_chart: dict = None
) -> dict:
    """
    Kullanıcı ölçülerine göre beden tavsiyesi yapar.

    Parametreler:
        chest: Göğüs çevresi (cm)
        waist: Bel çevresi (cm)
        hip: Kalça çevresi (cm)
        height: Boy (cm) — opsiyonel
        weight: Kilo (kg) — opsiyonel
        gender: 'men', 'women', 'unisex'
        size_chart: Özel beden tablosu (opsiyonel)

    Döndürür:
        Tavsiye edilen beden ve detaylar
    """
    chart = size_chart or DEFAULT_SIZE_CHARTS.get(gender, DEFAULT_SIZE_CHARTS["unisex"])

    scores = {}

    for size, measurements in chart.items():
        score = 0
        total = 0

        if "chest" in measurements:
            min_c, max_c = measurements["chest"]
            if min_c <= chest <= max_c:
                score += 3  # Göğüs en önemli ölçü
            elif chest < min_c:
                score += max(0, 3 - (min_c - chest) / 4)
            else:
                score += max(0, 3 - (chest - max_c) / 4)
            total += 3

        if "waist" in measurements:
            min_w, max_w = measurements["waist"]
            if min_w <= waist <= max_w:
                score += 2
            elif waist < min_w:
                score += max(0, 2 - (min_w - waist) / 4)
            else:
                score += max(0, 2 - (waist - max_w) / 4)
            total += 2

        if "hip" in measurements:
            min_h, max_h = measurements["hip"]
            if min_h <= hip <= max_h:
                score += 2
            elif hip < min_h:
                score += max(0, 2 - (min_h - hip) / 4)
            else:
                score += max(0, 2 - (hip - max_h) / 4)
            total += 2

        scores[size] = round(score / total * 100, 1) if total > 0 else 0

    # En yüksek skora göre sırala
    sorted_sizes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    recommended = sorted_sizes[0][0]
    confidence = sorted_sizes[0][1]

    # Fit tipi belirle
    fit_type = _determine_fit(chest, waist, hip, chart, recommended)

    # BMI hesapla (opsiyonel)
    bmi = None
    if height and weight and height > 0:
        bmi = round(weight / ((height / 100) ** 2), 1)

    return {
        "recommended_size": recommended,
        "confidence_percent": confidence,
        "fit_type": fit_type,
        "all_scores": dict(sorted_sizes),
        "input_measurements": {
            "chest_cm": chest,
            "waist_cm": waist,
            "hip_cm": hip,
            "height_cm": height,
            "weight_kg": weight,
            "bmi": bmi
        },
        "size_up_option": sorted_sizes[1][0] if len(sorted_sizes) > 1 else None,
        "advice": _generate_advice(confidence, fit_type, recommended)
    }


def _determine_fit(chest, waist, hip, chart, size) -> str:
    """Kıyafetin nasıl oturacağını belirler."""
    if size not in chart:
        return "normal"

    measurements = chart[size]
    chest_mid = sum(measurements["chest"]) / 2 if "chest" in measurements else chest
    waist_mid = sum(measurements["waist"]) / 2 if "waist" in measurements else waist

    chest_diff = chest - chest_mid
    waist_diff = waist - waist_mid

    if chest_diff < -4 or waist_diff < -4:
        return "loose"  # Bol
    elif chest_diff > 4 or waist_diff > 4:
        return "tight"  # Dar
    else:
        return "regular"  # Normal


def _generate_advice(confidence: float, fit_type: str, size: str) -> str:
    """Kullanıcıya tavsiye metni oluşturur."""
    if confidence >= 80:
        base = f"{size} beden tam ölçünüze uygun."
    elif confidence >= 60:
        base = f"{size} beden ölçünüze yakın, iyi oturabilir."
    else:
        base = f"{size} beden en yakın seçenek, denemenizi öneririz."

    if fit_type == "loose":
        base += " Kıyafet biraz bol düşebilir."
    elif fit_type == "tight":
        base += " Kıyafet biraz dar gelebilir, bir üst bedeni değerlendirebilirsiniz."

    return base


if __name__ == "__main__":
    # Test
    result = recommend_size(
        chest=92,
        waist=76,
        hip=98,
        height=175,
        weight=70,
        gender="unisex"
    )

    print(f"Tavsiye edilen beden: {result['recommended_size']}")
    print(f"Güven oranı: %{result['confidence_percent']}")
    print(f"Fit tipi: {result['fit_type']}")
    print(f"Tavsiye: {result['advice']}")
    print(f"Tüm bedenler: {result['all_scores']}")
    if result.get('bmi'):
        print(f"BMI: {result['bmi']}")