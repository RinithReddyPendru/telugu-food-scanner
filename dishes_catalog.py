"""
Telugu Dish & ICMR-NIN (Hyderabad) Nutrition Catalog.
Loads all 93 Andhra & Telangana dishes from JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx
and merges them with grounded ICMR-NIN (Indian Food Composition Tables) per-100g
and per-standard-serving macro & micronutrient profiles, plus 37+ everyday Telugu staples.
"""

from __future__ import annotations
import pathlib
import re
from typing import Dict, List, Optional, Any
import openpyxl

APP_DIR = pathlib.Path(__file__).resolve().parent
LOCAL_EXCEL_PATH = APP_DIR / "JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx"
PARENT_EXCEL_PATH = APP_DIR.parent / "JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx"
EXCEL_PATH = LOCAL_EXCEL_PATH if LOCAL_EXCEL_PATH.exists() else PARENT_EXCEL_PATH

# Grounded ICMR-NIN (Hyderabad) & NIN Dietary Guidelines for Indians values per 100g cooked
# Format:
# key (sort_order or slug) -> {
#   serving_unit: str ("1 katori (150g)", "2 pieces (120g)", "1 tbsp (20g)", etc.),
#   serving_grams: int,
#   per_100g: {calories, protein_g, carbs_g, fat_g, fiber_g, iron_mg, calcium_mg, folate_ug, vit_a_ug, vit_c_mg, sodium_mg},
#   gi_tier: "Low" | "Medium" | "High",
#   telugu_aliases: list[str]
# }

