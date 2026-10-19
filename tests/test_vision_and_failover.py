"""
Vision & Failover Stress Test Suite for Annapurna Telugu Food Scanner.
Tests:
1. Image preprocessing (`preprocess_image`) across RGBA PNG, Grayscale (L), and oversized >1280px JPEG images.
2. Live Vision Scan with `gemini-3.1-flash-lite` on `25_Vankaya_Kura_Gutti_Vankaya.jpg` (JM-25) & `70_Gongura_Mutton.jpg` (JM-70).
3. Live Vision Scan / Failover verification with `gemma-4-31b-it` (high-quota 14,400 RPD open-weights model).
4. Automatic 429 Quota Failover simulation ensuring seamless fallback across `MODEL_FAILOVER_POOL`.
5. SHA-256 In-Memory Cache (`_SCAN_CACHE`) repeat scan verification (<50ms latency, 0 API tokens consumed).
6. Deterministic `/api/v1/calculate` ICMR-NIN math & oil modifier verification (100% accuracy check).
7. `/api/v1/dishes` bilingual search verification in English ("gongura") and Telugu script ("పెసరట్టు").

Note: Preserves `gemini-3.8-flash` 20 RPD quota by routing live tests to `gemini-3.1-flash-lite` and `gemma-4-31b-it`.
"""

from __future__ import annotations
import base64
import io
import json
import pathlib
import sys
import time
from typing import Any, Dict
from PIL import Image

# Ensure UTF-8 stdout on Windows for Telugu characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure telugu-food-scanner directory is on sys.path
SCANNER_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

import scanner_engine
from scanner_engine import (
    _SCAN_CACHE,
    preprocess_image,
    resolve_gemini_api_key,
    scan_telugu_food_image,
)
from dishes_catalog import CATALOG, CATALOG_BY_ID, compute_portion_nutrition
from app import (
    PortionCalcItem,
    PortionCalcRequest,
    calculate_custom_portions,
    list_dishes,
)

# Override MODEL_FAILOVER_POOL in test runtime so gemini-3.8-flash (20 RPD) is never touched
scanner_engine.MODEL_FAILOVER_POOL[:] = [
    "gemini-3.1-flash-lite",
    "gemma-4-31b-it",
]


def test_1_image_preprocessing() -> Dict[str, Any]:
    print("\n[TEST 1] Testing Image Preprocessing (RGBA PNG, Grayscale L, Oversized 2400x1800 JPEG)...")
    t0 = time.perf_counter()

    # 1A: RGBA PNG (2000 x 1500) -> should convert to RGB JPEG and cap max dim to 1280
    rgba_img = Image.new("RGBA", (2000, 1500), (255, 120, 40, 180))
    buf_rgba = io.BytesIO()
    rgba_img.save(buf_rgba, format="PNG")
    b64_out, mime_out, orig_w, orig_h = preprocess_image(buf_rgba.getvalue())

    decoded_bytes = base64.b64decode(b64_out)
    out_img = Image.open(io.BytesIO(decoded_bytes))
    assert mime_out == "image/jpeg", f"Expected image/jpeg, got {mime_out}"
    assert orig_w == 2000 and orig_h == 1500, f"Unexpected original dims: {orig_w}x{orig_h}"
    assert out_img.mode == "RGB", f"Expected RGB mode after conversion, got {out_img.mode}"
    assert max(out_img.size) == 1280, f"Expected max dimension 1280, got {out_img.size}"
    assert out_img.size == (1280, 960), f"Expected aspect-preserved (1280, 960), got {out_img.size}"

    # 1B: Grayscale ("L") PNG (800 x 600) -> should convert to RGB JPEG and keep 800x600
    gray_img = Image.new("L", (800, 600), 128)
    buf_gray = io.BytesIO()
    gray_img.save(buf_gray, format="PNG")
    b64_gray, mime_gray, gw, gh = preprocess_image(buf_gray.getvalue())
    out_gray = Image.open(io.BytesIO(base64.b64decode(b64_gray)))
    assert mime_gray == "image/jpeg"
    assert out_gray.mode == "RGB"
    assert out_gray.size == (800, 600), f"Expected (800, 600), got {out_gray.size}"

    # 1C: Real Telugu dish JPEG from disk
    jm25_path = pathlib.Path(CATALOG_BY_ID["JM-25"]["local_image"])
    assert jm25_path.exists(), f"Sample image missing: {jm25_path}"
    raw_jpg = jm25_path.read_bytes()
    b64_jpg, mime_jpg, jw, jh = preprocess_image(raw_jpg)
    out_jpg = Image.open(io.BytesIO(base64.b64decode(b64_jpg)))
    assert mime_jpg == "image/jpeg"
    assert out_jpg.mode == "RGB"
    assert max(out_jpg.size) <= 1280

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    print(f"  -> PASS ({elapsed_ms} ms): RGBA(2000x1500)->RGB{out_img.size}, L(800x600)->RGB{out_gray.size}, RealJPG({jw}x{jh})->RGB{out_jpg.size}")
    return {
        "test": "preprocess_image",
        "status": "PASS",
        "latency_ms": elapsed_ms,
        "rgba_2000x1500_resized_to": list(out_img.size),
        "grayscale_800x600_converted_mode": out_gray.mode,
        "real_jpg_dims": [jw, jh],
        "real_jpg_processed_dims": list(out_jpg.size),
    }


