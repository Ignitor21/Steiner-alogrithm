#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import glob
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE / "SMT-benchmarks"
OUT_DIR = HERE / "results"
os.makedirs(OUT_DIR, exist_ok=True)

spec = importlib.util.spec_from_file_location("my_steiner",
                                              os.path.join(HERE, "steiner.py"))
ms = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ms)

rows = []
files = sorted(glob.glob(os.path.join(BENCH_DIR, "*.json")))
for path in files:
    terminals = ms.read_input(path)

    terminal_pts = [(t["x"], t["y"]) for t in terminals]
    rmst_ref = ms.rmst_length(terminal_pts)

    pts_b, edges_b, len_b, t_b = ms.build_tree(terminals, use_modified=False)
    pts_m, edges_m, len_m, t_m = ms.build_tree(terminals, use_modified=True)

    name = os.path.basename(path)
    n = len(terminals)
    imp_b = (rmst_ref - len_b) / rmst_ref * 100 if rmst_ref else 0
    imp_m = (rmst_ref - len_m) / rmst_ref * 100 if rmst_ref else 0
    rows.append({
        "test": name,
        "N": n,
        "RMST": rmst_ref,
        "SMT_basic": len_b,
        "time_basic_s": t_b,
        "steiner_basic": len(pts_b) - n,
        "SMT_mod": len_m,
        "time_mod_s": t_m,
        "steiner_mod": len(pts_m) - n,
        "impr_basic_pct": imp_b,
        "impr_mod_pct": imp_m,
    })
    print(f"{name:20s} N={n:3d}  RMST={rmst_ref:6d}  "
          f"basic: L={len_b:6d} t={t_b:7.3f}s  "
          f"mod:   L={len_m:6d} t={t_m:7.3f}s")

import csv
csv_path = os.path.join(OUT_DIR, "benchmark_results.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)

md_path = os.path.join(OUT_DIR, "benchmark_results.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("# Результаты бенчмарков\n\n")
    f.write("| Тест | N | RMST | Базовый I1S | t, с | Точек Ш. | Мод. I1S | t, с | Точек Ш. | Δ базового | Δ мод. | Ускорение |\n")
    f.write("|------|---|------|-------------|------|----------|----------|------|----------|------------|--------|-----------|\n")
    tot_basic = tot_mod = tot_rmst = 0
    tot_tb = tot_tm = 0.0
    for r in rows:
        speedup = (r["time_basic_s"] / r["time_mod_s"]) if r["time_mod_s"] > 0 else float("inf")
        f.write(f"| {r['test']} | {r['N']} | {r['RMST']} | "
                f"{r['SMT_basic']} | {r['time_basic_s']:.3f} | {r['steiner_basic']} | "
                f"{r['SMT_mod']} | {r['time_mod_s']:.3f} | {r['steiner_mod']} | "
                f"{r['impr_basic_pct']:.2f}% | {r['impr_mod_pct']:.2f}% | "
                f"{speedup:.1f}x |\n")
        tot_basic += r["SMT_basic"]; tot_mod += r["SMT_mod"]; tot_rmst += r["RMST"]
        tot_tb += r["time_basic_s"]; tot_tm += r["time_mod_s"]
    f.write(f"\n## Сводка\n\n")
    f.write(f"- Тестов: {len(rows)}\n")
    f.write(f"- Сумма длин RMST:       **{tot_rmst}**\n")
    f.write(f"- Сумма длин Basic I1S:  **{tot_basic}**  (улучшение {(tot_rmst-tot_basic)/tot_rmst*100:.2f}%)\n")
    f.write(f"- Сумма длин Mod.  I1S:  **{tot_mod}**    (улучшение {(tot_rmst-tot_mod)/tot_rmst*100:.2f}%)\n")
    f.write(f"- Суммарное время Basic: {tot_tb:.3f} с\n")
    f.write(f"- Суммарное время Mod.:  {tot_tm:.3f} с (ускорение {tot_tb/tot_tm:.1f}x)\n")
    f.write(f"- Разница длин Mod − Basic: {tot_mod - tot_basic} "
            f"({(tot_mod - tot_basic)/tot_basic*100:+.2f}%)\n")

print(f"\nCSV:  {csv_path}")
print(f"MD:   {md_path}")
