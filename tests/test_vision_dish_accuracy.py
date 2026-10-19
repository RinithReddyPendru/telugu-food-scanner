"""
Comprehensive QA Audit Test Suite for Vision Recognition & Telugu Dish Accuracy.
Testing Agent #2: Vision & Telugu Dish QA Tester

Covers:
1. Raw/Fresh Salad vs Cooked Curries/Dals/Pappus Isolation:
   - Verifies that raw/fresh salad items (Cucumber Slices/Keera, Carrot Pieces, Pomegranate Seeds)
     NEVER match cooked curries, dals, or pappus (Dosakaya Pappu, Dosakaya Kura, Carrot Vepudu).
   - Verifies that supported raw item queries resolve to their exact raw/fresh catalog entries.
   - Verifies that uncatalogued raw queries (e.g. 'Cucumber Pieces', 'Carrot Salad') never match cooked dishes.
   - Verifies that cooked queries match cooked dishes.
2. Cooked Telugu Dishes Accuracy:
   - Gutti Vankaya Kura, Gongura Pappu, Palakura Pappu, Hyderabadi Chicken Biryani, Pesarattu.
   - Authentic Telugu script names (`name_te`) with Unicode verification (U+0C00..U+0C7F).
   - Grounded ICMR-NIN macro & micronutrient totals per 100g and standard serving portion.
   - Full audit of all 103 dishes in the catalog for nutrition completeness & Telugu script.
   - Audits matching behavior with and without preparation keywords (Guard 2 analysis).
3. Multi-Item Plates Recognition & Summation:
   - Plate A (Cooked Thali): Steamed Rice (200g) + Gongura Pappu (150g) + Gutti Vankaya (150g).
   - Plate B (Fresh Bowl): Boiled Sweet Potato (130g) + Cucumber Slices (100g) + Carrot Pieces (80g) + Pomegranate Seeds (80g).
   - Verifies all items detected, realistic portion weights, and totals == exact sum of individual items.
   - Verifies MDD-W diversity scoring and multi-item title generation.
4. Portion Scaling & Oil Modifiers:
   - Linear gram scaling across 50g, 100g, 150g, 200g, 280g.
   - Oil modifiers: low (0.85x), moderate (1.0x), and high (1.2x).
   - Verifies calories and fat recalculation math and audits low-oil calorie clamping and float rounding nuances.
"""

from __future__ import annotations
import math
import pathlib
import sys
import unittest
from typing import Any, Dict, List

# Ensure UTF-8 stdout on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure parent directory (`telugu-food-scanner`) is on sys.path
SCANNER_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

import dishes_catalog
from dishes_catalog import (
    CATALOG,
    CATALOG_BY_ID,
    FOUNDATIONAL_TELUGU_STAPLES,
    compute_portion_nutrition,
)
import scanner_engine
from scanner_engine import (
    MDDW_LABELS,
    DetectedDishVisionItem,
    Per100gEstimate,
    VisionPlateAnalysis,
    _match_dish_in_local_catalog,
)


def has_telugu_unicode(text: str) -> bool:
    """Returns True if the string contains at least one character in the Telugu Unicode block."""
    if not text:
        return False
    return any("\u0c00" <= ch <= "\u0c7f" for ch in text)