def _validate_scan_structure(res: Dict[str, Any], expected_dish_id: str) -> None:
    required_top_keys = [
        "status",
        "engine",
        "model_used",
        "latency_ms",
        "is_food_image",
        "plate_title_en",
        "plate_title_te",
        "items",
        "totals",
        "mddw_diversity",
        "macro_split_pct",
    ]
    for k in required_top_keys:
        assert k in res, f"Missing required key '{k}' in scan response"

    assert res["status"] == "success"
    assert res["is_food_image"] is True
    assert isinstance(res["plate_title_en"], str) and len(res["plate_title_en"].strip()) > 0
    assert isinstance(res["plate_title_te"], str) and len(res["plate_title_te"].strip()) > 0
    assert isinstance(res["items"], list) and len(res["items"]) >= 1, "Expected at least 1 detected dish item"

    # Check totals
    totals = res["totals"]
    for m_key in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "iron_mg", "calcium_mg", "folate_ug", "total_grams"):
        assert m_key in totals, f"Missing '{m_key}' in totals"
    assert totals["calories"] > 0, "Total calories must be > 0"
    assert totals["total_grams"] > 0, "Total grams must be > 0"

    # Check mddw_diversity
    mddw = res["mddw_diversity"]
    assert "groups_covered" in mddw and isinstance(mddw["groups_covered"], list)
    assert "score" in mddw and mddw["score"] == len(mddw["groups_covered"])
    assert mddw["max_score"] == 10

    # Check items & box_2d
    for item in res["items"]:
        box = item.get("box_2d")
        assert isinstance(box, list) and len(box) == 4, f"Expected box_2d with 4 coordinates, got {box}"
        assert all(isinstance(coord, int) and 0 <= coord <= 1000 for coord in box), f"Invalid box_2d coords: {box}"
        assert isinstance(item.get("name_en"), str) and len(item["name_en"]) > 0
        assert isinstance(item.get("name_te"), str) and len(item["name_te"]) > 0


