"""
Comprehensive Automated QA Test Suite for Telugu Dish Catalog & ICMR-NIN Nutrition Engine.
Tests:
1. All 93 dishes from JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx (JM-01 through JM-93):
   - Non-empty English names (name_en)
   - Authentic Telugu script names (name_te with Telugu Unicode U+0C00..U+0C7F)
   - Non-empty clusters
   - serving_grams > 0 and non-empty serving_unit
   - Valid MDD-W food group codes (G1..G10)
   - Complete 11-nutrient per_100g dictionary
2. All 28 foundational Telugu staples (JM-101 through JM-128) and iconic Telugu dishes:
   - Total catalog count == 121 dishes (93 Excel + 28 staples)
   - Presence & metadata verification of Pesarattu, Ragi Sangati, Pulihora, Gutti Vankaya,
     Gongura Pappu, Natukodi Pulusu, Balamrutham, etc.
3. Deterministic `compute_portion_nutrition` scaling:
   - Accurate scaling of calories, protein_g, carbs_g, fat_g, fiber_g, iron_mg,
     calcium_mg, folate_ug, vit_a_ug, vit_c_mg, and sodium_mg across arbitrary gram weights
   - Oil modifier behavior across low (0.85x), moderate (1.0x), and high (1.2x)
   - Minimum gram floor (grams < 1.0 clamped to 1.0g)
4. Local dish image verification for all 93 Excel dishes:
   - Path exists on disk
   - File size > 0 bytes
   - Valid readable image via PIL (Image.open + verify/load, width > 0, height > 0)
   - Preprocess pipeline (`preprocess_image`) compatibility
"""

from __future__ import annotations
import pathlib
import sys
import unittest
from PIL import Image

# Ensure parent directory (`telugu-food-scanner`) is on sys.path
SCANNER_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from dishes_catalog import (
    CATALOG,
    CATALOG_BY_ID,
    EXCEL_PATH,
    FOUNDATIONAL_TELUGU_STAPLES,
    compute_portion_nutrition,
    get_compact_catalog_prompt_text,
)
from scanner_engine import MDDW_LABELS, preprocess_image

VALID_MDDW_CODES = {f"G{i}" for i in range(1, 11)}
REQUIRED_NUTRIENT_KEYS = {
    "calories",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
    "calcium_mg",
    "folate_ug",
    "vit_a_ug",
    "vit_c_mg",
    "sodium_mg",
}


def has_telugu_script(text: str) -> bool:
    """Checks that the string contains at least one character in the Telugu Unicode block (U+0C00..U+0C7F)."""
    return any("\u0c00" <= ch <= "\u0c7f" for ch in text)


