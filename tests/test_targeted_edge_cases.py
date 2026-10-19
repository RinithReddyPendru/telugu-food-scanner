import json
import pathlib
import sys
import time
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BENCHMARK_DIR = pathlib.Path(__file__).resolve().parent / "benchmark_100"
IMAGES_DIR = BENCHMARK_DIR / "images"

CASES = [
    {
        "test_id": "TEST-082",
        "file": "082_Pesarattu.jpg",
        "expected": "Pesarattu / MLA Upma Pesarattu",
        "expected_keywords": ["pesarattu", "mla pesarattu", "upma pesarattu"],
    },
    {
        "test_id": "TEST-044",
        "file": "044_Guddu_Porutu_Egg_Bhurji.jpg",
        "expected": "Guddu Porutu (Egg Bhurji)",
        "expected_keywords": ["guddu", "porutu", "egg", "bhurji"],
    },
    {
        "test_id": "TEST-065",
        "file": "065_Dosakaya_Mukkala_Pulusu.jpg",
        "expected": "Dosakaya Mukkala Pulusu",
        "expected_keywords": ["dosakaya", "pulusu", "cucumber"],
    },
    {
        "test_id": "TEST-068",
        "file": "068_Chamadumpa_Vepudu.jpg",
        "expected": "Chamadumpa Pulusu / Colocasia",
        "expected_keywords": ["chamadumpa", "colocasia", "arbi", "taro"],
    },
    {
        "test_id": "TEST-075",
        "file": "075_Gongura_Mutton.jpg",
        "expected": "Gongura Mutton (Gongura Mamsam)",
        "expected_keywords": ["gongura mutton", "gongura mamsam", "gongura", "mutton", "mamsam"],
    },
    {
        "test_id": "TEST-090",
        "file": "090_Rava_Upma.jpg",
        "expected": "Rava Upma with Sambar",
        "expected_keywords": ["upma", "rava upma", "suji upma"],
    },
]

print("=" * 60)
print("TESTING 6 TARGETED TELUGU EDGE-CASE DISHES")
print("=" * 60)

passed = 0

for c in CASES:
    img_path = IMAGES_DIR / c["file"]
    if not img_path.exists():
        print(f"[{c['test_id']}] File not found: {img_path}")
        continue
    
    print(f"\nScanning [{c['test_id']}] {c['file']} (Expected: {c['expected']})...")
    t0 = time.perf_counter()
    resp = requests.post(
        "http://localhost:8005/api/v1/scan",
        files={"file": open(img_path, "rb")},
        data={"preferred_model": "gemini-3.5-flash-lite"},
        timeout=60,
    )
    elapsed = int((time.perf_counter() - t0) * 1000)
    
    if resp.status_code != 200:
        print(f"  -> HTTP {resp.status_code}: {resp.text[:120]}")
        continue
        
    data = resp.json()
    title_en = data.get("plate_title_en", "")
    title_te = data.get("plate_title_te", "")
    items = data.get("items", [])
    item_names = [it.get("name_en", "") for it in items]
    catalog_ids = [it.get("catalog_id", "") for it in items]
    
    all_text = (title_en + " " + " ".join(item_names)).lower()
    is_match = any(k in all_text for k in c["expected_keywords"])
    
    status_str = "PASS [EXACT/SEMANTIC MATCH]" if is_match else "FAIL [MISMATCH]"
    if is_match:
        passed += 1
        
    print(f"  Result: {status_str} ({elapsed}ms)")
    print(f"  Title EN:   {title_en}")
    print(f"  Title TE:   {title_te}")
    print(f"  Items:      {list(zip(item_names, catalog_ids))}")
    print(f"  Totals:     Calories: {data.get('totals', {}).get('calories')} kcal | Protein: {data.get('totals', {}).get('protein_g')} g")
    
    time.sleep(2.5)

print("\n" + "=" * 60)
print(f"TARGETED TEST COMPLETE: {passed}/{len(CASES)} PASSED")
print("=" * 60)