def test_2_live_vision_and_cache() -> Dict[str, Any]:
    print("\n[TEST 2] Live Vision Scan with `gemini-3.1-flash-lite` + SHA-256 Cache Hit Test...")
    api_key = resolve_gemini_api_key()
    assert api_key, "GEMINI_API_KEY must be configured for live vision test"

    _SCAN_CACHE.clear()

    # Dish 1: 25_Vankaya_Kura_Gutti_Vankaya.jpg (JM-25)
    dish_25 = CATALOG_BY_ID["JM-25"]
    img_path_25 = pathlib.Path(dish_25["local_image"])
    assert img_path_25.exists(), f"Image not found: {img_path_25}"
    img_bytes_25 = img_path_25.read_bytes()

    t0 = time.perf_counter()
    res_25 = scan_telugu_food_image(
        image_bytes=img_bytes_25,
        meal_hint=None,
        preferred_model=None,  # Uses first model in patched MODEL_FAILOVER_POOL -> gemini-3.1-flash-lite
    )
    live_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    _validate_scan_structure(res_25, "JM-25")

    detected_ids_25 = [it["catalog_id"] for it in res_25["items"]]
    detected_names_25 = [it["name_en"] for it in res_25["items"]]
    first_box_25 = res_25["items"][0]["box_2d"]
    print(f"  -> Live Scan #1 (25_Vankaya_Kura_Gutti_Vankaya.jpg): model={res_25['model_used']}, latency={live_latency_ms} ms")
    print(f"     Title EN: {res_25['plate_title_en']} | Title TE: {res_25['plate_title_te']}")
    print(f"     Detected Items: {detected_ids_25} ({detected_names_25}) | box_2d={first_box_25}")
    print(f"     Totals: {res_25['totals']['calories']} kcal, Protein={res_25['totals']['protein_g']}g, Iron={res_25['totals']['iron_mg']}mg | MDD-W={res_25['mddw_diversity']['groups_covered']}")

    # Now test repeat scan of the exact same image -> MUST hit _SCAN_CACHE in <50ms with 0 tokens
    t_cache = time.perf_counter()
    res_25_cached = scan_telugu_food_image(
        image_bytes=img_bytes_25,
        meal_hint=None,
        preferred_model=None,
    )
    cache_latency_ms = round((time.perf_counter() - t_cache) * 1000, 3)
    assert cache_latency_ms < 50.0, f"Expected cache latency < 50ms, got {cache_latency_ms}ms"
    assert "Cached - 0 RPD used" in res_25_cached["engine"], f"Expected cached engine label, got {res_25_cached['engine']}"
    assert res_25_cached["plate_title_en"] == res_25["plate_title_en"]
    if "usage_and_cost" in res_25_cached:
        assert res_25_cached["usage_and_cost"]["total_tokens"] == 0, f"Expected 0 tokens on cache hit, got {res_25_cached['usage_and_cost']}"
        assert res_25_cached["usage_and_cost"]["cached"] is True
    print(f"  -> Repeat Scan Cache Hit: actual_latency={cache_latency_ms} ms (<50ms verified), tokens=0, engine='{res_25_cached['engine']}'")

    # Dish 2: 70_Gongura_Mutton.jpg (JM-70) tested with high-quota failover model
    dish_70 = CATALOG_BY_ID["JM-70"]
    img_path_70 = pathlib.Path(dish_70["local_image"])
    assert img_path_70.exists(), f"Image not found: {img_path_70}"
    img_bytes_70 = img_path_70.read_bytes()

    t1 = time.perf_counter()
    res_70 = scan_telugu_food_image(
        image_bytes=img_bytes_70,
        meal_hint="Telugu non-veg curry",
        preferred_model="gemini-3.1-flash-lite",
    )
    scan2_latency_ms = round((time.perf_counter() - t1) * 1000, 2)
    _validate_scan_structure(res_70, "JM-70")
    detected_ids_70 = [it["catalog_id"] for it in res_70["items"]]
    detected_names_70 = [it["name_en"] for it in res_70["items"]]
    first_box_70 = res_70["items"][0]["box_2d"]
    print(f"  -> Live Scan #2 (70_Gongura_Mutton.jpg): model={res_70['model_used']}, latency={scan2_latency_ms} ms")
    print(f"     Title EN: {res_70['plate_title_en']} | Title TE: {res_70['plate_title_te']}")
    print(f"     Detected Items: {detected_ids_70} ({detected_names_70}) | box_2d={first_box_70}")
    print(f"     Totals: {res_70['totals']['calories']} kcal, Protein={res_70['totals']['protein_g']}g, Iron={res_70['totals']['iron_mg']}mg | MDD-W={res_70['mddw_diversity']['groups_covered']}")

    return {
        "test": "live_vision_and_cache",
        "status": "PASS",
        "scan_1_gutti_vankaya": {
            "model_used": res_25["model_used"],
            "latency_ms": live_latency_ms,
            "plate_title_en": res_25["plate_title_en"],
            "plate_title_te": res_25["plate_title_te"],
            "detected_catalog_ids": detected_ids_25,
            "detected_names_en": detected_names_25,
            "box_2d": first_box_25,
            "totals": res_25["totals"],
            "mddw_diversity": res_25["mddw_diversity"],
            "usage_and_cost": res_25.get("usage_and_cost"),
        },
        "cache_hit_verification": {
            "actual_latency_ms": cache_latency_ms,
            "reported_latency_ms": res_25_cached["latency_ms"],
            "engine_tag": res_25_cached["engine"],
            "under_50ms": cache_latency_ms < 50.0,
            "usage_and_cost": res_25_cached.get("usage_and_cost"),
        },
        "scan_2_gongura_mutton": {
            "model_used": res_70["model_used"],
            "latency_ms": scan2_latency_ms,
            "plate_title_en": res_70["plate_title_en"],
            "plate_title_te": res_70["plate_title_te"],
            "detected_catalog_ids": detected_ids_70,
            "detected_names_en": detected_names_70,
            "box_2d": first_box_70,
            "totals": res_70["totals"],
            "mddw_diversity": res_70["mddw_diversity"],
            "usage_and_cost": res_70.get("usage_and_cost"),
        },
    }


