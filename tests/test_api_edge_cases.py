"""
Comprehensive QA Audit & Edge-Case Test Suite for Telugu Food Scanner API.
Targets: http://127.0.0.1:8005 / http://localhost:8005

Audited Endpoints:
1. GET  /api/v1/health
2. GET  /api/v1/stats
3. GET  /api/v1/dishes (q=pappu, q=keera, q=dosakaya, Telugu script, cluster & MDD-W group filters)
4. GET  /api/v1/samples & GET /api/v1/sample-image/{dish_id}
5. POST /api/v1/calculate (valid dishes, empty items, unknown IDs, oil modifiers, whitespace, negative grams)
6. POST /api/v1/scan-base64 (valid base64, data URI prefix, malformed base64, non-image bytes, empty string)
7. POST /api/v1/scan (multipart upload: valid, empty, corrupt, oversized)
8. Edge-Case: Smartphone EXIF Orientation handling (Orientation 1, 3, 6, 8)
9. Edge-Case: Rapid concurrent back-to-back requests (event loop blocking & memory leaks)
"""

from __future__ import annotations
import asyncio
import base64
import concurrent.futures
import io
import json
import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import requests
from PIL import Image, ImageDraw, ImageOps

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Use 127.0.0.1 by default on Windows to prevent the 2000ms IPv6 localhost SYN-timeout
BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8005")
SCANNER_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

# Result collectors
AUDIT_LOGS: List[Dict[str, Any]] = []
BUGS_AND_ANOMALIES: List[Dict[str, Any]] = []


def record_result(category: str, test_name: str, passed: bool, details: str, severity: str = "INFO"):
    AUDIT_LOGS.append({
        "category": category,
        "test_name": test_name,
        "passed": passed,
        "details": details,
        "severity": severity,
    })
    status_str = "PASS" if passed else f"FAIL [{severity}]"
    print(f"  [{status_str}] {test_name}: {details}")
    if not passed and severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        BUGS_AND_ANOMALIES.append({
            "category": category,
            "test_name": test_name,
            "severity": severity,
            "details": details,
        })


def get_sample_local_image_path() -> Optional[pathlib.Path]:
    """Finds a valid local Telugu dish image for testing."""
    img_candidates = [
        SCANNER_DIR / "static" / "25_Vankaya_Kura_Gutti_Vankaya.jpg",
        SCANNER_DIR / "static" / "11_Gongura_Pappu.jpg",
        SCANNER_DIR / "static" / "50_Allam_Pachadi.jpg",
    ]
    for p in img_candidates:
        if p.exists() and p.stat().st_size > 0:
            return p
    # Search in dishes_catalog
    try:
        from dishes_catalog import CATALOG
        for d in CATALOG:
            if d.get("local_image"):
                lp = pathlib.Path(d["local_image"])
                if lp.exists() and lp.stat().st_size > 0:
                    return lp
    except Exception:
        pass
    return None