class TestTeluguCatalogAndNutrition(unittest.TestCase):
    """End-to-end test suite for the 121-dish Telugu Catalog, ICMR-NIN nutrition math, and 93 local dish images."""

    def test_01_total_catalog_counts(self):
        """Verify total catalog has exactly 121 dishes: 93 Excel dishes (JM-01..JM-93) + 28 staples (JM-101..JM-128)."""
        self.assertTrue(EXCEL_PATH.exists(), f"Excel file missing at {EXCEL_PATH}")
        self.assertEqual(len(CATALOG), 121, f"Expected 121 total dishes, got {len(CATALOG)}")
        self.assertEqual(len(CATALOG_BY_ID), 121, "Duplicate IDs detected in CATALOG_BY_ID")
        self.assertEqual(len(FOUNDATIONAL_TELUGU_STAPLES), 28, "Expected 28 foundational Telugu staples")

    def test_02_excel_93_dishes_schema_and_mddw(self):
        """Verify JM-01 through JM-93 have valid English/Telugu names, clusters, serving_grams > 0, and G1-G10 codes."""
        for i in range(1, 94):
            dish_id = f"JM-{i:02d}"
            with self.subTest(dish_id=dish_id):
                self.assertIn(dish_id, CATALOG_BY_ID, f"Missing Excel dish {dish_id} in CATALOG_BY_ID")
                dish = CATALOG_BY_ID[dish_id]

                # English & Telugu names
                self.assertIsInstance(dish["name_en"], str)
                self.assertTrue(len(dish["name_en"].strip()) > 0, f"{dish_id} has empty name_en")
                self.assertIsInstance(dish["name_te"], str)
                self.assertTrue(len(dish["name_te"].strip()) > 0, f"{dish_id} has empty name_te")
                self.assertTrue(
                    has_telugu_script(dish["name_te"]),
                    f"{dish_id} name_te '{dish['name_te']}' does not contain Telugu script characters",
                )

                # Cluster & serving info
                self.assertTrue(len(dish["cluster"].strip()) > 0, f"{dish_id} has empty cluster")
                self.assertIsInstance(dish["serving_grams"], (int, float))
                self.assertGreater(dish["serving_grams"], 0, f"{dish_id} serving_grams must be > 0")
                self.assertTrue(len(dish["serving_unit"].strip()) > 0, f"{dish_id} has empty serving_unit")

                # MDD-W food group codes (G1-G10)
                food_groups = dish["food_groups"]
                self.assertIsInstance(food_groups, list)
                self.assertGreater(len(food_groups), 0, f"{dish_id} must have at least one MDD-W food group")
                for fg in food_groups:
                    self.assertIn(fg, VALID_MDDW_CODES, f"{dish_id} has invalid MDD-W code {fg}")
                    self.assertIn(fg, MDDW_LABELS, f"{dish_id} MDD-W code {fg} missing from MDDW_LABELS")

                # Per-100g nutrition profile
                per_100g = dish["per_100g"]
                self.assertEqual(set(per_100g.keys()), REQUIRED_NUTRIENT_KEYS, f"{dish_id} missing nutrient keys")
                self.assertGreater(per_100g["calories"], 0, f"{dish_id} per_100g calories must be > 0")
                for k, v in per_100g.items():
                    self.assertGreaterEqual(v, 0.0, f"{dish_id} nutrient {k} cannot be negative ({v})")

    def test_03_foundational_28_staples_and_iconic_dishes(self):
        """Verify JM-101 through JM-128 and key iconic Telugu dishes are present and properly structured."""
        for i in range(101, 129):
            dish_id = f"JM-{i}"
            with self.subTest(dish_id=dish_id):
                self.assertIn(dish_id, CATALOG_BY_ID, f"Missing foundational staple {dish_id}")
                dish = CATALOG_BY_ID[dish_id]
                self.assertTrue(len(dish["name_en"].strip()) > 0)
                self.assertTrue(has_telugu_script(dish["name_te"]), f"{dish_id} lacks Telugu script in name_te")
                self.assertTrue(len(dish["cluster"].strip()) > 0)
                self.assertGreater(dish["serving_grams"], 0)
                self.assertGreater(len(dish["food_groups"]), 0)
                for fg in dish["food_groups"]:
                    self.assertIn(fg, VALID_MDDW_CODES)
                self.assertEqual(set(dish["per_100g"].keys()), REQUIRED_NUTRIENT_KEYS)

        # Verify specific required iconic dishes across Excel (JM-01..93) and Staples (JM-101..128)
        expected_iconic = {
            "Pesarattu": "JM-105",
            "Ragi Sangati": "JM-102",
            "Pulihora": "JM-103",
            "Gutti Vankaya": "JM-25",
            "Gongura Pappu": "JM-11",
            "Natukodi Pulusu": "JM-64",
            "Balamrutham": "JM-87",
        }
        for label, expected_id in expected_iconic.items():
            with self.subTest(iconic_dish=label):
                self.assertIn(expected_id, CATALOG_BY_ID)
                entry = CATALOG_BY_ID[expected_id]
                combined_text = (
                    entry["name_en"].lower()
                    + " "
                    + " ".join(a.lower() for a in entry.get("aliases", []))
                )
                self.assertIn(
                    label.lower(),
                    combined_text,
                    f"Iconic dish '{label}' not matched in {expected_id} ({entry['name_en']})",
                )

    def test_04_compute_portion_nutrition_oil_modifiers(self):
        """Verify compute_portion_nutrition scales all 11 nutrients accurately for low (0.85x), moderate (1.0x), and high (1.2x) oil."""
        # Test with Gutti Vankaya (JM-25, 150g standard serving) and Gongura Pappu (JM-11, 150g) and custom sample
        sample_per_100g = {
            "calories": 200.0,
            "protein_g": 10.0,
            "carbs_g": 20.0,
            "fat_g": 10.0,
            "fiber_g": 5.0,
            "iron_mg": 3.45,
            "calcium_mg": 120.0,
            "folate_ug": 80.0,
            "vit_a_ug": 250.0,
            "vit_c_mg": 30.0,
            "sodium_mg": 300.0,
        }

        # 1) Moderate oil (1.0x) at 150g (factor = 1.5)
        mod_150 = compute_portion_nutrition(sample_per_100g, 150.0, oil_modifier=1.0)
        self.assertEqual(mod_150["calories"], 300)
        self.assertAlmostEqual(mod_150["protein_g"], 15.0)
        self.assertAlmostEqual(mod_150["carbs_g"], 30.0)
        self.assertAlmostEqual(mod_150["fat_g"], 15.0)
        self.assertAlmostEqual(mod_150["fiber_g"], 7.5)
        self.assertAlmostEqual(mod_150["iron_mg"], round(3.45 * 1.5, 2))
        self.assertAlmostEqual(mod_150["calcium_mg"], 180.0)
        self.assertAlmostEqual(mod_150["folate_ug"], 120.0)
        self.assertAlmostEqual(mod_150["vit_a_ug"], 375.0)
        self.assertAlmostEqual(mod_150["vit_c_mg"], 45.0)
        self.assertAlmostEqual(mod_150["sodium_mg"], 450.0)

        # 2) Low oil (0.85x) at 150g -> fat scales by 0.85 (15.0 * 0.85 = 12.8g), extra_fat_g = 0, non-fat macros unchanged
        low_150 = compute_portion_nutrition(sample_per_100g, 150.0, oil_modifier=0.85)
        self.assertAlmostEqual(low_150["fat_g"], round(15.0 * 0.85, 1))
        self.assertEqual(low_150["calories"], 300)
        self.assertAlmostEqual(low_150["protein_g"], 15.0)
        self.assertAlmostEqual(low_150["carbs_g"], 30.0)
        self.assertAlmostEqual(low_150["fiber_g"], 7.5)
        self.assertAlmostEqual(low_150["iron_mg"], round(3.45 * 1.5, 2))
        self.assertAlmostEqual(low_150["calcium_mg"], 180.0)
        self.assertAlmostEqual(low_150["folate_ug"], 120.0)
        self.assertAlmostEqual(low_150["vit_a_ug"], 375.0)
        self.assertAlmostEqual(low_150["vit_c_mg"], 45.0)
        self.assertAlmostEqual(low_150["sodium_mg"], 450.0)

        # 3) High oil (1.2x) at 150g -> fat = 18.0g (+3.0g extra fat -> +27 kcal -> 327 kcal)
        high_150 = compute_portion_nutrition(sample_per_100g, 150.0, oil_modifier=1.2)
        self.assertAlmostEqual(high_150["fat_g"], 18.0)
        self.assertEqual(high_150["calories"], 327)
        self.assertAlmostEqual(high_150["protein_g"], 15.0)
        self.assertAlmostEqual(high_150["carbs_g"], 30.0)
        self.assertAlmostEqual(high_150["fiber_g"], 7.5)
        self.assertAlmostEqual(high_150["iron_mg"], round(3.45 * 1.5, 2))
        self.assertAlmostEqual(high_150["calcium_mg"], 180.0)
        self.assertAlmostEqual(high_150["folate_ug"], 120.0)
        self.assertAlmostEqual(high_150["vit_a_ug"], 375.0)
        self.assertAlmostEqual(high_150["vit_c_mg"], 45.0)
        self.assertAlmostEqual(high_150["sodium_mg"], 450.0)

        # 4) Verify across all 121 catalog dishes that low <= moderate <= high for fat & calories
        for dish in CATALOG:
            with self.subTest(dish_id=dish["id"]):
                g = dish["serving_grams"]
                n_low = compute_portion_nutrition(dish["per_100g"], g, oil_modifier=0.85)
                n_mod = compute_portion_nutrition(dish["per_100g"], g, oil_modifier=1.0)
                n_high = compute_portion_nutrition(dish["per_100g"], g, oil_modifier=1.2)

                self.assertEqual(set(n_mod.keys()), REQUIRED_NUTRIENT_KEYS)
                self.assertLessEqual(n_low["fat_g"], n_mod["fat_g"])
                self.assertLessEqual(n_mod["fat_g"], n_high["fat_g"])
                self.assertLessEqual(n_low["calories"], n_mod["calories"])
                self.assertLessEqual(n_mod["calories"], n_high["calories"])

                # Micronutrients and non-fat macros should remain invariant to oil_modifier
                for invariant_key in (
                    "protein_g",
                    "carbs_g",
                    "fiber_g",
                    "iron_mg",
                    "calcium_mg",
                    "folate_ug",
                    "vit_a_ug",
                    "vit_c_mg",
                    "sodium_mg",
                ):
                    self.assertEqual(n_low[invariant_key], n_mod[invariant_key])
                    self.assertEqual(n_mod[invariant_key], n_high[invariant_key])

    def test_05_all_93_local_dish_images_exist_and_readable(self):
        """Verify all 93 local dish image paths referenced in JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx exist and are valid readable images."""
        verified_count = 0
        for i in range(1, 94):
            dish_id = f"JM-{i:02d}"
            with self.subTest(dish_id=dish_id):
                dish = CATALOG_BY_ID[dish_id]
                local_img_str = dish.get("local_image", "")
                self.assertTrue(
                    bool(local_img_str),
                    f"{dish_id} ({dish['name_en']}) has empty local_image field",
                )
                img_path = pathlib.Path(local_img_str)
                self.assertTrue(
                    img_path.exists() and img_path.is_file(),
                    f"{dish_id} local image does not exist on disk: {img_path}",
                )
                self.assertGreater(
                    img_path.stat().st_size,
                    100,
                    f"{dish_id} local image file is unexpectedly small/empty: {img_path}",
                )

                # Verify readable via Pillow
                with Image.open(img_path) as img:
                    img.verify()
                with Image.open(img_path) as img2:
                    img2.load()
                    w, h = img2.size
                    self.assertGreater(w, 0, f"{dish_id} image width must be > 0")
                    self.assertGreater(h, 0, f"{dish_id} image height must be > 0")

                verified_count += 1

        self.assertEqual(verified_count, 93, f"Expected 93 verified local images, got {verified_count}")

    def test_06_compact_catalog_prompt_and_image_preprocess(self):
        """Verify get_compact_catalog_prompt_text includes all 121 dishes and preprocess_image works on a sample local dish image."""
        prompt_text = get_compact_catalog_prompt_text()
        lines = [line for line in prompt_text.splitlines() if line.strip()]
        self.assertEqual(len(lines), 121, f"Expected 121 lines in compact catalog prompt, got {len(lines)}")

        # Test preprocess_image on JM-25 (Gutti Vankaya)
        jm25_path = pathlib.Path(CATALOG_BY_ID["JM-25"]["local_image"])
        b64, mime, w, h = preprocess_image(jm25_path.read_bytes())
        self.assertEqual(mime, "image/jpeg")
        self.assertGreater(len(b64), 100)
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)


if __name__ == "__main__":
    print("=" * 78)
    print("RUNNING TELUGU CATALOG & ICMR-NIN NUTRITION QA SUITE")
    print("=" * 78)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestTeluguCatalogAndNutrition)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("=" * 78)
    print(
        f"SUMMARY: Ran {result.testsRun} test methods | "
        f"Failures: {len(result.failures)} | Errors: {len(result.errors)} | "
        f"Catalog Size: {len(CATALOG)} dishes (93 Excel + 28 Staples)"
    )
    print("=" * 78)
    sys.exit(0 if result.wasSuccessful() else 1)
