import asyncio

async def debug_trendyol(url: str):
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Görsel mod
        page = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        print("Sayfa yükleniyor...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)
        
        print("\n--- Renk elementleri aranıyor ---")
        
        # Farklı selector'ları test et
        test_selectors = [
            ".slc-img",
            ".color-swatch",
            "[class*='color'] img",
            "[class*='variant'] img",
            ".variants img",
            ".color-list img",
            "img[alt*='renk']",
            "img[alt*='Renk']",
        ]
        
        for sel in test_selectors:
            items = await page.query_selector_all(sel)
            if items:
                print(f"✓ {sel}: {len(items)} element bulundu")
                for item in items[:3]:
                    src = await item.get_attribute("src") or ""
                    alt = await item.get_attribute("alt") or ""
                    print(f"   src: {src[:80]}")
                    print(f"   alt: {alt}")
            else:
                print(f"✗ {sel}: bulunamadı")
        
        print("\n--- Tüm img elementleri ---")
        all_imgs = await page.eval_on_selector_all(
            "img",
            """imgs => imgs
                .filter(img => img.src && img.src.includes('cdn'))
                .slice(0, 10)
                .map(img => ({src: img.src.substring(0, 100), alt: img.alt, w: img.naturalWidth, h: img.naturalHeight}))
            """
        )
        for img in all_imgs:
            print(f"  {img['w']}x{img['h']} | {img['alt']} | {img['src']}")
        
        input("\nTarayıcıyı inceleyebilirsin. Kapatmak için Enter'a bas...")
        await browser.close()

if __name__ == "__main__":
    url = "https://www.trendyol.com/defacto/100-pamuk-oversize-genis-kalip-bisiklet-yaka-basic-duz-kisa-kollu-tisort-e6885axns-p-921307210?boutiqueId=61&merchantId=1188"
    asyncio.run(debug_trendyol(url))