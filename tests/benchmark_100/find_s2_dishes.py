import os
import sys
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

excel = r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx"
p1_dir = r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\AP_50_Dish_Images\All_50_Dishes"
p2_dir = r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\AP_Dish_Images\All_70_New_Dishes"

df1 = pd.read_excel(excel, sheet_name="Final 50 AP Dishes")
df2 = pd.read_excel(excel, sheet_name="Super Admin - AP New Dishes")

s1_files = sorted(os.listdir(p1_dir))
s2_files = sorted(os.listdir(p2_dir))

print(f"Total in S1: {len(s1_files)}, Total in S2: {len(s2_files)}")

# Check file names in S2 that are not in S1 or represent new dishes
# Let's see which dishes in S2 are NOT in S1
# S1 has 50 dishes. S2 has 70 dishes.
# 70 - 50 = 20 dishes that are brand new in S2!
# But wait: prompt says:
# "Source 2 (30 distinct curries, dals & fries): C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\AP_Dish_Images\All_70_New_Dishes\ (pick 30 distinct dishes not already in Source 1, such as Gongura Mutton, Royyala Kura, Chepala Pulusu, Natukodi Kura, Pachadi varieties, Podis, etc.). Copy them with clean names (051_... to 080_...)."

# Let's inspect all 70 dishes of S2 vs 50 dishes of S1
s1_slugs = []
for f in s1_files:
    # remove number prefix
    parts = f.split("_", 1)[1] if "_" in f else f
    s1_slugs.append(parts.lower())

print("\n--- S2 dishes comparison ---")
s2_new = []
s2_existing = []
for f in s2_files:
    order = int(f.split("_")[0])
    row = df2[df2["SORT ORDER"] == order]
    name_en = row["NAME (EN) *"].values[0] if len(row) > 0 else f
    name_te = row["Telugu Name"].values[0] if len(row) > 0 else ""
    cluster = row["CLUSTER"].values[0] if len(row) > 0 else ""
    
    # check if in S1
    # Let's find matches
    match_s1 = False
    for s1_f in s1_files:
        # compare base names
        s1_core = s1_f.split("_", 1)[1].lower().replace("_kura", "").replace("_vepudu", "").replace("_pulusu", "")
        s2_core = f.split("_", 1)[1].lower().replace("_kura", "").replace("_vepudu", "").replace("_pulusu", "")
        if s1_core == s2_core or s1_f.split("_", 1)[1].lower() == f.split("_", 1)[1].lower():
            match_s1 = True
            break
    
    if match_s1:
        s2_existing.append((f, name_en, cluster, name_te))
    else:
        s2_new.append((f, name_en, cluster, name_te))

print(f"Distinct/New in S2: {len(s2_new)}")
for item in s2_new:
    print(f"  {item[0]} -> {item[1]} ({item[2]})")

print(f"\nExisting/Overlap with S1: {len(s2_existing)}")
for item in s2_existing:
    print(f"  {item[0]} -> {item[1]} ({item[2]})")
