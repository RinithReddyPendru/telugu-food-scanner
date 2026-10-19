import os
import sys
import shutil
import json
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(r"c:\Users\rinit\.gemini\antigravity\playground\shadow-ionosphere\telugu-food-scanner")
BENCHMARK_DIR = BASE_DIR / "tests" / "benchmark_100"
IMAGES_DIR = BENCHMARK_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

SRC1_DIR = Path(r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\AP_50_Dish_Images\All_50_Dishes")
SRC2_DIR = Path(r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\AP_Dish_Images\All_70_New_Dishes")
WEB1_DIR = BASE_DIR / "tests" / "web_harvest_agent1" / "images"
WEB2_DIR = BASE_DIR / "tests" / "web_harvest_agent2" / "images"
DL_DIR = BENCHMARK_DIR / "downloaded"

# Definition of all 100 items
# Each item: {
#   "test_num": 1..100,
#   "src_path": Path,
#   "dest_filename": str,
#   "expected_dish_name": str,
#   "expected_dish_te": str,
#   "expected_cluster": str,
#   "macro_category": str, # For report: Leafy Greens, Dals, Curries, Non-Veg, Tiffins/Rice, Salads/Staples, Sweets/Snacks
#   "is_raw_salad": bool,
#   "serving_grams": int,
#   "per_100g_cal": float,
#   "per_100g_prot": float,
#   "key_ingredients": list[str]
# }

ITEMS = []

# --- Source 1: Dishes 1 to 50 ---
s1_specs = [
    # 01
    (SRC1_DIR / "01_Thotakura_Vepudu_Kura.jpg", "001_Thotakura_Vepudu.jpg",
     "Thotakura Vepudu (Amaranth Leaves Stir Fry)", "తోటకూర వేపుడు", "Leafy Green Curries", "Leafy Greens", False,
     120, 92, 3.6, ["thotakura", "amaranth", "vepudu", "leafy"]),
    # 02
    (SRC1_DIR / "02_Palakura_Kura_Vepudu.jpg", "002_Palakura_Vepudu.jpg",
     "Palakura Vepudu / Kura (Spinach Stir Fry)", "పాలకూర వేపుడు / కూర", "Leafy Green Curries", "Leafy Greens", False,
     120, 86, 2.9, ["palakura", "spinach", "vepudu", "kura"]),
    # 03
    (SRC1_DIR / "03_Gongura_Kura_Pulusu.jpg", "003_Gongura_Pulusu.jpg",
     "Gongura Pulusu / Kura (Sorrel Leaves Stew)", "గోంగూర పులుసు / కూర", "Leafy Green Curries", "Leafy Greens", False,
     120, 108, 2.4, ["gongura", "sorrel", "pulusu", "leaves"]),
    # 04
    (SRC1_DIR / "04_Menthi_Kura_Vepudu_Kura.jpg", "004_Menthi_Kura_Vepudu.jpg",
     "Menthi Kura Vepudu (Fenugreek Leaves Stir Fry)", "మెంతికూర వేపుడు", "Leafy Green Curries", "Leafy Greens", False,
     120, 96, 4.1, ["menthi", "fenugreek", "vepudu", "menthikura"]),
    # 05
    (SRC1_DIR / "05_Munagaku_Vepudu_Kura.jpg", "005_Munagaku_Vepudu.jpg",
     "Munagaku Vepudu (Moringa / Drumstick Leaves Stir Fry)", "మునగాకు వేపుడు", "Leafy Green Curries", "Leafy Greens", False,
     100, 112, 6.2, ["munagaku", "moringa", "drumstick leaves", "vepudu"]),
    # 06
    (SRC1_DIR / "06_Palakura_Pappu.jpg", "006_Palakura_Pappu.jpg",
     "Palakura Pappu (Spinach Dal)", "పాలకూర పప్పు", "Dals & Pappu", "Dals", False,
     150, 118, 6.4, ["palakura", "spinach", "pappu", "dal", "toor dal"]),
    # 07
    (SRC1_DIR / "07_Thotakura_Pappu.jpg", "007_Thotakura_Pappu.jpg",
     "Thotakura Pappu (Amaranth Dal)", "తోటకూర పప్పు", "Dals & Pappu", "Dals", False,
     150, 122, 6.8, ["thotakura", "amaranth", "pappu", "dal"]),
    # 08
    (SRC1_DIR / "08_Gongura_Pappu.jpg", "008_Gongura_Pappu.jpg",
     "Gongura Pappu (Andhra Sorrel Leaves Dal)", "గోంగూర పప్పు", "Dals & Pappu", "Dals", False,
     150, 126, 6.5, ["gongura", "sorrel", "pappu", "andhra dal"]),
    # 09
    (SRC1_DIR / "09_Menthi_Kura_Pappu.jpg", "009_Menthi_Kura_Pappu.jpg",
     "Menthi Kura Pappu (Fenugreek Leaves Dal)", "మెంతికూర పప్పు", "Dals & Pappu", "Dals", False,
     150, 121, 6.9, ["menthi", "fenugreek", "pappu", "dal"]),
    # 10
    (SRC1_DIR / "10_Chukkakura_Pappu.jpg", "010_Chukkakura_Pappu.jpg",
     "Chukkakura Pappu (Green Sorrel Dal)", "చుక్కకూర పప్పు", "Dals & Pappu", "Dals", False,
     150, 119, 6.3, ["chukkakura", "green sorrel", "pappu", "dal"]),
    # 11
    (SRC1_DIR / "11_Dosakaya_Pappu.jpg", "011_Dosakaya_Pappu.jpg",
     "Dosakaya Pappu (Yellow Cucumber Dal)", "దోసకాయ పప్పు", "Dals & Pappu", "Dals", False,
     150, 114, 5.9, ["dosakaya", "yellow cucumber", "pappu", "dal"]),
    # 12
    (SRC1_DIR / "12_Sorakaya_Pappu.jpg", "012_Sorakaya_Pappu.jpg",
     "Sorakaya Pappu (Bottle Gourd Dal)", "సొరకాయ పప్పు", "Dals & Pappu", "Dals", False,
     150, 108, 5.6, ["sorakaya", "bottle gourd", "pappu", "dal"]),
    # 13
    (SRC1_DIR / "13_Mamidikaya_Pappu.jpg", "013_Mamidikaya_Pappu.jpg",
     "Mamidikaya Pappu (Raw Mango Dal)", "మామిడికాయ పప్పు", "Dals & Pappu", "Dals", False,
     150, 120, 6.0, ["mamidikaya", "raw mango", "mango", "pappu", "dal"]),
    # 14
    (SRC1_DIR / "14_Beerakaya_Pappu.jpg", "014_Beerakaya_Pappu.jpg",
     "Beerakaya Pappu (Ridge Gourd Dal)", "బీరకాయ పప్పు", "Dals & Pappu", "Dals", False,
     150, 110, 5.7, ["beerakaya", "ridge gourd", "pappu", "dal"]),
    # 15
    (SRC1_DIR / "15_Vankaya_Kura_Gutti_Vankaya.jpg", "015_Gutti_Vankaya_Kura.jpg",
     "Gutti Vankaya Kura (Stuffed Brinjal Curry)", "గుత్తి వంకాయ కూర", "Vegetable Curries", "Curries", False,
     150, 148, 3.8, ["vankaya", "gutti vankaya", "brinjal", "eggplant"]),
    # 16
    (SRC1_DIR / "16_Bendakaya_Vepudu_Pulusu.jpg", "016_Bendakaya_Vepudu.jpg",
     "Bendakaya Vepudu (Okra / Ladies Finger Fry)", "బెండకాయ వేపుడు", "Vegetable Curries", "Curries", False,
     130, 112, 2.4, ["bendakaya", "okra", "ladies finger", "vepudu"]),
    # 17
    (SRC1_DIR / "17_Bangaladumpa_Aloo_Vepudu.jpg", "017_Bangaladumpa_Aloo_Vepudu.jpg",
     "Bangaladumpa Vepudu (Spiced Potato Fry)", "బంగాళాదుంప వేపుడు", "Vegetable Curries", "Curries", False,
     140, 136, 2.2, ["bangaladumpa", "aloo", "potato", "vepudu"]),
    # 18
    (SRC1_DIR / "18_Dondakaya_Vepudu.jpg", "018_Dondakaya_Vepudu.jpg",
     "Dondakaya Vepudu (Ivy Gourd Stir Fry)", "దొండకాయ వేపుడు", "Vegetable Curries", "Curries", False,
     130, 104, 2.1, ["dondakaya", "ivy gourd", "tindora", "vepudu"]),
    # 19
    (SRC1_DIR / "19_Beerakaya_Kura.jpg", "019_Beerakaya_Kura.jpg",
     "Beerakaya Kura (Ridge Gourd Curry)", "బీరకాయ కూర", "Vegetable Curries", "Curries", False,
     140, 78, 1.8, ["beerakaya", "ridge gourd", "kura", "curry"]),
    # 20
    (SRC1_DIR / "20_Sorakaya_Anapakaya_Kura.jpg", "020_Sorakaya_Kura.jpg",
     "Sorakaya / Anapakaya Kura (Bottle Gourd Curry)", "సొరకాయ కూర", "Vegetable Curries", "Curries", False,
     150, 74, 1.6, ["sorakaya", "anapakaya", "bottle gourd", "kura"]),
    # 21
    (SRC1_DIR / "21_Kakarakaya_Vepudu_Pulusu.jpg", "021_Kakarakaya_Vepudu.jpg",
     "Kakarakaya Vepudu (Bitter Gourd Stir Fry)", "కాకరకాయ వేపుడు", "Vegetable Curries", "Curries", False,
     120, 118, 2.5, ["kakarakaya", "bitter gourd", "karela", "vepudu"]),
    # 22
    (SRC1_DIR / "22_Cabbage_Vepudu.jpg", "022_Cabbage_Vepudu.jpg",
     "Cabbage Vepudu (Cabbage Stir Fry)", "క్యాబేజీ వేపుడు", "Vegetable Curries", "Curries", False,
     130, 84, 2.1, ["cabbage", "vepudu", "senagapappu", "stir fry"]),
    # 23
    (SRC1_DIR / "23_Cauliflower_Kura.jpg", "023_Cauliflower_Kura.jpg",
     "Cauliflower Kura (Cauliflower Curry)", "కాలిఫ్లవర్ కూర", "Vegetable Curries", "Curries", False,
     140, 92, 2.4, ["cauliflower", "gobi", "kura", "curry"]),
    # 24
    (SRC1_DIR / "24_Beans_Vepudu.jpg", "024_Beans_Vepudu.jpg",
     "Beans Vepudu (French Beans Stir Fry)", "బీన్స్ వేపుడు", "Vegetable Curries", "Curries", False,
     130, 88, 2.6, ["beans", "french beans", "vepudu", "poriyal"]),
    # 25
    (SRC1_DIR / "25_Chikkudukaya_Kura.jpg", "025_Chikkudukaya_Kura.jpg",
     "Chikkudukaya Kura (Broad Beans Curry)", "చిక్కుడుకాయ కూర", "Vegetable Curries", "Curries", False,
     140, 106, 4.5, ["chikkudukaya", "broad beans", "country beans", "kura"]),
    # 26
    (SRC1_DIR / "26_Goruchikkudu_Kura.jpg", "026_Goruchikkudu_Kura.jpg",
     "Goruchikkudu Kura (Cluster Beans Curry)", "గోరుచిక్కుడు కూర", "Vegetable Curries", "Curries", False,
     130, 98, 3.4, ["goruchikkudu", "cluster beans", "gavar", "kura"]),
    # 27
    (SRC1_DIR / "27_Dosakaya_Kura_Mukkala_Pulusu.jpg", "027_Dosakaya_Mukkala_Pulusu.jpg",
     "Dosakaya Mukkala Pulusu (Yellow Cucumber Stew)", "దోసకాయ ముక్కల పులుసు", "Vegetable Curries", "Curries", False,
     150, 76, 1.5, ["dosakaya", "yellow cucumber", "pulusu", "mukkala pulusu"]),
    # 28
    (SRC1_DIR / "28_Munakkaya_Kura_Pulusu.jpg", "028_Munakkaya_Pulusu.jpg",
     "Munakkaya Pulusu / Kura (Drumstick Stew)", "మునక్కాయ పులుసు / కూర", "Vegetable Curries", "Curries", False,
     150, 90, 2.6, ["munakkaya", "mulakkada", "drumstick", "pulusu"]),
    # 29
    (SRC1_DIR / "29_Aratikaya_Vepudu_Kura.jpg", "029_Aratikaya_Vepudu.jpg",
     "Aratikaya Vepudu (Raw Plantain Fry)", "అరటికాయ వేపుడు", "Vegetable Curries", "Curries", False,
     130, 132, 1.9, ["aratikaya", "raw banana", "plantain", "vepudu"]),
    # 30
    (SRC1_DIR / "30_Chamadumpa_Pulusu_Vepudu.jpg", "030_Chamadumpa_Pulusu.jpg",
     "Chamadumpa Pulusu (Colocasia / Taro Root Stew)", "చామదుంప పులుసు", "Vegetable Curries", "Curries", False,
     140, 138, 2.6, ["chamadumpa", "colocasia", "arbi", "pulusu"]),
    # 31
    (SRC1_DIR / "31_Potlakaya_Kura.jpg", "031_Potlakaya_Kura.jpg",
     "Potlakaya Kura (Snake Gourd Curry)", "పొట్లకాయ కూర", "Vegetable Curries", "Curries", False,
     140, 82, 2.5, ["potlakaya", "snake gourd", "kura"]),
    # 32
    (SRC1_DIR / "32_Meal_Maker_Soya_Chunks_Kura.jpg", "032_Meal_Maker_Soya_Chunks_Kura.jpg",
     "Meal Maker Kura (Soya Chunks Curry)", "మీల్ మేకర్ కూర", "Vegetable Curries", "Curries", False,
     150, 152, 14.8, ["meal maker", "soya chunks", "soya curry", "protein"]),
    # 33
    (SRC1_DIR / "33_Senagala_Kura.jpg", "033_Senagala_Kura.jpg",
     "Senagala Kura (Black Chickpea Curry)", "శనగల కూర", "Vegetable Curries", "Curries", False,
     150, 158, 7.8, ["senagalu", "chana", "black chickpeas", "kura"]),
    # 34
    (SRC1_DIR / "34_Majjiga_Pulusu_Majjiga_Charu.jpg", "034_Majjiga_Pulusu.jpg",
     "Majjiga Pulusu / Majjiga Charu (Seasoned Buttermilk Stew)", "మజ్జిగ పులుసు", "Vegetable Curries", "Curries", False,
     150, 68, 2.8, ["majjiga", "buttermilk", "kadhi", "pulusu", "charu"]),
    # 35
    (SRC1_DIR / "35_Palli_Pachadi.jpg", "035_Palli_Pachadi.jpg",
     "Palli Pachadi (Peanut / Groundnut Chutney)", "పల్లీ పచ్చడి", "Chutneys & Podis", "Curries", False,
     40, 248, 9.8, ["palli", "peanut", "groundnut", "pachadi", "chutney"]),
    # 36
    (SRC1_DIR / "36_Kobbari_Pachadi.jpg", "036_Kobbari_Pachadi.jpg",
     "Kobbari Pachadi (Coconut Chutney)", "కొబ్బరి పచ్చడి", "Chutneys & Podis", "Curries", False,
     40, 232, 3.4, ["kobbari", "coconut", "pachadi", "chutney"]),
    # 37
    (SRC1_DIR / "37_Allam_Pachadi.jpg", "037_Allam_Pachadi.jpg",
     "Allam Pachadi (Ginger Chutney)", "అల్లం పచ్చడి", "Chutneys & Podis", "Curries", False,
     30, 178, 2.2, ["allam", "ginger", "pachadi", "jaggery chutney"]),
    # 38
    (SRC1_DIR / "38_Tomato_Pachadi_Roti_Pachadi.jpg", "038_Tomato_Pachadi.jpg",
     "Tomato Pachadi (Roti Pachadi)", "టమాటా పచ్చడి", "Chutneys & Podis", "Curries", False,
     40, 115, 2.4, ["tomato", "tamata", "pachadi", "roti pachadi"]),
    # 39
    (SRC1_DIR / "39_Gongura_Pachadi.jpg", "039_Gongura_Pachadi.jpg",
     "Gongura Pachadi (Spicy Sorrel Leaves Chutney)", "గోంగూర పచ్చడి", "Chutneys & Podis", "Curries", False,
     40, 154, 3.1, ["gongura", "sorrel", "pachadi", "andhra pickle"]),
    # 40
    (SRC1_DIR / "40_Dosakaya_Pachadi.jpg", "040_Dosakaya_Pachadi.jpg",
     "Dosakaya Pachadi (Yellow Cucumber Chutney)", "దోసకాయ పచ్చడి", "Chutneys & Podis", "Curries", False,
     40, 122, 3.2, ["dosakaya", "cucumber", "pachadi", "chutney"]),
    # 41
    (SRC1_DIR / "41_Kandi_Podi.jpg", "041_Kandi_Podi.jpg",
     "Kandi Podi (Gunpowder / Spiced Dal Powder)", "కంది పొడి", "Chutneys & Podis", "Curries", False,
     20, 368, 21.4, ["kandi podi", "dal powder", "gunpowder", "toor dal powder"]),
    # 42
    (SRC1_DIR / "42_Karivepaku_Podi.jpg", "042_Karivepaku_Podi.jpg",
     "Karivepaku Podi (Curry Leaves Powder)", "కరివేపాకు పొడి", "Chutneys & Podis", "Curries", False,
     20, 342, 16.8, ["karivepaku", "curry leaves", "podi", "powder"]),
    # 43
    (SRC1_DIR / "43_Nuvvula_Podi.jpg", "043_Nuvvula_Podi.jpg",
     "Nuvvula Podi (Sesame Seed Powder)", "నువ్వుల పొడి", "Chutneys & Podis", "Curries", False,
     20, 518, 19.2, ["nuvvulu", "sesame", "til", "podi"]),
    # 44
    (SRC1_DIR / "44_Guddu_Porutu_Egg_Bhurji.jpg", "044_Guddu_Porutu_Egg_Bhurji.jpg",
     "Guddu Porutu (Spiced Scrambled Egg / Bhurji)", "గుడ్డు పొరుటు / ఎగ్ బుర్జీ", "Eggs, Meat & Fish", "Non-Veg", False,
     120, 176, 10.8, ["guddu", "egg", "bhurji", "scramble", "porutu"]),
    # 45
    (SRC1_DIR / "45_Natukodi_Pulusu.jpg", "045_Natukodi_Pulusu.jpg",
     "Natukodi Pulusu (Country Chicken Curry)", "నాటుకోడి పులుసు", "Eggs, Meat & Fish", "Non-Veg", False,
     170, 164, 18.2, ["natukodi", "chicken", "country chicken", "pulusu"]),
    # 46
    (SRC1_DIR / "46_Gongura_Chicken.jpg", "046_Gongura_Chicken.jpg",
     "Gongura Chicken (Chicken with Sorrel Leaves)", "గోంగూర చికెన్", "Eggs, Meat & Fish", "Non-Veg", False,
     160, 178, 16.4, ["gongura chicken", "sorrel chicken", "kodi kura", "chicken"]),
    # 47
    (SRC1_DIR / "47_Endu_Chepalu_Kura.jpg", "047_Endu_Chepalu_Kura.jpg",
     "Endu Chepalu Kura (Dry Fish Curry)", "ఎండు చేపల కూర", "Eggs, Meat & Fish", "Non-Veg", False,
     120, 192, 24.8, ["endu chepalu", "dry fish", "fish curry", "chepa"]),
    # 48
    (SRC1_DIR / "48_Ragi_Laddu.jpg", "048_Ragi_Laddu.jpg",
     "Ragi Laddu (Finger Millet & Jaggery Sweet)", "రాగి లడ్డూ", "Snacks & Sweets", "Salads/Staples", False,
     45, 418, 7.8, ["ragi", "laddu", "finger millet", "jaggery"]),
    # 49
    (SRC1_DIR / "49_Guggillu.jpg", "049_Guggillu.jpg",
     "Guggillu (Seasoned Boiled Pulses / Sundal)", "గుగ్గిళ్ళు", "Snacks & Sweets", "Salads/Staples", False,
     120, 152, 8.8, ["guggillu", "sundal", "boiled chickpeas", "tempered"]),
    # 50
    (SRC1_DIR / "50_Coconut_Water.jpg", "050_Coconut_Water.jpg",
     "Coconut Water (Kobbari Bondam)", "కొబ్బరి బొండం", "Fruits & Salads", "Salads/Staples", False,
     250, 19, 0.7, ["coconut water", "kobbari bondam", "tender coconut", "hydrating"]),
]

# --- Source 2: Dishes 51 to 80 ---
s2_specs = [
    # 51
    (SRC2_DIR / "06_Ponaganti_Kura_Vepudu.jpg", "051_Ponaganti_Kura_Vepudu.jpg",
     "Ponaganti Kura Vepudu (Alternanthera Leaves Stir Fry)", "పొన్నగంటి కూర వేపుడు", "Leafy Green Curries", "Leafy Greens", False,
     120, 94, 3.8, ["ponnaganti", "ponaganti", "alternanthera", "vepudu", "leafy green"]),
    # 52
    (SRC2_DIR / "07_Bachali_Kura_Pulusu.jpg", "052_Bachali_Kura_Pulusu.jpg",
     "Bachali Kura Pulusu (Malabar Spinach Stew)", "బచ్చలికూర పులుసు", "Leafy Green Curries", "Leafy Greens", False,
     130, 82, 2.4, ["bachali", "malabar spinach", "pulusu", "leafy"]),
    # 53
    (SRC2_DIR / "08_Chukkakura_Kura.jpg", "053_Chukkakura_Kura.jpg",
     "Chukkakura Kura (Green Sorrel Leaves Curry)", "చుక్కకూర కూర", "Leafy Green Curries", "Leafy Greens", False,
     120, 88, 2.6, ["chukkakura", "green sorrel", "khatta palak", "kura"]),
    # 54
    (SRC2_DIR / "14_Bachali_Kura_Pappu.jpg", "054_Bachali_Kura_Pappu.jpg",
     "Bachali Kura Pappu (Malabar Spinach Dal)", "బచ్చలికూర పప్పు", "Dals & Pappu", "Dals", False,
     150, 116, 6.2, ["bachali", "malabar spinach", "pappu", "dal"]),
    # 55
    (SRC2_DIR / "15_Munagaku_Pappu.jpg", "055_Munagaku_Pappu.jpg",
     "Munagaku Pappu (Moringa / Drumstick Leaves Dal)", "మునగాకు పప్పు", "Dals & Pappu", "Dals", False,
     150, 128, 7.6, ["munagaku", "moringa", "drumstick leaves", "pappu", "dal"]),
    # 56
    (SRC2_DIR / "16_Ponaganti_Kura_Pappu.jpg", "056_Ponaganti_Kura_Pappu.jpg",
     "Ponaganti Kura Pappu (Alternanthera Dal)", "పొన్నగంటి కూర పప్పు", "Dals & Pappu", "Dals", False,
     150, 120, 6.6, ["ponnaganti", "ponaganti", "pappu", "dal"]),
    # 57
    (SRC2_DIR / "18_Sorakaya_Anapakaya_Pappu.jpg", "057_Sorakaya_Anapakaya_Pappu.jpg",
     "Sorakaya Anapakaya Pappu (Bottle Gourd Lentil Dal)", "సొరకాయ / ఆనపకాయ పప్పు", "Dals & Pappu", "Dals", False,
     150, 108, 5.6, ["sorakaya", "anapakaya", "bottle gourd", "pappu", "dal"]),
    # 58
    (SRC2_DIR / "21_Munakkaya_Pappu.jpg", "058_Munakkaya_Pappu.jpg",
     "Munakkaya Pappu (Drumstick Dal)", "మునక్కాయ పప్పు", "Dals & Pappu", "Dals", False,
     150, 116, 6.1, ["munakkaya", "drumstick", "pappu", "dal"]),
    # 59
    (SRC2_DIR / "24_Bangaladumpa_Aloo_Kura_Vepudu.jpg", "059_Bangaladumpa_Aloo_Kurma.jpg",
     "Bangaladumpa Aloo Kurma (Potato Gravy Curry)", "బంగాళాదుంప కుర్మా", "Vegetable Curries", "Curries", False,
     150, 124, 2.6, ["bangaladumpa", "aloo", "kurma", "potato curry", "gravy"]),
    # 60
    (SRC2_DIR / "27_Sorakaya_Anapakaya_Kura_Pulusu.jpg", "060_Sorakaya_Pulusu.jpg",
     "Sorakaya Pulusu (Tamarind Bottle Gourd Stew)", "సొరకాయ పులుసు", "Vegetable Curries", "Curries", False,
     150, 72, 1.5, ["sorakaya", "anapakaya", "pulusu", "tamarind stew"]),
    # 61
    (SRC2_DIR / "28_Kakarakaya_Vepudu_Pulusu.jpg", "061_Kakarakaya_Bellam_Pulusu.jpg",
     "Kakarakaya Bellam Pulusu (Sweet & Sour Bitter Gourd Stew)", "కాకరకాయ బెల్లం పులుసు", "Vegetable Curries", "Curries", False,
     140, 102, 2.1, ["kakarakaya", "bellam", "bitter gourd", "pulusu", "jaggery"]),
    # 62
    (SRC2_DIR / "30_Cauliflower_Gobi_Kura.jpg", "062_Cauliflower_Gobi_Kura.jpg",
     "Cauliflower Gobi Tomato Kura (Cauliflower Tomato Curry)", "కాలిఫ్లవర్ టమాటా కూర", "Vegetable Curries", "Curries", False,
     140, 92, 2.4, ["cauliflower", "gobi", "tomato", "kura"]),
    # 63
    (SRC2_DIR / "33_Goruchikkudu_Kura_Vepudu.jpg", "063_Goruchikkudu_Vepudu.jpg",
     "Goruchikkudu Vepudu (Cluster Beans Stir Fry)", "గోరుచిక్కుడు వేపుడు", "Vegetable Curries", "Curries", False,
     130, 98, 3.4, ["goruchikkudu", "cluster beans", "vepudu", "stir fry"]),
    # 64
    (SRC2_DIR / "34_Potlakaya_Kura_Perugu_Kura.jpg", "064_Potlakaya_Perugu_Kura.jpg",
     "Potlakaya Perugu Kura (Snake Gourd Curd Curry)", "పొట్లకాయ పెరుగు కూర", "Vegetable Curries", "Curries", False,
     140, 82, 2.5, ["potlakaya", "snake gourd", "perugu", "curd curry"]),
    # 65
    (SRC2_DIR / "35_Dosakaya_Kura_Mukkala_Pulusu.jpg", "065_Dosakaya_Mukkala_Pulusu.jpg",
     "Dosakaya Mukkala Pulusu (Yellow Cucumber Tangy Stew)", "దోసకాయ ముక్కల పులుసు", "Vegetable Curries", "Curries", False,
     150, 76, 1.5, ["dosakaya", "yellow cucumber", "mukkala pulusu"]),
    # 66
    (SRC2_DIR / "37_Beetroot_Vepudu_Kura.jpg", "066_Beetroot_Vepudu.jpg",
     "Beetroot Vepudu (Beetroot Stir Fry)", "బీట్‌రూట్ వేపుడు", "Vegetable Curries", "Curries", False,
     130, 96, 2.1, ["beetroot", "vepudu", "poriyal", "stir fry"]),
    # 67
    (SRC2_DIR / "38_Aratikaya_Vepudu_Kura.jpg", "067_Aratikaya_Kura.jpg",
     "Aratikaya Kura (Raw Plantain Mustard Curry / Ava Pettina Kura)", "అరటికాయ కూర", "Vegetable Curries", "Curries", False,
     140, 126, 2.0, ["aratikaya", "raw plantain", "kura", "banana curry"]),
    # 68
    (SRC2_DIR / "39_Chamadumpa_Pulusu_Vepudu.jpg", "068_Chamadumpa_Vepudu.jpg",
     "Chamadumpa Vepudu (Crispy Taro Root / Arbi Fry)", "చామదుంప వేపుడు", "Vegetable Curries", "Curries", False,
     130, 142, 2.2, ["chamadumpa", "arbi", "colocasia", "vepudu", "fry"]),
    # 69
    (SRC2_DIR / "40_Kanda_Kura_Pulusu.jpg", "069_Kanda_Kura_Pulusu.jpg",
     "Kanda Pulusu / Kura (Elephant Foot Yam Curry)", "కంద కూర / పులుసు", "Vegetable Curries", "Curries", False,
     140, 128, 2.2, ["kanda", "suran", "elephant foot yam", "pulusu", "kura"]),
    # 70
    (SRC2_DIR / "44_Bobbarlu_Alasandalu_Kura.jpg", "070_Bobbarlu_Alasandalu_Kura.jpg",
     "Bobbarlu / Alasandalu Kura (Cowpea / Black Eyed Peas Curry)", "బొబ్బర్లు / అలసందల కూర", "Vegetable Curries", "Curries", False,
     150, 146, 8.1, ["bobbarlu", "alasandalu", "cowpeas", "lobia", "kura"]),
    # 71
    (SRC2_DIR / "54_Munagaku_Podi.jpg", "071_Munagaku_Podi.jpg",
     "Munagaku Podi (Moringa / Drumstick Leaf Spice Powder)", "మునగాకు పొడి", "Chutneys & Podis", "Curries", False,
     20, 336, 22.5, ["munagaku podi", "moringa powder", "drumstick leaf podi"]),
    # 72
    (SRC2_DIR / "56_Natukodi_Pulusu.jpg", "072_Natukodi_Kura.jpg",
     "Natukodi Kura (Spicy Andhra Country Chicken Curry)", "నాటుకోడి కూర", "Eggs, Meat & Fish", "Non-Veg", False,
     170, 164, 18.2, ["natukodi", "country chicken", "kodi kura", "spicy chicken"]),
    # 73
    (SRC2_DIR / "57_Chicken_Liver_Fry.jpg", "073_Chicken_Liver_Fry.jpg",
     "Chicken Liver Fry (Kodi Liver Vepudu)", "చికెన్ లివర్ వేపుడు", "Eggs, Meat & Fish", "Non-Veg", False,
     120, 186, 20.6, ["chicken liver", "kodi liver", "liver fry", "vepudu"]),
    # 74
    (SRC2_DIR / "59_Mutton_Liver_Kaleji_Fry.jpg", "074_Mutton_Liver_Kaleji_Fry.jpg",
     "Mutton Liver Fry (Kaleji Vepudu)", "మటన్ లివర్ / కలేజీ వేపుడు", "Eggs, Meat & Fish", "Non-Veg", False,
     120, 198, 21.2, ["mutton liver", "kaleji", "liver fry", "vepudu"]),
    # 75
    (SRC2_DIR / "60_Gongura_Mutton.jpg", "075_Gongura_Mutton.jpg",
     "Gongura Mutton (Spicy Sorrel Leaves Lamb Curry)", "గోంగూర మటన్", "Eggs, Meat & Fish", "Non-Veg", False,
     160, 204, 16.8, ["gongura mutton", "gongura mamsam", "mutton", "sorrel mutton"]),
    # 76
    (SRC2_DIR / "62_Endu_Royyalu_Kura.jpg", "076_Endu_Royyalu_Kura.jpg",
     "Endu Royyalu Kura (Dried Prawns Curry / Royyala Iguru)", "ఎండు రొయ్యల కూర", "Eggs, Meat & Fish", "Non-Veg", False,
     120, 184, 23.6, ["endu royyalu", "dry prawns", "prawns", "shrimp curry", "kura"]),
    # 77
    (SRC2_DIR / "65_Balamrutham.jpg", "077_Balamrutham.jpg",
     "Balamrutham (Nutrient-Dense Anganwadi THR Weaning Porridge)", "బాలామృతం (అంగన్‌వాడీ)", "Snacks & Sweets", "Salads/Staples", False,
     100, 412, 11.4, ["balamrutham", "anganwadi", "thr", "fortified flour", "porridge"]),
    # 78
    (SRC2_DIR / "66_Palli_Chikki_Palli_Patti.jpg", "078_Palli_Chikki.jpg",
     "Palli Chikki (Peanut & Jaggery Brittle)", "పల్లీ చిక్కీ / పల్లీ పట్టీ", "Snacks & Sweets", "Salads/Staples", False,
     40, 488, 14.6, ["palli chikki", "peanut brittle", "palli patti", "jaggery"]),
    # 79
    (SRC2_DIR / "68_Dry_Fruit_Laddu.jpg", "079_Dry_Fruit_Laddu.jpg",
     "Dry Fruit Laddu (Dates & Nuts Energy Laddu)", "డ్రై ఫ్రూట్ లడ్డూ", "Snacks & Sweets", "Salads/Staples", False,
     40, 465, 11.2, ["dry fruit laddu", "dates", "nuts", "healthy sweet", "laddu"]),
    # 80
    (SRC2_DIR / "70_Boiled_Sweet_Corn.jpg", "080_Boiled_Sweet_Corn.jpg",
     "Boiled Sweet Corn (Mokkajonna Kanki)", "ఉడకబెట్టిన మొక్కజొన్న", "Snacks & Sweets", "Salads/Staples", False,
     125, 96, 3.4, ["sweet corn", "mokkajonna", "corn on the cob", "boiled corn"]),
]

# --- Source 3: Dishes 81 to 100 ---
s3_specs = [
    # 81
    (WEB1_DIR / "01_Hyderabadi_Chicken_Biryani.jpg", "081_Hyderabadi_Chicken_Biryani.jpg",
     "Hyderabadi Chicken Biryani (Spicy Dum Biryani)", "హైదరాబాదీ చికెన్ బిర్యానీ", "Eggs, Meat & Fish", "Non-Veg", False,
     280, 188, 10.4, ["biryani", "chicken biryani", "dum biryani", "basmati rice", "kodi pulao"]),
    # 82
    (WEB1_DIR / "05_Pesarattu.jpg", "082_Pesarattu.jpg",
     "Pesarattu (Andhra Green Moong Dal Crepe)", "పెసరట్టు", "Tiffins & Breads", "Tiffins/Rice", False,
     150, 186, 9.4, ["pesarattu", "moong dal dosa", "green gram crepe", "allam pachadi"]),
    # 83
    (DL_DIR / "ragi_sangati.jpg", "083_Ragi_Sangati.jpg",
     "Ragi Sangati (Rayalaseema Finger Millet Ball)", "రాగి సంగటి / రాగి ముద్ద", "Rice & Millet Dishes", "Tiffins/Rice", False,
     200, 138, 3.6, ["ragi sangati", "ragi mudda", "finger millet ball", "ragi"]),
    # 84
    (WEB1_DIR / "06_Pulihora_rice.jpg", "084_Pulihora.jpg",
     "Pulihora (Andhra Tamarind Spiced Rice)", "చింతపండు పులిహోర", "Rice & Millet Dishes", "Tiffins/Rice", False,
     200, 178, 4.1, ["pulihora", "tamarind rice", "chintapandu", "sesame", "peanuts"]),
    # 85
    (WEB1_DIR / "08_Curd_rice_South_India.jpg", "085_Perugu_Annam.jpg",
     "Perugu Annam (Tempered Curd Rice / Daddojanam)", "పెరుగు అన్నం / దద్దోజనం", "Rice & Millet Dishes", "Tiffins/Rice", False,
     200, 116, 3.5, ["perugu annam", "curd rice", "daddojanam", "yogurt rice"]),
    # 86
    (DL_DIR / "steamed_rice_pappu.jpg", "086_Steamed_Rice_with_Pappu.jpg",
     "Steamed White Rice with Pappu (Vandi Annam & Dal)", "తెల్ల అన్నం & పప్పు", "Rice & Millet Dishes", "Tiffins/Rice", False,
     250, 128, 4.8, ["steamed rice", "white rice", "annam", "mudda pappu", "dal"]),
    # 87
    (WEB1_DIR / "02_Masala_Dosa.jpg", "087_Plain_Dosa_with_Chutney.jpg",
     "Plain Dosa with Chutney (Crispy Fermented Rice Crepe)", "దోస & చట్నీ", "Tiffins & Breads", "Tiffins/Rice", False,
     150, 196, 5.2, ["dosa", "plain dosa", "chutney", "breakfast crepe"]),
    # 88
    (WEB1_DIR / "03_Idli_Sambar.jpg", "088_Idli_with_Sambar.jpg",
     "Idli with Sambar (Steamed Rice-Lentil Cakes with Lentil Stew)", "ఇడ్లీ & సాంబార్", "Tiffins & Breads", "Tiffins/Rice", False,
     220, 126, 4.8, ["idli", "sambar", "steamed cakes", "breakfast"]),
    # 89
    (WEB1_DIR / "04_Medu_Vada.jpg", "089_Medu_Vada_Minapa_Garelu.jpg",
     "Medu Vada (Crispy Minapa Garelu / Lentil Fritters)", "మినప గారెలు / వడ", "Tiffins & Breads", "Tiffins/Rice", False,
     100, 284, 9.8, ["medu vada", "garelu", "minapa garelu", "urad dal fritter"]),
    # 90
    (WEB1_DIR / "07_Upma_dish.jpg", "090_Rava_Upma.jpg",
     "Rava Upma (Tempered Semolina Porridge)", "రవ్వ ఉప్మా", "Tiffins & Breads", "Tiffins/Rice", False,
     160, 162, 4.4, ["upma", "rava upma", "suji upma", "bansi rava"]),
    # 91
    (WEB1_DIR / "12_Poori_curry_Indian.jpg", "091_Poori_with_Potato_Curry.jpg",
     "Poori with Potato Curry (Puri Masala / Kura)", "పూరి & బంగాళాదుంప కూర", "Tiffins & Breads", "Tiffins/Rice", False,
     200, 240, 5.6, ["poori", "puri", "potato masala", "aloo kura"]),
    # 92
    (WEB2_DIR / "08_roti_chapati.jpg", "092_Chapati_with_Dal.jpg",
     "Chapati with Dal (Whole Wheat Flatbread with Lentil Curry)", "చపాతీ & పప్పు", "Tiffins & Breads", "Tiffins/Rice", False,
     160, 198, 7.2, ["chapati", "pulka", "roti", "dal", "wheat bread"]),
    # 93
    (WEB2_DIR / "06_samosa.jpg", "093_Samosa.jpg",
     "Samosa (Crispy Potato & Pea Savory Pastry)", "సమోసా", "Snacks & Sweets", "Salads/Staples", False,
     100, 262, 4.8, ["samosa", "potato pastry", "aloo samosa", "snack"]),
    # 94
    (DL_DIR / "boiled_sweet_potato.jpg", "094_Boiled_Sweet_Potato.jpg",
     "Boiled Sweet Potato (Chilakada Dumpa / Genusu Gadda)", "ఉడకబెట్టిన చిలకడదుంప", "Snacks & Sweets", "Salads/Staples", False,
     130, 86, 1.6, ["sweet potato", "chilakadumpa", "genusu gadda", "boiled tuber"]),
    # 95
    (DL_DIR / "cucumber_slices.jpg", "095_Cucumber_Slices_Salad.jpg",
     "Cucumber Slices Salad (Keera Dosakaya)", "కీరా దోసకాయ ముక్కలు", "Fruits & Salads", "Salads/Staples", True,
     100, 15, 0.7, ["cucumber", "keera", "dosakaya slices", "raw salad", "hydrating"]),
    # 96
    (DL_DIR / "mixed_healthy_bowl.jpg", "096_Mixed_Healthy_Bowl.jpg",
     "Mixed Healthy Bowl (Sweet Potato, Cucumber, Carrot & Pomegranate)", "మిక్స్‌డ్ హెల్తీ సలాడ్ బౌల్", "Fruits & Salads", "Salads/Staples", True,
     180, 58, 1.4, ["salad bowl", "sweet potato", "cucumber", "carrot", "pomegranate", "healthy bowl"]),
    # 97
    (DL_DIR / "boiled_eggs.jpg", "097_Boiled_Eggs.jpg",
     "Boiled Eggs (Udakabettina Guddu)", "ఉడకబెట్టిన కోడిగుడ్లు", "Eggs, Meat & Fish", "Non-Veg", False,
     100, 155, 12.6, ["boiled eggs", "guddu", "protein egg", "hard boiled"]),
    # 98
    (WEB1_DIR / "11_Chicken_65_dish.jpg", "098_Chicken_65_Kodi_Vepudu.jpg",
     "Chicken 65 / Kodi Vepudu (Spicy Andhra Chicken Fry)", "చికెన్ 65 / కోడి వేపుడు", "Eggs, Meat & Fish", "Non-Veg", False,
     140, 218, 21.4, ["chicken 65", "kodi vepudu", "chicken fry", "crispy chicken"]),
    # 99
    (WEB1_DIR / "10_Mirchi_Bajji.jpg", "099_Mirchi_Bajji.jpg",
     "Mirchi Bajji (Andhra Stuffed Chili Fritters)", "మిర్చి బజ్జీ", "Snacks & Sweets", "Salads/Staples", False,
     90, 268, 6.6, ["mirchi bajji", "chili fritters", "besan bajji", "street food"]),
    # 100
    (WEB2_DIR / "09_gulab_jamun.jpg", "100_Gulab_Jamun.jpg",
     "Gulab Jamun (Traditional Milk-Solid Sweet in Saffron Syrup)", "గులాబ్ జామూన్", "Snacks & Sweets", "Salads/Staples", False,
     80, 320, 4.2, ["gulab jamun", "sweet", "khoya sweet", "dessert"]),
]

all_specs = s1_specs + s2_specs + s3_specs
print(f"Total specs configured: {len(all_specs)}")
assert len(all_specs) == 100, f"Expected 100, got {len(all_specs)}"

manifest_entries = []

for idx, spec in enumerate(all_specs, 1):
    src_file, dest_file, name_en, name_te, cluster, macro_cat, is_raw, serving_g, cal_100g, prot_100g, ingredients = spec
    
    # Destination image path
    dest_path = IMAGES_DIR / dest_file
    
    # Check source file exists
    if not src_file.exists():
        raise FileNotFoundError(f"Source file not found: {src_file}")
    
    # Copy file to destination
    shutil.copy2(src_file, dest_path)
    
    # Verify image with PIL
    with Image.open(dest_path) as im:
        im.verify()
    
    # Calculate serving nutrition bounds
    # Serving baseline:
    serving_cal = (cal_100g * serving_g) / 100.0
    serving_prot = (prot_100g * serving_g) / 100.0
    
    # Tolerances: min = max(5, round(0.65 * min(cal_100g, serving_cal)))
    #            max = round(1.35 * max(cal_100g, serving_cal))
    cal_min = max(5, int(round(min(cal_100g, serving_cal) * 0.65 / 5.0) * 5))
    cal_max = int(round(max(cal_100g, serving_cal) * 1.35 / 5.0) * 5)
    
    prot_min = max(0.2, round(min(prot_100g, serving_prot) * 0.65, 1))
    prot_max = round(max(prot_100g, serving_prot) * 1.40, 1)
    
    # Form absolute path with forward slashes for cross-platform compatibility
    abs_img_path = str(dest_path.resolve()).replace("\\", "/")
    
    item = {
        "test_id": f"TEST-{idx:03d}",
        "filename": dest_file,
        "image_path": abs_img_path,
        "expected_dish_name": name_en,
        "expected_dish_te": name_te,
        "expected_cluster": cluster,
        "macro_category": macro_cat,
        "is_raw_salad": is_raw,
        "expected_cal_min": cal_min,
        "expected_cal_max": cal_max,
        "expected_protein_min": prot_min,
        "expected_protein_max": prot_max,
        "key_ingredients": ingredients
    }
    manifest_entries.append(item)

# Write manifest to disk
manifest_path = BENCHMARK_DIR / "test_manifest_100.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest_entries, f, indent=2, ensure_ascii=False)

print(f"\nSuccessfully wrote manifest to {manifest_path}")
print(f"Total manifest entries: {len(manifest_entries)}")

# Verification
print("\n--- Integrity Verification ---")
total_bytes = 0
for entry in manifest_entries:
    p = Path(entry["image_path"])
    assert p.exists(), f"Image does not exist: {p}"
    size = p.stat().st_size
    assert size > 5000, f"Image too small ({size} bytes): {p}"
    total_bytes += size

print(f"All 100 images verified! Total dataset size: {total_bytes / (1024*1024):.2f} MB")

# Category breakdown
from collections import Counter
cat_counts = Counter(e["macro_category"] for e in manifest_entries)
cluster_counts = Counter(e["expected_cluster"] for e in manifest_entries)

print("\n--- Macro Category Breakdown ---")
for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {cnt} dishes")

print("\n--- Cluster Breakdown ---")
for cluster, cnt in sorted(cluster_counts.items(), key=lambda x: -x[1]):
    print(f"  {cluster}: {cnt} dishes")
