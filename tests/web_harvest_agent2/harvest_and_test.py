import os
import sys
import time
import json
import urllib.request
import urllib.parse
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"c:\Users\rinit\.gemini\antigravity\playground\shadow-ionosphere\telugu-food-scanner\tests\web_harvest_agent2"
IMAGES_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "TeluguFoodScannerTestBot/2.0 (https://example.org/food-scanner; test@example.org) Python-urllib/3.11"
}

DISH_QUERIES = [
    {"id": "01_masala_chai", "ground_truth": "Masala Chai (Indian Milk Tea)", "queries": ["Masala chai cup", "Indian masala tea cup"], "force_redownload": False},
    {"id": "02_veg_hakka_noodles", "ground_truth": "Veg Hakka Noodles / Chowmein", "queries": ["Veg Hakka Noodles", "Vegetable chow mein Indian"], "force_redownload": False},
    {"id": "03_ripe_banana", "ground_truth": "Ripe Banana", "queries": ["Single ripe banana fruit", "Cavendish banana fruit"], "force_redownload": False},
    {"id": "04_egg_curry", "ground_truth": "Egg Curry (Guddu Pulusu / Boiled Egg Masala)", "queries": ["Spicy Anda Curry", "Indian egg curry"], "force_redownload": False},
    {"id": "05_paneer_butter_masala", "ground_truth": "Paneer Butter Masala", "queries": ["Paneer butter masala", "Paneer makhani dish"], "force_redownload": False},
    {"id": "06_samosa", "ground_truth": "Samosa (with Chole)", "queries": ["Indian samosa plate", "Punjabi samosa"], "force_redownload": False},
    {"id": "07_aloo_gobi", "ground_truth": "Aloo Gobi (Potato Cauliflower Curry)", "queries": ["Aloo gobi dish", "Aloo gobhi Indian"], "force_redownload": False},
    {"id": "08_roti_chapati", "ground_truth": "Roti / Chapati", "queries": ["Roti, Indian flatbread", "Phulka chapati plate"], "force_redownload": True},
    {"id": "09_gulab_jamun", "ground_truth": "Gulab Jamun", "queries": ["Gulab jamun bowl", "Gulab jamun Indian sweet"], "force_redownload": False},
    {"id": "10_chole_masala", "ground_truth": "Chole / Chana Masala", "queries": ["Chana masala dish", "Chole masala bowl"], "force_redownload": True},
    {"id": "11_omelette", "ground_truth": "Egg Omelette", "queries": ["Masala omelette Indian", "Egg omelette plate"], "force_redownload": False},
    {"id": "12_apple_fruit", "ground_truth": "Red Apple Fruit", "queries": ["Red apple fruit whole", "Fresh red apple"], "force_redownload": False}
]

def search_and_download_wikimedia(dish_entry):
    dish_id = dish_entry["id"]
    existing_jpg = os.path.join(IMAGES_DIR, f"{dish_id}.jpg")
    existing_png = os.path.join(IMAGES_DIR, f"{dish_id}.png")
    if not dish_entry.get("force_redownload"):
        for p, mime in [(existing_jpg, "image/jpeg"), (existing_png, "image/png")]:
            if os.path.exists(p) and os.path.getsize(p) > 5000:
                print(f"[CACHED] {dish_id} -> {p} ({os.path.getsize(p)} bytes)")
                return {
                    "local_path": p,
                    "wiki_title": f"Cached:{os.path.basename(p)}",
                    "img_url": "https://commons.wikimedia.org/",
                    "mime": mime,
                    "bytes": os.path.getsize(p)
                }

    for query in dish_entry["queries"]:
        params = urllib.parse.urlencode({
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": 6,
            "gsrlimit": 8,
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": 800,
            "format": "json"
        })
        url = f"https://commons.wikimedia.org/w/api.php?{params}"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            sorted_pages = sorted(pages.values(), key=lambda x: x.get("index", 999))
            for page in sorted_pages:
                title = page.get("title", "").lower()
                if any(bad in title for bad in ["icon", "logo", "map", "diagram", "stamp", "chart", "sign", "vector", "making", "tiffin", ".svg", ".tif", ".pdf"]):
                    continue
                iinfo = page.get("imageinfo", [{}])[0]
                mime = iinfo.get("mime", "")
                if mime not in ("image/jpeg", "image/png"):
                    continue
                img_url = iinfo.get("thumburl") or iinfo.get("url")
                if not img_url:
                    continue
                ext = ".jpg" if "jpeg" in mime or img_url.lower().endswith(".jpg") or img_url.lower().endswith(".jpeg") else ".png"
                local_path = os.path.join(IMAGES_DIR, f"{dish_id}{ext}")
                img_req = urllib.request.Request(img_url, headers=HEADERS)
                with urllib.request.urlopen(img_req, timeout=20) as img_resp:
                    img_bytes = img_resp.read()
                if len(img_bytes) < 5000:
                    continue
                with open(local_path, "wb") as f:
                    f.write(img_bytes)
                print(f"[DOWNLOADED] {dish_id} -> {page.get('title')} ({len(img_bytes)} bytes) from {img_url}")
                return {
                    "local_path": local_path,
                    "wiki_title": page.get("title"),
                    "img_url": img_url,
                    "mime": mime,
                    "bytes": len(img_bytes)
                }
        except Exception as e:
            print(f"[WARN] Error searching {query}: {e}")
        time.sleep(0.5)
    return None