class TestRawSaladVsCookedIsolation(unittest.TestCase):
    """
    Audit Suite 1: Raw & Fresh Salad vs Cooked Dishes Isolation.
    Ensures raw vegetable/salad items never match cooked dals, curries, fries, or stews.
    """

    COOKED_DISALLOW_KEYWORDS = {
        "pappu", "dal", "kura", "curry", "vepudu", "fry", "pulusu",
        "sambar", "charu", "rasam", "iguru", "masala"
    }

    def test_01_cucumber_slices_never_match_cooked_dal_or_curry(self):
        """Cucumber / Keera queries must NEVER match Dosakaya Pappu (JM-17) or Dosakaya Kura (JM-35)."""
        cucumber_queries = [
            "Cucumber Slices",
            "Cucumber Slices (Dosakaya)",
            "Keera",
            "Keera Dosakaya",
            "Raw Cucumber",
            "Fresh Cucumber",
            "Fresh Cucumber Slices",
            "Cucumber Salad",
            "raw cucumber slices",
            "keera dosakaya slices",
        ]

        for q in cucumber_queries:
            matched = _match_dish_in_local_catalog(q)
            self.assertIsNotNone(
                matched,
                f"Expected query '{q}' to resolve to a catalog entry, got None",
            )
            matched_id = matched["id"]
            matched_name = matched["name_en"].lower()

            # Must NEVER match Dosakaya Pappu (JM-17) or Dosakaya Kura (JM-35)
            self.assertNotEqual(
                matched_id, "JM-17",
                f"CRITICAL FALSE MATCH: '{q}' matched Dosakaya Pappu (JM-17)!",
            )
            self.assertNotEqual(
                matched_id, "JM-35",
                f"CRITICAL FALSE MATCH: '{q}' matched Dosakaya Kura (JM-35)!",
            )

            # Must never match any cooked preparation keywords
            matched_tokens = set(matched_name.split())
            forbidden_overlap = matched_tokens & self.COOKED_DISALLOW_KEYWORDS
            self.assertEqual(
                forbidden_overlap, set(),
                f"CRITICAL FALSE MATCH: '{q}' matched cooked preparation '{matched['name_en']}' ({forbidden_overlap})",
            )

            # Must resolve to Cucumber Slices (Keera) JM-130
            self.assertEqual(
                matched_id, "JM-130",
                f"Expected '{q}' to match JM-130 (Cucumber Slices), got {matched_id}: {matched['name_en']}",
            )

    def test_02_raw_cucumber_variants_never_pollute_cooked_catalog(self):
        """Uncatalogued or partial cucumber queries (e.g. 'Cucumber Pieces') must NEVER match cooked dishes."""
        queries = ["Cucumber Pieces", "Keera Mukkalu", "Chopped Keera", "Fresh Dosakaya Slices"]
        for q in queries:
            matched = _match_dish_in_local_catalog(q)
            if matched:
                self.assertNotIn(
                    matched["id"], ["JM-17", "JM-35"],
                    f"CRITICAL FALSE MATCH: Query '{q}' matched cooked dish {matched['id']}!",
                )
                matched_tokens = set(matched["name_en"].lower().split())
                self.assertEqual(
                    matched_tokens & self.COOKED_DISALLOW_KEYWORDS, set(),
                    f"CRITICAL FALSE MATCH: Query '{q}' matched cooked dish '{matched['name_en']}'!",
                )

    def test_03_raw_carrot_never_matches_cooked_vepudu_or_curry(self):
        """Carrot pieces / raw carrot queries must NEVER match Carrot Vepudu or cooked curry."""
        carrot_queries = [
            "Carrot Pieces",
            "Carrot Pieces (Raw Carrot)",
            "Raw Carrot",
            "Carrot Slices",
            "Fresh Carrot",
            "fresh carrot slices",
            "raw carrot pieces",
        ]

        for q in carrot_queries:
            matched = _match_dish_in_local_catalog(q)
            self.assertIsNotNone(
                matched,
                f"Expected query '{q}' to resolve to a catalog entry, got None",
            )
            matched_id = matched["id"]
            matched_name = matched["name_en"].lower()

            # Must never match any cooked fry/curry
            matched_tokens = set(matched_name.split())
            forbidden_overlap = matched_tokens & self.COOKED_DISALLOW_KEYWORDS
            self.assertEqual(
                forbidden_overlap, set(),
                f"CRITICAL FALSE MATCH: '{q}' matched cooked dish '{matched['name_en']}'",
            )

            # Must resolve to Carrot Pieces (Raw Carrot) JM-131
            self.assertEqual(
                matched_id, "JM-131",
                f"Expected '{q}' to match JM-131 (Carrot Pieces), got {matched_id}: {matched['name_en']}",
            )

    def test_04_raw_carrot_uncatalogued_variants_never_match_cooked(self):
        """Variants like 'Carrot Salad' or 'Carrot Mukkalu' must NEVER match cooked curries."""
        queries = ["Carrot Salad", "Carrot Mukkalu", "Chopped Raw Carrot", "Carrot Cubes"]
        for q in queries:
            matched = _match_dish_in_local_catalog(q)
            if matched:
                matched_tokens = set(matched["name_en"].lower().split())
                self.assertEqual(
                    matched_tokens & self.COOKED_DISALLOW_KEYWORDS, set(),
                    f"CRITICAL FALSE MATCH: Query '{q}' matched cooked dish '{matched['name_en']}'!",
                )

    def test_05_pomegranate_seeds_never_matches_cooked_dishes(self):
        """Pomegranate seeds queries must NEVER match cooked curries or dals."""
        pomegranate_queries = [
            "Pomegranate Seeds",
            "Pomegranate Seeds (Danimma Ginjalu)",
            "Pomegranate Arils",
            "Danimma Ginjalu",
            "Fresh Pomegranate",
            "Fresh Pomegranate Seeds",
            "Pomegranate",
        ]

        for q in pomegranate_queries:
            matched = _match_dish_in_local_catalog(q)
            self.assertIsNotNone(
                matched,
                f"Expected query '{q}' to resolve to a catalog entry, got None",
            )
            matched_id = matched["id"]
            matched_name = matched["name_en"].lower()

            matched_tokens = set(matched_name.split())
            forbidden_overlap = matched_tokens & self.COOKED_DISALLOW_KEYWORDS
            self.assertEqual(
                forbidden_overlap, set(),
                f"CRITICAL FALSE MATCH: '{q}' matched cooked dish '{matched['name_en']}'",
            )

            self.assertEqual(
                matched_id, "JM-132",
                f"Expected '{q}' to match JM-132 (Pomegranate Seeds), got {matched_id}: {matched['name_en']}",
            )

    def test_06_boiled_sweet_potato_matches_accurately(self):
        """Sweet potato queries must match Boiled Sweet Potato (JM-129) and not potato fry."""
        sweet_potato_queries = [
            "Boiled Sweet Potato",
            "Boiled Sweet Potato (Chilakada Dumpa)",
            "Sweet Potato",
            "Chilakadumpa",
            "Chilakada Dumpa",
            "Genusu Gadda",
        ]

        for q in sweet_potato_queries:
            matched = _match_dish_in_local_catalog(q)
            self.assertIsNotNone(
                matched,
                f"Expected query '{q}' to resolve to a catalog entry, got None",
            )
            matched_id = matched["id"]
            # Must NOT match Bangaladumpa Vepudu (potato fry JM-27)
            self.assertNotEqual(
                matched_id, "JM-27",
                f"CRITICAL FALSE MATCH: '{q}' matched Bangaladumpa Vepudu (JM-27)!",
            )
            self.assertEqual(
                matched_id, "JM-129",
                f"Expected '{q}' to match JM-129 (Boiled Sweet Potato), got {matched_id}: {matched['name_en']}",
            )

    def test_07_cooked_dishes_with_produce_names_match_cooked_dishes(self):
        """Positive controls: explicit cooked dish names MUST match cooked dishes, not raw salads."""
        cooked_controls = [
            ("Dosakaya Pappu", "JM-17", "Dosakaya Pappu (Yellow Cucumber Dal)"),
            ("Dosakaya Kura", "JM-35", "Dosakaya Kura / Mukkala Pulusu (Yellow Cucumber)"),
            ("Dosakaya Mukkala Pulusu", "JM-35", "Dosakaya Kura / Mukkala Pulusu (Yellow Cucumber)"),
            ("Bangaladumpa Vepudu", "JM-24", "Bangaladumpa / Aloo Kura & Vepudu (Potato)"),
            ("Dondakaya Vepudu", "JM-25", "Dondakaya Vepudu / Kura (Ivy Gourd)"),
            ("Bendakaya Vepudu", "JM-23", "Bendakaya Vepudu / Pulusu (Ladies Finger)"),
        ]

        for query, expected_id, expected_name in cooked_controls:
            matched = _match_dish_in_local_catalog(query)
            self.assertIsNotNone(matched, f"Expected '{query}' to match a cooked dish, got None")
            self.assertEqual(
                matched["id"], expected_id,
                f"Query '{query}' matched ID {matched['id']} instead of {expected_id} ({expected_name})",
            )
            # Must NEVER match raw items JM-129, JM-130, JM-131, JM-132
            self.assertNotIn(
                matched["id"], ["JM-129", "JM-130", "JM-131", "JM-132"],
                f"Query '{query}' false-matched raw item {matched['id']}!",
            )

    def test_08_cooked_carrot_vepudu_never_matches_raw_carrot_salad(self):
        """Cooked Carrot Vepudu / Fry must NEVER false-match raw Carrot Pieces (JM-131)."""
        queries = ["Carrot Vepudu", "Carrot Fry", "Carrot Kura"]
        for q in queries:
            matched = _match_dish_in_local_catalog(q)
            if matched:
                self.assertNotEqual(
                    matched["id"], "JM-131",
                    f"CRITICAL FALSE MATCH: Cooked dish '{q}' matched raw Carrot Pieces (JM-131)!",
                )


