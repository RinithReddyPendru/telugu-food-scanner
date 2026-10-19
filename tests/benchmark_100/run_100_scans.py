"""
Automated 100-Dish Benchmark Scan Runner for Telugu Food Scanner.
Executes scans against POST http://localhost:8005/api/v1/scan.

Features:
- Reads benchmark manifest of 100 Telugu dishes.
- Alternates between 'gemini-3.5-flash-lite' and 'gemma-4-31b-it' to strictly protect the 20 RPD cap on gemini-3.8-flash.
- Spacing of 2.0s between requests to comfortably remain within the 15 RPM rate limit.
- Automatic 5s backoff and model-failover on 429 rate limit or temporary errors.
- Incremental checkpointing to scan_results_100.json on every completed scan.
- Detailed end-of-run statistical summary.
"""

from __future__ import annotations
import argparse
import datetime
import json
import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional
import requests

BENCHMARK_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_DIR = BENCHMARK_DIR.parent.parent
MANIFEST_PATH = BENCHMARK_DIR / "test_manifest_100.json"
DEFAULT_RESULTS_PATH = BENCHMARK_DIR / "scan_results_v2_100.json"
IMAGES_DIR = BENCHMARK_DIR / "images"
API_URL = "http://localhost:8005/api/v1/scan"

MODELS = ["gemini-3.5-flash-lite", "gemma-4-31b-it"]
REQUEST_DELAY_SEC = 2.0
RETRY_BACKOFF_SEC = 5.0
MAX_RETRIES = 3


def load_manifest() -> List[Dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"[INIT] Loaded {len(manifest)} test cases from {MANIFEST_PATH.name}")
    return manifest


def load_existing_results(results_path: pathlib.Path) -> Dict[str, Dict[str, Any]]:
    if results_path.exists():
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {item["test_id"]: item for item in data if "test_id" in item}
        except Exception as e:
            print(f"[WARN] Could not parse existing results ({e}), starting fresh.")
    return {}


def save_results(results_map: Dict[str, Dict[str, Any]], results_path: pathlib.Path) -> None:
    # Save as list sorted by test_id
    sorted_items = sorted(results_map.values(), key=lambda x: x.get("test_id", ""))
    temp_path = results_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(sorted_items, f, indent=2, ensure_ascii=False)
    temp_path.replace(results_path)


