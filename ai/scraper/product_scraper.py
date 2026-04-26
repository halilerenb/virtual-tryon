import asyncio
import uuid
import httpx
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
import json


async def scrape_product_variants(url: str, output_dir: str = "data/uploads") -> dict:
    """
    E-ticaret URL'sinden ürün görsellerini çeker.
    Playwright gerektirmez — httpx + BeautifulSoup kullanır.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    domain = urlparse(url).netloc.replace("www.", "")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            }
            res = await client.get(url, headers=headers)
            html = res.text
            soup = BeautifulSoup(html, "html.parser")

            # Ürün adı
            product_name = _get_product_name(soup, domain)

            # Görselleri çek
            if "trendyol.com" in domain:
                variants = await _trendyol_images(html, soup, url, output_dir, client, headers)
            elif "hepsiburada.com" in domain:
                variants = await _hepsiburada_images(soup, output_dir, client, headers)
            else:
                variants = await _generic_images(soup, output_dir, client, headers)

            if not variants:
                return {"success": False, "error": "Görsel bulunamadı", "url": url}

            return {
                "success": True,
                "product_name": product_name,
                "domain": domain,
                "variants": variants,
                "total": len(variants)
            }

    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


def _get_product_name(soup, domain: str) -> str:
    """Ürün adını çeker."""
    for sel in ["h1.pr-new-br", "h1[class*='product']", "h1[class*='title']", "h1"]:
        el = soup.select_one(sel)
        if el and el.text.strip():
            return el.text.strip()[:100]
    
    og_title = soup.find("meta", property="og:title")
    if og_title:
        return og_title.get("content", "Ürün")[:100]
    
    return "Ürün"


async def _trendyol_images(html: str, soup, url: str, output_dir: Path, client, headers) -> list:
    """Trendyol'dan ürün görsellerini çeker."""
    image_urls = set()

    # JSON-LD verisinden çek
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                images = data.get("image", [])
                if isinstance(images, str):
                    images = [images]
                for img in images:
                    if img.startswith("http"):
                        image_urls.add(img)
        except:
            continue

    # HTML içinden CDN URL'lerini bul
    cdn_pattern = re.compile(r'https://cdn\.dsmcdn\.com/[^\s"\'\\]+\.jpg')
    found = cdn_pattern.findall(html)
    for img_url in found:
        if "mnresize" in img_url and "icon" not in img_url and "banner" not in img_url:
            # Büyük boyuta çevir
            big = re.sub(r'/mnresize/\d+/\d+/', '/mnresize/1200/1800/', img_url)
            image_urls.add(big)

    # og:image
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        image_urls.add(og["content"])

    # Unique URL'leri indir
    variants = []
    seen_base = set()
    for img_url in list(image_urls)[:6]:
        # Aynı görselin farklı boyutlarını filtrele
        base = re.sub(r'/mnresize/\d+/\d+/', '/', img_url)
        if base in seen_base:
            continue
        seen_base.add(base)

        result = await _download_image(img_url, output_dir, "trendyol", client, headers)
        if result["success"] and result["size_bytes"] > 10000:
            variants.append({
                "color": f"Görsel {len(variants)+1}",
                "image_url": img_url,
                "image_path": result["image_path"],
                "filename": result["filename"]
            })

    return variants


async def _hepsiburada_images(soup, output_dir: Path, client, headers) -> list:
    """Hepsiburada'dan görsel çeker."""
    variants = []
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        result = await _download_image(og["content"], output_dir, "hepsiburada", client, headers)
        if result["success"]:
            variants.append({
                "color": "Varsayılan",
                "image_url": og["content"],
                "image_path": result["image_path"],
                "filename": result["filename"]
            })
    return variants


async def _generic_images(soup, output_dir: Path, client, headers) -> list:
    """Genel görsel çekme."""
    variants = []
    for meta_prop in ["og:image", "twitter:image"]:
        tag = soup.find("meta", property=meta_prop) or soup.find("meta", attrs={"name": meta_prop})
        if tag and tag.get("content"):
            result = await _download_image(tag["content"], output_dir, "generic", client, headers)
            if result["success"]:
                variants.append({
                    "color": "Varsayılan",
                    "image_url": tag["content"],
                    "image_path": result["image_path"],
                    "filename": result["filename"]
                })
            break
    return variants


async def _download_image(image_url: str, output_dir: Path, domain: str, client, headers) -> dict:
    """Görseli indirir."""
    try:
        res = await client.get(image_url, headers=headers)
        content_type = res.headers.get("content-type", "image/jpeg")
        ext = "jpg" if "jpeg" in content_type or "jpg" in image_url else "png"
        filename = f"scraped_{domain}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = output_dir / filename
        with open(filepath, "wb") as f:
            f.write(res.content)
        return {
            "success": True,
            "image_path": str(filepath),
            "image_url": image_url,
            "filename": filename,
            "size_bytes": len(res.content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def scrape_sync(url: str, output_dir: str = "data/uploads") -> dict:
    return asyncio.run(scrape_product_variants(url, output_dir))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = scrape_sync(sys.argv[1])
        if result["success"]:
            print(f"✓ Ürün: {result['product_name']}")
            print(f"  {result['total']} görsel bulundu:")
            for v in result["variants"]:
                print(f"  - {v['color']}: {v['image_path']}")
        else:
            print(f"✗ Hata: {result['error']}")
    else:
        print("Kullanım: python product_scraper.py <url>")