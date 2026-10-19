import os
import sys
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

excel = r"C:\Users\rinit\Downloads\Jm_app_asha_visit_sample\JM_Dishes_Mapping_Expanded_SuperAdmin.xlsx"
df1 = pd.read_excel(excel, sheet_name="Final 50 AP Dishes")
df2 = pd.read_excel(excel, sheet_name="Super Admin - AP New Dishes")

with open("tests/benchmark_100/source_1_dishes.txt", "w", encoding="utf-8") as f:
    f.write("=== Source 1 (Final 50 AP Dishes) ===\n")
    for idx, r in df1.iterrows():
        f.write(f"{int(r['SORT ORDER']):02d} | {r['NAME (EN) *']} | {r['Telugu Name']} | {r['CLUSTER']}\n")

with open("tests/benchmark_100/source_2_dishes.txt", "w", encoding="utf-8") as f:
    f.write("=== Source 2 (Super Admin - AP New Dishes) ===\n")
    for idx, r in df2.iterrows():
        f.write(f"{int(r['SORT ORDER']):02d} | {r['NAME (EN) *']} | {r['Telugu Name']} | {r['CLUSTER']}\n")

print("Wrote source_1_dishes.txt and source_2_dishes.txt successfully")
