import os
import sys
import pandas as pd

excel = r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx"
p1 = r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\AP_50_Dish_Images\All_50_Dishes"
p2 = r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\AP_Dish_Images\All_70_New_Dishes"

df1 = pd.read_excel(excel, sheet_name="Final 50 AP Dishes")
df2 = pd.read_excel(excel, sheet_name="Super Admin - AP New Dishes")

files1 = sorted(os.listdir(p1))
files2 = sorted(os.listdir(p2))

print("=== Source 1 Files (50) ===")
for i, f in enumerate(files1, 1):
    row = df1[df1["SORT ORDER"] == i]
    name_en = row["NAME (EN) *"].values[0] if len(row) > 0 else "UNKNOWN"
    name_te = row["Telugu Name"].values[0] if len(row) > 0 else "UNKNOWN"
    cluster = row["CLUSTER"].values[0] if len(row) > 0 else "UNKNOWN"
    print(f"{i:02d}: file='{f}' -> name_en='{name_en}', cluster='{cluster}'")

print("\n=== Source 2 Files (70) ===")
for i, f in enumerate(files2, 1):
    row = df2[df2["SORT ORDER"] == i]
    name_en = row["NAME (EN) *"].values[0] if len(row) > 0 else "UNKNOWN"
    cluster = row["CLUSTER"].values[0] if len(row) > 0 else "UNKNOWN"
    print(f"{i:02d}: file='{f}' -> name_en='{name_en}', cluster='{cluster}'")
