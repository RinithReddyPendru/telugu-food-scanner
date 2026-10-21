"""
FastAPI Backend + Drop-in Spike API Replacement for Telugu Food Scanner.
Provides:
- POST /api/v1/scan (multipart file upload)
- POST /api/v1/scan-base64 (JSON base64 payload - easy drop-in for mobile/web apps)
- POST /api/v1/scan-sample/{dish_id} (1-click test using local Telugu dish images)
- GET  /api/v1/dishes (searchable 121-dish Telugu + ICMR-NIN nutrition catalog)
- POST /api/v1/calculate (instant deterministic nutrition recalculation for custom portions)
- GET  /api/v1/samples & /api/v1/sample-image/{dish_id}
- GET  / (Serves the Telugu Food Scanner Web UI)
"""

from __future__ import annotations
import asyncio
import base64
import binascii
import io
import json
import pathlib
import time
import urllib.request
from typing import Any, Dict, List, Optional
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from dishes_catalog import (
    CATALOG,
    CATALOG_BY_ID,
    compute_portion_nutrition,
)
from scanner_engine import (
    MDDW_LABELS,
    MODEL_FAILOVER_POOL,
    MODEL_PRICING_PER_1M,
    _SCAN_CACHE,
    resolve_gemini_api_key,
    scan_telugu_food_image,
)

