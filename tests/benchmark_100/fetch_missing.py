import os
import sys
import json
import urllib.request
import urllib.parse
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGET_DIR = r"c:\Users\rinit\.gemini\antigravity\playground\shadow-ionosphere\telugu-food-scanner\tests\benchmark_100\downloaded"
os.makedirs(TARGET_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "TeluguFoodScannerCurator/1.0 (https://example.org/telugu-food; curator@example.org) Python-urllib/3.14"
}

ITEMS_TO_FETCH = [
    {
        "id": "ragi_sangati",
        "name": "Ragi Sangati (Finger Millet Ball)",
        "queries": ["Ragi mudde", "Ragi sangati", "Finger millet ball"]
    },
    {
        "id": "steamed_rice_pappu",
        "name": "Steamed White Rice with Pappu",
        "queries": ["Dal rice plate Indian", "Rice and dal Indian", "Steamed rice with dal"]
    },
    {
        "id": "boiled_sweet_potato",
        "name": "Boiled Sweet Potato (Chilakada Dumpa)",
        "queries": ["Boiled sweet potato", "Cooked sweet potato pieces", "Steamed sweet potato"]
    },
    {
        "id": "cucumber_slices",
        "name": "Cucumber Slices Salad (Keera Dosakaya)",
        "queries": ["Sliced cucumber salad", "Fresh cucumber slices", "Cucumber slices plate"]
    },
    {
        "id": "mixed_healthy_bowl",
        "name": "Mixed Healthy Bowl",
        "queries": ["Fresh vegetable salad bowl", "Vegetable salad bowl", "Healthy garden salad bowl", "Salad bowl carrot cucumber"]
    },
    {
        "id": "boiled_eggs",
        "name": "Boiled Eggs (Guddu)",
        "queries": ["Boiled eggs halved", "Hard boiled eggs", "Hard-boiled eggs plate"]
    }
]

def search_and_download(item):
    item_id = item["id"]
    for query in item["queries"]:
        params = urllib.parse.urlencode({
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": 6,
            "gsrlimit": 10,
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 1000,
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
                if any(bad in title for bad in ["icon", "logo", "map", "diagram", "stamp", "chart", "sign", "vector", ".svg", ".tif", ".pdf", ".ogg"]):
                    continue
                iinfo = page.get("imageinfo", [{}])[0]
                mime = iinfo.get("mime", "")
                if mime not in ("image/jpeg", "image/png"):
                    continue
                img_url = iinfo.get("thumburl") or iinfo.get("url")
                if not img_url:
                    continue
                ext = ".jpg" if "jpeg" in mime or ".jpg" in img_url.lower() or ".jpeg" in img_url.lower() else ".png"
                local_path = os.path.join(TARGET_DIR, f"{item_id}{ext}")
                
                img_req = urllib.request.Request(img_url, headers=HEADERS)
                with urllib.request.urlopen(img_req, timeout=20) as img_resp:
                    img_bytes = img_resp.read()
                if len(img_bytes) < 10000:
                    continue
                with open(local_path, "wb") as f:
                    f.write(img_bytes)
                
                # verify image with PIL
                with Image.open(local_path) as im:
                    im.verify()
                
                print(f"[OK] Downloaded {item_id}: {page.get('title')} ({len(img_bytes)} bytes) -> {local_path}")
                return local_path
        except Exception as e:
            print(f"[WARN] Error with query '{query}': {e}")
    return None

results = {}
for item in ITEMS_TO_FETCH:
    res = search_and_download(item)
    results[item["id"]] = res

print("\nFetch Summary:")
for k, v in results.items():
    print(f"  {k}: {v}")