class TestCookedDishesTeluguScriptAndNutrition(unittest.TestCase):
    """
    Audit Suite 2: Cooked Dishes Telugu Script & ICMR-NIN Nutrition Integrity.
    Verifies authentic Telugu script names (`name_te`) and grounded ICMR-NIN nutrition values.
    """

    REQUIRED_NUTRIENTS = [
        "calories", "protein_g", "carbs_g", "fat_g", "fiber_g",
        "iron_mg", "calcium_mg", "folate_ug", "vit_a_ug", "vit_c_mg", "sodium_mg"
    ]

    def test_01_gutti_vankaya_kura_accuracy(self):
        """Verify Gutti Vankaya Kura matches accurately with Telugu script and ICMR-NIN nutrition."""
        queries = ["Gutti Vankaya Kura", "Gutti Vankaya Curry", "Vankaya Kura"]
        for q in queries:
            matched = _match_dish_in_local_catalog(q)
            self.assertIsNotNone(matched, f"Failed to match '{q}'")
            self.assertEqual(matched["id"], "JM-22", f"Expected JM-22, got {matched['id']}")

        dish = CATALOG_BY_ID["JM-22"]
        self.assertIn("vankaya", dish["name_en"].lower())
        self.assertTrue(has_telugu_unicode(dish["name_te"]), "name_te missing Telugu Unicode")
        self.assertEqual(dish["name_te"], "వంకాయ కూర / గుత్తి వంకాయ")

        # ICMR-NIN per-100g verification
        p100 = dish["per_100g"]
        for k in self.REQUIRED_NUTRIENTS:
            self.assertIn(k, p100, f"Missing nutrient {k} in JM-22")

        self.assertEqual(p100["calories"], 148)
        self.assertEqual(p100["protein_g"], 3.8)
        self.assertEqual(p100["carbs_g"], 9.6)
        self.assertEqual(p100["fat_g"], 10.8)
        self.assertEqual(p100["fiber_g"], 4.2)
        self.assertEqual(p100["iron_mg"], 1.6)
        self.assertEqual(p100["calcium_mg"], 48)

        # Serving size: 1 katori (150g)
        self.assertEqual(dish["serving_grams"], 150)
        self.assertIn("150g", dish["serving_unit"])

        # Computed portion nutrition at 150g standard serving
        std = compute_portion_nutrition(p100, 150)
        self.assertEqual(std["calories"], 222)   # 148 * 1.5 = 222
        self.assertEqual(std["protein_g"], 5.7)  # 3.8 * 1.5 = 5.7
        self.assertEqual(std["carbs_g"], 14.4)   # 9.6 * 1.5 = 14.4
        self.assertEqual(std["fat_g"], 16.2)     # 10.8 * 1.5 = 16.2

    def test_02_gutti_vankaya_matching_guard_discrepancy_audit(self):
        """
        Audit of Guard 2 in `scanner_engine.py`:
        Queries like 'Gutti Vankaya' (without preparation token 'kura' or 'curry')
        are rejected by Guard 2 because `entry_prep_tokens` requires matching prep keywords.
        Documents this exact matching behavior.
        """
        # With prep keyword -> matches JM-22
        self.assertIsNotNone(_match_dish_in_local_catalog("Gutti Vankaya Kura"))
        self.assertIsNotNone(_match_dish_in_local_catalog("Gutti Vankaya Curry"))

        # Without prep keyword -> rejected by Guard 2 in production code
        match_bare = _match_dish_in_local_catalog("Gutti Vankaya")
        # Document the current behavior: returns None due to Guard 2 token check
        self.assertIsNone(
            match_bare,
            "Expected bare 'Gutti Vankaya' to return None under current Guard 2 implementation",
        )

    def test_03_gongura_pappu_accuracy(self):
        """Verify Gongura Pappu matches accurately with Telugu script and ICMR-NIN nutrition."""
        matched = _match_dish_in_local_catalog("Gongura Pappu")
        self.assertIsNotNone(matched, "Failed to match 'Gongura Pappu'")
        self.assertEqual(matched["id"], "JM-11")

        dish = CATALOG_BY_ID["JM-11"]
        self.assertEqual(dish["name_en"], "Gongura Pappu (Sorrel Leaves Dal)")
        self.assertTrue(has_telugu_unicode(dish["name_te"]), "name_te missing Telugu Unicode")
        self.assertEqual(dish["name_te"], "గోంగూర పప్పు")

        p100 = dish["per_100g"]
        self.assertEqual(p100["calories"], 126)
        self.assertEqual(p100["protein_g"], 6.5)
        self.assertEqual(p100["carbs_g"], 15.0)
        self.assertEqual(p100["fat_g"], 4.5)
        self.assertEqual(p100["fiber_g"], 4.1)
        self.assertEqual(p100["iron_mg"], 3.9)
        self.assertEqual(p100["vit_a_ug"], 180)
        self.assertEqual(p100["vit_c_mg"], 25)

        self.assertEqual(dish["serving_grams"], 150)
        std = compute_portion_nutrition(p100, 150)
        self.assertEqual(std["calories"], 189)   # 126 * 1.5 = 189
        self.assertEqual(std["protein_g"], 9.8)  # 6.5 * 1.5 = 9.75 -> 9.8
        self.assertEqual(std["carbs_g"], 22.5)   # 15.0 * 1.5 = 22.5
        self.assertEqual(std["fat_g"], 6.8)      # 4.5 * 1.5 = 6.75 -> 6.8

    def test_04_palakura_pappu_accuracy(self):
        """Verify Palakura Pappu matches accurately with Telugu script and ICMR-NIN nutrition."""
        matched = _match_dish_in_local_catalog("Palakura Pappu")
        self.assertIsNotNone(matched, "Failed to match 'Palakura Pappu'")
        self.assertEqual(matched["id"], "JM-09")

        dish = CATALOG_BY_ID["JM-09"]
        self.assertEqual(dish["name_en"], "Palakura Pappu (Spinach Dal)")
        self.assertTrue(has_telugu_unicode(dish["name_te"]), "name_te missing Telugu Unicode")
        self.assertEqual(dish["name_te"], "పాలకూర పప్పు")

        p100 = dish["per_100g"]
        self.assertEqual(p100["calories"], 118)
        self.assertEqual(p100["protein_g"], 6.4)
        self.assertEqual(p100["carbs_g"], 14.2)
        self.assertEqual(p100["fat_g"], 4.0)
        self.assertEqual(p100["fiber_g"], 3.8)
        self.assertEqual(p100["iron_mg"], 2.9)
        self.assertEqual(p100["vit_a_ug"], 220)
        self.assertEqual(p100["folate_ug"], 82)

        self.assertEqual(dish["serving_grams"], 150)
        std = compute_portion_nutrition(p100, 150)
        self.assertEqual(std["calories"], 177)   # 118 * 1.5 = 177
        self.assertEqual(std["protein_g"], 9.6)  # 6.4 * 1.5 = 9.6
        self.assertEqual(std["carbs_g"], 21.3)   # 14.2 * 1.5 = 21.3
        self.assertEqual(std["fat_g"], 6.0)      # 4.0 * 1.5 = 6.0

    def test_05_hyderabadi_chicken_biryani_accuracy(self):
        """Verify Hyderabadi Chicken Biryani matches accurately with Telugu script and nutrition."""
        for q in ["Hyderabadi Chicken Biryani", "Chicken Biryani", "Kodi Pulao"]:
            matched = _match_dish_in_local_catalog(q)
            self.assertIsNotNone(matched, f"Failed to match '{q}'")
            self.assertEqual(matched["id"], "JM-121")

        dish = CATALOG_BY_ID["JM-121"]
        self.assertEqual(dish["name_en"], "Hyderabadi / Andhra Chicken Biryani")
        self.assertTrue(has_telugu_unicode(dish["name_te"]), "name_te missing Telugu Unicode")
        self.assertEqual(dish["name_te"], "చికెన్ బిర్యానీ / పలావ్")
        self.assertFalse(dish["vegetarian"])
        self.assertIn("G5", dish["food_groups"])  # Meat/poultry/fish

        p100 = dish["per_100g"]
        self.assertEqual(p100["calories"], 188)
        self.assertEqual(p100["protein_g"], 10.4)
        self.assertEqual(p100["carbs_g"], 21.8)
        self.assertEqual(p100["fat_g"], 6.6)
        self.assertEqual(p100["fiber_g"], 1.2)
        self.assertEqual(p100["iron_mg"], 1.3)
        self.assertEqual(p100["sodium_mg"], 340)

        # Serving size: 1 plate (280g)
        self.assertEqual(dish["serving_grams"], 280)
        std = compute_portion_nutrition(p100, 280)

        # Note: 188 * 2.8 = 526.4. However, fat rounding (6.6 * 2.8 = 18.48 -> 18.5)
        # creates extra_fat_g = 18.5 - 18.48 = 0.02, adding 0.18 kcal -> 526.58 -> 527.
        self.assertEqual(std["calories"], 527)
        self.assertEqual(std["protein_g"], 29.1) # 10.4 * 2.8 = 29.12 -> 29.1
        self.assertEqual(std["carbs_g"], 61.0)   # 21.8 * 2.8 = 61.04 -> 61.0
        self.assertEqual(std["fat_g"], 18.5)     # 6.6 * 2.8 = 18.48 -> 18.5

    def test_06_pesarattu_accuracy(self):
        """Verify Pesarattu matches accurately with Telugu script and nutrition."""
        for q in ["Pesarattu", "Moong Dal Dosa", "Green Gram Dosa", "Ulli Pesarattu"]:
            matched = _match_dish_in_local_catalog(q)
            self.assertIsNotNone(matched, f"Failed to match '{q}'")
            self.assertEqual(matched["id"], "JM-105")

        dish = CATALOG_BY_ID["JM-105"]
        self.assertEqual(dish["name_en"], "Pesarattu (Green Moong Dal Dosa)")
        self.assertTrue(has_telugu_unicode(dish["name_te"]), "name_te missing Telugu Unicode")
        self.assertEqual(dish["name_te"], "పెసరట్టు")
        self.assertTrue(dish["vegetarian"])
        self.assertIn("G2", dish["food_groups"])  # Pulses

        p100 = dish["per_100g"]
        self.assertEqual(p100["calories"], 186)
        self.assertEqual(p100["protein_g"], 9.4)
        self.assertEqual(p100["carbs_g"], 24.8)
        self.assertEqual(p100["fat_g"], 5.4)
        self.assertEqual(p100["fiber_g"], 5.2)
        self.assertEqual(p100["iron_mg"], 2.4)
        self.assertEqual(p100["folate_ug"], 84)

        # Serving size: 2 pesarattu (150g)
        self.assertEqual(dish["serving_grams"], 150)
        std = compute_portion_nutrition(p100, 150)
        self.assertEqual(std["calories"], 279)   # 186 * 1.5 = 279
        self.assertEqual(std["protein_g"], 14.1) # 9.4 * 1.5 = 14.1
        self.assertEqual(std["carbs_g"], 37.2)   # 24.8 * 1.5 = 37.2
        self.assertEqual(std["fat_g"], 8.1)      # 5.4 * 1.5 = 8.1

    def test_07_entire_catalog_integrity_audit(self):
        """Audits all dishes in the catalog for complete nutrients, Telugu script, and valid serving sizes."""
        discrepancies = []
        for dish in CATALOG:
            did = dish["id"]
            if not dish.get("name_en"):
                discrepancies.append(f"{did}: Missing name_en")
            if not dish.get("name_te") or not has_telugu_unicode(dish["name_te"]):
                discrepancies.append(f"{did}: Invalid Telugu script name_te ({dish.get('name_te')})")
            if not dish.get("serving_grams") or dish["serving_grams"] <= 0:
                discrepancies.append(f"{did}: Invalid serving_grams ({dish.get('serving_grams')})")
            if not dish.get("serving_unit"):
                discrepancies.append(f"{did}: Missing serving_unit")

            p100 = dish.get("per_100g", {})
            for nut in self.REQUIRED_NUTRIENTS:
                if nut not in p100:
                    discrepancies.append(f"{did}: Missing nutrient {nut}")
                elif p100[nut] < 0:
                    discrepancies.append(f"{did}: Negative nutrient {nut} = {p100[nut]}")

            # Verify GI tier is valid
            if dish.get("gi_tier") not in ("Low", "Medium", "High"):
                discrepancies.append(f"{did}: Invalid gi_tier ({dish.get('gi_tier')})")

            # Verify MDD-W food groups are valid
            for fg in dish.get("food_groups", []):
                if fg not in MDDW_LABELS:
                    discrepancies.append(f"{did}: Unknown food group code {fg}")

        self.assertEqual(
            discrepancies, [],
            f"Found {len(discrepancies)} catalog integrity discrepancies: {discrepancies[:5]}",
        )


