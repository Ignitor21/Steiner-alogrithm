#!/usr/bin/env python3

import json, glob, os, sys, importlib.util, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH_DIR = HERE / "SMT-benchmarks"

errors = 0
with tempfile.TemporaryDirectory() as tmpd:
    for inp in sorted(glob.glob(os.path.join(BENCH_DIR, "*.json"))):
        for mode in (""):
            cmd = ["python3", os.path.join(HERE, "steiner.py")]
            if mode: cmd.append(mode)
            cmd.append(inp)
            subprocess.run(cmd, cwd=tmpd, check=True, capture_output=True)
            base = os.path.basename(inp)[:-5]
            out = os.path.join(tmpd, f"{base}_out.json")
            data = json.load(open(out))
            nodes = data["node"]; edges = data["edge"]
            N = len(nodes); E = len(edges)
            ok = True
            if E != N - 1:
                print(f"[FAIL edges!=N-1] {base} {mode or 'basic'}: N={N}, E={E}")
                ok = False
            deg = {n["id"]: 0 for n in nodes}
            for e in edges:
                deg[e["vertices"][0]] += 1
                deg[e["vertices"][1]] += 1
            for n in nodes:
                if n["type"] == "s" and deg[n["id"]] < 3:
                    print(f"[FAIL deg(S)<3] {base} {mode or 'basic'}: id={n['id']} deg={deg[n['id']]}")
                    ok = False
            from collections import defaultdict, deque
            adj = defaultdict(list)
            for e in edges:
                a, b = e["vertices"]
                adj[a].append(b); adj[b].append(a)
            start = nodes[0]["id"]
            vis = {start}; q = deque([start])
            while q:
                v = q.popleft()
                for u in adj[v]:
                    if u not in vis:
                        vis.add(u); q.append(u)
            if len(vis) != N:
                print(f"[FAIL not connected] {base} {mode or 'basic'}: visited {len(vis)}/{N}")
                ok = False
            coord = {n["id"]: (n["x"], n["y"]) for n in nodes}
            L = sum(abs(coord[e["vertices"][0]][0] - coord[e["vertices"][1]][0]) +
                    abs(coord[e["vertices"][0]][1] - coord[e["vertices"][1]][1])
                    for e in edges)
            if L != data["total_length"]:
                print(f"[FAIL length] {base} {mode or 'basic'}: sum={L} stated={data['total_length']}")
                ok = False
            if not ok:
                errors += 1

print(f"\nВсего проверено тестов: {len(glob.glob(os.path.join(BENCH_DIR,'*.json')))*2}, ошибок: {errors}")




