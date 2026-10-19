import os
import sys
import time
import json
import urllib.request
import urllib.parse
import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = r"c:\Users\rinit\.gemini\antigravity\playground\shadow-ionosphere\telugu-food-scanner\tests\web_harvest_agent1"
APP_DIR = r"c:\Users\rinit\.gemini\antigravity\playground\shadow-ionosphere\telugu-food-scanner"
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

IMG_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

DISH_LIST = [
    {
        "index": 1,
        "dish_label": "Hyderabadi Chicken Biryani",
        "search_query": "Hyderabadi Chicken Biryani",
        "filename": "01_Hyderabadi_Chicken_Biryani.jpg",
        "wiki_title": "File:Shrimp Biriyani.JPG / Homemade Biryani Plate",
    },
    {
        "index": 2,
        "dish_label": "Masala Dosa",
        "search_query": "Masala Dosa",
        "filename": "02_Masala_Dosa.jpg",
        "wiki_title": "File:Masala dosa 01.jpg",
    },
    {
        "index": 3,
        "dish_label": "Idli with Sambar & Chutney",
        "search_query": "Idli Sambar",
        "filename": "03_Idli_Sambar.jpg",
        "wiki_title": "File:Idli Sambar-Noida-UP-SP004.jpg",
    },
    {
        "index": 4,
        "dish_label": "Medu Vada (Minapa Garelu)",
        "search_query": "Medu Vada",
        "filename": "04_Medu_Vada.jpg",
        "wiki_title": "File:Aesthetic Medu Vadai.jpg",
    },
    {
        "index": 5,
        "dish_label": "Pesarattu (Green Moong Dosa)",
        "search_query": "Pesarattu dosa",
        "filename": "05_Pesarattu_dosa.jpg",
        "wiki_title": "File:Pesarattu.jpg",
    },
    {
        "index": 6,
        "dish_label": "Pulihora (Tamarind Rice)",
        "search_query": "Pulihora",
        "filename": "06_Pulihora_rice.jpg",
        "wiki_title": "File:A background of tamarind rice ~ A specialitate of South India.jpg",
    },
    {
        "index": 7,
        "dish_label": "Upma (Rava Upma)",
        "search_query": "Rava Upma",
        "filename": "07_Upma_dish.jpg",
        "wiki_title": "File:Poori Upma Tarkari.jpg",
    },
    {
        "index": 8,
        "dish_label": "Curd Rice (Perugu Annam / Daddojanam)",
        "search_query": "Curd rice",
        "filename": "08_Curd_rice_South_India.jpg",
        "wiki_title": "File:Cool and Colorful - Curd Rice.jpg",
    },
    {
        "index": 9,
        "dish_label": "Sambar / Pappu Charu",
        "search_query": "Sambar",
        "filename": "09_Sambar.jpg",
        "wiki_title": "File:Sambar.jpg",
    },
    {
        "index": 10,
        "dish_label": "Mirchi Bajji (Stuffed Chili Fritters)",
        "search_query": "Mirchi Bajji",
        "filename": "10_Mirchi_Bajji.jpg",
        "wiki_title": "File:Andhra famous mirchi bajji.JPG",
    },
    {
        "index": 11,
        "dish_label": "Chicken 65 / Kodi Vepudu (Chicken Fry)",
        "search_query": "Chicken 65",
        "filename": "11_Chicken_65_dish.jpg",
        "wiki_title": "File:Chicken65.jpg",
    },
    {
        "index": 12,
        "dish_label": "Poori with Potato Masala / Curry",
        "search_query": "Poori curry Indian",
        "filename": "12_Poori_curry_Indian.jpg",
        "wiki_title": "File:Jeera Puri sabji.jpg",
    },
]

HEADERS = {
    "User-Agent": "TeluguFoodScannerTestBot/1.0 (https://example.org; contact@example.org) Python-urllib/3.11"
}