def create_synthetic_dish_image(width: int = 400, height: int = 300) -> bytes:
    """Generates a small valid JPEG of a bowl with food colors."""
    img = Image.new("RGB", (width, height), color=(245, 235, 220))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(40, 20), (width - 40, height - 20)], fill=(220, 210, 195), outline=(140, 120, 100), width=4)
    draw.ellipse([(80, 50), (width - 80, height - 50)], fill=(180, 70, 20))
    draw.rectangle([(width // 2 - 20, height // 2 - 20), (width // 2 + 20, height // 2 + 20)], fill=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# ==============================================================================
# 1. HEALTH & STATS ENDPOINTS
# ==============================================================================
def test_health_endpoint(session: requests.Session):
    print("\n=== [SUITE 1.1] GET /api/v1/health ===")
    url = f"{BASE_URL}/api/v1/health"
    try:
        resp = session.get(url, timeout=5)
        passed = (resp.status_code == 200)
        data = resp.json() if passed else {}
        record_result(
            "HEALTH", "HTTP Status 200", passed,
            f"Status code {resp.status_code}", "CRITICAL"
        )

        expected_fields = ["status", "model", "failover_pool", "catalog_size", "cached_scans", "api_key_configured", "nutrition_standard"]
        missing = [f for f in expected_fields if f not in data]
        record_result(
            "HEALTH", "Response Schema", len(missing) == 0,
            f"Missing fields: {missing}" if missing else f"All {len(expected_fields)} schema fields present", "HIGH"
        )
        record_result(
            "HEALTH", "API Key Configured", data.get("api_key_configured") is True,
            f"api_key_configured={data.get('api_key_configured')}", "HIGH"
        )
        record_result(
            "HEALTH", "Catalog Size > 0", data.get("catalog_size", 0) > 0,
            f"catalog_size={data.get('catalog_size')}", "MEDIUM"
        )
    except Exception as exc:
        record_result("HEALTH", "Health check execution", False, str(exc), "CRITICAL")


def test_stats_endpoint(session: requests.Session):
    print("\n=== [SUITE 1.2] GET /api/v1/stats ===")
    url = f"{BASE_URL}/api/v1/stats"
    try:
        resp = session.get(url, timeout=5)
        passed = (resp.status_code == 200)
        data = resp.json() if passed else {}
        record_result("STATS", "HTTP Status 200", passed, f"Status code {resp.status_code}", "CRITICAL")

        expected_fields = ["status", "cached_scans", "failover_pool", "pricing_per_1m_usd", "catalog_size", "api_key_configured", "serverless_ready", "nutrition_standard"]
        missing = [f for f in expected_fields if f not in data]
        record_result(
            "STATS", "Response Schema", len(missing) == 0,
            f"Missing fields: {missing}" if missing else f"All {len(expected_fields)} fields present", "HIGH"
        )
        pricing = data.get("pricing_per_1m_usd", {})
        record_result(
            "STATS", "Pricing Map Complete", ("gemini-3.8-flash" in pricing and "gemini-3.5-flash-lite" in pricing),
            f"Configured models in pricing: {list(pricing.keys())}", "MEDIUM"
        )
    except Exception as exc:
        record_result("STATS", "Stats execution", False, str(exc), "CRITICAL")


# ==============================================================================
# 2. DISHES CATALOG ENDPOINT (SEARCH & FILTERS)
# ==============================================================================
def test_dishes_endpoint(session: requests.Session):
    print("\n=== [SUITE 2] GET /api/v1/dishes (Search & Filtering) ===")
    url = f"{BASE_URL}/api/v1/dishes"

    # 2.1 Unfiltered Catalog
    try:
        r = session.get(url, timeout=5)
        data = r.json()
        record_result(
            "DISHES", "All Dishes Unfiltered", r.status_code == 200 and data["count"] > 0,
            f"Status {r.status_code}, count={data.get('count')}, total_catalog={data.get('total_catalog')}", "CRITICAL"
        )
        record_result(
            "DISHES", "Clusters and MDD-W metadata returned",
            ("clusters" in data and len(data["clusters"]) > 0 and "mddw_groups" in data),
            f"{len(data.get('clusters', []))} clusters, {len(data.get('mddw_groups', {}))} MDD-W groups", "MEDIUM"
        )
    except Exception as exc:
        record_result("DISHES", "All Dishes", False, str(exc), "CRITICAL")

    # 2.2 Text Search Queries: q=pappu
    try:
        r = session.get(f"{url}?q=pappu", timeout=5)
        data = r.json()
        has_pappu = any("pappu" in d["name_en"].lower() or "pappu" in d.get("name_te", "") or any("pappu" in a.lower() for a in d.get("aliases", [])) for d in data.get("dishes", []))
        record_result(
            "DISHES", "Search q=pappu", r.status_code == 200 and data["count"] >= 3 and has_pappu,
            f"Found {data.get('count')} dishes for 'pappu' (e.g. {[d['name_en'] for d in data.get('dishes', [])[:3]]})", "HIGH"
        )
    except Exception as exc:
        record_result("DISHES", "Search q=pappu", False, str(exc), "HIGH")

    # 2.3 Text Search Queries: q=keera
    try:
        r = session.get(f"{url}?q=keera", timeout=5)
        data = r.json()
        record_result(
            "DISHES", "Search q=keera", r.status_code == 200 and data["count"] >= 1,
            f"Found {data.get('count')} dishes for 'keera' ({[d['name_en'] for d in data.get('dishes', [])]})", "HIGH"
        )
    except Exception as exc:
        record_result("DISHES", "Search q=keera", False, str(exc), "HIGH")

    # 2.4 Text Search Queries: q=dosakaya
    try:
        r = session.get(f"{url}?q=dosakaya", timeout=5)
        data = r.json()
        record_result(
            "DISHES", "Search q=dosakaya", r.status_code == 200 and data["count"] >= 1,
            f"Found {data.get('count')} dishes for 'dosakaya' ({[d['name_en'] for d in data.get('dishes', [])[:3]]})", "HIGH"
        )
    except Exception as exc:
        record_result("DISHES", "Search q=dosakaya", False, str(exc), "HIGH")

    # 2.5 Text Search with Telugu script: q=పప్పు
    try:
        r = session.get(f"{url}?q=పప్పు", timeout=5)
        data = r.json()
        record_result(
            "DISHES", "Search Telugu Script q=పప్పు", r.status_code == 200 and data["count"] >= 1,
            f"Found {data.get('count')} dishes for Telugu Unicode 'పప్పు'", "HIGH"
        )
    except Exception as exc:
        record_result("DISHES", "Search Telugu Script", False, str(exc), "HIGH")

    # 2.6 Case-insensitivity & whitespace: q=  PAPPU
    try:
        r = session.get(f"{url}?q=%20%20PAPPU%20%20", timeout=5)
        data = r.json()
        r_clean = session.get(f"{url}?q=pappu", timeout=5).json()
        record_result(
            "DISHES", "Case-insensitive & Whitespace-trimmed Search",
            r.status_code == 200 and data["count"] == r_clean["count"],
            f"q='  PAPPU  ' returned {data.get('count')} vs q='pappu' returned {r_clean.get('count')}", "MEDIUM"
        )
    except Exception as exc:
        record_result("DISHES", "Case-insensitive search", False, str(exc), "MEDIUM")

    # 2.7 Search for Non-existent dish
    try:
        r = session.get(f"{url}?q=NonExistentPizzaBurger12345", timeout=5)
        data = r.json()
        record_result(
            "DISHES", "Non-existent query returns 0 gracefully",
            r.status_code == 200 and data["count"] == 0 and len(data["dishes"]) == 0,
            f"Returned count={data.get('count')}", "MEDIUM"
        )
    except Exception as exc:
        record_result("DISHES", "Non-existent search", False, str(exc), "MEDIUM")

    # 2.8 Cluster Filter: cluster=Dals & Pappu
    try:
        r = session.get(f"{url}?cluster=Dals%20%26%20Pappu", timeout=5)
        data = r.json()
        all_match = all(d["cluster"] == "Dals & Pappu" for d in data.get("dishes", []))
        record_result(
            "DISHES", "Filter cluster='Dals & Pappu'",
            r.status_code == 200 and data["count"] > 0 and all_match,
            f"Returned {data.get('count')} dishes, all_match={all_match}", "HIGH"
        )
    except Exception as exc:
        record_result("DISHES", "Cluster filter", False, str(exc), "HIGH")

    # 2.9 Cluster Filter for Tiffins & Breads
    try:
        r_tiff = session.get(f"{url}?cluster=Tiffins%20%26%20Breads", timeout=5)
        data_tiff = r_tiff.json()
        record_result(
            "DISHES", "Filter cluster='Tiffins & Breads' (Breakfast Staples)",
            r_tiff.status_code == 200 and data_tiff["count"] > 0,
            f"Returned {data_tiff.get('count')} dishes for 'Tiffins & Breads'", "HIGH"
        )
    except Exception as exc:
        record_result("DISHES", "Cluster Tiffins & Breads", False, str(exc), "HIGH")

    # 2.10 Cluster Filter discrepancy: cluster=Breakfast returns 0 dishes
    try:
        r_bf = session.get(f"{url}?cluster=Breakfast", timeout=5)
        data_bf = r_bf.json()
        is_empty = (data_bf.get("count") == 0)
        record_result(
            "DISHES", "Cluster discrepancy: cluster='Breakfast' returns 0 (classified as 'Tiffins & Breads')",
            not is_empty,
            f"cluster='Breakfast' returned {data_bf.get('count')} dishes. Catalog uses 'Tiffins & Breads', causing frontend cluster mismatch!",
            "MEDIUM" if is_empty else "INFO"
        )
    except Exception as exc:
        record_result("DISHES", "Cluster Breakfast check", False, str(exc), "MEDIUM")

    # 2.11 MDD-W Food Group Filter: food_group=G7 (Dark Green Leafy Veg)
    try:
        r = session.get(f"{url}?food_group=G7", timeout=5)
        data = r.json()
        all_have_g7 = all("G7" in d["food_groups"] for d in data.get("dishes", []))
        record_result(
            "DISHES", "Filter food_group=G7 (Leafy Greens)",
            r.status_code == 200 and data["count"] > 0 and all_have_g7,
            f"Returned {data.get('count')} dishes, all_have_g7={all_have_g7}", "HIGH"
        )
    except Exception as exc:
        record_result("DISHES", "Food group G7 filter", False, str(exc), "HIGH")

    # 2.12 Case-insensitive Food Group Filter: food_group=g7 (lowercase)
    try:
        r = session.get(f"{url}?food_group=g7", timeout=5)
        data = r.json()
        r_upper = session.get(f"{url}?food_group=G7", timeout=5).json()
        record_result(
            "DISHES", "Case-insensitive food_group=g7",
            r.status_code == 200 and data["count"] == r_upper["count"],
            f"Returned {data.get('count')} dishes vs upper={r_upper.get('count')}", "MEDIUM"
        )
    except Exception as exc:
        record_result("DISHES", "Food group lowercase filter", False, str(exc), "MEDIUM")

    # 2.13 Invalid / Non-existent Food Group Filter: food_group=G99
    try:
        r = session.get(f"{url}?food_group=G99", timeout=5)
        data = r.json()
        record_result(
            "DISHES", "Invalid food_group=G99 returns 0",
            r.status_code == 200 and data["count"] == 0,
            f"Returned count={data.get('count')}", "LOW"
        )
    except Exception as exc:
        record_result("DISHES", "Invalid food group filter", False, str(exc), "LOW")


# ==============================================================================
# 3. SAMPLES & SAMPLE IMAGE ENDPOINTS
# ==============================================================================
def test_samples_and_images(session: requests.Session):
    print("\n=== [SUITE 3] GET /api/v1/samples & /api/v1/sample-image/{dish_id} ===")
    url_samples = f"{BASE_URL}/api/v1/samples"

    # 3.1 Fetch sample list
    samples_list = []
    try:
        r = session.get(url_samples, timeout=5)
        passed = (r.status_code == 200)
        data = r.json() if passed else {}
        samples_list = data.get("samples", [])
        record_result(
            "SAMPLES", "GET /api/v1/samples Status 200", passed and len(samples_list) > 0,
            f"Status {r.status_code}, returned {len(samples_list)} sample dishes", "HIGH"
        )
    except Exception as exc:
        record_result("SAMPLES", "GET /api/v1/samples", False, str(exc), "HIGH")

    # 3.2 Verify every returned sample's image returns HTTP 200 with valid JPEG content
    broken_images = []
    success_count = 0
    for s in samples_list:
        dish_id = s.get("id")
        img_url = f"{BASE_URL}{s.get('sample_image_url')}"
        try:
            img_resp = session.get(img_url, timeout=5)
            if img_resp.status_code != 200:
                broken_images.append((dish_id, img_resp.status_code, "Non-200 status"))
            elif len(img_resp.content) < 100:
                broken_images.append((dish_id, img_resp.status_code, "File size too small (<100b)"))
            elif "image" not in img_resp.headers.get("content-type", "").lower():
                broken_images.append((dish_id, img_resp.status_code, f"Unexpected Content-Type: {img_resp.headers.get('content-type')}"))
            else:
                success_count += 1
        except Exception as e:
            broken_images.append((dish_id, 0, str(e)))

    record_result(
        "SAMPLES", "All Featured Sample Images return HTTP 200 Image",
        len(broken_images) == 0 and success_count > 0,
        f"{success_count}/{len(samples_list)} images loaded successfully. Broken: {broken_images}",
        "HIGH"
    )

    # 3.3 Test Case-Insensitivity of /api/v1/sample-image/{dish_id} (e.g. 'jm-25' vs 'JM-25')
    try:
        r_lower = session.get(f"{BASE_URL}/api/v1/sample-image/jm-25", timeout=5)
        record_result(
            "SAMPLES", "Sample image route handles lowercase dish_id ('jm-25')",
            r_lower.status_code == 200,
            f"Status code {r_lower.status_code}", "MEDIUM"
        )
    except Exception as exc:
        record_result("SAMPLES", "Sample image lowercase dish_id", False, str(exc), "MEDIUM")

    # 3.4 Non-existent dish ID: /api/v1/sample-image/NONEXISTENT_999
    try:
        r_404 = session.get(f"{BASE_URL}/api/v1/sample-image/NONEXISTENT_999", timeout=5)
        record_result(
            "SAMPLES", "Unknown dish ID returns 404",
            r_404.status_code == 404,
            f"Status code {r_404.status_code}, detail: {r_404.json().get('detail')}", "MEDIUM"
        )
    except Exception as exc:
        record_result("SAMPLES", "Sample image unknown dish ID", False, str(exc), "MEDIUM")

    # 3.5 Check phantom IDs in featured_ids list (JM-71, JM-75, JM-77, JM-87, JM-91)
    # These IDs were hardcoded in app.py featured_ids but don't exist in CATALOG_BY_ID
    phantom_ids = ["JM-71", "JM-75", "JM-77", "JM-87", "JM-91"]
    for pid in phantom_ids:
        try:
            r_ph = session.get(f"{BASE_URL}/api/v1/sample-image/{pid}", timeout=5)
            record_result(
                "SAMPLES", f"Hardcoded featured_id {pid} absent from catalog",
                r_ph.status_code == 404,
                f"Status {r_ph.status_code} (detail: {r_ph.json().get('detail')}). ID {pid} is listed in app.py featured_ids but not defined in dishes_catalog.py!",
                "MEDIUM"
            )
        except Exception as exc:
            record_result("SAMPLES", f"Phantom ID {pid}", False, str(exc), "MEDIUM")

    # 3.6 Path Traversal Security check
    try:
        r_trav = session.get(f"{BASE_URL}/api/v1/sample-image/..%2F..%2Fapp.py", timeout=5)
        record_result(
            "SAMPLES", "Path traversal injection handled safely (404/400)",
            r_trav.status_code in (404, 400, 422),
            f"Status code {r_trav.status_code}", "HIGH"
        )
    except Exception as exc:
        record_result("SAMPLES", "Path traversal test", False, str(exc), "HIGH")


# ==============================================================================
# 4. DETERMINISTIC NUTRITION CALCULATOR (POST /api/v1/calculate)
# ==============================================================================
def test_calculate_endpoint(session: requests.Session):
    print("\n=== [SUITE 4] POST /api/v1/calculate (Nutrition Calculation Engine) ===")
    url = f"{BASE_URL}/api/v1/calculate"

    # 4.1 Valid Single Item: JM-11 (Gongura Pappu), 150g, moderate oil
    try:
        payload = {
            "items": [
                {"catalog_id": "JM-11", "grams": 150.0, "oil_ghee_level": "moderate"}
            ]
        }
        r = session.post(url, json=payload, timeout=5)
        passed = (r.status_code == 200)
        data = r.json() if passed else {}
        totals = data.get("totals", {})
        items = data.get("items", [])

        has_nutr = (
            totals.get("calories", 0) > 0
            and totals.get("protein_g", 0) > 0
            and totals.get("iron_mg", 0) > 0
            and totals.get("total_grams") == 150
            and len(items) == 1
        )
        record_result(
            "CALCULATE", "Valid Single Dish (JM-11, 150g)", passed and has_nutr,
            f"Status {r.status_code}, calories={totals.get('calories')}, protein={totals.get('protein_g')}g, iron={totals.get('iron_mg')}mg",
            "CRITICAL"
        )
    except Exception as exc:
        record_result("CALCULATE", "Valid Single Dish", False, str(exc), "CRITICAL")

    # 4.2 Multi-Item Meal Calculation (Pappu JM-11 + Vankaya JM-25 + Palakura JM-09)
    try:
        payload = {
            "items": [
                {"catalog_id": "JM-11", "grams": 150.0, "oil_ghee_level": "moderate"},
                {"catalog_id": "JM-25", "grams": 120.0, "oil_ghee_level": "moderate"},
                {"catalog_id": "JM-09", "grams": 100.0, "oil_ghee_level": "moderate"},
            ]
        }
        r = session.post(url, json=payload, timeout=5)
        data = r.json()
        totals = data.get("totals", {})
        items = data.get("items", [])

        sum_cal = sum(it["nutrition"]["calories"] for it in items)
        sum_grams = sum(it["grams"] for it in items)
        math_correct = (totals.get("total_grams") == int(sum_grams) and abs(totals.get("calories", 0) - sum_cal) <= 2)
        groups = data.get("mddw_groups_covered", [])

        record_result(
            "CALCULATE", "Multi-Dish Plate Math & MDD-W Aggregation",
            r.status_code == 200 and math_correct and len(groups) >= 2,
            f"Calories={totals.get('calories')} (sum of parts={sum_cal}), total_grams={totals.get('total_grams')}, MDD-W groups={groups}",
            "HIGH"
        )
    except Exception as exc:
        record_result("CALCULATE", "Multi-Dish Plate", False, str(exc), "HIGH")

    # 4.3 Oil Modifiers: Low vs Moderate vs High
    try:
        p_low = {"items": [{"catalog_id": "JM-25", "grams": 100.0, "oil_ghee_level": "low"}]}
        p_mod = {"items": [{"catalog_id": "JM-25", "grams": 100.0, "oil_ghee_level": "moderate"}]}
        p_high = {"items": [{"catalog_id": "JM-25", "grams": 100.0, "oil_ghee_level": "high"}]}

        r_low = session.post(url, json=p_low, timeout=5).json()
        r_mod = session.post(url, json=p_mod, timeout=5).json()
        r_high = session.post(url, json=p_high, timeout=5).json()

        fat_low = r_low["totals"]["fat_g"]
        fat_mod = r_mod["totals"]["fat_g"]
        fat_high = r_high["totals"]["fat_g"]
        cal_low = r_low["totals"]["calories"]
        cal_mod = r_mod["totals"]["calories"]
        cal_high = r_high["totals"]["calories"]

        order_correct = (fat_low < fat_mod < fat_high) and (cal_low <= cal_mod < cal_high)
        record_result(
            "CALCULATE", "Oil Modifier Impact (low < moderate < high)",
            order_correct,
            f"Fat: {fat_low}g < {fat_mod}g < {fat_high}g; Calories: {cal_low} < {cal_mod} < {cal_high}",
            "HIGH"
        )
    except Exception as exc:
        record_result("CALCULATE", "Oil Modifiers", False, str(exc), "HIGH")

    # 4.4 Custom / Unknown oil level (graceful fallback to 1.0)
    try:
        p_unk = {"items": [{"catalog_id": "JM-11", "grams": 100.0, "oil_ghee_level": "extra-crispy-oil"}]}
        r_unk = session.post(url, json=p_unk, timeout=5)
        record_result(
            "CALCULATE", "Unknown oil modifier defaults gracefully to 1.0",
            r_unk.status_code == 200,
            f"Status {r_unk.status_code}, calories={r_unk.json()['totals']['calories']}", "MEDIUM"
        )
    except Exception as exc:
        record_result("CALCULATE", "Unknown oil modifier", False, str(exc), "MEDIUM")

    # 4.5 Empty Items List: {"items": []}
    try:
        p_empty = {"items": []}
        r_empty = session.post(url, json=p_empty, timeout=5)
        data = r_empty.json()
        record_result(
            "CALCULATE", "Empty items list handled gracefully (200 with zero totals)",
            r_empty.status_code == 200 and data.get("totals", {}).get("calories") == 0 and len(data.get("items", [])) == 0,
            f"Status {r_empty.status_code}, totals={data.get('totals')}", "MEDIUM"
        )
    except Exception as exc:
        record_result("CALCULATE", "Empty items list", False, str(exc), "MEDIUM")

    # 4.6 Unknown Catalog ID: {"catalog_id": "NONEXISTENT_999"}
    try:
        p_bad_id = {"items": [{"catalog_id": "NONEXISTENT_999", "grams": 100.0, "oil_ghee_level": "moderate"}]}
        r_bad_id = session.post(url, json=p_bad_id, timeout=5)
        record_result(
            "CALCULATE", "Unknown catalog ID returns 404",
            r_bad_id.status_code == 404,
            f"Status {r_bad_id.status_code}, detail: {r_bad_id.json().get('detail')}", "HIGH"
        )
    except Exception as exc:
        record_result("CALCULATE", "Unknown catalog ID", False, str(exc), "HIGH")

    # 4.7 Untrimmed Whitespace in catalog_id: {"catalog_id": "  JM-11  "}
    try:
        p_ws = {"items": [{"catalog_id": "  JM-11  ", "grams": 100.0, "oil_ghee_level": "moderate"}]}
        r_ws = session.post(url, json=p_ws, timeout=5)
        record_result(
            "CALCULATE", "Untrimmed whitespace in catalog_id ('  JM-11  ') returns 404 (needs .strip())",
            r_ws.status_code == 200,
            f"Status {r_ws.status_code} (detail: {r_ws.json().get('detail') if r_ws.status_code != 200 else 'resolved'}). Missing .strip() before catalog lookup!",
            "LOW" if r_ws.status_code == 200 else "MEDIUM"
        )
    except Exception as exc:
        record_result("CALCULATE", "Whitespace catalog_id", False, str(exc), "LOW")

    # 4.8 Negative Grams Portion: {"grams": -100}
    try:
        p_neg = {"items": [{"catalog_id": "JM-11", "grams": -100.0, "oil_ghee_level": "moderate"}]}
        r_neg = session.post(url, json=p_neg, timeout=5)
        data_neg = r_neg.json()
        total_g = data_neg.get("totals", {}).get("total_grams", 0)
        passed_neg = (r_neg.status_code in (400, 422))
        record_result(
            "CALCULATE", "Negative grams validation rejected (400/422)",
            passed_neg,
            f"Status {r_neg.status_code}, total_grams became {total_g} (Pydantic PortionCalcItem lacks gt=0 validator!)",
            "MEDIUM" if not passed_neg else "LOW"
        )
    except Exception as exc:
        record_result("CALCULATE", "Negative grams portion", False, str(exc), "LOW")

    # 4.9 Malformed schema: {}
    try:
        r_malformed = session.post(url, json={"invalid_key": 123}, timeout=5)
        record_result(
            "CALCULATE", "Malformed schema returns 422 Unprocessable Entity",
            r_malformed.status_code == 422,
            f"Status {r_malformed.status_code}", "MEDIUM"
        )
    except Exception as exc:
        record_result("CALCULATE", "Malformed schema", False, str(exc), "MEDIUM")


# ==============================================================================
# 5. BASE64 FOOD SCAN ENDPOINT (POST /api/v1/scan-base64)
# ==============================================================================
def test_scan_base64_endpoint(session: requests.Session):
    print("\n=== [SUITE 5] POST /api/v1/scan-base64 (JSON Base64 Scan) ===")
    url = f"{BASE_URL}/api/v1/scan-base64"

    sample_img_path = get_sample_local_image_path()
    if sample_img_path:
        raw_img_bytes = sample_img_path.read_bytes()
    else:
        raw_img_bytes = create_synthetic_dish_image()

    valid_b64 = base64.b64encode(raw_img_bytes).decode("utf-8")
    data_uri_b64 = f"data:image/jpeg;base64,{valid_b64}"

    # 5.1 Valid Base64 Scan (Data URI Prefix)
    try:
        payload = {
            "image_base64": data_uri_b64,
            "meal_hint": "Gutti Vankaya or Andhra Curry",
            "preferred_model": "gemini-3.5-flash-lite",
        }
        t0 = time.perf_counter()
        r = session.post(url, json=payload, timeout=25)
        lat = int((time.perf_counter() - t0) * 1000)
        passed = (r.status_code == 200)
        data = r.json() if passed else {}
        record_result(
            "SCAN-BASE64", "Valid Base64 with data URI prefix",
            passed and data.get("status") == "success",
            f"Status {r.status_code}, latency={lat}ms, model={data.get('model_used')}, dish_count={data.get('dish_count')}",
            "CRITICAL"
        )

        # 5.2 Repeat Scan Cache Hit Check (<150ms)
        t1 = time.perf_counter()
        r_cached = session.post(url, json=payload, timeout=5)
        cached_lat = int((time.perf_counter() - t1) * 1000)
        passed_cache = (r_cached.status_code == 200 and cached_lat < 150)
        record_result(
            "SCAN-BASE64", "SHA-256 Cache Hit (<150ms)",
            passed_cache,
            f"Latency={cached_lat}ms, is_cached={r_cached.json().get('usage_and_cost', {}).get('cached')}, server_latency_ms={r_cached.json().get('latency_ms')}",
            "HIGH" if not passed_cache else "INFO"
        )
    except Exception as exc:
        record_result("SCAN-BASE64", "Valid Base64 scan", False, str(exc), "CRITICAL")

    # 5.3 Valid Base64 without data URI prefix (raw base64)
    try:
        payload_raw = {
            "image_base64": valid_b64,
            "meal_hint": "Gutti Vankaya or Andhra Curry",
            "preferred_model": "gemini-3.5-flash-lite",
        }
        r_raw = session.post(url, json=payload_raw, timeout=25)
        record_result(
            "SCAN-BASE64", "Raw Base64 without data URI prefix",
            r_raw.status_code == 200,
            f"Status {r_raw.status_code}", "HIGH"
        )
    except Exception as exc:
        record_result("SCAN-BASE64", "Raw Base64 scan", False, str(exc), "HIGH")

    # 5.4 Malformed / Invalid Base64 String: "ThisIsNotBase64!@#$%"
    try:
        payload_bad = {
            "image_base64": "ThisIsNotBase64!@#$%",
            "meal_hint": "Test",
        }
        r_bad = session.post(url, json=payload_bad, timeout=5)
        record_result(
            "SCAN-BASE64", "Malformed Base64 string returns 400 Bad Request",
            r_bad.status_code == 400,
            f"Status {r_bad.status_code}, detail: {r_bad.json().get('detail')}", "HIGH"
        )
    except Exception as exc:
        record_result("SCAN-BASE64", "Malformed Base64 test", False, str(exc), "HIGH")

    # 5.5 Valid Base64 of Non-Image / Corrupt Bytes (e.g. text file or garbage)
    try:
        corrupt_b64 = base64.b64encode(b"This is just plain text, not a valid JPEG or PNG!").decode("utf-8")
        payload_corrupt = {"image_base64": corrupt_b64}
        r_corrupt = session.post(url, json=payload_corrupt, timeout=5)
        # Note: UnidentifiedImageError raises 500 instead of 400!
        record_result(
            "SCAN-BASE64", "Corrupt image bytes error code (400 Bad Request vs 500)",
            r_corrupt.status_code == 400,
            f"Status {r_corrupt.status_code} (detail: {r_corrupt.json().get('detail')}). Expected 400 Bad Request, got {r_corrupt.status_code}!",
            "MEDIUM" if r_corrupt.status_code == 500 else "LOW"
        )
    except Exception as exc:
        record_result("SCAN-BASE64", "Corrupt image bytes test", False, str(exc), "MEDIUM")

    # 5.6 Empty Base64 String: {"image_base64": ""}
    try:
        payload_empty = {"image_base64": ""}
        r_empty = session.post(url, json=payload_empty, timeout=5)
        record_result(
            "SCAN-BASE64", "Empty Base64 string error handling (400 vs 500)",
            r_empty.status_code == 400,
            f"Status {r_empty.status_code}, detail: {r_empty.json().get('detail')}. Empty string triggers 500 instead of 400!",
            "MEDIUM" if r_empty.status_code == 500 else "LOW"
        )
    except Exception as exc:
        record_result("SCAN-BASE64", "Empty base64 string", False, str(exc), "MEDIUM")

    # 5.7 Missing Required Field: {}
    try:
        r_missing = session.post(url, json={}, timeout=5)
        record_result(
            "SCAN-BASE64", "Missing image_base64 field returns 422",
            r_missing.status_code == 422,
            f"Status {r_missing.status_code}", "LOW"
        )
    except Exception as exc:
        record_result("SCAN-BASE64", "Missing field test", False, str(exc), "LOW")


# ==============================================================================
# 6. MULTIPART UPLOAD SCAN ENDPOINT (POST /api/v1/scan)
# ==============================================================================
def test_scan_multipart_upload_endpoint(session: requests.Session):
    print("\n=== [SUITE 6] POST /api/v1/scan (Multipart Form Upload) ===")
    url = f"{BASE_URL}/api/v1/scan"

    sample_img_path = get_sample_local_image_path()
    if sample_img_path:
        raw_img_bytes = sample_img_path.read_bytes()
    else:
        raw_img_bytes = create_synthetic_dish_image()

    # 6.1 Valid File Upload
    try:
        files = {"file": ("test_dish.jpg", raw_img_bytes, "image/jpeg")}
        data = {"meal_hint": "Lunch Thali", "preferred_model": "gemini-3.5-flash-lite"}
        t0 = time.perf_counter()
        r = session.post(url, files=files, data=data, timeout=25)
        lat = int((time.perf_counter() - t0) * 1000)
        passed = (r.status_code == 200)
        res_data = r.json() if passed else {}
        record_result(
            "SCAN-UPLOAD", "Valid Multipart File Upload",
            passed and res_data.get("status") == "success",
            f"Status {r.status_code}, latency={lat}ms, plate_title={res_data.get('plate_title_en')}",
            "CRITICAL"
        )
    except Exception as exc:
        record_result("SCAN-UPLOAD", "Valid File Upload", False, str(exc), "CRITICAL")

    # 6.2 Empty File (0 bytes) -> Check bug where HTTPException(400) is caught by except Exception -> 500!
    try:
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        r_empty = session.post(url, files=files, timeout=5)
        record_result(
            "SCAN-UPLOAD", "Empty File (0 bytes) returns 400 Bad Request",
            r_empty.status_code == 400,
            f"Status {r_empty.status_code}, detail: {r_empty.json().get('detail')}. "
            f"{'BUG: HTTPException(400) caught by generic except Exception in app.py line 227!' if r_empty.status_code == 500 else ''}",
            "HIGH" if r_empty.status_code == 500 else "INFO"
        )
    except Exception as exc:
        record_result("SCAN-UPLOAD", "Empty File Upload", False, str(exc), "HIGH")

    # 6.3 Corrupt Image File (random binary bytes)
    try:
        corrupt_bytes = b"GIF89aNOT_REALLY_A_VALID_IMAGE_JUST_RANDOM_CORRUPT_BYTES_XYZ" * 20
        files = {"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}
        r_corrupt = session.post(url, files=files, timeout=5)
        record_result(
            "SCAN-UPLOAD", "Corrupt Image File error code (400 vs 500)",
            r_corrupt.status_code == 400,
            f"Status {r_corrupt.status_code} (detail: {r_corrupt.json().get('detail')}). Expected 400 Bad Request, got {r_corrupt.status_code}!",
            "MEDIUM" if r_corrupt.status_code == 500 else "LOW"
        )
    except Exception as exc:
        record_result("SCAN-UPLOAD", "Corrupt File Upload", False, str(exc), "MEDIUM")

    # 6.4 Oversized / Huge Image Upload (e.g. high-res 4000x3000 JPEG)
    try:
        print("    Generating high-res 4000x3000 test image...")
        huge_img = Image.new("RGB", (4000, 3000), color=(200, 150, 100))
        draw = ImageDraw.Draw(huge_img)
        draw.rectangle([(500, 500), (3500, 2500)], fill=(50, 180, 50))
        buf = io.BytesIO()
        huge_img.save(buf, format="JPEG", quality=90)
        huge_bytes = buf.getvalue()
        huge_size_mb = len(huge_bytes) / (1024 * 1024)

        files = {"file": ("huge_phone_camera.jpg", huge_bytes, "image/jpeg")}
        data = {"preferred_model": "gemini-3.5-flash-lite"}
        t0 = time.perf_counter()
        r_huge = session.post(url, files=files, data=data, timeout=30)
        lat = int((time.perf_counter() - t0) * 1000)
        passed = (r_huge.status_code == 200)
        dim = r_huge.json().get("image_dimensions", {}) if passed else {}
        record_result(
            "SCAN-UPLOAD", f"Huge File Upload ({huge_size_mb:.1f} MB, 4000x3000)",
            passed,
            f"Status {r_huge.status_code}, latency={lat}ms, dimensions reported: {dim}", "HIGH"
        )
    except Exception as exc:
        record_result("SCAN-UPLOAD", "Huge File Upload", False, str(exc), "HIGH")

    # 6.5 Missing 'file' field in multipart form
    try:
        r_nofile = session.post(url, data={"meal_hint": "Test"}, timeout=5)
        record_result(
            "SCAN-UPLOAD", "Missing file field returns 422 Unprocessable Entity",
            r_nofile.status_code == 422,
            f"Status {r_nofile.status_code}", "LOW"
        )
    except Exception as exc:
        record_result("SCAN-UPLOAD", "Missing file field", False, str(exc), "LOW")


# ==============================================================================
# 7. EDGE CASE: SMARTPHONE EXIF ORIENTATION HANDLING
# ==============================================================================
def test_exif_orientation_handling():
    print("\n=== [SUITE 7] EDGE CASE: Smartphone EXIF Orientation Handling ===")
    from scanner_engine import preprocess_image

    orientations_to_test = [
        (1, "Normal (0 deg)"),
        (3, "Upside Down (180 deg)"),
        (6, "Smartphone Portrait (90 deg CW)"),
        (8, "Smartphone Portrait (270 deg CW)"),
    ]

    for ori_val, ori_desc in orientations_to_test:
        img = Image.new("RGB", (400, 200), color=(255, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 100), (400, 200)], fill=(0, 0, 255))

        exif = img.getexif()
        exif[0x0112] = ori_val
        buf = io.BytesIO()
        img.save(buf, format="JPEG", exif=exif)
        raw_bytes = buf.getvalue()

        b64, mime, rep_w, rep_h = preprocess_image(raw_bytes)
        processed_img = Image.open(io.BytesIO(base64.b64decode(b64)))
        processed_exif = processed_img.getexif()
        has_exif_in_output = (0x0112 in processed_exif)

        correct_transposed = ImageOps.exif_transpose(Image.open(io.BytesIO(raw_bytes)))
        expected_size = correct_transposed.size
        is_size_transposed = (processed_img.size == expected_size)

        if ori_val in (6, 8):
            is_handled_correctly = is_size_transposed and (not has_exif_in_output or processed_exif.get(0x0112) == 1)
            record_result(
                "EXIF", f"EXIF Orientation {ori_val} ({ori_desc})",
                is_handled_correctly,
                f"Input size=(400, 200), processed size={processed_img.size}, expected={expected_size}. "
                f"EXIF in output: {processed_exif.get(0x0112, 'STRIPPED')}. "
                f"{'FAIL: Orientation NOT applied and EXIF stripped — image sent sideways to Gemini!' if not is_handled_correctly else 'PASS'}",
                "HIGH" if not is_handled_correctly else "INFO"
            )
        elif ori_val == 3:
            px = processed_img.getpixel((0, 0))
            is_blue = (px[2] > 240 and px[0] < 20)
            record_result(
                "EXIF", f"EXIF Orientation 3 ({ori_desc})",
                is_blue,
                f"Top-left pixel: {px}, expected predominantly blue (e.g. (0,0,254~255)). "
                f"{'FAIL: Orientation NOT applied — image upside down!' if not is_blue else 'PASS'}",
                "HIGH" if not is_blue else "INFO"
            )
        else:
            record_result(
                "EXIF", f"EXIF Orientation {ori_val} ({ori_desc})",
                True, f"Normal orientation preserved: {processed_img.size}", "INFO"
            )


# ==============================================================================
# 8. CONCURRENCY, EVENT LOOP & STRESS TESTING
# ==============================================================================
def test_concurrency_and_stress(session: requests.Session):
    print("\n=== [SUITE 8] Rapid Concurrent Requests & Event Loop Non-blocking Test ===")
    concurrency = 50
    urls_and_methods = [
        ("GET", f"{BASE_URL}/api/v1/health", None),
        ("GET", f"{BASE_URL}/api/v1/stats", None),
        ("GET", f"{BASE_URL}/api/v1/dishes?q=pappu", None),
        ("GET", f"{BASE_URL}/api/v1/dishes?cluster=Tiffins%20%26%20Breads", None),
        ("POST", f"{BASE_URL}/api/v1/calculate", {"items": [{"catalog_id": "JM-11", "grams": 150.0, "oil_ghee_level": "moderate"}]}),
    ]

    tasks = [urls_and_methods[i % len(urls_and_methods)] for i in range(concurrency)]

    def _make_req(task_info: Tuple[str, str, Optional[Dict[str, Any]]]) -> Tuple[int, float, Optional[str]]:
        method, url, payload = task_info
        t0 = time.perf_counter()
        try:
            if method == "GET":
                resp = session.get(url, timeout=10)
            else:
                resp = session.post(url, json=payload, timeout=10)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return resp.status_code, elapsed_ms, None
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return 0, elapsed_ms, str(exc)

    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(_make_req, tasks))
    total_time_s = time.perf_counter() - t_start

    status_codes = [r[0] for r in results]
    latencies = [r[1] for r in results]
    errors = [r[2] for r in results if r[2] is not None]

    status_200_count = sum(1 for c in status_codes if c == 200)
    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    p95_lat = sorted(latencies)[int(0.95 * len(latencies))] if latencies else 0
    rps = concurrency / total_time_s if total_time_s > 0 else 0

    all_200 = (status_200_count == concurrency)
    record_result(
        "CONCURRENCY", f"{concurrency} Rapid Concurrent Requests (Pooled Session)",
        all_200 and len(errors) == 0,
        f"{status_200_count}/{concurrency} requests succeeded (200 OK) in {total_time_s:.2f}s "
        f"({rps:.1f} req/s). Avg: {avg_lat:.1f}ms, P95: {p95_lat:.1f}ms. Errors: {len(errors)}",
        "HIGH" if not all_200 else "INFO"
    )


# ==============================================================================
# MAIN RUNNER & REPORT GENERATOR
# ==============================================================================
def run_all_tests():
    print("=" * 80)
    print("Annapurna Telugu Food Scanner — Full API & Edge-Case QA Audit Suite")
    print(f"Target Server: {BASE_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Use a persistent session with connection pooling
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # 1. Health & Stats
    test_health_endpoint(session)
    test_stats_endpoint(session)

    # 2. Dishes Catalog
    test_dishes_endpoint(session)

    # 3. Samples & Sample Images
    test_samples_and_images(session)

    # 4. Nutrition Calculation
    test_calculate_endpoint(session)

    # 5. Base64 Scan
    test_scan_base64_endpoint(session)

    # 6. Multipart Upload Scan
    test_scan_multipart_upload_endpoint(session)

    # 7. EXIF Orientation
    test_exif_orientation_handling()

    # 8. Concurrency & Stress
    test_concurrency_and_stress(session)

    # Summary
    print("\n" + "=" * 80)
    total_tests = len(AUDIT_LOGS)
    total_passed = sum(1 for log in AUDIT_LOGS if log["passed"])
    total_failed = total_tests - total_passed
    print(f"AUDIT SUMMARY: {total_passed}/{total_tests} Tests Passed ({total_failed} Failed)")
    print("=" * 80)

    if BUGS_AND_ANOMALIES:
        print(f"\nDiscovered {len(BUGS_AND_ANOMALIES)} Bugs / Edge-Case Anomalies:")
        for idx, b in enumerate(BUGS_AND_ANOMALIES, 1):
            print(f"  {idx}. [{b['severity']}] {b['category']} — {b['test_name']}: {b['details']}")
    else:
        print("\nAll endpoints and edge cases passed with flying colors!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
