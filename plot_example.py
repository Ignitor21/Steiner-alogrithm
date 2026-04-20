#!/usr/bin/env python3
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

path = sys.argv[1] if len(sys.argv) > 1 else "test_example_out.json"
data = json.load(open(path))
nodes = {n["id"]: n for n in data["node"]}

fig, ax = plt.subplots(figsize=(7, 6))

for e in data["edge"]:
    a, b = e["vertices"]
    x1, y1 = nodes[a]["x"], nodes[a]["y"]
    x2, y2 = nodes[b]["x"], nodes[b]["y"]

    ax.plot([x1, x2, x2], [y1, y1, y2], "-", color="steelblue", linewidth=2)


for n in data["node"]:
    if n["type"] == "t":
        ax.plot(n["x"], n["y"], "o", color="royalblue", markersize=11)
        ax.annotate(f"  {n['id']}", (n["x"], n["y"]),
                    fontsize=11, color="black")
    else:
        ax.plot(n["x"], n["y"], "s", color="crimson", markersize=9)
        ax.annotate(f"  s{n['id']}", (n["x"], n["y"]),
                    fontsize=10, color="crimson")

ax.set_title(f"Steiner tree ({data.get('algorithm', '?')}), "
             f"L = {data['total_length']}")
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.grid(True, linestyle=":", alpha=0.4)
ax.set_aspect("equal", adjustable="datalim")

out = os.path.splitext(path)[0] + ".png"
fig.tight_layout()
fig.savefig(out, dpi=130)
print("saved:", out)