def scan_single_image(
    image_path: pathlib.Path,
    preferred_model: str,
    alternate_model: str,
) -> tuple[Dict[str, Any], int, str]:
    """
    Calls POST /api/v1/scan with multipart file.
    Retries with alternate model on 429 or errors.
    Returns: (parsed_json_response, http_status_code, model_attempted)
    """
    models_to_try = [preferred_model, alternate_model, preferred_model]
    last_exc = None
    last_status = 500
    last_body = {}

    for attempt, model in enumerate(models_to_try, start=1):
        try:
            with open(image_path, "rb") as f:
                files = {"file": (image_path.name, f, "image/jpeg")}
                data = {"preferred_model": model}
                resp = requests.post(API_URL, files=files, data=data, timeout=45)

            last_status = resp.status_code
            if resp.status_code == 200:
                return resp.json(), 200, model
            elif resp.status_code == 429:
                print(f"      [429 RATE LIMIT] Model {model} rate limited on attempt {attempt}. Backing off {RETRY_BACKOFF_SEC}s...")
                time.sleep(RETRY_BACKOFF_SEC)
            else:
                print(f"      [HTTP {resp.status_code}] Error from {model}: {resp.text[:120]}. Backing off {RETRY_BACKOFF_SEC}s...")
                time.sleep(RETRY_BACKOFF_SEC)
        except Exception as exc:
            last_exc = exc
            print(f"      [EXCEPTION] Attempt {attempt} with {model} failed: {exc}. Backing off {RETRY_BACKOFF_SEC}s...")
            time.sleep(RETRY_BACKOFF_SEC)

    # If all retries failed, return fallback record
    return {
        "status": "error",
        "error": str(last_exc) if last_exc else f"HTTP {last_status}",
        "model_used": models_to_try[0],
        "latency_ms": 0,
        "usage_and_cost": {"total_tokens": 0, "estimated_paid_cost_inr": 0.0},
        "is_food_image": False,
        "plate_title_en": "Scan Failed",
        "plate_title_te": "విఫలమైంది",
        "meal_type": "Unknown",
        "items": [],
        "totals": {
            "calories": 0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0,
            "fiber_g": 0.0, "iron_mg": 0.0, "calcium_mg": 0.0, "sodium_mg": 0.0
        },
        "mddw_diversity": {"score": 0},
    }, last_status, models_to_try[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated 100-Dish Benchmark Scan Runner")
    parser.add_argument("--output", type=str, default=str(DEFAULT_RESULTS_PATH), help="Path to save scan results JSON")
    args = parser.parse_args()

    results_path = pathlib.Path(args.output).resolve()

    print("=" * 75)
    print("  ANNAPURNA TELUGU FOOD SCANNER: 100-DISH BENCHMARK TEST RUNNER")
    print(f"  Target Results File: {results_path.name}")
    print("=" * 75)

    manifest = load_manifest()
    results_map = load_existing_results(results_path)
    total_dishes = len(manifest)

    print(f"[STATUS] Total test cases in manifest: {total_dishes}")
    print(f"[STATUS] Pre-existing completed scans: {len(results_map)}")
    print(f"[CONFIG] Primary model rotation: {MODELS[0]} <-> {MODELS[1]}")
    print(f"[CONFIG] Inter-request sleep: {REQUEST_DELAY_SEC}s")
    print("-" * 75)

    start_time = time.perf_counter()

    for idx, item in enumerate(manifest):
        test_id = item["test_id"]
        filename = item["filename"]
        expected_name = item.get("expected_dish_name", "")
        expected_te = item.get("expected_dish_te", "")
        expected_cluster = item.get("expected_cluster", "")

        # Check if already processed
        if test_id in results_map and results_map[test_id].get("http_status") == 200:
            existing = results_map[test_id]
            print(f"[{idx+1:03d}/{total_dishes}] {test_id}: {filename} [CACHED 200 OK] -> {existing.get('recognized_plate_title_en')}")
            continue

        # Locate image
        img_path = pathlib.Path(item.get("image_path", ""))
        if not img_path.exists():
            img_path = IMAGES_DIR / filename
        if not img_path.exists():
            print(f"[ERROR] Missing image file for {test_id}: {filename}")
            continue

        # Alternate preferred model
        preferred_model = MODELS[idx % 2]
        alternate_model = MODELS[(idx + 1) % 2]

        print(f"[{idx+1:03d}/{total_dishes}] {test_id} ({filename}) -> Requesting {preferred_model}...")

        scan_t0 = time.perf_counter()
        resp_json, status_code, attempted_model = scan_single_image(img_path, preferred_model, alternate_model)
        scan_elapsed_ms = int((time.perf_counter() - scan_t0) * 1000)

        # Extract scan response fields
        model_used = resp_json.get("model_used") or attempted_model
        latency_ms = resp_json.get("latency_ms") or scan_elapsed_ms
        usage = resp_json.get("usage_and_cost", {})
        tokens_used = usage.get("total_tokens", 0)
        cost_inr = usage.get("estimated_paid_cost_inr", 0.0)
        is_food = bool(resp_json.get("is_food_image", False))
        plate_en = resp_json.get("plate_title_en", "")
        plate_te = resp_json.get("plate_title_te", "")
        meal_type = resp_json.get("meal_type", "")
        raw_totals = resp_json.get("totals", {})

        totals_filtered = {
            "calories": raw_totals.get("calories", 0),
            "protein_g": raw_totals.get("protein_g", 0.0),
            "carbs_g": raw_totals.get("carbs_g", 0.0),
            "fat_g": raw_totals.get("fat_g", 0.0),
            "fiber_g": raw_totals.get("fiber_g", 0.0),
            "iron_mg": raw_totals.get("iron_mg", 0.0),
            "calcium_mg": raw_totals.get("calcium_mg", 0.0),
            "sodium_mg": raw_totals.get("sodium_mg", 0.0),
        }

        recognized_items = []
        for it in resp_json.get("items", []):
            recognized_items.append({
                "name_en": it.get("name_en", ""),
                "name_te": it.get("name_te", ""),
                "cluster": it.get("cluster", ""),
                "estimated_grams": it.get("estimated_grams", 0),
                "matched_catalog_id": it.get("catalog_id", "CUSTOM-TE"),
                "matched_in_excel_catalog": bool(it.get("matched_in_excel_catalog", False)),
            })

        mddw_score = resp_json.get("mddw_diversity", {}).get("score", 0)

        result_record = {
            "test_id": test_id,
            "filename": filename,
            "expected_dish_name": expected_name,
            "expected_dish_te": expected_te,
            "expected_cluster": expected_cluster,
            "model_used": model_used,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "estimated_cost_inr": cost_inr,
            "is_food_image": is_food,
            "recognized_plate_title_en": plate_en,
            "recognized_plate_title_te": plate_te,
            "recognized_meal_type": meal_type,
            "recognized_items": recognized_items,
            "totals": totals_filtered,
            "mddw_score": mddw_score,
            "http_status": status_code,
            "scan_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        results_map[test_id] = result_record
        save_results(results_map, results_path)

        matched_str = "MATCHED" if any(it["matched_in_excel_catalog"] for it in recognized_items) else "CUSTOM"
        print(f"      -> HTTP {status_code} ({latency_ms}ms) [{model_used}] | Recognized: '{plate_en}' ({matched_str}) | Calories: {totals_filtered['calories']}kcal | MDD-W: {mddw_score}/10")

        # Rate limit safety delay
        time.sleep(REQUEST_DELAY_SEC)

    total_wall_sec = round(time.perf_counter() - start_time, 1)
    print("=" * 75)
    print(f"  BENCHMARK COMPLETE: 100 SCANS PROCESSED IN {total_wall_sec}s")
    print("=" * 75)

    # Compute Statistics
    all_results = list(results_map.values())
    total_count = len(all_results)
    success_count = sum(1 for r in all_results if r.get("http_status") == 200)
    success_rate = (success_count / total_count * 100.0) if total_count else 0.0

    model_latencies: Dict[str, List[int]] = {}
    total_tokens = 0
    total_cost_inr = 0.0
    catalog_matched_count = 0

    for r in all_results:
        mod = r.get("model_used", "unknown")
        lat = r.get("latency_ms", 0)
        model_latencies.setdefault(mod, []).append(lat)
        total_tokens += r.get("tokens_used", 0)
        total_cost_inr += r.get("estimated_cost_inr", 0.0)
        if any(it.get("matched_in_excel_catalog") for it in r.get("recognized_items", [])):
            catalog_matched_count += 1

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("\n--- BENCHMARK SUMMARY STATISTICS ---")
    print(f"Total Scans Completed: {total_count}/100")
    print(f"Success Rate (HTTP 200): {success_count}/{total_count} ({success_rate:.1f}%)")
    print(f"Catalog Match Rate: {catalog_matched_count}/{total_count} ({catalog_matched_count/total_count*100.0:.1f}%)")
    print(f"Total Tokens Consumed: {total_tokens:,}")
    print(f"Total Estimated Cost: Rs. {total_cost_inr:.4f} INR")

    print("\nAverage Latency per Model:")
    for mod, lats in sorted(model_latencies.items()):
        avg_lat = sum(lats) / len(lats) if lats else 0
        print(f"  - {mod}: {avg_lat:.1f} ms ({len(lats)} scans)")

    print("\nSample 5 Recognized Dishes vs Expected:")
    sample_indices = [0, 20, 40, 60, 80]
    for si in sample_indices:
        if si < len(all_results):
            sr = all_results[si]
            print(f"  [{sr['test_id']}] Expected: '{sr['expected_dish_name']}'")
            print(f"            Got:      '{sr['recognized_plate_title_en']}' (Telugu: {sr['recognized_plate_title_te']})")
            print(f"            Model: {sr['model_used']} | Cal: {sr['totals']['calories']} | Items: {len(sr['recognized_items'])}\n")


if __name__ == "__main__":
    main()