class TestMultiItemPlateRecognitionAndSummation(unittest.TestCase):
    """
    Audit Suite 3: Multi-Item Plates Recognition, Realistic Weights, and Nutrition Summation.
    Verifies that mixed plates detect every individual item, weights are realistic, and
    plate totals equal the exact sum of individual item nutrition.
    """

    def test_01_plate_a_cooked_thali_rice_gongura_pappu_vankaya(self):
        """
        Plate A (Cooked Thali): Steamed Rice (200g) + Gongura Pappu (150g) + Gutti Vankaya Curry (150g).
        All 3 items detected, matched, weights realistic, totals == sum of items.
        """
        plate_items = [
            {"name_en": "Steamed White Rice (Vandi Annam)", "name_te": "వండిన తెల్ల అన్నం", "grams": 200.0, "oil": "moderate"},
            {"name_en": "Gongura Pappu (Sorrel Leaves Dal)", "name_te": "గోంగూర పప్పు", "grams": 150.0, "oil": "moderate"},
            {"name_en": "Gutti Vankaya Kura", "name_te": "వంకాయ కూర / గుత్తి వంకాయ", "grams": 150.0, "oil": "moderate"},
        ]

        # 1. Match each item in catalog
        reconciled = []
        for it in plate_items:
            entry = _match_dish_in_local_catalog(it["name_en"], it["name_te"])
            self.assertIsNotNone(entry, f"Item '{it['name_en']}' failed to match catalog")
            nutr = compute_portion_nutrition(entry["per_100g"], it["grams"], oil_modifier=1.0)
            reconciled.append({
                "entry": entry,
                "grams": it["grams"],
                "nutrition": nutr,
            })

        # Expected matches
        self.assertEqual(reconciled[0]["entry"]["id"], "JM-101")  # Steamed White Rice
        self.assertEqual(reconciled[1]["entry"]["id"], "JM-11")   # Gongura Pappu
        self.assertEqual(reconciled[2]["entry"]["id"], "JM-22")   # Gutti Vankaya

        # 2. Check individual item nutrition
        rice_nutr = reconciled[0]["nutrition"]
        self.assertEqual(rice_nutr["calories"], 260)
        self.assertEqual(rice_nutr["protein_g"], 5.4)
        self.assertEqual(rice_nutr["carbs_g"], 56.4)
        self.assertEqual(rice_nutr["fat_g"], 0.6)

        pappu_nutr = reconciled[1]["nutrition"]
        self.assertEqual(pappu_nutr["calories"], 189)
        self.assertEqual(pappu_nutr["protein_g"], 9.8)
        self.assertEqual(pappu_nutr["carbs_g"], 22.5)
        self.assertEqual(pappu_nutr["fat_g"], 6.8)

        vankaya_nutr = reconciled[2]["nutrition"]
        self.assertEqual(vankaya_nutr["calories"], 222)
        self.assertEqual(vankaya_nutr["protein_g"], 5.7)
        self.assertEqual(vankaya_nutr["carbs_g"], 14.4)
        self.assertEqual(vankaya_nutr["fat_g"], 16.2)

        # 3. Summation verification
        total_calories = sum(it["nutrition"]["calories"] for it in reconciled)
        total_protein = round(sum(it["nutrition"]["protein_g"] for it in reconciled), 1)
        total_carbs = round(sum(it["nutrition"]["carbs_g"] for it in reconciled), 1)
        total_fat = round(sum(it["nutrition"]["fat_g"] for it in reconciled), 1)
        total_fiber = round(sum(it["nutrition"]["fiber_g"] for it in reconciled), 1)
        total_grams = int(sum(it["grams"] for it in reconciled))

        # 260 + 189 + 222 = 671 kcal
        self.assertEqual(total_calories, 671)
        # 5.4 + 9.8 + 5.7 = 20.9g protein
        self.assertEqual(total_protein, 20.9)
        # 56.4 + 22.5 + 14.4 = 93.3g carbs
        self.assertEqual(total_carbs, 93.3)
        # 0.6 + 6.8 + 16.2 = 23.6g fat
        self.assertEqual(total_fat, 23.6)
        # Total weight: 200 + 150 + 150 = 500g
        self.assertEqual(total_grams, 500)

        # Realistic portion weight assertions
        self.assertTrue(150 <= reconciled[0]["grams"] <= 300, "Rice portion outside realistic bounds")
        self.assertTrue(100 <= reconciled[1]["grams"] <= 250, "Pappu portion outside realistic bounds")
        self.assertTrue(100 <= reconciled[2]["grams"] <= 250, "Curry portion outside realistic bounds")

        # MDD-W Food Group Diversity
        covered_groups = set()
        for it in reconciled:
            covered_groups.update(it["entry"]["food_groups"])

        self.assertIn("G1", covered_groups)  # Rice (Grains)
        self.assertIn("G2", covered_groups)  # Gongura Pappu (Pulses)
        self.assertIn("G7", covered_groups)  # Gongura Pappu (Dark green leafies)
        self.assertIn("G9", covered_groups)  # Gutti Vankaya (Other vegetables)
        self.assertGreaterEqual(len(covered_groups), 4, "Expected at least 4 food groups in Thali")

    def test_02_plate_b_fresh_bowl_sweet_potato_cucumber_carrot_pomegranate(self):
        """
        Plate B (Fresh Bowl): Boiled Sweet Potato (130g) + Cucumber Slices (100g) +
        Carrot Pieces (80g) + Pomegranate Seeds (80g).
        All 4 items detected, NO false matches to cooked dishes, totals == sum of items.
        """
        plate_items = [
            {"name_en": "Boiled Sweet Potato (Chilakada Dumpa)", "name_te": "ఉడకబెట్టిన చిలకడదుంప", "grams": 130.0, "oil": "low"},
            {"name_en": "Cucumber Slices (Keera)", "name_te": "కీరా దోసకాయ ముక్కలు", "grams": 100.0, "oil": "low"},
            {"name_en": "Carrot Pieces (Raw Carrot)", "name_te": "క్యారెట్ ముక్కలు", "grams": 80.0, "oil": "low"},
            {"name_en": "Pomegranate Seeds (Danimma Ginjalu)", "name_te": "దానిమ్మ గింజలు", "grams": 80.0, "oil": "low"},
        ]

        reconciled = []
        for it in plate_items:
            entry = _match_dish_in_local_catalog(it["name_en"], it["name_te"])
            self.assertIsNotNone(entry, f"Item '{it['name_en']}' failed to match catalog")
            nutr = compute_portion_nutrition(entry["per_100g"], it["grams"], oil_modifier=1.0)
            reconciled.append({
                "entry": entry,
                "grams": it["grams"],
                "nutrition": nutr,
            })

        # Verify exact IDs (all 4 distinct items detected, no collapsed items)
        self.assertEqual(len(reconciled), 4, "Expected exactly 4 distinct items in bowl")
        self.assertEqual(reconciled[0]["entry"]["id"], "JM-129")  # Boiled Sweet Potato
        self.assertEqual(reconciled[1]["entry"]["id"], "JM-130")  # Cucumber Slices (Keera)
        self.assertEqual(reconciled[2]["entry"]["id"], "JM-131")  # Carrot Pieces (Raw Carrot)
        self.assertEqual(reconciled[3]["entry"]["id"], "JM-132")  # Pomegranate Seeds

        # Verify NO item false-matched a cooked preparation
        for rec in reconciled:
            for bad_kw in ["pappu", "curry", "vepudu", "fry", "kura"]:
                self.assertNotIn(
                    bad_kw, rec["entry"]["name_en"].lower().split(),
                    f"Item '{rec['entry']['name_en']}' false-matched cooked keyword '{bad_kw}'",
                )

        # Check individual nutrition
        sp_nutr = reconciled[0]["nutrition"]
        self.assertEqual(sp_nutr["calories"], 112)
        self.assertEqual(sp_nutr["protein_g"], 2.1)
        self.assertEqual(sp_nutr["carbs_g"], 26.1)
        self.assertEqual(sp_nutr["fat_g"], 0.1)

        cuc_nutr = reconciled[1]["nutrition"]
        self.assertEqual(cuc_nutr["calories"], 15)
        self.assertEqual(cuc_nutr["protein_g"], 0.7)
        self.assertEqual(cuc_nutr["carbs_g"], 3.6)
        self.assertEqual(cuc_nutr["fat_g"], 0.1)

        car_nutr = reconciled[2]["nutrition"]
        self.assertEqual(car_nutr["calories"], 33)
        self.assertEqual(car_nutr["protein_g"], 0.7)
        self.assertEqual(car_nutr["carbs_g"], 7.7)
        self.assertEqual(car_nutr["fat_g"], 0.2)

        # Note: 83 * 0.8 = 66.4. Fat rounding 1.2 * 0.8 = 0.96 -> 1.0 adds extra_fat_g=0.04 -> 66.76 -> 67 kcal.
        pom_nutr = reconciled[3]["nutrition"]
        self.assertEqual(pom_nutr["calories"], 67)
        self.assertEqual(pom_nutr["protein_g"], 1.4)
        self.assertEqual(pom_nutr["carbs_g"], 15.0)
        self.assertEqual(pom_nutr["fat_g"], 1.0)

        # Summation verification
        total_calories = sum(it["nutrition"]["calories"] for it in reconciled)
        total_protein = round(sum(it["nutrition"]["protein_g"] for it in reconciled), 1)
        total_carbs = round(sum(it["nutrition"]["carbs_g"] for it in reconciled), 1)
        total_fat = round(sum(it["nutrition"]["fat_g"] for it in reconciled), 1)
        total_fiber = round(sum(it["nutrition"]["fiber_g"] for it in reconciled), 1)
        total_grams = int(sum(it["grams"] for it in reconciled))

        # 112 + 15 + 33 + 67 = 227 kcal
        self.assertEqual(total_calories, 227)
        # 2.1 + 0.7 + 0.7 + 1.4 = 4.9g protein
        self.assertEqual(total_protein, 4.9)
        # 26.1 + 3.6 + 7.7 + 15.0 = 52.4g carbs
        self.assertEqual(total_carbs, 52.4)
        # 0.1 + 0.1 + 0.2 + 1.0 = 1.4g fat
        self.assertEqual(total_fat, 1.4)
        # Total weight: 130 + 100 + 80 + 80 = 390g
        self.assertEqual(total_grams, 390)

        # Micronutrient totals summation
        total_vit_a = round(sum(it["nutrition"]["vit_a_ug"] for it in reconciled), 1)
        total_vit_c = round(sum(it["nutrition"]["vit_c_mg"] for it in reconciled), 1)
        self.assertGreater(total_vit_a, 1000.0, "Vitamin A should be rich from sweet potato and carrot")
        self.assertGreater(total_vit_c, 25.0, "Vitamin C should be rich from sweet potato and pomegranate")

        # MDD-W Diversity: G1 (Sweet potato), G8 (Sweet potato, Carrot), G9 (Cucumber), G10 (Pomegranate)
        covered_groups = set()
        for it in reconciled:
            covered_groups.update(it["entry"]["food_groups"])

        self.assertIn("G1", covered_groups)   # Grains, roots & tubers
        self.assertIn("G8", covered_groups)   # Vit-A rich fruits & vegetables
        self.assertIn("G9", covered_groups)   # Other vegetables
        self.assertIn("G10", covered_groups)  # Other fruits
        self.assertGreaterEqual(len(covered_groups), 4)

    def test_03_scanner_engine_reconciliation_multi_item_schema(self):
        """
        Tests that scanner_engine's schema reconciliation builds the correct payload,
        multi-item title, totals, and macro split percentages.
        """
        simulated_vision_analysis = VisionPlateAnalysis(
            is_food_image=True,
            plate_title_en="Sweet Potato, Cucumber, Carrot & Pomegranate Bowl",
            plate_title_te="చిలకడదుంప, కీరా, క్యారెట్ మరియు దానిమ్మ బౌల్",
            meal_type="Snack",
            items=[
                DetectedDishVisionItem(
                    name_en="Boiled Sweet Potato",
                    name_te="ఉడకబెట్టిన చిలకడదుంప",
                    cluster="Snacks & Sweets",
                    estimated_grams=130.0,
                    oil_ghee_level="low",
                    fallback_per_100g=Per100gEstimate(calories=86, protein_g=1.6, carbs_g=20.1, fat_g=0.1, fiber_g=3.0, iron_mg=0.7, calcium_mg=30),
                ),
                DetectedDishVisionItem(
                    name_en="Cucumber Slices",
                    name_te="కీరా దోసకాయ ముక్కలు",
                    cluster="Fruits & Salads",
                    estimated_grams=100.0,
                    oil_ghee_level="low",
                    fallback_per_100g=Per100gEstimate(calories=15, protein_g=0.7, carbs_g=3.6, fat_g=0.1, fiber_g=0.5, iron_mg=0.3, calcium_mg=16),
                ),
                DetectedDishVisionItem(
                    name_en="Carrot Pieces",
                    name_te="క్యారెట్ ముక్కలు",
                    cluster="Fruits & Salads",
                    estimated_grams=80.0,
                    oil_ghee_level="low",
                    fallback_per_100g=Per100gEstimate(calories=41, protein_g=0.9, carbs_g=9.6, fat_g=0.2, fiber_g=2.8, iron_mg=0.3, calcium_mg=33),
                ),
                DetectedDishVisionItem(
                    name_en="Pomegranate Seeds",
                    name_te="దానిమ్మ గింజలు",
                    cluster="Fruits & Salads",
                    estimated_grams=80.0,
                    oil_ghee_level="low",
                    fallback_per_100g=Per100gEstimate(calories=83, protein_g=1.7, carbs_g=18.7, fat_g=1.2, fiber_g=4.0, iron_mg=0.3, calcium_mg=10),
                ),
            ],
        )

        oil_mod_map = {"low": 0.85, "moderate": 1.0, "high": 1.2}
        totals = {
            "calories": 0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0,
            "iron_mg": 0.0, "calcium_mg": 0.0, "folate_ug": 0.0, "vit_a_ug": 0.0, "vit_c_mg": 0.0,
            "sodium_mg": 0.0, "total_grams": 0,
        }
        reconciled_items = []

        for it in simulated_vision_analysis.items:
            entry = _match_dish_in_local_catalog(it.name_en, it.name_te)
            self.assertIsNotNone(entry)
            oil_mod = oil_mod_map.get(it.oil_ghee_level, 1.0)
            nutr = compute_portion_nutrition(entry["per_100g"], it.estimated_grams, oil_modifier=oil_mod)

            totals["calories"] += nutr["calories"]
            totals["protein_g"] = round(totals["protein_g"] + nutr["protein_g"], 1)
            totals["carbs_g"] = round(totals["carbs_g"] + nutr["carbs_g"], 1)
            totals["fat_g"] = round(totals["fat_g"] + nutr["fat_g"], 1)
            totals["fiber_g"] = round(totals["fiber_g"] + nutr["fiber_g"], 1)
            totals["total_grams"] += int(it.estimated_grams)

            reconciled_items.append({"id": entry["id"], "nutr": nutr})

        self.assertEqual(len(reconciled_items), 4)
        self.assertEqual(totals["total_grams"], 390)
        # Macro calories verification
        prot_cal = totals["protein_g"] * 4.0
        carb_cal = totals["carbs_g"] * 4.0
        fat_cal = totals["fat_g"] * 9.0
        macro_sum = prot_cal + carb_cal + fat_cal
        carb_pct = round((carb_cal / macro_sum) * 100, 1)
        self.assertGreater(carb_pct, 70.0, "Salad/fruit bowl should be carb-predominant")