APP_DIR = pathlib.Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="AIM FOOD SCANNER — Telugu Food Scanner & ICMR-NIN Nutrition API",
    description=(
        "High-accuracy Andhra & Telangana dish recognition and macro/micronutrient engine "
        "powered by Gemini 3.8 Flash Vision + ICMR-NIN (Hyderabad) IFCT & Janani Mitra 93-Dish Catalog. "
        "Designed as a superior drop-in replacement for Spike API / LogMeal."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Base64ScanRequest(BaseModel):
    image_base64: str = Field(description="Base64-encoded JPEG/PNG/WebP image (with or without data:image/... prefix)")
    meal_hint: Optional[str] = Field(default=None, description="Optional meal context or hint, e.g., 'Lunch thali' or 'Breakfast'")
    preferred_model: Optional[str] = Field(default="auto", description="Model selector: 'auto' (failover pool) or specific model ID")
    api_key: Optional[str] = Field(default=None, description="Optional Gemini API key override")


class PortionCalcItem(BaseModel):
    catalog_id: str = Field(description="Dish ID from catalog, e.g. 'JM-11' or 'JM-25'")
    grams: float = Field(gt=0, description="Portion weight in grams (must be > 0)")
    oil_ghee_level: str = Field(default="moderate", description="'low', 'moderate', or 'high'")

    @field_validator("catalog_id")
    @classmethod
    def clean_catalog_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("catalog_id cannot be empty")
        return v.strip().upper()


class PortionCalcRequest(BaseModel):
    items: List[PortionCalcItem]


@app.get("/api/v1/health")
def health_check():
    has_key = bool(resolve_gemini_api_key())
    return {
        "status": "ok",
        "model": "gemini-3.8-flash",
        "failover_pool": MODEL_FAILOVER_POOL,
        "catalog_size": len(CATALOG),
        "cached_scans": len(_SCAN_CACHE),
        "api_key_configured": has_key,
        "nutrition_standard": "ICMR-NIN (Hyderabad) IFCT + JM SuperAdmin 93-Dish Mapping",
    }


@app.get("/api/v1/stats")
def get_scanner_stats():
    """Returns live cache count, active model failover pool, pricing reference, and catalog metrics."""
    has_key = bool(resolve_gemini_api_key())
    return {
        "status": "ok",
        "cached_scans": len(_SCAN_CACHE),
        "failover_pool": MODEL_FAILOVER_POOL,
        "pricing_per_1m_usd": MODEL_PRICING_PER_1M,
        "catalog_size": len(CATALOG),
        "api_key_configured": has_key,
        "serverless_ready": True,
        "nutrition_standard": "ICMR-NIN (Hyderabad) IFCT + JM SuperAdmin 93-Dish Mapping",
    }


@app.get("/api/v1/dishes")
def list_dishes(
    q: Optional[str] = Query(default=None, description="Search by English name, Telugu name, or alias"),
    cluster: Optional[str] = Query(default=None, description="Filter by dish cluster/category"),
    food_group: Optional[str] = Query(default=None, description="Filter by MDD-W group code (G1..G10)"),
):
    results = CATALOG
    if q and isinstance(q, str) and q.strip():
        q_low = q.strip().lower()
        results = [
            d for d in results
            if q_low in d["name_en"].lower()
            or q_low in d["name_te"]
            or q_low in d["id"].lower()
            or any(q_low in alias.lower() for alias in d.get("aliases", []))
        ]
    if cluster and isinstance(cluster, str) and cluster.strip():
        c_low = cluster.strip().lower()
        if c_low in ("breakfast", "tiffin", "tiffins", "tiffins & breads"):
            results = [d for d in results if d["cluster"].lower() in ("tiffins & breads", "breakfast", "tiffin")]
        else:
            results = [d for d in results if d["cluster"].lower() == c_low]
    if food_group and isinstance(food_group, str) and food_group.strip():
        fg_up = food_group.strip().upper()
        results = [d for d in results if fg_up in d["food_groups"]]

    enriched = []
    for d in results:
        item = dict(d)
        item["standard_serving_nutrition"] = compute_portion_nutrition(
            d["per_100g"], d["serving_grams"]
        )
        item["has_local_sample"] = bool(d.get("local_image") and pathlib.Path(d["local_image"]).exists())
        enriched.append(item)

    clusters = sorted({d["cluster"] for d in CATALOG})
    return {
        "count": len(enriched),
        "total_catalog": len(CATALOG),
        "clusters": clusters,
        "mddw_groups": MDDW_LABELS,
        "dishes": enriched,
    }


@app.get("/api/v1/samples")
def get_featured_samples():
    """Returns curated sample Telugu dishes that have local images on disk for 1-click testing."""
    featured_ids = [
        "JM-22",  # Gutti Vankaya
        "JM-11",  # Gongura Pappu
        "JM-09",  # Palakura Pappu
        "JM-05",  # Munagaku Vepudu
        "JM-47",  # Allam Pachadi
        "JM-49",  # Gongura Pachadi
        "JM-51",  # Kandi Podi
        "JM-55",  # Guddu Porutu
        "JM-56",  # Natukodi Pulusu
        "JM-60",  # Gongura Mutton
        "JM-101", # Steamed White Rice
        "JM-102", # Ragi Sangati
        "JM-105", # Pesarattu
        "JM-107", # Idli Sambar
        "JM-129", # Sambar
    ]
    samples = []
    for fid in featured_ids:
        d = CATALOG_BY_ID.get(fid)
        if d:
            has_img = bool(d.get("local_image") and pathlib.Path(d["local_image"]).exists())
            samples.append({
                "id": d["id"],
                "name_en": d["name_en"],
                "name_te": d["name_te"],
                "cluster": d["cluster"],
                "emoji": d["emoji"],
                "serving_unit": d["serving_unit"],
                "food_groups": d["food_groups"],
                "has_local_image": has_img,
                "sample_image_url": f"/api/v1/sample-image/{d['id']}" if has_img else "",
            })
    return {"samples": samples}


@app.get("/api/v1/sample-image/{dish_id}")
def get_sample_image(dish_id: str):
    d = CATALOG_BY_ID.get(dish_id.upper())
    if not d or not d.get("local_image"):
        raise HTTPException(status_code=404, detail="Sample image not found for this dish ID")
    img_path = pathlib.Path(d["local_image"])
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Local image file missing on disk")
    return FileResponse(str(img_path), media_type="image/jpeg")


def _generate_thumbnail_data_url(image_bytes: bytes, max_dim: int = 800) -> str:
    """Generate a crisp, high-definition JPEG base64 data URL for admin dashboard & UI viewing (~70-95KB)."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGB")
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85, optimize=True)
            b64_str = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/jpeg;base64,{b64_str}"
    except Exception:
        return ""


def sync_scan_to_firestore_server(result: Dict[str, Any], image_bytes: Optional[bytes] = None) -> Optional[str]:
    """
    Directly persists scan results and food photo thumbnail into Firestore collection `food_scanner`
    using the Firebase REST API. Returns the created document ID.
    """
    firebase_api_key = os.environ.get("FIREBASE_API_KEY", "").strip()
    if not firebase_api_key:
        # If no FIREBASE_API_KEY environment variable is configured, graceful bypass (client-side will persist)
        return None

    try:
        url = (
            "https://firestore.googleapis.com/v1/projects/mddw-app/databases/(default)/documents/food_scanner"
            f"?key={firebase_api_key}"
        )
        totals = result.get("totals") or {}
        items = result.get("items") or []
        dish_name = result.get("plate_title_en") or (items[0].get("name_en") if items else "Recognized Dish")

        img_data_url = _generate_thumbnail_data_url(image_bytes) if image_bytes else ""

        items_val = []
        for it in items:
            it_fields = {
                "name_en": {"stringValue": str(it.get("name_en") or "")},
                "name_te": {"stringValue": str(it.get("name_te") or "")},
                "cluster": {"stringValue": str(it.get("cluster") or "")},
                "grams": {"integerValue": str(int(it.get("estimated_grams") or it.get("grams") or 0))},
            }
            if it.get("nutrition"):
                it_fields["calories"] = {"doubleValue": float(it["nutrition"].get("calories", 0))}
            items_val.append({"mapValue": {"fields": it_fields}})

        fields = {
            "name": {"stringValue": str(dish_name)},
            "category": {"stringValue": str(result.get("meal_type") or "Food")},
            "mealLabel": {"stringValue": str(result.get("meal_type") or "Meal")},
            "status": {"stringValue": "Scanned"},
            "calories": {"doubleValue": float(totals.get("calories", 0))},
            "protein_g": {"doubleValue": float(totals.get("protein_g", 0))},
            "carbs_g": {"doubleValue": float(totals.get("carbs_g", 0))},
            "fiber_g": {"doubleValue": float(totals.get("fiber_g", 0))},
            "iron_mg": {"doubleValue": float(totals.get("iron_mg", 0))},
            "calcium_mg": {"doubleValue": float(totals.get("calcium_mg", 0))},
            "timestamp": {"integerValue": str(int(time.time() * 1000))},
            "source": {"stringValue": "AIM FOOD SCANNER (Direct Server Sync)"},
            "items": {"arrayValue": {"values": items_val}},
        }
        if img_data_url:
            fields["imageUrl"] = {"stringValue": img_data_url}

        body_bytes = json.dumps({"fields": fields}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            doc_name = data.get("name", "")
            return doc_name.split("/")[-1] if doc_name else None
    except Exception as exc:
        print(f"[Firestore Server Sync Warning]: {exc}")
        return None


@app.post("/api/v1/scan")
async def scan_food_upload(
    file: UploadFile = File(...),
    meal_hint: Optional[str] = Form(default=None),
    preferred_model: Optional[str] = Form(default="auto"),
    api_key: Optional[str] = Form(default=None),
    x_gemini_api_key: Optional[str] = Header(default=None),
):
    """
    Primary endpoint to scan an uploaded Telugu food photo (multipart/form-data).
    Returns dish identification (English + Telugu), portion weight, macros, micronutrients, and MDD-W groups.
    """
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image file is empty.")
    key_override = api_key or x_gemini_api_key
    try:
        result = await asyncio.to_thread(
            scan_telugu_food_image,
            image_bytes=image_bytes,
            meal_hint=meal_hint,
            api_key_override=key_override,
            preferred_model=preferred_model,
        )
        # Instantly guarantee Firestore persistence from server
        try:
            doc_id = await asyncio.to_thread(sync_scan_to_firestore_server, result, image_bytes)
            if doc_id:
                result["firestore_id"] = doc_id
        except Exception:
            pass
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except (ValueError, UnidentifiedImageError, binascii.Error) as ve:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(ve)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Food scan failed: {str(exc)}")


@app.post("/api/v1/scan-base64")
async def scan_food_base64(
    payload: Base64ScanRequest,
    x_gemini_api_key: Optional[str] = Header(default=None),
):
    """
    JSON base64 endpoint — ideal as a direct backend/mobile drop-in replacement for Spike API.
    """
    raw_b64 = (payload.image_base64 or "").strip()
    if not raw_b64:
        raise HTTPException(status_code=400, detail="Image base64 string is empty.")
    if "," in raw_b64 and raw_b64.startswith("data:"):
        raw_b64 = raw_b64.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(raw_b64)
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Decoded image is empty.")
        key_override = payload.api_key or x_gemini_api_key
        result = await asyncio.to_thread(
            scan_telugu_food_image,
            image_bytes=image_bytes,
            meal_hint=payload.meal_hint,
            api_key_override=key_override,
            preferred_model=payload.preferred_model,
        )
        # Instantly guarantee Firestore persistence from server
        try:
            doc_id = await asyncio.to_thread(sync_scan_to_firestore_server, result, image_bytes)
            if doc_id:
                result["firestore_id"] = doc_id
        except Exception:
            pass
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except (ValueError, UnidentifiedImageError, binascii.Error) as ve:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(ve)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Base64 food scan failed: {str(exc)}")


@app.post("/api/v1/scan-sample/{dish_id}")
async def scan_sample_dish(
    dish_id: str,
    preferred_model: Optional[str] = Query(default="auto"),
    api_key: Optional[str] = Query(default=None),
    x_gemini_api_key: Optional[str] = Header(default=None),
):
    """Scans one of the local Telugu dish images by ID."""
    clean_id = (dish_id or "").strip().upper()
    d = CATALOG_BY_ID.get(clean_id)
    if not d or not d.get("local_image"):
        raise HTTPException(status_code=404, detail=f"No sample image found for {dish_id}")
    img_path = pathlib.Path(d["local_image"])
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Sample image file not found on disk")
    try:
        image_bytes = img_path.read_bytes()
        key_override = api_key or x_gemini_api_key
        result = await asyncio.to_thread(
            scan_telugu_food_image,
            image_bytes=image_bytes,
            meal_hint=f"Reference sample dish: {d['id']} - {d['name_en']} ({d['name_te']})",
            api_key_override=key_override,
            preferred_model=preferred_model,
        )
        try:
            doc_id = await asyncio.to_thread(sync_scan_to_firestore_server, result, image_bytes)
            if doc_id:
                result["firestore_id"] = doc_id
        except Exception:
            pass
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sample scan failed: {str(exc)}")


@app.post("/api/v1/calculate")
def calculate_custom_portions(req: PortionCalcRequest):
    """Deterministic ICMR-NIN nutrition calculator for any list of catalog dishes and gram weights."""
    oil_mod_map = {"low": 0.85, "moderate": 1.0, "high": 1.2}
    items_out = []
    totals = {
        "calories": 0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0,
        "iron_mg": 0.0, "calcium_mg": 0.0, "folate_ug": 0.0, "vit_a_ug": 0.0, "vit_c_mg": 0.0,
        "sodium_mg": 0.0, "total_grams": 0,
    }
    groups_set = set()

    for entry in req.items:
        clean_id = (entry.catalog_id or "").strip().upper()
        d = CATALOG_BY_ID.get(clean_id)
        if not d:
            raise HTTPException(status_code=404, detail=f"Catalog ID '{entry.catalog_id}' not found")
        oil_mod = oil_mod_map.get(entry.oil_ghee_level.lower(), 1.0)
        nutr = compute_portion_nutrition(d["per_100g"], entry.grams, oil_modifier=oil_mod)
        for fg in d["food_groups"]:
            groups_set.add(fg)
        for k in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "iron_mg", "calcium_mg", "folate_ug", "vit_a_ug", "vit_c_mg", "sodium_mg"):
            totals[k] = round(totals[k] + nutr[k], 2 if k == "iron_mg" else (0 if k in ("calories", "sodium_mg") else 1))
        totals["total_grams"] += int(entry.grams)
        items_out.append({
            "catalog_id": d["id"],
            "name_en": d["name_en"],
            "name_te": d["name_te"],
            "grams": entry.grams,
            "oil_ghee_level": entry.oil_ghee_level,
            "nutrition": nutr,
        })

    return {
        "totals": totals,
        "mddw_groups_covered": sorted(groups_set),
        "items": items_out,
    }


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>UI loading...</h1>")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin.html", response_class=HTMLResponse)
def serve_admin():
    admin_file = STATIC_DIR / "admin.html"
    if not admin_file.exists():
        return HTMLResponse("<h1>Admin UI not found</h1>", status_code=404)
    return HTMLResponse(admin_file.read_text(encoding="utf-8"))