def ensure_image(item: dict) -> dict:
    local_path = os.path.join(IMG_DIR, item["filename"])
    if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
        return {
            "dish_label": item["dish_label"],
            "search_query": item["search_query"],
            "wiki_title": item["wiki_title"],
            "local_path": local_path,
            "mime": "image/jpeg",
            "size_bytes": os.path.getsize(local_path),
        }

    # Try downloading from Wikimedia Commons if not cached locally
    params = urllib.parse.urlencode({
        "action": "query",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {item['search_query']}",
        "gsrnamespace": 6,
        "gsrlimit": 10,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": 800,
        "format": "json"
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    pages = data.get("query", {}).get("pages", {})
    sorted_pages = sorted(pages.values(), key=lambda p: p.get("index", 999))
    for page in sorted_pages:
        title = page.get("title", "")
        iinfo = page.get("imageinfo", [{}])[0]
        mime = iinfo.get("mime", "")
        if mime not in ("image/jpeg", "image/png"):
            continue
        img_url = iinfo.get("thumburl") or iinfo.get("url")
        if not img_url:
            continue
        img_req = urllib.request.Request(img_url, headers=HEADERS)
        with urllib.request.urlopen(img_req, timeout=20) as img_resp:
            img_bytes = img_resp.read()
        if len(img_bytes) > 5000:
            with open(local_path, "wb") as f:
                f.write(img_bytes)
            return {
                "dish_label": item["dish_label"],
                "search_query": item["search_query"],
                "wiki_title": title,
                "local_path": local_path,
                "mime": mime,
                "size_bytes": len(img_bytes),
            }
    raise RuntimeError(f"Could not obtain image for {item['dish_label']}")

def main():
    from fastapi.testclient import TestClient
    from app import app

    models = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemma-4-31b-it"]
    results = []

    http_client = httpx.Client(timeout=90.0)
    asgi_client = TestClient(app)

    for idx, item in enumerate(DISH_LIST, start=1):
        dish_label = item["dish_label"]
        print(f"[{idx}/{len(DISH_LIST)}] Preparing: {dish_label}...", flush=True)
        try:
            meta = ensure_image(item)
            print(f"  -> Image ready: {meta['wiki_title']} ({meta['size_bytes']} bytes)", flush=True)
        except Exception as e:
            print(f"  -> Skipping {dish_label} (no image): {e}", flush=True)
            continue

        model_choice = models[(idx - 1) % len(models)]
        print(f"  -> Scanning with preferred_model={model_choice}...", flush=True)

        t0 = time.perf_counter()
        resp = None
        transport_used = "http://localhost:8005"
        try:
            with open(meta["local_path"], "rb") as f:
                files = {"file": (os.path.basename(meta["local_path"]), f, meta["mime"])}
                data = {"preferred_model": model_choice}
                resp = http_client.post("http://localhost:8005/api/v1/scan", files=files, data=data)
        except Exception as net_err:
            transport_used = "TestClient(app) [http://localhost:8005/api/v1/scan]"
            with open(meta["local_path"], "rb") as f:
                files = {"file": (os.path.basename(meta["local_path"]), f, meta["mime"])}
                data = {"preferred_model": model_choice}
                resp = asgi_client.post("http://localhost:8005/api/v1/scan", files=files, data=data)

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        if resp is not None and resp.status_code == 200:
            scan_json = resp.json()
            meta["status"] = "OK"
            meta["http_status"] = 200
            meta["transport"] = transport_used
            meta["preferred_model"] = model_choice
            meta["client_elapsed_ms"] = elapsed_ms
            meta["scan_result"] = scan_json
            totals = scan_json.get("totals", {})
            items_det = scan_json.get("items", [])
            first_item = f"{items_det[0].get('name_en')} ({items_det[0].get('name_te')})" if items_det else "None"
            print(
                f"  -> Recognized: '{scan_json.get('plate_title_en')}' | Primary: {first_item} | "
                f"Cal: {totals.get('calories')} kcal, Pro: {totals.get('protein_g')}g, "
                f"Fe: {totals.get('iron_mg')}mg, Ca: {totals.get('calcium_mg')}mg | "
                f"Model: {scan_json.get('model_used')} ({scan_json.get('latency_ms')} ms)",
                flush=True
            )
        else:
            meta["status"] = "HTTP_ERROR"
            meta["http_status"] = resp.status_code if resp is not None else None
            meta["error_text"] = resp.text[:500] if resp is not None else "No response"
            print(f"  -> Error: {meta['http_status']} {meta['error_text']}", flush=True)

        results.append(meta)
        if idx < len(DISH_LIST):
            time.sleep(3.5)

    out_file = os.path.join(BASE_DIR, "results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} results to {out_file}", flush=True)

if __name__ == "__main__":
    main()