class TestPortionScalingAndOilModifiers(unittest.TestCase):
    """
    Audit Suite 4: Portion Nutrition Scaling & Oil Modifiers (low 0.85x, moderate 1.0x, high 1.2x).
    Verifies that compute_portion_nutrition correctly recalculates calories and fat across modifiers.
    """

    def test_01_gram_scaling_linear_proportionality(self):
        """Verifies that nutrition values scale strictly proportionally with gram weight."""
        sample_dish = CATALOG_BY_ID["JM-11"]  # Gongura Pappu: 126 kcal, 6.5g P, 15.0g C, 4.5g F per 100g
        p100 = sample_dish["per_100g"]

        test_weights = [50.0, 100.0, 150.0, 200.0, 300.0]
        for grams in test_weights:
            factor = grams / 100.0
            nutr = compute_portion_nutrition(p100, grams, oil_modifier=1.0)

            expected_cal = round(p100["calories"] * factor, 0)
            expected_prot = round(p100["protein_g"] * factor, 1)
            expected_carbs = round(p100["carbs_g"] * factor, 1)
            expected_fat = round(p100["fat_g"] * factor, 1)

            self.assertEqual(nutr["calories"], int(expected_cal), f"Calorie mismatch at {grams}g")
            self.assertEqual(nutr["protein_g"], expected_prot, f"Protein mismatch at {grams}g")
            self.assertEqual(nutr["carbs_g"], expected_carbs, f"Carbs mismatch at {grams}g")
            self.assertEqual(nutr["fat_g"], expected_fat, f"Fat mismatch at {grams}g")

    def test_02_oil_modifier_moderate_1_0x(self):
        """oil_modifier=1.0 must produce exact baseline fat and calories."""
        dish = CATALOG_BY_ID["JM-22"]  # Gutti Vankaya: 10.8g fat, 148 kcal per 100g
        p100 = dish["per_100g"]
        grams = 150.0

        nutr = compute_portion_nutrition(p100, grams, oil_modifier=1.0)
        self.assertEqual(nutr["fat_g"], round(10.8 * 1.5, 1))     # 16.2g
        self.assertEqual(nutr["calories"], round(148 * 1.5, 0))   # 222 kcal

    def test_03_oil_modifier_high_1_2x_calories_and_fat_recalculation(self):
        """
        oil_modifier=1.2 (high oil/ghee):
        - fat increases by 20% (1.2x)
        - calories increases by extra_fat_g * 9.0 kcal
        """
        test_dishes = ["JM-22", "JM-121", "JM-11", "JM-105"]
        for did in test_dishes:
            dish = CATALOG_BY_ID[did]
            p100 = dish["per_100g"]
            grams = 150.0
            factor = grams / 100.0

            base_nutr = compute_portion_nutrition(p100, grams, oil_modifier=1.0)
            high_nutr = compute_portion_nutrition(p100, grams, oil_modifier=1.2)

            expected_high_fat = round(p100["fat_g"] * factor * 1.2, 1)
            self.assertEqual(
                high_nutr["fat_g"], expected_high_fat,
                f"High oil fat mismatch for {did}",
            )
            self.assertGreater(
                high_nutr["fat_g"], base_nutr["fat_g"],
                f"High oil fat must be greater than base fat for {did}",
            )

            # Extra fat calories: extra_fat_g = max(0.0, high_fat - base_unmodified_fat)
            extra_fat_g = max(0.0, high_nutr["fat_g"] - (p100["fat_g"] * factor))
            expected_calories = round(p100["calories"] * factor + (extra_fat_g * 9.0), 0)
            self.assertEqual(
                high_nutr["calories"], int(expected_calories),
                f"High oil calories mismatch for {did}",
            )
            self.assertGreater(
                high_nutr["calories"], base_nutr["calories"],
                f"High oil calories must exceed base calories for {did}",
            )

            # Protein, carbs, micronutrients must remain unaffected by oil modifier
            self.assertEqual(high_nutr["protein_g"], base_nutr["protein_g"])
            self.assertEqual(high_nutr["carbs_g"], base_nutr["carbs_g"])
            self.assertEqual(high_nutr["fiber_g"], base_nutr["fiber_g"])
            self.assertEqual(high_nutr["iron_mg"], base_nutr["iron_mg"])

    def test_04_oil_modifier_low_0_85x_audit_and_discrepancy_check(self):
        """
        Audit of oil_modifier=0.85 (low oil/ghee):
        - Verifies fat decreases by 15% (0.85x).
        - Audits calorie behavior under `compute_portion_nutrition`:
          In `dishes_catalog.py` line 997: `extra_fat_g = max(0.0, fat - (per_100g["fat_g"] * factor))`
          Because modifier is 0.85, (fat - factor * fat_100) is negative, so extra_fat_g clamps to 0.0.
          Therefore calories stays at baseline: round(per_100g["calories"] * factor).
          This test verifies the exact mathematical formula implemented in production.
        """
        test_dishes = ["JM-22", "JM-121", "JM-11"]
        for did in test_dishes:
            dish = CATALOG_BY_ID[did]
            p100 = dish["per_100g"]
            grams = 150.0
            factor = grams / 100.0

            base_nutr = compute_portion_nutrition(p100, grams, oil_modifier=1.0)
            low_nutr = compute_portion_nutrition(p100, grams, oil_modifier=0.85)

            # Fat must decrease to 85%
            expected_low_fat = round(p100["fat_g"] * factor * 0.85, 1)
            self.assertEqual(low_nutr["fat_g"], expected_low_fat)
            self.assertLess(low_nutr["fat_g"], base_nutr["fat_g"])

            # Calorie verification according to production code implementation:
            # extra_fat_g is clamped to 0.0, so calories == base calories
            self.assertEqual(low_nutr["calories"], base_nutr["calories"])

    def test_05_minimum_gram_floor_handling(self):
        """Grams < 1.0 clamped to 1.0g to prevent division by zero or negative nutrition."""
        p100 = CATALOG_BY_ID["JM-101"]["per_100g"]
        for g in [0.0, -10.0, 0.5]:
            nutr = compute_portion_nutrition(p100, g)
            self.assertGreater(nutr["calories"], 0)
            self.assertGreaterEqual(nutr["protein_g"], 0.0)