EXCEL_DISH_NUTRITION_BY_ORDER: Dict[int, Dict[str, Any]] = {
    # Leafy Green Curries (1-8)
    1: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 92, "protein_g": 3.6, "carbs_g": 7.2, "fat_g": 5.4, "fiber_g": 4.1, "iron_mg": 4.8, "calcium_mg": 215, "folate_ug": 72, "vit_a_ug": 290, "vit_c_mg": 38, "sodium_mg": 240},
        "aliases": ["thotakura vepudu", "thotakura fry", "amaranth stir fry", "erra thotakura"]
    },
    2: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 86, "protein_g": 2.9, "carbs_g": 6.0, "fat_g": 5.5, "fiber_g": 3.2, "iron_mg": 3.5, "calcium_mg": 98, "folate_ug": 110, "vit_a_ug": 420, "vit_c_mg": 28, "sodium_mg": 250},
        "aliases": ["palakura kura", "palakura vepudu", "palak fry", "spinach curry"]
    },
    3: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 108, "protein_g": 2.4, "carbs_g": 8.5, "fat_g": 7.2, "fiber_g": 3.8, "iron_mg": 5.4, "calcium_mg": 140, "folate_ug": 64, "vit_a_ug": 260, "vit_c_mg": 42, "sodium_mg": 290},
        "aliases": ["gongura pulusu", "gongura kura", "puntikura", "ambadi curry"]
    },
    4: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 96, "protein_g": 4.1, "carbs_g": 7.4, "fat_g": 5.6, "fiber_g": 4.5, "iron_mg": 4.2, "calcium_mg": 190, "folate_ug": 78, "vit_a_ug": 240, "vit_c_mg": 34, "sodium_mg": 230},
        "aliases": ["menthikura vepudu", "methi fry", "fenugreek leaves curry"]
    },
    5: {
        "serving_unit": "1 katori (100g)", "serving_grams": 100, "gi_tier": "Low",
        "per_100g": {"calories": 112, "protein_g": 6.2, "carbs_g": 9.8, "fat_g": 5.4, "fiber_g": 4.8, "iron_mg": 6.5, "calcium_mg": 310, "folate_ug": 95, "vit_a_ug": 520, "vit_c_mg": 85, "sodium_mg": 220},
        "aliases": ["munagaku vepudu", "moringa leaves fry", "drumstick leaves stir fry"]
    },
    6: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 94, "protein_g": 3.8, "carbs_g": 7.8, "fat_g": 5.3, "fiber_g": 4.2, "iron_mg": 4.4, "calcium_mg": 230, "folate_ug": 68, "vit_a_ug": 310, "vit_c_mg": 32, "sodium_mg": 230},
        "aliases": ["ponnaganti kura", "ponnaganti vepudu", "alternanthera fry"]
    },
    7: {
        "serving_unit": "1 katori (130g)", "serving_grams": 130, "gi_tier": "Low",
        "per_100g": {"calories": 82, "protein_g": 2.4, "carbs_g": 6.8, "fat_g": 5.0, "fiber_g": 2.9, "iron_mg": 3.1, "calcium_mg": 125, "folate_ug": 88, "vit_a_ug": 340, "vit_c_mg": 45, "sodium_mg": 245},
        "aliases": ["bachali kura", "bachali pulusu", "malabar spinach curry"]
    },
    8: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 88, "protein_g": 2.6, "carbs_g": 6.5, "fat_g": 5.6, "fiber_g": 3.1, "iron_mg": 3.6, "calcium_mg": 110, "folate_ug": 70, "vit_a_ug": 275, "vit_c_mg": 48, "sodium_mg": 260},
        "aliases": ["chukkakura", "green sorrel curry", "khatta palak"]
    },

    # Dals & Pappu (9-24)
    9: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 118, "protein_g": 6.4, "carbs_g": 14.2, "fat_g": 4.0, "fiber_g": 3.8, "iron_mg": 2.9, "calcium_mg": 68, "folate_ug": 82, "vit_a_ug": 220, "vit_c_mg": 16, "sodium_mg": 260},
        "aliases": ["palakura pappu", "spinach dal", "palak pappu"]
    },
    10: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 122, "protein_g": 6.8, "carbs_g": 14.8, "fat_g": 4.1, "fiber_g": 4.0, "iron_mg": 3.6, "calcium_mg": 118, "folate_ug": 76, "vit_a_ug": 195, "vit_c_mg": 22, "sodium_mg": 255},
        "aliases": ["thotakura pappu", "amaranth dal"]
    },
    11: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 126, "protein_g": 6.5, "carbs_g": 15.0, "fat_g": 4.5, "fiber_g": 4.1, "iron_mg": 3.9, "calcium_mg": 95, "folate_ug": 70, "vit_a_ug": 180, "vit_c_mg": 25, "sodium_mg": 280},
        "aliases": ["gongura pappu", "sorrel dal", "andhra gongura pappu"]
    },
    12: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 121, "protein_g": 6.9, "carbs_g": 14.5, "fat_g": 4.1, "fiber_g": 4.2, "iron_mg": 3.2, "calcium_mg": 92, "folate_ug": 74, "vit_a_ug": 165, "vit_c_mg": 18, "sodium_mg": 250},
        "aliases": ["menthikura pappu", "methi dal", "fenugreek dal"]
    },
    13: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 119, "protein_g": 6.3, "carbs_g": 14.4, "fat_g": 4.1, "fiber_g": 3.7, "iron_mg": 2.8, "calcium_mg": 72, "folate_ug": 68, "vit_a_ug": 175, "vit_c_mg": 24, "sodium_mg": 265},
        "aliases": ["chukkakura pappu", "sour leafy dal"]
    },
    14: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 116, "protein_g": 6.2, "carbs_g": 14.0, "fat_g": 3.9, "fiber_g": 3.6, "iron_mg": 2.7, "calcium_mg": 80, "folate_ug": 78, "vit_a_ug": 210, "vit_c_mg": 20, "sodium_mg": 250},
        "aliases": ["bachali kura pappu", "malabar spinach dal"]
    },
    15: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 128, "protein_g": 7.6, "carbs_g": 15.4, "fat_g": 4.2, "fiber_g": 4.4, "iron_mg": 4.5, "calcium_mg": 165, "folate_ug": 88, "vit_a_ug": 310, "vit_c_mg": 42, "sodium_mg": 255},
        "aliases": ["munagaku pappu", "moringa dal", "drumstick leaves dal"]
    },
    16: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 120, "protein_g": 6.6, "carbs_g": 14.6, "fat_g": 4.0, "fiber_g": 3.9, "iron_mg": 3.1, "calcium_mg": 105, "folate_ug": 72, "vit_a_ug": 190, "vit_c_mg": 19, "sodium_mg": 250},
        "aliases": ["ponnaganti pappu", "ponaganti kura pappu"]
    },
    17: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 114, "protein_g": 5.9, "carbs_g": 14.5, "fat_g": 3.7, "fiber_g": 3.4, "iron_mg": 1.9, "calcium_mg": 42, "folate_ug": 58, "vit_a_ug": 45, "vit_c_mg": 12, "sodium_mg": 260},
        "aliases": ["dosakaya pappu", "yellow cucumber dal"]
    },
    18: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 108, "protein_g": 5.6, "carbs_g": 13.8, "fat_g": 3.5, "fiber_g": 3.3, "iron_mg": 1.8, "calcium_mg": 38, "folate_ug": 54, "vit_a_ug": 35, "vit_c_mg": 10, "sodium_mg": 240},
        "aliases": ["sorakaya pappu", "anapakaya pappu", "bottle gourd dal", "lauki dal"]
    },
    19: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 120, "protein_g": 6.0, "carbs_g": 15.6, "fat_g": 3.8, "fiber_g": 3.5, "iron_mg": 2.0, "calcium_mg": 40, "folate_ug": 60, "vit_a_ug": 65, "vit_c_mg": 24, "sodium_mg": 270},
        "aliases": ["mamidikaya pappu", "raw mango dal", "mango pappu"]
    },
    20: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 110, "protein_g": 5.7, "carbs_g": 14.0, "fat_g": 3.6, "fiber_g": 3.4, "iron_mg": 1.8, "calcium_mg": 36, "folate_ug": 56, "vit_a_ug": 48, "vit_c_mg": 11, "sodium_mg": 245},
        "aliases": ["beerakaya pappu", "ridge gourd dal"]
    },
    21: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 116, "protein_g": 6.1, "carbs_g": 14.8, "fat_g": 3.7, "fiber_g": 3.8, "iron_mg": 2.1, "calcium_mg": 52, "folate_ug": 62, "vit_a_ug": 58, "vit_c_mg": 35, "sodium_mg": 255},
        "aliases": ["munakkaya pappu", "drumstick dal"]
    },
    22: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 134, "protein_g": 7.8, "carbs_g": 18.5, "fat_g": 3.2, "fiber_g": 4.2, "iron_mg": 2.2, "calcium_mg": 34, "folate_ug": 68, "vit_a_ug": 42, "vit_c_mg": 2, "sodium_mg": 210},
        "aliases": ["mudda pappu", "kandipappu", "plain toor dal", "pappu"]
    },
    23: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 124, "protein_g": 7.6, "carbs_g": 17.2, "fat_g": 2.9, "fiber_g": 3.8, "iron_mg": 2.1, "calcium_mg": 32, "folate_ug": 72, "vit_a_ug": 38, "vit_c_mg": 4, "sodium_mg": 220},
        "aliases": ["pesara pappu", "moong dal", "ulli pesara pappu"]
    },
    24: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 142, "protein_g": 7.9, "carbs_g": 18.8, "fat_g": 4.1, "fiber_g": 4.8, "iron_mg": 2.5, "calcium_mg": 40, "folate_ug": 78, "vit_a_ug": 40, "vit_c_mg": 5, "sodium_mg": 250},
        "aliases": ["senaga pappu kura", "chana dal curry"]
    },

    # Vegetable Curries (25-47)
    25: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 148, "protein_g": 3.8, "carbs_g": 9.6, "fat_g": 10.8, "fiber_g": 4.2, "iron_mg": 1.6, "calcium_mg": 48, "folate_ug": 34, "vit_a_ug": 45, "vit_c_mg": 9, "sodium_mg": 310},
        "aliases": ["gutti vankaya", "vankaya kura", "stuffed brinjal curry", "bagara baingan", "vankaya vepudu"]
    },
    26: {
        "serving_unit": "1 katori (130g)", "serving_grams": 130, "gi_tier": "Low",
        "per_100g": {"calories": 112, "protein_g": 2.4, "carbs_g": 8.8, "fat_g": 7.6, "fiber_g": 3.9, "iron_mg": 1.2, "calcium_mg": 78, "folate_ug": 48, "vit_a_ug": 52, "vit_c_mg": 16, "sodium_mg": 270},
        "aliases": ["bendakaya vepudu", "bendakaya pulusu", "bhindi fry", "okra curry"]
    },
    27: {
        "serving_unit": "1 katori (140g)", "serving_grams": 140, "gi_tier": "High",
        "per_100g": {"calories": 136, "protein_g": 2.2, "carbs_g": 18.4, "fat_g": 6.0, "fiber_g": 2.4, "iron_mg": 0.9, "calcium_mg": 18, "folate_ug": 22, "vit_a_ug": 25, "vit_c_mg": 14, "sodium_mg": 280},
        "aliases": ["bangaladumpa vepudu", "aloo kura", "potato fry", "bangaladumpa kurma"]
    },
    28: {
        "serving_unit": "1 katori (130g)", "serving_grams": 130, "gi_tier": "Low",
        "per_100g": {"calories": 104, "protein_g": 2.1, "carbs_g": 7.2, "fat_g": 7.4, "fiber_g": 3.5, "iron_mg": 1.4, "calcium_mg": 46, "folate_ug": 32, "vit_a_ug": 48, "vit_c_mg": 18, "sodium_mg": 260},
        "aliases": ["dondakaya vepudu", "dondakaya kura", "tindora fry", "ivy gourd stir fry"]
    },
    29: {
        "serving_unit": "1 katori (140g)", "serving_grams": 140, "gi_tier": "Low",
        "per_100g": {"calories": 78, "protein_g": 1.8, "carbs_g": 6.4, "fat_g": 5.1, "fiber_g": 2.6, "iron_mg": 0.9, "calcium_mg": 32, "folate_ug": 28, "vit_a_ug": 42, "vit_c_mg": 10, "sodium_mg": 230},
        "aliases": ["beerakaya kura", "ridge gourd curry", "beerakaya палу పోసిన కూర"]
    },
    30: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 74, "protein_g": 1.6, "carbs_g": 6.8, "fat_g": 4.6, "fiber_g": 2.5, "iron_mg": 0.8, "calcium_mg": 30, "folate_ug": 24, "vit_a_ug": 30, "vit_c_mg": 9, "sodium_mg": 235},
        "aliases": ["sorakaya kura", "anapakaya pulusu", "bottle gourd stew", "sorakaya dappalam"]
    },
    31: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 118, "protein_g": 2.5, "carbs_g": 8.9, "fat_g": 8.1, "fiber_g": 4.1, "iron_mg": 1.9, "calcium_mg": 38, "folate_ug": 52, "vit_a_ug": 68, "vit_c_mg": 54, "sodium_mg": 285},
        "aliases": ["kakarakaya vepudu", "kakarakaya pulusu", "bitter gourd fry", "karela curry"]
    },
    32: {
        "serving_unit": "1 katori (130g)", "serving_grams": 130, "gi_tier": "Low",
        "per_100g": {"calories": 84, "protein_g": 2.1, "carbs_g": 7.0, "fat_g": 5.4, "fiber_g": 3.2, "iron_mg": 0.9, "calcium_mg": 45, "folate_ug": 42, "vit_a_ug": 35, "vit_c_mg": 32, "sodium_mg": 240},
        "aliases": ["cabbage vepudu", "cabbage kura", "cabbage senagapappu"]
    },
    33: {
        "serving_unit": "1 katori (140g)", "serving_grams": 140, "gi_tier": "Low",
        "per_100g": {"calories": 92, "protein_g": 2.4, "carbs_g": 7.6, "fat_g": 5.9, "fiber_g": 3.0, "iron_mg": 1.0, "calcium_mg": 34, "folate_ug": 48, "vit_a_ug": 28, "vit_c_mg": 38, "sodium_mg": 255},
        "aliases": ["cauliflower kura", "gobi vepudu", "cauliflower tomato curry"]
    },
    34: {
        "serving_unit": "1 katori (130g)", "serving_grams": 130, "gi_tier": "Low",
        "per_100g": {"calories": 88, "protein_g": 2.6, "carbs_g": 8.2, "fat_g": 5.1, "fiber_g": 3.8, "iron_mg": 1.4, "calcium_mg": 48, "folate_ug": 38, "vit_a_ug": 45, "vit_c_mg": 14, "sodium_mg": 240},
        "aliases": ["beans vepudu", "beans kura", "french beans stir fry"]
    },
    35: {
        "serving_unit": "1 katori (140g)", "serving_grams": 140, "gi_tier": "Low",
        "per_100g": {"calories": 106, "protein_g": 4.5, "carbs_g": 11.2, "fat_g": 4.9, "fiber_g": 4.8, "iron_mg": 1.8, "calcium_mg": 58, "folate_ug": 54, "vit_a_ug": 52, "vit_c_mg": 15, "sodium_mg": 250},
        "aliases": ["chikkudukaya kura", "chikkudukaya vepudu", "broad beans curry"]
    },
    36: {
        "serving_unit": "1 katori (130g)", "serving_grams": 130, "gi_tier": "Low",
        "per_100g": {"calories": 98, "protein_g": 3.4, "carbs_g": 9.8, "fat_g": 5.2, "fiber_g": 4.6, "iron_mg": 1.7, "calcium_mg": 110, "folate_ug": 46, "vit_a_ug": 48, "vit_c_mg": 18, "sodium_mg": 250},
        "aliases": ["goruchikkudu vepudu", "cluster beans curry", "gavar fry"]
    },
    37: {
        "serving_unit": "1 katori (140g)", "serving_grams": 140, "gi_tier": "Low",
        "per_100g": {"calories": 82, "protein_g": 2.5, "carbs_g": 6.8, "fat_g": 5.0, "fiber_g": 2.4, "iron_mg": 0.9, "calcium_mg": 55, "folate_ug": 26, "vit_a_ug": 32, "vit_c_mg": 10, "sodium_mg": 235},
        "aliases": ["potlakaya perugu pachadi", "potlakaya kura", "snake gourd curry"]
    },
    38: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 76, "protein_g": 1.5, "carbs_g": 7.4, "fat_g": 4.6, "fiber_g": 2.2, "iron_mg": 0.8, "calcium_mg": 28, "folate_ug": 24, "vit_a_ug": 28, "vit_c_mg": 14, "sodium_mg": 255},
        "aliases": ["dosakaya kura", "dosakaya mukkala pulusu", "yellow cucumber curry", "dosakaya pulusu", "yellow cucumber pulusu"]
    },
    39: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 90, "protein_g": 2.6, "carbs_g": 8.8, "fat_g": 5.2, "fiber_g": 3.9, "iron_mg": 1.4, "calcium_mg": 56, "folate_ug": 42, "vit_a_ug": 54, "vit_c_mg": 62, "sodium_mg": 270},
        "aliases": ["munakkaya pulusu", "munakkaya kura", "drumstick curry", "mulakkada tomato"]
    },
    40: {
        "serving_unit": "1 katori (130g)", "serving_grams": 130, "gi_tier": "Medium",
        "per_100g": {"calories": 96, "protein_g": 2.1, "carbs_g": 11.4, "fat_g": 4.8, "fiber_g": 3.4, "iron_mg": 1.2, "calcium_mg": 24, "folate_ug": 86, "vit_a_ug": 18, "vit_c_mg": 10, "sodium_mg": 250},
        "aliases": ["beetroot vepudu", "beetroot kura", "beetroot poriyal"]
    },
    41: {
        "serving_unit": "1 katori (130g)", "serving_grams": 130, "gi_tier": "Medium",
        "per_100g": {"calories": 132, "protein_g": 1.9, "carbs_g": 19.2, "fat_g": 5.4, "fiber_g": 3.6, "iron_mg": 0.9, "calcium_mg": 22, "folate_ug": 26, "vit_a_ug": 32, "vit_c_mg": 15, "sodium_mg": 250},
        "aliases": ["aratikaya vepudu", "aratikaya kura", "raw banana fry", "plantain stir fry"]
    },
    42: {
        "serving_unit": "1 katori (140g)", "serving_grams": 140, "gi_tier": "Medium",
        "per_100g": {"calories": 138, "protein_g": 2.6, "carbs_g": 19.6, "fat_g": 5.6, "fiber_g": 3.8, "iron_mg": 1.1, "calcium_mg": 38, "folate_ug": 30, "vit_a_ug": 24, "vit_c_mg": 12, "sodium_mg": 275},
        "aliases": ["chamadumpa pulusu", "chamadumpa vepudu", "arbi fry", "colocasia curry", "chamadumpa kura", "taro root curry", "taro pulusu", "taro root", "colocasia"]
    },
    43: {
        "serving_unit": "1 katori (140g)", "serving_grams": 140, "gi_tier": "Medium",
        "per_100g": {"calories": 128, "protein_g": 2.2, "carbs_g": 18.0, "fat_g": 5.2, "fiber_g": 3.7, "iron_mg": 1.2, "calcium_mg": 48, "folate_ug": 28, "vit_a_ug": 65, "vit_c_mg": 11, "sodium_mg": 265},
        "aliases": ["kanda kura", "kanda bachali", "suran curry", "elephant foot yam"]
    },
    44: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 68, "protein_g": 2.8, "carbs_g": 5.6, "fat_g": 3.8, "fiber_g": 1.2, "iron_mg": 0.6, "calcium_mg": 95, "folate_ug": 18, "vit_a_ug": 36, "vit_c_mg": 8, "sodium_mg": 230},
        "aliases": ["majjiga pulusu", "majjiga charu", "challacharu", "buttermilk stew"]
    },
    45: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 152, "protein_g": 14.8, "carbs_g": 10.6, "fat_g": 5.8, "fiber_g": 4.5, "iron_mg": 3.8, "calcium_mg": 92, "folate_ug": 65, "vit_a_ug": 42, "vit_c_mg": 12, "sodium_mg": 290},
        "aliases": ["meal maker kura", "soya chunks curry", "soya curry"]
    },
    46: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 158, "protein_g": 7.8, "carbs_g": 19.4, "fat_g": 5.6, "fiber_g": 5.8, "iron_mg": 2.7, "calcium_mg": 54, "folate_ug": 88, "vit_a_ug": 46, "vit_c_mg": 14, "sodium_mg": 310},
        "aliases": ["senagala kura", "chole masala", "chickpea curry", "kabuli chana curry"]
    },
    47: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 146, "protein_g": 8.1, "carbs_g": 18.8, "fat_g": 4.4, "fiber_g": 5.2, "iron_mg": 2.9, "calcium_mg": 48, "folate_ug": 94, "vit_a_ug": 40, "vit_c_mg": 10, "sodium_mg": 280},
        "aliases": ["bobbarlu kura", "alasandalu kura", "cowpea curry", "lobia curry"]
    },

    # Chutneys & Podis (48-57)
    48: {
        "serving_unit": "2 tbsp (40g)", "serving_grams": 40, "gi_tier": "Low",
        "per_100g": {"calories": 248, "protein_g": 9.8, "carbs_g": 9.4, "fat_g": 19.6, "fiber_g": 3.8, "iron_mg": 1.8, "calcium_mg": 42, "folate_ug": 52, "vit_a_ug": 22, "vit_c_mg": 6, "sodium_mg": 340},
        "aliases": ["palli pachadi", "groundnut chutney", "peanut chutney", "verusenaga pachadi"]
    },
    49: {
        "serving_unit": "2 tbsp (40g)", "serving_grams": 40, "gi_tier": "Low",
        "per_100g": {"calories": 232, "protein_g": 3.4, "carbs_g": 8.6, "fat_g": 20.8, "fiber_g": 4.4, "iron_mg": 1.4, "calcium_mg": 24, "folate_ug": 22, "vit_a_ug": 15, "vit_c_mg": 5, "sodium_mg": 320},
        "aliases": ["kobbari pachadi", "coconut chutney"]
    },
    50: {
        "serving_unit": "1.5 tbsp (30g)", "serving_grams": 30, "gi_tier": "Medium",
        "per_100g": {"calories": 178, "protein_g": 2.2, "carbs_g": 28.5, "fat_g": 6.4, "fiber_g": 2.8, "iron_mg": 2.1, "calcium_mg": 38, "folate_ug": 16, "vit_a_ug": 45, "vit_c_mg": 8, "sodium_mg": 410},
        "aliases": ["allam pachadi", "ginger chutney", "pesarattu allam pachadi"]
    },
    51: {
        "serving_unit": "2 tbsp (40g)", "serving_grams": 40, "gi_tier": "Low",
        "per_100g": {"calories": 115, "protein_g": 2.4, "carbs_g": 9.2, "fat_g": 7.8, "fiber_g": 2.6, "iron_mg": 1.2, "calcium_mg": 28, "folate_ug": 24, "vit_a_ug": 85, "vit_c_mg": 22, "sodium_mg": 380},
        "aliases": ["tomato pachadi", "roti pachadi", "tamata pachadi"]
    },
    52: {
        "serving_unit": "2 tbsp (40g)", "serving_grams": 40, "gi_tier": "Low",
        "per_100g": {"calories": 154, "protein_g": 3.1, "carbs_g": 10.4, "fat_g": 11.4, "fiber_g": 4.2, "iron_mg": 5.8, "calcium_mg": 148, "folate_ug": 58, "vit_a_ug": 240, "vit_c_mg": 36, "sodium_mg": 440},
        "aliases": ["gongura pachadi", "gongura nilava pachadi", "sorrel chutney"]
    },
    53: {
        "serving_unit": "2 tbsp (40g)", "serving_grams": 40, "gi_tier": "Low",
        "per_100g": {"calories": 122, "protein_g": 3.2, "carbs_g": 8.4, "fat_g": 8.6, "fiber_g": 2.8, "iron_mg": 1.3, "calcium_mg": 34, "folate_ug": 26, "vit_a_ug": 38, "vit_c_mg": 14, "sodium_mg": 350},
        "aliases": ["dosakaya pachadi", "dosakaya mukkala pachadi"]
    },
    54: {
        "serving_unit": "1.5 tbsp (20g)", "serving_grams": 20, "gi_tier": "Low",
        "per_100g": {"calories": 368, "protein_g": 21.4, "carbs_g": 52.0, "fat_g": 8.2, "fiber_g": 9.6, "iron_mg": 4.8, "calcium_mg": 86, "folate_ug": 115, "vit_a_ug": 65, "vit_c_mg": 4, "sodium_mg": 520},
        "aliases": ["kandi podi", "paruppu podi", "dal powder"]
    },
    55: {
        "serving_unit": "1.5 tbsp (20g)", "serving_grams": 20, "gi_tier": "Low",
        "per_100g": {"calories": 342, "protein_g": 16.8, "carbs_g": 44.5, "fat_g": 10.6, "fiber_g": 12.4, "iron_mg": 8.6, "calcium_mg": 420, "folate_ug": 92, "vit_a_ug": 480, "vit_c_mg": 12, "sodium_mg": 490},
        "aliases": ["karivepaku podi", "karivepaku pachadi", "curry leaves powder"]
    },
    56: {
        "serving_unit": "1.5 tbsp (20g)", "serving_grams": 20, "gi_tier": "Low",
        "per_100g": {"calories": 518, "protein_g": 19.2, "carbs_g": 24.6, "fat_g": 39.8, "fiber_g": 10.8, "iron_mg": 9.4, "calcium_mg": 780, "folate_ug": 84, "vit_a_ug": 32, "vit_c_mg": 2, "sodium_mg": 450},
        "aliases": ["nuvvula podi", "nuvvula pachadi", "sesame powder", "til podi"]
    },
    57: {
        "serving_unit": "1.5 tbsp (20g)", "serving_grams": 20, "gi_tier": "Low",
        "per_100g": {"calories": 336, "protein_g": 22.5, "carbs_g": 42.0, "fat_g": 8.8, "fiber_g": 13.2, "iron_mg": 11.2, "calcium_mg": 610, "folate_ug": 130, "vit_a_ug": 690, "vit_c_mg": 28, "sodium_mg": 470},
        "aliases": ["munagaku podi", "moringa leaf powder", "drumstick leaf podi"]
    },

    # Eggs, Meat & Fish (58-74)
    58: {
        "serving_unit": "1 boiled egg (50g)", "serving_grams": 50, "gi_tier": "Low",
        "per_100g": {"calories": 155, "protein_g": 12.6, "carbs_g": 1.1, "fat_g": 10.6, "fiber_g": 0.0, "iron_mg": 1.8, "calcium_mg": 50, "folate_ug": 44, "vit_a_ug": 140, "vit_c_mg": 0, "sodium_mg": 124},
        "aliases": ["udakabettina guddu", "boiled egg", "guddu"]
    },
    59: {
        "serving_unit": "1 double/single omelette (75g)", "serving_grams": 75, "gi_tier": "Low",
        "per_100g": {"calories": 188, "protein_g": 11.4, "carbs_g": 3.2, "fat_g": 14.5, "fiber_g": 0.6, "iron_mg": 1.7, "calcium_mg": 48, "folate_ug": 40, "vit_a_ug": 135, "vit_c_mg": 4, "sodium_mg": 290},
        "aliases": ["egg omelette", "omlet", "ulli omelette"]
    },
    60: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 176, "protein_g": 10.8, "carbs_g": 5.4, "fat_g": 12.4, "fiber_g": 1.2, "iron_mg": 1.8, "calcium_mg": 52, "folate_ug": 38, "vit_a_ug": 125, "vit_c_mg": 8, "sodium_mg": 310},
        "aliases": ["guddu porutu", "egg bhurji", "guddu ulli kura", "egg scramble", "scrambled egg", "guddu vepudu", "egg fry", "spicy scrambled egg"]
    },
    61: {
        "serving_unit": "1 katori with 2 eggs (180g)", "serving_grams": 180, "gi_tier": "Low",
        "per_100g": {"calories": 144, "protein_g": 8.4, "carbs_g": 6.8, "fat_g": 9.4, "fiber_g": 1.5, "iron_mg": 1.6, "calcium_mg": 46, "folate_ug": 34, "vit_a_ug": 110, "vit_c_mg": 10, "sodium_mg": 300},
        "aliases": ["guddu pulusu", "egg pulusu", "egg curry", "kodiguddu pulusu"]
    },
    62: {
        "serving_unit": "1 katori (160g)", "serving_grams": 160, "gi_tier": "Low",
        "per_100g": {"calories": 172, "protein_g": 16.8, "carbs_g": 4.8, "fat_g": 9.6, "fiber_g": 1.1, "iron_mg": 1.4, "calcium_mg": 28, "folate_ug": 18, "vit_a_ug": 42, "vit_c_mg": 6, "sodium_mg": 340},
        "aliases": ["kodi kura", "andhra chicken curry", "chicken curry"]
    },
    63: {
        "serving_unit": "1 katori (140g)", "serving_grams": 140, "gi_tier": "Low",
        "per_100g": {"calories": 218, "protein_g": 21.4, "carbs_g": 4.2, "fat_g": 12.8, "fiber_g": 1.2, "iron_mg": 1.6, "calcium_mg": 30, "folate_ug": 16, "vit_a_ug": 38, "vit_c_mg": 5, "sodium_mg": 380},
        "aliases": ["kodi vepudu", "chicken fry", "andhra kodi vepudu"]
    },
    64: {
        "serving_unit": "1 katori (170g)", "serving_grams": 170, "gi_tier": "Low",
        "per_100g": {"calories": 164, "protein_g": 18.2, "carbs_g": 4.4, "fat_g": 8.2, "fiber_g": 1.0, "iron_mg": 1.9, "calcium_mg": 34, "folate_ug": 20, "vit_a_ug": 46, "vit_c_mg": 6, "sodium_mg": 350},
        "aliases": ["natukodi pulusu", "natukodi kura", "country chicken curry"]
    },
    65: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 186, "protein_g": 20.6, "carbs_g": 3.8, "fat_g": 9.8, "fiber_g": 0.8, "iron_mg": 9.2, "calcium_mg": 22, "folate_ug": 420, "vit_a_ug": 2800, "vit_c_mg": 14, "sodium_mg": 330},
        "aliases": ["chicken liver fry", "kodi liver vepudu"]
    },
    66: {
        "serving_unit": "1 katori (160g)", "serving_grams": 160, "gi_tier": "Low",
        "per_100g": {"calories": 178, "protein_g": 16.4, "carbs_g": 5.6, "fat_g": 10.2, "fiber_g": 2.2, "iron_mg": 3.4, "calcium_mg": 72, "folate_ug": 42, "vit_a_ug": 145, "vit_c_mg": 18, "sodium_mg": 360},
        "aliases": ["gongura chicken", "gongura kodi kura"]
    },
    67: {
        "serving_unit": "1 katori (160g)", "serving_grams": 160, "gi_tier": "Low",
        "per_100g": {"calories": 208, "protein_g": 17.6, "carbs_g": 4.6, "fat_g": 13.4, "fiber_g": 1.0, "iron_mg": 2.8, "calcium_mg": 26, "folate_ug": 14, "vit_a_ug": 32, "vit_c_mg": 5, "sodium_mg": 360},
        "aliases": ["mutton curry", "veta mamsam kura", "meka mamsam kura", "mutton pulusu"]
    },
    68: {
        "serving_unit": "1 katori (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 216, "protein_g": 18.4, "carbs_g": 5.2, "fat_g": 13.6, "fiber_g": 1.2, "iron_mg": 3.0, "calcium_mg": 28, "folate_ug": 16, "vit_a_ug": 36, "vit_c_mg": 6, "sodium_mg": 370},
        "aliases": ["mutton kheema", "keema kura", "minced mutton curry"]
    },
    69: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 198, "protein_g": 21.2, "carbs_g": 4.0, "fat_g": 10.8, "fiber_g": 0.8, "iron_mg": 10.4, "calcium_mg": 24, "folate_ug": 380, "vit_a_ug": 3200, "vit_c_mg": 16, "sodium_mg": 340},
        "aliases": ["mutton liver fry", "kaleji vepudu", "mutton kaleji"]
    },
    70: {
        "serving_unit": "1 katori (160g)", "serving_grams": 160, "gi_tier": "Low",
        "per_100g": {"calories": 204, "protein_g": 16.8, "carbs_g": 5.8, "fat_g": 12.8, "fiber_g": 2.4, "iron_mg": 4.6, "calcium_mg": 78, "folate_ug": 44, "vit_a_ug": 155, "vit_c_mg": 18, "sodium_mg": 375},
        "aliases": ["gongura mutton", "gongura mamsam", "mutton gongura", "mamsam gongura kura", "mutton curry with gongura", "mutton palakura", "palakura mutton", "mutton in sorrel gravy"]
    },
    71: {
        "serving_unit": "1 katori (170g)", "serving_grams": 170, "gi_tier": "Low",
        "per_100g": {"calories": 146, "protein_g": 15.8, "carbs_g": 5.2, "fat_g": 7.0, "fiber_g": 1.2, "iron_mg": 1.4, "calcium_mg": 115, "folate_ug": 22, "vit_a_ug": 55, "vit_c_mg": 8, "sodium_mg": 360},
        "aliases": ["chepala pulusu", "nellore chepala pulusu", "fish curry", "fish tamarind curry"]
    },
    72: {
        "serving_unit": "2 pieces (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 206, "protein_g": 20.4, "carbs_g": 3.8, "fat_g": 12.2, "fiber_g": 0.6, "iron_mg": 1.5, "calcium_mg": 98, "folate_ug": 18, "vit_a_ug": 48, "vit_c_mg": 4, "sodium_mg": 370},
        "aliases": ["chepala vepudu", "fish fry", "apollo fish"]
    },
    73: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 192, "protein_g": 24.8, "carbs_g": 6.4, "fat_g": 7.6, "fiber_g": 1.4, "iron_mg": 3.8, "calcium_mg": 420, "folate_ug": 24, "vit_a_ug": 42, "vit_c_mg": 6, "sodium_mg": 680},
        "aliases": ["endu chepalu kura", "dry fish curry", "bommidala pulusu"]
    },
    74: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 184, "protein_g": 23.6, "carbs_g": 6.2, "fat_g": 7.2, "fiber_g": 1.3, "iron_mg": 4.1, "calcium_mg": 380, "folate_ug": 26, "vit_a_ug": 45, "vit_c_mg": 8, "sodium_mg": 640},
        "aliases": ["endu royyalu kura", "dry prawns curry", "royyala iguru"]
    },

    # Tiffins & Breads (75-81)
    75: {
        "serving_unit": "2 rotis (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 236, "protein_g": 7.2, "carbs_g": 46.8, "fat_g": 2.4, "fiber_g": 6.8, "iron_mg": 2.9, "calcium_mg": 24, "folate_ug": 28, "vit_a_ug": 12, "vit_c_mg": 0, "sodium_mg": 160},
        "aliases": ["jonna rotti", "jowar roti", "jowar bhakri"]
    },
    76: {
        "serving_unit": "2 rotis (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 242, "protein_g": 6.4, "carbs_g": 45.2, "fat_g": 3.8, "fiber_g": 7.6, "iron_mg": 3.4, "calcium_mg": 265, "folate_ug": 32, "vit_a_ug": 28, "vit_c_mg": 4, "sodium_mg": 190},
        "aliases": ["ragi rotti", "finger millet flatbread", "choddo rotti"]
    },
    77: {
        "serving_unit": "3 idlis (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 144, "protein_g": 5.2, "carbs_g": 27.6, "fat_g": 1.4, "fiber_g": 4.2, "iron_mg": 2.4, "calcium_mg": 168, "folate_ug": 36, "vit_a_ug": 14, "vit_c_mg": 1, "sodium_mg": 210},
        "aliases": ["ragi idli", "finger millet idli"]
    },
    78: {
        "serving_unit": "2 dosas (140g)", "serving_grams": 140, "gi_tier": "Low",
        "per_100g": {"calories": 182, "protein_g": 5.8, "carbs_g": 31.4, "fat_g": 3.8, "fiber_g": 4.6, "iron_mg": 2.8, "calcium_mg": 185, "folate_ug": 34, "vit_a_ug": 16, "vit_c_mg": 2, "sodium_mg": 240},
        "aliases": ["ragi dosa", "finger millet dosa"]
    },
    79: {
        "serving_unit": "1 bowl (160g)", "serving_grams": 160, "gi_tier": "Medium",
        "per_100g": {"calories": 156, "protein_g": 4.2, "carbs_g": 24.8, "fat_g": 4.6, "fiber_g": 2.2, "iron_mg": 1.2, "calcium_mg": 26, "folate_ug": 24, "vit_a_ug": 48, "vit_c_mg": 6, "sodium_mg": 280},
        "aliases": ["semiya upma", "vermicelli upma"]
    },
    80: {
        "serving_unit": "1 bowl (160g)", "serving_grams": 160, "gi_tier": "Low",
        "per_100g": {"calories": 142, "protein_g": 4.8, "carbs_g": 22.6, "fat_g": 3.8, "fiber_g": 4.8, "iron_mg": 1.9, "calcium_mg": 28, "folate_ug": 32, "vit_a_ug": 45, "vit_c_mg": 6, "sodium_mg": 260},
        "aliases": ["godhuma rava upma", "broken wheat upma", "dalia upma", "erra rava upma"]
    },
    81: {
        "serving_unit": "2 slices + 150ml milk (210g)", "serving_grams": 210, "gi_tier": "Medium",
        "per_100g": {"calories": 134, "protein_g": 5.1, "carbs_g": 18.6, "fat_g": 4.2, "fiber_g": 1.2, "iron_mg": 0.8, "calcium_mg": 105, "folate_ug": 22, "vit_a_ug": 46, "vit_c_mg": 1, "sodium_mg": 180},
        "aliases": ["bread and milk", "bread toast", "paalu bread"]
    },

    # Rice & Millet Dishes (82)
    82: {
        "serving_unit": "1 plate/bowl (200g)", "serving_grams": 200, "gi_tier": "Low",
        "per_100g": {"calories": 128, "protein_g": 4.3, "carbs_g": 23.4, "fat_g": 1.6, "fiber_g": 3.4, "iron_mg": 1.4, "calcium_mg": 16, "folate_ug": 18, "vit_a_ug": 8, "vit_c_mg": 0, "sodium_mg": 20},
        "aliases": ["korra annam", "foxtail millet rice", "korralu rice"]
    },

    # Fruits & Nuts (83-86)
    83: {
        "serving_unit": "1 bowl (150g)", "serving_grams": 150, "gi_tier": "Low",
        "per_100g": {"calories": 34, "protein_g": 0.8, "carbs_g": 8.2, "fat_g": 0.2, "fiber_g": 0.9, "iron_mg": 0.3, "calcium_mg": 9, "folate_ug": 21, "vit_a_ug": 169, "vit_c_mg": 36, "sodium_mg": 16},
        "aliases": ["kharbuja", "muskmelon", "cantaloupe"]
    },
    84: {
        "serving_unit": "1 bowl (150g)", "serving_grams": 150, "gi_tier": "Medium",
        "per_100g": {"calories": 30, "protein_g": 0.6, "carbs_g": 7.6, "fat_g": 0.2, "fiber_g": 0.4, "iron_mg": 0.2, "calcium_mg": 7, "folate_ug": 3, "vit_a_ug": 28, "vit_c_mg": 8, "sodium_mg": 1},
        "aliases": ["puchakaya", "watermelon"]
    },
    85: {
        "serving_unit": "1 handful (30g)", "serving_grams": 30, "gi_tier": "Medium",
        "per_100g": {"calories": 299, "protein_g": 3.1, "carbs_g": 79.2, "fat_g": 0.5, "fiber_g": 3.7, "iron_mg": 1.9, "calcium_mg": 50, "folate_ug": 5, "vit_a_ug": 0, "vit_c_mg": 2, "sodium_mg": 11},
        "aliases": ["endu draksha", "kismis", "raisins"]
    },
    86: {
        "serving_unit": "1 tender coconut (250ml)", "serving_grams": 250, "gi_tier": "Low",
        "per_100g": {"calories": 19, "protein_g": 0.7, "carbs_g": 3.7, "fat_g": 0.2, "fiber_g": 1.1, "iron_mg": 0.3, "calcium_mg": 24, "folate_ug": 3, "vit_a_ug": 0, "vit_c_mg": 2.4, "sodium_mg": 105},
        "aliases": ["kobbari bondam", "kobbari neellu", "coconut water", "tender coconut"]
    },

    # Snacks & Sweets (87-93)
    87: {
        "serving_unit": "1 katori porridge/laddu (100g)", "serving_grams": 100, "gi_tier": "Low",
        "per_100g": {"calories": 412, "protein_g": 11.4, "carbs_g": 64.0, "fat_g": 12.2, "fiber_g": 4.6, "iron_mg": 9.0, "calcium_mg": 380, "folate_ug": 110, "vit_a_ug": 350, "vit_c_mg": 25, "sodium_mg": 140},
        "aliases": ["balamrutham", "anganwadi thr", "balamrutham laddu", "balamrutham porridge"]
    },
    88: {
        "serving_unit": "2 pieces (40g)", "serving_grams": 40, "gi_tier": "Medium",
        "per_100g": {"calories": 488, "protein_g": 14.6, "carbs_g": 46.2, "fat_g": 27.4, "fiber_g": 4.8, "iron_mg": 4.2, "calcium_mg": 68, "folate_ug": 62, "vit_a_ug": 4, "vit_c_mg": 0, "sodium_mg": 35},
        "aliases": ["palli chikki", "palli patti", "verusenaga chikki", "peanut jaggery brittle"]
    },
    89: {
        "serving_unit": "1 laddu (45g)", "serving_grams": 45, "gi_tier": "Low",
        "per_100g": {"calories": 418, "protein_g": 7.8, "carbs_g": 54.6, "fat_g": 18.8, "fiber_g": 6.4, "iron_mg": 3.9, "calcium_mg": 245, "folate_ug": 32, "vit_a_ug": 42, "vit_c_mg": 0, "sodium_mg": 25},
        "aliases": ["ragi laddu", "chodi laddu", "finger millet laddu"]
    },
    90: {
        "serving_unit": "1 laddu (40g)", "serving_grams": 40, "gi_tier": "Low",
        "per_100g": {"calories": 465, "protein_g": 11.2, "carbs_g": 44.8, "fat_g": 26.8, "fiber_g": 6.8, "iron_mg": 3.8, "calcium_mg": 120, "folate_ug": 48, "vit_a_ug": 18, "vit_c_mg": 2, "sodium_mg": 22},
        "aliases": ["dry fruit laddu", "dates nut laddu"]
    },
    91: {
        "serving_unit": "1 katori (120g)", "serving_grams": 120, "gi_tier": "Low",
        "per_100g": {"calories": 152, "protein_g": 8.8, "carbs_g": 23.6, "fat_g": 2.4, "fiber_g": 6.8, "iron_mg": 2.6, "calcium_mg": 52, "folate_ug": 96, "vit_a_ug": 24, "vit_c_mg": 6, "sodium_mg": 210},
        "aliases": ["guggillu", "senaga guggillu", "pesalu guggillu", "bobbarlu guggillu", "sundal"]
    },
    92: {
        "serving_unit": "1 cob / bowl (125g)", "serving_grams": 125, "gi_tier": "Medium",
        "per_100g": {"calories": 96, "protein_g": 3.4, "carbs_g": 21.0, "fat_g": 1.5, "fiber_g": 2.7, "iron_mg": 0.5, "calcium_mg": 4, "folate_ug": 46, "vit_a_ug": 18, "vit_c_mg": 6, "sodium_mg": 15},
        "aliases": ["mokkajonna kanki", "boiled sweet corn", "corn on the cob"]
    },
    93: {
        "serving_unit": "1 medium (130g)", "serving_grams": 130, "gi_tier": "Low",
        "per_100g": {"calories": 86, "protein_g": 1.6, "carbs_g": 20.1, "fat_g": 0.1, "fiber_g": 3.0, "iron_mg": 0.7, "calcium_mg": 30, "folate_ug": 11, "vit_a_ug": 709, "vit_c_mg": 19, "sodium_mg": 36},
        "aliases": ["chilakadumpa", "boiled sweet potato", "genusu gadda"]
    },
}