def main():
    results = []
    models = ["gemma-4-31b-it", "gemini-3.5-flash-lite"]
    
    print("=== STEP 1: HARVESTING 12 REAL FOOD IMAGES FROM WIKIMEDIA COMMONS ===")
    downloaded_items = []
    for idx, dish in enumerate(DISH_QUERIES):
        dl_info = search_and_download_wikimedia(dish)
        if dl_info:
            dish_copy = dict(dish)
            dish_copy.update(dl_info)
            downloaded_items.append(dish_copy)
        else:
            print(f"[ERROR] Failed to download image for {dish['id']}")

    print(f"\nSuccessfully prepared {len(downloaded_items)}/{len(DISH_QUERIES)} images.")
    
    print("\n=== STEP 2: SCANNING IMAGES AGAINST LIVE SERVER http://localhost:8005 ===")
    with httpx.Client(timeout=120.0) as client:
        for idx, item in enumerate(downloaded_items):
            preferred_model = models[idx % len(models)]
            if idx > 0:
                print("Waiting 4.0 seconds for rate-limit spacing...")
                time.sleep(4.0)
            
            t0 = time.perf_counter()
            rec = None
            try:
                with open(item["local_path"], "rb") as f:
                    files = {"file": (os.path.basename(item["local_path"]), f, item["mime"])}
                    data = {"preferred_model": preferred_model}
                    resp = client.post("http://localhost:8005/api/v1/scan", files=files, data=data)
                elapsed_ms = round((time.perf_counter() - t0) * 1000)
                if resp.status_code == 200:
                    payload = resp.json()
                    items_list = payload.get("items", [])
                    first_item = items_list[0] if items_list else {}
                    totals = payload.get("totals", {})
                    rec = {
                        "id": item["id"],
                        "ground_truth": item["ground_truth"],
                        "wiki_title": item["wiki_title"],
                        "img_url": item["img_url"],
                        "local_path": item["local_path"],
                        "requested_model": preferred_model,
                        "model_used": payload.get("model_used"),
                        "latency_ms": payload.get("analysis_ms") or elapsed_ms,
                        "wall_ms": elapsed_ms,
                        "plate_title_en": payload.get("plate_title_en"),
                        "plate_title_te": payload.get("plate_title_te"),
                        "primary_item_en": first_item.get("name_en"),
                        "primary_item_te": first_item.get("name_te"),
                        "primary_serving_g": first_item.get("estimated_serving_g"),
                        "primary_source": first_item.get("nutrition_source"),
                        "all_items": [
                            {
                                "name_en": it.get("name_en"),
                                "name_te": it.get("name_te"),
                                "serving_g": it.get("estimated_serving_g"),
                                "calories": it.get("calories"),
                                "protein_g": it.get("protein_g"),
                                "iron_mg": it.get("iron_mg"),
                                "calcium_mg": it.get("calcium_mg"),
                                "source": it.get("nutrition_source")
                            }
                            for it in items_list
                        ],
                        "totals": {
                            "weight_g": totals.get("weight_g"),
                            "calories": totals.get("calories"),
                            "protein_g": totals.get("protein_g"),
                            "carbs_g": totals.get("carbs_g"),
                            "fat_g": totals.get("fat_g"),
                            "fiber_g": totals.get("fiber_g"),
                            "iron_mg": totals.get("iron_mg"),
                            "calcium_mg": totals.get("calcium_mg"),
                        },
                        "status": "OK"
                    }
                else:
                    rec = {
                        "id": item["id"],
                        "ground_truth": item["ground_truth"],
                        "wiki_title": item["wiki_title"],
                        "local_path": item["local_path"],
                        "requested_model": preferred_model,
                        "status": f"HTTP_{resp.status_code}",
                        "error": resp.text[:400]
                    }
            except Exception as e:
                rec = {
                    "id": item["id"],
                    "ground_truth": item["ground_truth"],
                    "wiki_title": item["wiki_title"],
                    "local_path": item["local_path"],
                    "requested_model": preferred_model,
                    "status": "EXCEPTION",
                    "error": str(e)
                }
            results.append(rec)
            # Safe print outside try/except block
            if rec.get("status") == "OK":
                print(
                    f"[{idx+1}/{len(downloaded_items)}] {item['ground_truth']} -> "
                    f"Plate: '{rec['plate_title_en']}' | Primary: '{rec['primary_item_en']}' | "
                    f"Kcal: {rec['totals']['calories']}, P: {rec['totals']['protein_g']}g, "
                    f"Fe: {rec['totals']['iron_mg']}mg, Ca: {rec['totals']['calcium_mg']}mg | "
                    f"Model: {rec['model_used']} ({rec['latency_ms']}ms)"
                )
            else:
                print(f"[{idx+1}/{len(downloaded_items)}] {item['ground_truth']} -> {rec.get('status')}: {rec.get('error')}")

            # Save incremental results after each scan
            report_path = os.path.join(BASE_DIR, "agent2_scan_results.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved full JSON results to {os.path.join(BASE_DIR, 'agent2_scan_results.json')}")

if __name__ == "__main__":
    main()