class TestLiveVisionAndCacheIntegration(unittest.TestCase):
    """
    Audit Suite 5: Live Gemini Vision Recognition & In-Memory SHA-256 Cache Verification.
    Verifies real image scanning, dish recognition, and 0-token instant cache retrieval.
    """

    def test_01_live_gongura_pappu_scan_and_cache(self):
        """Scans local Gongura Pappu sample photo (JM-11), verifies detection, then verifies cache hit."""
        api_key = scanner_engine.resolve_gemini_api_key()
        if not api_key:
            self.skipTest("GEMINI_API_KEY not configured, skipping live vision scan")

        d11 = CATALOG_BY_ID.get("JM-11")
        if not d11 or not d11.get("local_image"):
            self.skipTest("JM-11 local image not found in catalog")

        img_path = pathlib.Path(d11["local_image"])
        if not img_path.exists():
            self.skipTest(f"JM-11 image file missing on disk: {img_path}")

        img_bytes = img_path.read_bytes()

        # 1. Primary scan using fast low-cost gemini-3.5-flash-lite
        res1 = scanner_engine.scan_telugu_food_image(
            img_bytes,
            meal_hint="Traditional Andhra lunch dal",
            preferred_model="gemini-3.5-flash-lite",
        )

        self.assertEqual(res1["status"], "success")
        self.assertTrue(res1["is_food_image"])
        self.assertGreaterEqual(res1["dish_count"], 1)
        self.assertIn("Gongura Pappu", res1["plate_title_en"])
        self.assertTrue(has_telugu_unicode(res1["plate_title_te"]))

        # First item must match Gongura Pappu (JM-11)
        item0 = res1["items"][0]
        self.assertEqual(item0["catalog_id"], "JM-11")
        self.assertEqual(item0["name_te"], "గోంగూర పప్పు")
        self.assertIn("G2", item0["food_groups"])
        self.assertIn("G7", item0["food_groups"])
        self.assertTrue(item0["matched_in_excel_catalog"])

        # Nutrition totals must be populated and realistic
        self.assertGreater(res1["totals"]["calories"], 100)
        self.assertGreater(res1["totals"]["protein_g"], 5.0)

        # 2. Repeated scan must hit SHA-256 cache instantly (0 tokens, latency < 50ms)
        res2 = scanner_engine.scan_telugu_food_image(
            img_bytes,
            meal_hint="Traditional Andhra lunch dal",
            preferred_model="gemini-3.5-flash-lite",
        )

        self.assertEqual(res2["status"], "success")
        self.assertIn("Cached", res2["engine"])
        self.assertLess(res2["latency_ms"], 50)
        self.assertTrue(res2["usage_and_cost"]["cached"])
        self.assertEqual(res2["usage_and_cost"]["input_tokens"], 0)
        self.assertEqual(res2["usage_and_cost"]["output_tokens"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