# Foundational Telugu Staples (Rice, Tiffins, Biryanis, Classics, Sweets, Accompaniments)
# IDs 101+ so they seamlessly join the 1-93 SuperAdmin catalog
FOUNDATIONAL_TELUGU_STAPLES: List[Dict[str, Any]] = [
    {
        "id": "JM-101", "sort_order": 101,
        "name_en": "Steamed White Rice (Vandi Annam)",
        "name_te": "వండిన తెల్ల అన్నం",
        "cluster": "Rice & Millet Dishes", "emoji": "🍚", "meal_tabs": "Meals",
        "food_groups": ["G1"], "food_groups_raw": "G1 Grains, roots & tubers",
        "vegetarian": True, "contains_egg": False, "gi_tier": "High",
        "serving_unit": "1 plate / 2 cups (200g)", "serving_grams": 200,
        "per_100g": {"calories": 130, "protein_g": 2.7, "carbs_g": 28.2, "fat_g": 0.3, "fiber_g": 0.4, "iron_mg": 0.4, "calcium_mg": 10, "folate_ug": 8, "vit_a_ug": 0, "vit_c_mg": 0, "sodium_mg": 5},
        "aliases": ["annam", "white rice", "steamed rice", "sona masoori rice"]
    },
    {
        "id": "JM-102", "sort_order": 102,
        "name_en": "Ragi Sangati / Ragi Mudda (Finger Millet Ball)",
        "name_te": "రాగి సంగటి / రాగి ముద్ద",
        "cluster": "Rice & Millet Dishes", "emoji": "🍘", "meal_tabs": "Meals",
        "food_groups": ["G1"], "food_groups_raw": "G1 Grains, roots & tubers",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 ball (200g)", "serving_grams": 200,
        "per_100g": {"calories": 138, "protein_g": 3.6, "carbs_g": 28.4, "fat_g": 1.2, "fiber_g": 4.2, "iron_mg": 2.1, "calcium_mg": 162, "folate_ug": 16, "vit_a_ug": 6, "vit_c_mg": 0, "sodium_mg": 45},
        "aliases": ["ragi sangati", "ragi mudda", "rayalaseema ragi sangati"]
    },
    {
        "id": "JM-103", "sort_order": 103,
        "name_en": "Pulihora / Chintapandu Pulihora (Tamarind Rice)",
        "name_te": "చింతపండు పులిహోర",
        "cluster": "Rice & Millet Dishes", "emoji": "🍋", "meal_tabs": "Breakfast, Meals",
        "food_groups": ["G1", "G3"], "food_groups_raw": "G1 Grains, roots & tubers, G3 Nuts and seeds",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 plate (200g)", "serving_grams": 200,
        "per_100g": {"calories": 178, "protein_g": 4.1, "carbs_g": 27.6, "fat_g": 5.8, "fiber_g": 2.1, "iron_mg": 1.3, "calcium_mg": 24, "folate_ug": 18, "vit_a_ug": 16, "vit_c_mg": 4, "sodium_mg": 310},
        "aliases": ["pulihora", "tamarind rice", "nimmakaya pulihora", "lemon rice"]
    },
    {
        "id": "JM-104", "sort_order": 104,
        "name_en": "Perugu Annam / Daddojanam (Curd Rice)",
        "name_te": "పెరుగు అన్నం / దద్దోజనం",
        "cluster": "Rice & Millet Dishes", "emoji": "🥣", "meal_tabs": "Meals",
        "food_groups": ["G1", "G4"], "food_groups_raw": "G1 Grains, roots & tubers, G4 Dairy",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 bowl (200g)", "serving_grams": 200,
        "per_100g": {"calories": 116, "protein_g": 3.5, "carbs_g": 18.4, "fat_g": 3.1, "fiber_g": 0.5, "iron_mg": 0.4, "calcium_mg": 86, "folate_ug": 12, "vit_a_ug": 22, "vit_c_mg": 1, "sodium_mg": 180},
        "aliases": ["perugu annam", "daddojanam", "curd rice", "bagala bath"]
    },
    {
        "id": "JM-105", "sort_order": 105,
        "name_en": "Pesarattu (Green Moong Dal Dosa)",
        "name_te": "పెసరట్టు",
        "cluster": "Tiffins & Breads", "emoji": "🥞", "meal_tabs": "Breakfast",
        "food_groups": ["G2"], "food_groups_raw": "G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "2 pesarattu (150g)", "serving_grams": 150,
        "per_100g": {"calories": 186, "protein_g": 9.4, "carbs_g": 24.8, "fat_g": 5.4, "fiber_g": 5.2, "iron_mg": 2.4, "calcium_mg": 48, "folate_ug": 84, "vit_a_ug": 32, "vit_c_mg": 6, "sodium_mg": 240},
        "aliases": ["pesarattu", "ulli pesarattu", "green gram dosa", "moong dal dosa"]
    },
    {
        "id": "JM-106", "sort_order": 106,
        "name_en": "MLA Pesarattu / Upma Pesarattu",
        "name_te": "ఉప్మా పెసరట్టు (MLA పెసరట్టు)",
        "cluster": "Tiffins & Breads", "emoji": "🥞", "meal_tabs": "Breakfast",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 stuffed pesarattu (180g)", "serving_grams": 180,
        "per_100g": {"calories": 176, "protein_g": 7.4, "carbs_g": 25.2, "fat_g": 5.2, "fiber_g": 3.8, "iron_mg": 1.9, "calcium_mg": 38, "folate_ug": 62, "vit_a_ug": 28, "vit_c_mg": 5, "sodium_mg": 265},
        "aliases": ["mla pesarattu", "upma pesarattu"]
    },
    {
        "id": "JM-107", "sort_order": 107,
        "name_en": "Idli (Steamed Rice & Urad Dal Cakes)",
        "name_te": "ఇడ్లీ",
        "cluster": "Tiffins & Breads", "emoji": "⚪", "meal_tabs": "Breakfast",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "3 idlis (150g)", "serving_grams": 150,
        "per_100g": {"calories": 146, "protein_g": 4.6, "carbs_g": 29.8, "fat_g": 0.8, "fiber_g": 1.8, "iron_mg": 1.1, "calcium_mg": 24, "folate_ug": 28, "vit_a_ug": 4, "vit_c_mg": 0, "sodium_mg": 195},
        "aliases": ["idli", "guntur idli", "neyyi karam idli", "steamed idli"]
    },
    {
        "id": "JM-108", "sort_order": 108,
        "name_en": "Plain / Karam Dosa (Fermented Rice-Lentil Crepe)",
        "name_te": "దోస / కారం దోస",
        "cluster": "Tiffins & Breads", "emoji": "🥞", "meal_tabs": "Breakfast",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "2 dosas (140g)", "serving_grams": 140,
        "per_100g": {"calories": 196, "protein_g": 5.2, "carbs_g": 31.8, "fat_g": 5.4, "fiber_g": 2.0, "iron_mg": 1.4, "calcium_mg": 28, "folate_ug": 30, "vit_a_ug": 18, "vit_c_mg": 2, "sodium_mg": 260},
        "aliases": ["dosa", "karam dosa", "kadapa karam dosa", "ulli dosa", "plain dosa"]
    },
    {
        "id": "JM-109", "sort_order": 109,
        "name_en": "Masala Dosa (Potato-Stuffed Dosa)",
        "name_te": "మసాలా దోస",
        "cluster": "Tiffins & Breads", "emoji": "🥞", "meal_tabs": "Breakfast",
        "food_groups": ["G1", "G2", "G9"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils), G9 Other vegetables",
        "vegetarian": True, "contains_egg": False, "gi_tier": "High",
        "serving_unit": "1 large masala dosa (180g)", "serving_grams": 180,
        "per_100g": {"calories": 208, "protein_g": 4.8, "carbs_g": 30.6, "fat_g": 7.4, "fiber_g": 2.4, "iron_mg": 1.3, "calcium_mg": 26, "folate_ug": 28, "vit_a_ug": 24, "vit_c_mg": 6, "sodium_mg": 290},
        "aliases": ["masala dosa", "aloo dosa"]
    },
    {
        "id": "JM-110", "sort_order": 110,
        "name_en": "Garelu / Minapa Garelu (Urad Dal Medu Vada)",
        "name_te": "మినప గారెలు / వడ",
        "cluster": "Tiffins & Breads", "emoji": "🍩", "meal_tabs": "Breakfast, Snacks",
        "food_groups": ["G2"], "food_groups_raw": "G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "2 garelu (100g)", "serving_grams": 100,
        "per_100g": {"calories": 284, "protein_g": 9.8, "carbs_g": 28.4, "fat_g": 14.6, "fiber_g": 4.8, "iron_mg": 2.4, "calcium_mg": 52, "folate_ug": 68, "vit_a_ug": 16, "vit_c_mg": 3, "sodium_mg": 310},
        "aliases": ["garelu", "minapa garelu", "medu vada", "vada", "perugu vada"]
    },
    {
        "id": "JM-111", "sort_order": 111,
        "name_en": "Punugulu / Challa Punugulu (Crispy Fritters)",
        "name_te": "పునుగులు / చల్ల పునుగులు",
        "cluster": "Snacks & Sweets", "emoji": "🧆", "meal_tabs": "Breakfast, Snacks",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "8 small punugulu (120g)", "serving_grams": 120,
        "per_100g": {"calories": 272, "protein_g": 6.4, "carbs_g": 34.2, "fat_g": 12.2, "fiber_g": 2.2, "iron_mg": 1.4, "calcium_mg": 32, "folate_ug": 34, "vit_a_ug": 12, "vit_c_mg": 3, "sodium_mg": 320},
        "aliases": ["punugulu", "bezawada punugulu", "challa punugulu", "bonda"]
    },
    {
        "id": "JM-112", "sort_order": 112,
        "name_en": "Dibba Rotti (Thick Pan-Roasted Idli Cake)",
        "name_te": "దిబ్బ రొట్టె",
        "cluster": "Tiffins & Breads", "emoji": "🫓", "meal_tabs": "Breakfast",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 wedge (150g)", "serving_grams": 150,
        "per_100g": {"calories": 192, "protein_g": 6.2, "carbs_g": 29.4, "fat_g": 5.4, "fiber_g": 2.6, "iron_mg": 1.6, "calcium_mg": 34, "folate_ug": 42, "vit_a_ug": 14, "vit_c_mg": 2, "sodium_mg": 240},
        "aliases": ["dibba rotti", "andhra dibba rotti", "minapa rotti"]
    },
    {
        "id": "JM-113", "sort_order": 113,
        "name_en": "Rava Upma / Suji Upma",
        "name_te": "రవ్వ ఉప్మా",
        "cluster": "Tiffins & Breads", "emoji": "🥣", "meal_tabs": "Breakfast",
        "food_groups": ["G1", "G3"], "food_groups_raw": "G1 Grains, roots & tubers, G3 Nuts and seeds",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 bowl (160g)", "serving_grams": 160,
        "per_100g": {"calories": 162, "protein_g": 4.4, "carbs_g": 25.4, "fat_g": 4.8, "fiber_g": 1.8, "iron_mg": 1.1, "calcium_mg": 22, "folate_ug": 24, "vit_a_ug": 32, "vit_c_mg": 5, "sodium_mg": 250},
        "aliases": ["upma", "rava upma", "bansi rava upma", "tomato bath", "suji upma", "sambar upma", "upma sambar", "upma with sambar"]
    },
    {
        "id": "JM-114", "sort_order": 114,
        "name_en": "Katte Pongali / Ven Pongal (Rice & Moong Dal)",
        "name_te": "కట్టె పొంగలి",
        "cluster": "Tiffins & Breads", "emoji": "🍲", "meal_tabs": "Breakfast",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 bowl (180g)", "serving_grams": 180,
        "per_100g": {"calories": 168, "protein_g": 5.4, "carbs_g": 23.8, "fat_g": 5.8, "fiber_g": 2.2, "iron_mg": 1.4, "calcium_mg": 28, "folate_ug": 38, "vit_a_ug": 45, "vit_c_mg": 1, "sodium_mg": 230},
        "aliases": ["katte pongali", "pongal", "ven pongal", "ghee pongal"]
    },
    {
        "id": "JM-115", "sort_order": 115,
        "name_en": "Chapati / Pulka (Whole Wheat Flatbread)",
        "name_te": "చపాతీ / పుల్కా",
        "cluster": "Tiffins & Breads", "emoji": "🫓", "meal_tabs": "Breakfast, Meals",
        "food_groups": ["G1"], "food_groups_raw": "G1 Grains, roots & tubers",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "2 chapatis (80g)", "serving_grams": 80,
        "per_100g": {"calories": 264, "protein_g": 8.4, "carbs_g": 48.2, "fat_g": 4.2, "fiber_g": 6.4, "iron_mg": 2.8, "calcium_mg": 32, "folate_ug": 34, "vit_a_ug": 12, "vit_c_mg": 0, "sodium_mg": 190},
        "aliases": ["chapati", "pulka", "roti", "godhuma rotti"]
    },
    {
        "id": "JM-116", "sort_order": 116,
        "name_en": "Pappu Charu / Sambar (Lentil & Vegetable Stew)",
        "name_te": "పప్పు చారు / సాంబార్",
        "cluster": "Dals & Pappu", "emoji": "🍲", "meal_tabs": "Breakfast, Meals",
        "food_groups": ["G2", "G9"], "food_groups_raw": "G2 Pulses (beans, peas, lentils), G9 Other vegetables",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 katori (160g)", "serving_grams": 160,
        "per_100g": {"calories": 82, "protein_g": 4.1, "carbs_g": 11.2, "fat_g": 2.4, "fiber_g": 2.8, "iron_mg": 1.4, "calcium_mg": 34, "folate_ug": 42, "vit_a_ug": 48, "vit_c_mg": 12, "sodium_mg": 260},
        "aliases": ["pappu charu", "sambar", "telangana pappu charu"]
    },
    {
        "id": "JM-117", "sort_order": 117,
        "name_en": "Rasam / Miriyala Charu (Pepper Tamarind Broth)",
        "name_te": "రసం / మిరియాల చారు",
        "cluster": "Dals & Pappu", "emoji": "🥣", "meal_tabs": "Meals",
        "food_groups": ["G9"], "food_groups_raw": "G9 Other vegetables",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 katori (150g)", "serving_grams": 150,
        "per_100g": {"calories": 38, "protein_g": 1.1, "carbs_g": 5.8, "fat_g": 1.2, "fiber_g": 0.9, "iron_mg": 0.8, "calcium_mg": 18, "folate_ug": 12, "vit_a_ug": 28, "vit_c_mg": 10, "sodium_mg": 240},
        "aliases": ["rasam", "miriyala charu", "tomato charu", "chintapandu charu"]
    },
    {
        "id": "JM-118", "sort_order": 118,
        "name_en": "Ulavacharu (Horse Gram Stew)",
        "name_te": "ఉలవచారు",
        "cluster": "Dals & Pappu", "emoji": "🍲", "meal_tabs": "Meals",
        "food_groups": ["G2"], "food_groups_raw": "G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 small bowl (100g)", "serving_grams": 100,
        "per_100g": {"calories": 148, "protein_g": 8.6, "carbs_g": 21.4, "fat_g": 3.4, "fiber_g": 5.4, "iron_mg": 4.2, "calcium_mg": 142, "folate_ug": 68, "vit_a_ug": 24, "vit_c_mg": 4, "sodium_mg": 310},
        "aliases": ["ulavacharu", "horse gram soup", "ulavacharu cream"]
    },
    {
        "id": "JM-119", "sort_order": 119,
        "name_en": "Perugu / Gatti Perugu (Curd / Yogurt)",
        "name_te": "పెరుగు",
        "cluster": "Dairy", "emoji": "🥛", "meal_tabs": "Meals",
        "food_groups": ["G4"], "food_groups_raw": "G4 Dairy",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 katori (100g)", "serving_grams": 100,
        "per_100g": {"calories": 62, "protein_g": 3.4, "carbs_g": 4.6, "fat_g": 3.3, "fiber_g": 0.0, "iron_mg": 0.2, "calcium_mg": 125, "folate_ug": 11, "vit_a_ug": 28, "vit_c_mg": 1, "sodium_mg": 48},
        "aliases": ["perugu", "curd", "dahi", "yogurt"]
    },
    {
        "id": "JM-120", "sort_order": 120,
        "name_en": "Avakaya (Andhra Spicy Mango Pickle)",
        "name_te": "ఆవకాయ పచ్చడి",
        "cluster": "Chutneys & Podis", "emoji": "🥭", "meal_tabs": "Meals",
        "food_groups": ["G9"], "food_groups_raw": "G9 Other vegetables",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 tbsp (20g)", "serving_grams": 20,
        "per_100g": {"calories": 265, "protein_g": 2.8, "carbs_g": 12.4, "fat_g": 23.2, "fiber_g": 3.6, "iron_mg": 2.4, "calcium_mg": 46, "folate_ug": 18, "vit_a_ug": 95, "vit_c_mg": 18, "sodium_mg": 1850},
        "aliases": ["avakaya", "mango pickle", "andhra avakaya", "magaya"]
    },
    {
        "id": "JM-121", "sort_order": 121,
        "name_en": "Hyderabadi / Andhra Chicken Biryani",
        "name_te": "చికెన్ బిర్యానీ / పలావ్",
        "cluster": "Eggs, Meat & Fish", "emoji": "🍗", "meal_tabs": "Meals",
        "food_groups": ["G1", "G5"], "food_groups_raw": "G1 Grains, roots & tubers, G5 Meat, poultry and fish",
        "vegetarian": False, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 plate (280g)", "serving_grams": 280,
        "per_100g": {"calories": 188, "protein_g": 10.4, "carbs_g": 21.8, "fat_g": 6.6, "fiber_g": 1.2, "iron_mg": 1.3, "calcium_mg": 32, "folate_ug": 18, "vit_a_ug": 38, "vit_c_mg": 3, "sodium_mg": 340},
        "aliases": ["chicken biryani", "kodi pulao", "hyderabadi chicken dum biryani", "raju gari kodi pulao"]
    },
    {
        "id": "JM-122", "sort_order": 122,
        "name_en": "Mutton Dum Biryani / Mamsam Pulao",
        "name_te": "మటన్ బిర్యానీ / మాంసం పలావ్",
        "cluster": "Eggs, Meat & Fish", "emoji": "🍖", "meal_tabs": "Meals",
        "food_groups": ["G1", "G5"], "food_groups_raw": "G1 Grains, roots & tubers, G5 Meat, poultry and fish",
        "vegetarian": False, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 plate (280g)", "serving_grams": 280,
        "per_100g": {"calories": 206, "protein_g": 10.8, "carbs_g": 21.2, "fat_g": 8.6, "fiber_g": 1.2, "iron_mg": 1.9, "calcium_mg": 30, "folate_ug": 16, "vit_a_ug": 34, "vit_c_mg": 3, "sodium_mg": 360},
        "aliases": ["mutton biryani", "hyderabadi mutton biryani", "mamsam pulao"]
    },
    {
        "id": "JM-123", "sort_order": 123,
        "name_en": "Bobbatlu / Bhakshalu /Polelu (Chana Dal Jaggery Flatbread)",
        "name_te": "బొబ్బట్లు / భక్ష్యాలు / పోలెలు",
        "cluster": "Snacks & Sweets", "emoji": "🫓", "meal_tabs": "Snacks",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 bobbattu (70g)", "serving_grams": 70,
        "per_100g": {"calories": 312, "protein_g": 6.8, "carbs_g": 52.4, "fat_g": 8.6, "fiber_g": 3.4, "iron_mg": 2.6, "calcium_mg": 45, "folate_ug": 48, "vit_a_ug": 52, "vit_c_mg": 0, "sodium_mg": 45},
        "aliases": ["bobbatlu", "bhakshalu", "polelu", "puran poli", "oligalu"]
    },
    {
        "id": "JM-124", "sort_order": 124,
        "name_en": "Poornam Boorelu (Stuffed Chana-Jaggery Dumplings)",
        "name_te": "పూర్ణం బూరెలు",
        "cluster": "Snacks & Sweets", "emoji": "🧆", "meal_tabs": "Snacks",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "2 boorelu (90g)", "serving_grams": 90,
        "per_100g": {"calories": 328, "protein_g": 7.2, "carbs_g": 48.6, "fat_g": 11.8, "fiber_g": 3.6, "iron_mg": 2.8, "calcium_mg": 48, "folate_ug": 54, "vit_a_ug": 22, "vit_c_mg": 0, "sodium_mg": 55},
        "aliases": ["boorelu", "poornam boorelu", "poornalu", "sugiyan"]
    },
    {
        "id": "JM-125", "sort_order": 125,
        "name_en": "Sunnundalu (Roasted Urad Dal & Jaggery Ghee Laddu)",
        "name_te": "సున్నుండలు",
        "cluster": "Snacks & Sweets", "emoji": "🧆", "meal_tabs": "Snacks",
        "food_groups": ["G2"], "food_groups_raw": "G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 laddu (45g)", "serving_grams": 45,
        "per_100g": {"calories": 438, "protein_g": 12.6, "carbs_g": 52.8, "fat_g": 19.6, "fiber_g": 5.4, "iron_mg": 4.4, "calcium_mg": 82, "folate_ug": 78, "vit_a_ug": 96, "vit_c_mg": 0, "sodium_mg": 28},
        "aliases": ["sunnundalu", "minapa sunnundalu", "urad dal laddu"]
    },
    {
        "id": "JM-126", "sort_order": 126,
        "name_en": "Sarvapindi / Tapala Chekkalu (Telangana Rice-Peanut Savory Pancake)",
        "name_te": "సర్వపిండి / తపాల చెక్కలు",
        "cluster": "Tiffins & Breads", "emoji": "🫓", "meal_tabs": "Breakfast, Snacks",
        "food_groups": ["G1", "G2", "G3"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils), G3 Nuts and seeds",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 piece (100g)", "serving_grams": 100,
        "per_100g": {"calories": 248, "protein_g": 6.8, "carbs_g": 36.2, "fat_g": 8.6, "fiber_g": 3.4, "iron_mg": 2.2, "calcium_mg": 64, "folate_ug": 42, "vit_a_ug": 28, "vit_c_mg": 4, "sodium_mg": 290},
        "aliases": ["sarvapindi", "tapala chekkalu", "ginne pindi"]
    },
    {
        "id": "JM-127", "sort_order": 127,
        "name_en": "Mirchi Bajji / Aratikaya Bajji (Gram Flour Fritters)",
        "name_te": "మిర్చి బజ్జీ / అరటికాయ బజ్జీ",
        "cluster": "Snacks & Sweets", "emoji": "🌶️", "meal_tabs": "Snacks",
        "food_groups": ["G2", "G9"], "food_groups_raw": "G2 Pulses (beans, peas, lentils), G9 Other vegetables",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "2 bajjis (90g)", "serving_grams": 90,
        "per_100g": {"calories": 268, "protein_g": 6.6, "carbs_g": 26.8, "fat_g": 14.8, "fiber_g": 3.6, "iron_mg": 1.8, "calcium_mg": 38, "folate_ug": 44, "vit_a_ug": 42, "vit_c_mg": 28, "sodium_mg": 330},
        "aliases": ["mirchi bajji", "aratikaya bajji", "uggani bajji", "stuffed mirchi bajji"]
    },
    {
        "id": "JM-128", "sort_order": 128,
        "name_en": "Uggani / Borugula Upma (Rayalaseema Puffed Rice Upma)",
        "name_te": "ఉగ్గాని / బొరుగుల ఉప్మా",
        "cluster": "Tiffins & Breads", "emoji": "🥣", "meal_tabs": "Breakfast, Snacks",
        "food_groups": ["G1", "G2"], "food_groups_raw": "G1 Grains, roots & tubers, G2 Pulses (beans, peas, lentils)",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Medium",
        "serving_unit": "1 plate (150g)", "serving_grams": 150,
        "per_100g": {"calories": 154, "protein_g": 4.2, "carbs_g": 24.6, "fat_g": 4.4, "fiber_g": 2.0, "iron_mg": 1.8, "calcium_mg": 24, "folate_ug": 28, "vit_a_ug": 26, "vit_c_mg": 6, "sodium_mg": 250},
        "aliases": ["uggani", "borugula upma", "maramarala upma"]
    },
    {
        "id": "JM-129", "sort_order": 129,
        "name_en": "Boiled Sweet Potato (Chilakada Dumpa)",
        "name_te": "ఉడకబెట్టిన చిలకడదుంప",
        "cluster": "Snacks & Sweets", "emoji": "🍠", "meal_tabs": "Breakfast, Snacks",
        "food_groups": ["G1", "G8"], "food_groups_raw": "G1 Grains, roots & tubers, G8 Vitamin-A rich fruits and vegetables",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 medium (130g)", "serving_grams": 130,
        "per_100g": {"calories": 86, "protein_g": 1.6, "carbs_g": 20.1, "fat_g": 0.1, "fiber_g": 3.0, "iron_mg": 0.7, "calcium_mg": 30, "folate_ug": 11, "vit_a_ug": 709, "vit_c_mg": 19, "sodium_mg": 36},
        "aliases": ["boiled sweet potato", "sweet potato", "chilakadumpa", "chilakada dumpa", "chilagadadumpa", "genusu gadda"]
    },
    {
        "id": "JM-130", "sort_order": 130,
        "name_en": "Cucumber Slices (Keera)",
        "name_te": "కీరా దోసకాయ ముక్కలు",
        "cluster": "Fruits & Salads", "emoji": "🥒", "meal_tabs": "Snacks, Meals",
        "food_groups": ["G9"], "food_groups_raw": "G9 Other vegetables",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 bowl slices (100g)", "serving_grams": 100,
        "per_100g": {"calories": 15, "protein_g": 0.7, "carbs_g": 3.6, "fat_g": 0.1, "fiber_g": 0.5, "iron_mg": 0.3, "calcium_mg": 16, "folate_ug": 7, "vit_a_ug": 5, "vit_c_mg": 3, "sodium_mg": 2},
        "aliases": ["cucumber slices", "raw cucumber", "fresh cucumber", "keera", "keera dosakaya", "cucumber salad"]
    },
    {
        "id": "JM-131", "sort_order": 131,
        "name_en": "Carrot Pieces (Raw Carrot)",
        "name_te": "క్యారెట్ ముక్కలు",
        "cluster": "Fruits & Salads", "emoji": "🥕", "meal_tabs": "Snacks, Meals",
        "food_groups": ["G8"], "food_groups_raw": "G8 Vitamin-A rich fruits and vegetables",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 small bowl (80g)", "serving_grams": 80,
        "per_100g": {"calories": 41, "protein_g": 0.9, "carbs_g": 9.6, "fat_g": 0.2, "fiber_g": 2.8, "iron_mg": 0.3, "calcium_mg": 33, "folate_ug": 19, "vit_a_ug": 835, "vit_c_mg": 6, "sodium_mg": 69},
        "aliases": ["carrot pieces", "carrot slices", "raw carrot", "fresh carrot", "gajara"]
    },
    {
        "id": "JM-132", "sort_order": 132,
        "name_en": "Pomegranate Seeds (Danimma Ginjalu)",
        "name_te": "దానిమ్మ గింజలు",
        "cluster": "Fruits & Salads", "emoji": "🍎", "meal_tabs": "Snacks, Breakfast",
        "food_groups": ["G10"], "food_groups_raw": "G10 Other fruits",
        "vegetarian": True, "contains_egg": False, "gi_tier": "Low",
        "serving_unit": "1 small bowl (80g)", "serving_grams": 80,
        "per_100g": {"calories": 83, "protein_g": 1.7, "carbs_g": 18.7, "fat_g": 1.2, "fiber_g": 4.0, "iron_mg": 0.3, "calcium_mg": 10, "folate_ug": 38, "vit_a_ug": 0, "vit_c_mg": 10, "sodium_mg": 3},
        "aliases": ["pomegranate seeds", "pomegranate arils", "pomegranate", "danimma ginjalu", "danmmakaya ginjalu"]
    },
    {
        "id": "JM-133", "sort_order": 133,
        "name_en": "Boiled Egg (Udakabettina Guddu)",
        "name_te": "ఉడకబెట్టిన కోడిగుడ్డు",
        "cluster": "Eggs, Meat & Fish", "emoji": "🥚", "meal_tabs": "Breakfast, Meals, Snacks",
        "food_groups": ["G6"], "food_groups_raw": "G6 Eggs",
        "vegetarian": False, "contains_egg": True, "gi_tier": "Low",
        "serving_unit": "1 boiled egg (50g)", "serving_grams": 50,
        "per_100g": {"calories": 155, "protein_g": 12.6, "carbs_g": 1.1, "fat_g": 10.6, "fiber_g": 0.0, "iron_mg": 1.8, "calcium_mg": 50, "folate_ug": 44, "vit_a_ug": 140, "vit_c_mg": 0, "sodium_mg": 124},
        "aliases": ["boiled egg", "udakabettina guddu", "hard boiled egg"]
    },
]