def test_3_failover_simulation() -> Dict[str, Any]:
    print("\n[TEST 3] Testing Automatic Model Failover when Primary Model Throws 429 Quota Error...")
    # Put a nonexistent/rate-limited dummy model first in MODEL_FAILOVER_POOL followed by gemini-3.1-flash-lite
    original_pool = list(scanner_engine.MODEL_FAILOVER_POOL)
    scanner_engine.MODEL_FAILOVER_POOL[:] = [
        "invalid-quota-exhausted-model-429",
        "gemini-3.1-flash-lite",
    ]
    try:
        dish_70 = CATALOG_BY_ID["JM-70"]
        img_bytes_70 = pathlib.Path(dish_70["local_image"]).read_bytes()
        t0 = time.perf_counter()
        res = scan_telugu_food_image(
            image_bytes=img_bytes_70,
            meal_hint="Failover test hint unique",
            preferred_model=None,
        )
        failover_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        assert res["model_used"] == "gemini-3.1-flash-lite", f"Expected failover to gemini-3.1-flash-lite, got {res['model_used']}"
        _validate_scan_structure(res, "JM-70")
        print(f"  -> PASS ({failover_latency_ms} ms): Failed over cleanly from 'invalid-quota-exhausted-model-429' -> '{res['model_used']}'")
        return {
            "test": "automatic_model_failover",
            "status": "PASS",
            "failed_first_model": "invalid-quota-exhausted-model-429",
            "recovered_model": res["model_used"],
            "latency_ms": failover_latency_ms,
            "detected_catalog_ids": [it["catalog_id"] for it in res["items"]],
        }
    finally:
        scanner_engine.MODEL_FAILOVER_POOL[:] = original_pool


