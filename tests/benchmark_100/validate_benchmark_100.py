import os
import sys
import json
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MANIFEST_PATH = Path(r"c:\Users\rinit\.gemini\antigravity\playground\shadow-ionosphere\telugu-food-scanner\tests\benchmark_100\test_manifest_100.json")

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total entries loaded: {len(data)}")
assert len(data) == 100, f"Expected 100, got {len(data)}"

required_keys = [
    "test_id", "filename", "image_path", "expected_dish_name", "expected_dish_te",
    "expected_cluster", "is_raw_salad", "expected_cal_min", "expected_cal_max",
    "expected_protein_min", "expected_protein_max", "key_ingredients"
]

errors = []
image_sizes = []

for idx, item in enumerate(data, 1):
    expected_id = f"TEST-{idx:03d}"
    if item.get("test_id") != expected_id:
        errors.append(f"Row {idx}: test_id mismatch ({item.get('test_id')} != {expected_id})")
    
    for rk in required_keys:
        if rk not in item:
            errors.append(f"Row {idx}: missing key {rk}")
    
    # Check numeric bounds
    c_min = item.get("expected_cal_min", 0)
    c_max = item.get("expected_cal_max", 0)
    if c_min >= c_max or c_min <= 0:
        errors.append(f"Row {idx}: invalid calories [{c_min}, {c_max}]")
        
    p_min = item.get("expected_protein_min", 0)
    p_max = item.get("expected_protein_max", 0)
    if p_min >= p_max or p_min <= 0:
        errors.append(f"Row {idx}: invalid protein [{p_min}, {p_max}]")
        
    if not isinstance(item.get("key_ingredients"), list) or len(item["key_ingredients"]) == 0:
        errors.append(f"Row {idx}: key_ingredients empty or not list")

    img_path = Path(item["image_path"])
    if not img_path.exists():
        errors.append(f"Row {idx}: image does not exist at {img_path}")
    else:
        try:
            with Image.open(img_path) as im:
                im.verify()
                image_sizes.append((img_path.name, im.size, img_path.stat().st_size))
        except Exception as e:
            errors.append(f"Row {idx}: PIL verify error on {img_path}: {e}")

if errors:
    print(f"Validation FAILED with {len(errors)} errors:")
    for e in errors[:10]:
        print(" ", e)
    sys.exit(1)
else:
    print("ALL VALIDATION CHECKS PASSED PERFECTLY!")

print(f"\nImage details verified: {len(image_sizes)} images")
min_size = min(s[2] for s in image_sizes)
max_size = max(s[2] for s in image_sizes)
avg_size = sum(s[2] for s in image_sizes) / len(image_sizes)
print(f"File size min: {min_size/1024:.1f} KB, max: {max_size/1024:.1f} KB, avg: {avg_size/1024:.1f} KB")

# Breakdown by Macro Category
from collections import defaultdict
macro_map = defaultdict(list)
for item in data:
    macro_map[item.get("macro_category", "Unknown")].append(item["expected_dish_name"])

print("\n================ CATEGORY BREAKDOWN ================")
for cat, dishes in sorted(macro_map.items()):
    print(f"\n--- {cat} ({len(dishes)} dishes) ---")
    for d in dishes[:5]:
        print(f"  * {d}")
    if len(dishes) > 5:
        print(f"  * ... and {len(dishes)-5} more")

# Print first 3 manifest items as sample
print("\n================ SAMPLE MANIFEST ENTRIES ================")
print(json.dumps(data[:2], indent=2, ensure_ascii=False))