def _extract_group_codes(raw_groups: str) -> List[str]:
    if not raw_groups:
        return []
    return re.findall(r"G\d+", str(raw_groups))


def _resolve_excel_nutrition_meta(name_en: str, sort_order: int) -> Dict[str, Any]:
    """Matches an Excel dish row to its exact entry in EXCEL_DISH_NUTRITION_BY_ORDER by dish name/alias."""
    norm_name = re.sub(r"[^a-z0-9\s]", " ", (name_en or "").lower()).strip()
    name_tokens = {t for t in norm_name.split() if len(t) > 2}

    best_meta = None
    best_score = 0.0
    for idx, meta in EXCEL_DISH_NUTRITION_BY_ORDER.items():
        aliases = [re.sub(r"[^a-z0-9\s]", " ", a.lower()).strip() for a in meta.get("aliases", [])]
        alias_tokens = set()
        for a in aliases:
            if a and a in norm_name:
                score = 10.0 + len(a) / 10.0
                if score > best_score:
                    best_score = score
                    best_meta = meta
            alias_tokens.update(t for t in a.split() if len(t) > 2)
        if name_tokens and alias_tokens:
            overlap = len(name_tokens & alias_tokens)
            if overlap >= 2 and overlap > best_score:
                best_score = float(overlap)
                best_meta = meta

    if best_meta is not None:
        return best_meta

    return EXCEL_DISH_NUTRITION_BY_ORDER.get(sort_order, {
        "serving_unit": "1 katori (150g)",
        "serving_grams": 150,
        "gi_tier": "Low",
        "per_100g": {"calories": 120, "protein_g": 5.0, "carbs_g": 14.0, "fat_g": 5.0, "fiber_g": 3.5, "iron_mg": 2.0, "calcium_mg": 50, "folate_ug": 45, "vit_a_ug": 80, "vit_c_mg": 15, "sodium_mg": 250},
        "aliases": []
    })