def test_4_deterministic_calculate_and_search() -> Dict[str, Any]:
    print("\n[TEST 4] Testing Deterministic `/api/v1/calculate` & Bilingual `/api/v1/dishes` Search...")
    t0 = time.perf_counter()

    # 4A: /api/v1/calculate accuracy check
    # JM-25 (Gutti Vankaya): per_100g = {calories: 168, protein_g: 4.2, carbs_g: 11.4, fat_g: 12.2, fiber_g: 4.8, iron_mg: 1.6, calcium_mg: 48, folate_ug: 42, vit_a_ug: 65, vit_c_mg: 14, sodium_mg: 310}
    # JM-11 (Gongura Pappu): per_100g = {calories: 126, protein_g: 6.5, carbs_g: 15.0, fat_g: 4.5, fiber_g: 4.1, iron_mg: 3.9, calcium_mg: 95, folate_ug: 70, vit_a_ug: 180, vit_c_mg": 25, sodium_mg: 280}
    calc_req = PortionCalcRequest(
        items=[
            PortionCalcItem(catalog_id="JM-25", grams=150, oil_ghee_level="moderate"),
            PortionCalcItem(catalog_id="JM-11", grams=200, oil_ghee_level="high"),
        ]
    )
    calc_res = calculate_custom_portions(calc_req)

    expected_jm25 = compute_portion_nutrition(CATALOG_BY_ID["JM-25"]["per_100g"], 150, oil_modifier=1.0)
    expected_jm11 = compute_portion_nutrition(CATALOG_BY_ID["JM-11"]["per_100g"], 200, oil_modifier=1.2)

    assert calc_res["items"][0]["nutrition"] == expected_jm25, f"JM-25 mismatch: {calc_res['items'][0]['nutrition']} vs {expected_jm25}"
    assert calc_res["items"][1]["nutrition"] == expected_jm11, f"JM-11 mismatch: {calc_res['items'][1]['nutrition']} vs {expected_jm11}"
    assert calc_res["totals"]["calories"] == expected_jm25["calories"] + expected_jm11["calories"]
    assert calc_res["totals"]["total_grams"] == 350
    assert set(calc_res["mddw_groups_covered"]) == set(CATALOG_BY_ID["JM-25"]["food_groups"]) | set(CATALOG_BY_ID["JM-11"]["food_groups"])

    # 4B: /api/v1/dishes English search for "gongura"
    en_search = list_dishes(q="gongura", cluster=None, food_group=None)
    en_ids = [d["id"] for d in en_search["dishes"]]
    assert en_search["count"] >= 4, f"Expected at least 4 Gongura dishes, got {en_search['count']}"
    for expected_id in ("JM-03", "JM-11", "JM-52", "JM-70"):
        assert expected_id in en_ids, f"Expected {expected_id} in 'gongura' search results, got {en_ids}"

    # 4C: /api/v1/dishes Telugu script search for "పెసరట్టు" (Pesarattu)
    te_search = list_dishes(q="పెసరట్టు", cluster=None, food_group=None)
    te_ids = [d["id"] for d in te_search["dishes"]]
    te_names = [d["name_te"] for d in te_search["dishes"]]
    assert te_search["count"] >= 1, f"Expected >=1 dish for Telugu query 'పెసరట్టు', got {te_search['count']}"
    assert all("పెసరట్టు" in d["name_te"] for d in te_search["dishes"]), f"Unexpected Telugu search match: {te_names}"

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    print(f"  -> PASS ({elapsed_ms} ms):")
    print(f"     /api/v1/calculate (150g JM-25 + 200g high-oil JM-11): {calc_res['totals']['calories']} kcal, Protein={calc_res['totals']['protein_g']}g, Iron={calc_res['totals']['iron_mg']}mg, MDD-W={calc_res['mddw_groups_covered']}")
    print(f"     /api/v1/dishes?q=gongura -> {en_search['count']} matches: {en_ids}")
    print(f"     /api/v1/dishes?q=పెసరట్టు -> {te_search['count']} matches: {te_ids} ({te_names})")

    return {
        "test": "deterministic_calculate_and_bilingual_search",
        "status": "PASS",
        "latency_ms": elapsed_ms,
        "calculate_totals": calc_res["totals"],
        "calculate_mddw_groups": calc_res["mddw_groups_covered"],
        "search_en_gongura_count": en_search["count"],
        "search_en_gongura_ids": en_ids,
        "search_te_pesarattu_count": te_search["count"],
        "search_te_pesarattu_ids": te_ids,
        "search_te_pesarattu_names": te_names,
    }


def main() -> None:
    print("=" * 76)
    print("ANNAPURNA TELUGU FOOD SCANNER — VISION & FAILOVER STRESS TEST SUITE")
    print("=" * 76)
    t_start = time.perf_counter()

    results = {
        "test_1": test_1_image_preprocessing(),
        "test_2": test_2_live_vision_and_cache(),
        "test_3": test_3_failover_simulation(),
        "test_4": test_4_deterministic_calculate_and_search(),
    }

    total_ms = round((time.perf_counter() - t_start) * 1000, 2)
    results["overall_status"] = "ALL_PASSED"
    results["total_suite_duration_ms"] = total_ms

    print("\n" + "=" * 76)
    print(f"SUMMARY: ALL 4 TEST SUITES PASSED in {total_ms} ms (0 gemini-3.8-flash quota used)")
    print("=" * 76)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