def load_full_catalog() -> List[Dict[str, Any]]:
    """Loads the dishes from JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx and appends foundational Telugu staples."""
    catalog: List[Dict[str, Any]] = []

    if EXCEL_PATH.exists():
        wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        for row in rows[1:]:
            if not row or not row[0]:
                continue
            try:
                sort_order = int(row[0])
            except (ValueError, TypeError):
                continue
            name_en = str(row[1] if len(row) > 1 and row[1] else "").strip()
            name_te = str(row[2] if len(row) > 2 and row[2] else "").strip()
            cluster = str(row[3] if len(row) > 3 and row[3] else "Telugu Dish").strip()
            emoji = str(row[4] if len(row) > 4 and row[4] else "🍲").strip()
            meal_tabs = str(row[5] if len(row) > 5 and row[5] else "Meals").strip()
            food_groups_raw = str(row[6] if len(row) > 6 and row[6] else "").strip()
            vegetarian = str(row[7] if len(row) > 7 and row[7] else "Yes").strip().lower() == "yes"
            contains_egg = str(row[8] if len(row) > 8 and row[8] else "No").strip().lower() == "yes"
            notes = str(row[10] if len(row) > 10 and row[10] else "").strip()
            c11 = row[11] if len(row) > 11 else None
            c12 = row[12] if len(row) > 12 else None
            image_url = str(c11 or c12 or "").strip()
            local_image = str(row[13] if len(row) > 13 and row[13] else "").strip()

            nutr_meta = _resolve_excel_nutrition_meta(name_en, sort_order)

            catalog.append({
                "id": f"JM-{sort_order:02d}",
                "sort_order": sort_order,
                "name_en": name_en,
                "name_te": name_te,
                "cluster": cluster,
                "emoji": emoji,
                "meal_tabs": meal_tabs,
                "food_groups": _extract_group_codes(food_groups_raw),
                "food_groups_raw": food_groups_raw,
                "vegetarian": vegetarian,
                "contains_egg": contains_egg,
                "notes": notes,
                "image_url": image_url,
                "local_image": local_image,
                "serving_unit": nutr_meta["serving_unit"],
                "serving_grams": nutr_meta["serving_grams"],
                "gi_tier": nutr_meta["gi_tier"],
                "per_100g": nutr_meta["per_100g"],
                "aliases": nutr_meta.get("aliases", []),
                "source": "JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx + ICMR-NIN IFCT",
            })

    # Append foundational staples
    for staple in FOUNDATIONAL_TELUGU_STAPLES:
        item = dict(staple)
        item["source"] = "Telugu Staples + ICMR-NIN IFCT"
        item.setdefault("notes", "Andhra & Telangana staple")
        item.setdefault("image_url", "")
        item.setdefault("local_image", "")
        catalog.append(item)

    return catalog


CATALOG: List[Dict[str, Any]] = load_full_catalog()
CATALOG_BY_ID: Dict[str, Dict[str, Any]] = {d["id"]: d for d in CATALOG}


def compute_portion_nutrition(per_100g: Dict[str, float], grams: float, oil_modifier: float = 1.0) -> Dict[str, float]:
    """Calculates nutrition for a given gram weight from per-100g ICMR-NIN values."""
    factor = max(grams, 1.0) / 100.0
    base_cal = per_100g["calories"] * factor
    base_fat = per_100g["fat_g"] * factor
    fat = round(base_fat * oil_modifier, 1)
    delta_fat = fat - base_fat
    calories = round(base_cal + (delta_fat * 9.0), 0)
    return {
        "calories": int(max(0.0, calories)),
        "protein_g": round(per_100g["protein_g"] * factor, 1),
        "carbs_g": round(per_100g["carbs_g"] * factor, 1),
        "fat_g": fat,
        "fiber_g": round(per_100g["fiber_g"] * factor, 1),
        "iron_mg": round(per_100g["iron_mg"] * factor, 2),
        "calcium_mg": round(per_100g["calcium_mg"] * factor, 1),
        "folate_ug": round(per_100g["folate_ug"] * factor, 1),
        "vit_a_ug": round(per_100g["vit_a_ug"] * factor, 1),
        "vit_c_mg": round(per_100g["vit_c_mg"] * factor, 1),
        "sodium_mg": round(per_100g["sodium_mg"] * factor, 0),
    }


def get_compact_catalog_prompt_text() -> str:
    """Returns a compact reference list of all Telugu dishes for the Gemini vision prompt."""
    lines = []
    for d in CATALOG:
        groups = ",".join(d["food_groups"])
        lines.append(
            f"{d['id']}: {d['name_en']} | {d['name_te']} | {d['cluster']} | Std: {d['serving_unit']} | Groups: {groups}"
        )
    return "\n".join(lines)
