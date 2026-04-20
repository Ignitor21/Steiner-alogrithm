#!/usr/bin/env python3

import json
import os
import sys
import time
import argparse
from itertools import combinations


def manhattan(p, q):
    return abs(p[0] - q[0]) + abs(p[1] - q[1])


def rmst_length_and_edges(points):
    n = len(points)
    if n == 0:
        return 0, []
    if n == 1:
        return 0, []

    INF = float("inf")
    in_tree = [False] * n
    best_dist = [INF] * n
    best_from = [-1] * n

    best_dist[0] = 0
    total = 0
    edges = []

    for _ in range(n):
        u = -1
        ud = INF
        for v in range(n):
            if not in_tree[v] and best_dist[v] < ud:
                ud = best_dist[v]
                u = v
        if u == -1:
            break
        in_tree[u] = True
        total += ud
        if best_from[u] != -1:
            edges.append((best_from[u], u))
        px, py = points[u]
        for v in range(n):
            if not in_tree[v]:
                d = abs(points[v][0] - px) + abs(points[v][1] - py)
                if d < best_dist[v]:
                    best_dist[v] = d
                    best_from[v] = u

    return total, edges


def rmst_length(points):
    n = len(points)
    if n <= 1:
        return 0

    INF = float("inf")
    in_tree = [False] * n
    best_dist = [INF] * n
    best_dist[0] = 0
    total = 0

    for _ in range(n):
        u = -1
        ud = INF
        for v in range(n):
            if not in_tree[v] and best_dist[v] < ud:
                ud = best_dist[v]
                u = v
        if u == -1:
            break
        in_tree[u] = True
        total += ud
        px, py = points[u]
        for v in range(n):
            if not in_tree[v]:
                d = abs(points[v][0] - px) + abs(points[v][1] - py)
                if d < best_dist[v]:
                    best_dist[v] = d

    return total


def hanan_grid(points):
    xs = sorted({p[0] for p in points})
    ys = sorted({p[1] for p in points})
    existing = set(points)
    candidates = []
    for x in xs:
        for y in ys:
            if (x, y) not in existing:
                candidates.append((x, y))
    return candidates


def i1s_basic(terminals):
    points = list(terminals) 
    current_len = rmst_length(points)

    while True:
        candidates = hanan_grid(points)
        if not candidates:
            break

        best_gain = 0
        best_c = None
        for c in candidates:
            new_len = rmst_length(points + [c])
            gain = current_len - new_len
            if gain > best_gain:
                best_gain = gain
                best_c = c

        if best_c is None:
            break  

        points.append(best_c)
        current_len -= best_gain

    return points


def i1s_batched(terminals):
    points = list(terminals)
    current_len = rmst_length(points)

    while True:
        candidates = hanan_grid(points)
        if not candidates:
            break

        gains = []
        for c in candidates:
            new_len = rmst_length(points + [c])
            g = current_len - new_len
            if g > 0:
                gains.append((g, c))

        if not gains:
            break

        gains.sort(key=lambda t: -t[0])

        added = []
        used_x = set()
        used_y = set()
        for g, c in gains:
            if c[0] in used_x and c[1] in used_y:
                continue
            added.append(c)
            used_x.add(c[0])
            used_y.add(c[1])

        if not added:
            break

        new_points = points + added
        new_len = rmst_length(new_points)
        if new_len >= current_len:
            best_c = gains[0][1]
            points.append(best_c)
            current_len = rmst_length(points)
        else:
            points = new_points
            current_len = new_len

    return points


def cleanup_tree(points, edges, num_terminals):
    points = list(points)
    adj = [set() for _ in points]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)

    changed = True
    while changed:
        changed = False
        for i in range(len(points)):
            if i < num_terminals:
                continue  
            deg = len(adj[i])
            if deg == 0:
                continue
            if deg == 1:
                (j,) = tuple(adj[i])
                adj[j].discard(i)
                adj[i].clear()
                changed = True
            elif deg == 2:
                a, b = tuple(adj[i])
                adj[a].discard(i)
                adj[b].discard(i)
                adj[i].clear()
                adj[a].add(b)
                adj[b].add(a)
                changed = True

    alive = [i for i in range(len(points))
             if i < num_terminals or len(adj[i]) >= 3]
    old_to_new = {old: new for new, old in enumerate(alive)}

    new_points = [points[i] for i in alive]
    new_edges = []
    seen = set()
    for i in alive:
        for j in adj[i]:
            if j in old_to_new:
                a, b = old_to_new[i], old_to_new[j]
                key = (min(a, b), max(a, b))
                if key not in seen:
                    seen.add(key)
                    new_edges.append(key)

    return new_points, new_edges


def read_input(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    nodes = data.get("node", [])
    terminals = []
    for n in nodes:
        if n.get("type", "t") == "t":
            terminals.append({
                "id": int(n["id"]),
                "x": int(n["x"]),
                "y": int(n["y"]),
                "name": n.get("name"),
            })
    return terminals


def write_output(path, terminals, points, edges, total_length, elapsed, algo):
    num_t = len(terminals)
    max_id = max((t["id"] for t in terminals), default=0)
    next_id = max_id + 1
    node_ids = []
    for i, p in enumerate(points):
        if i < num_t:
            node_ids.append(terminals[i]["id"])
        else:
            node_ids.append(next_id)
            next_id += 1

    edge_id_base = max(node_ids) + 1
    edge_entries = []
    node_edges_map = {nid: [] for nid in node_ids}
    for k, (a, b) in enumerate(edges):
        eid = edge_id_base + k
        va, vb = node_ids[a], node_ids[b]
        edge_entries.append({
            "id": eid,
            "vertices": [va, vb],
            "length": manhattan(points[a], points[b]),
        })
        node_edges_map[va].append(eid)
        node_edges_map[vb].append(eid)

    node_entries = []
    for i, p in enumerate(points):
        nid = node_ids[i]
        entry = {
            "id": nid,
            "x": int(p[0]),
            "y": int(p[1]),
            "type": "t" if i < num_t else "s",
            "edges": node_edges_map[nid],
        }
        if i < num_t and terminals[i].get("name") is not None:
            entry["name"] = terminals[i]["name"]
        node_entries.append(entry)

    out = {
        "algorithm": algo,
        "total_length": int(total_length),
        "elapsed_seconds": round(elapsed, 6),
        "node": node_entries,
        "edge": edge_entries,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def build_tree(terminals, use_modified):
    """Запустить выбранный алгоритм и вернуть (points, edges, length, elapsed)."""
    terminal_pts = [(t["x"], t["y"]) for t in terminals]
    num_t = len(terminal_pts)

    if num_t == 0:
        return [], [], 0, 0.0
    if num_t == 1:
        return list(terminal_pts), [], 0, 0.0

    t0 = time.perf_counter()
    if use_modified:
        all_pts = i1s_batched(terminal_pts)
    else:
        all_pts = i1s_basic(terminal_pts)
    length, edges = rmst_length_and_edges(all_pts)
    all_pts, edges = cleanup_tree(all_pts, edges, num_t)
    length = sum(manhattan(all_pts[a], all_pts[b]) for a, b in edges)
    elapsed = time.perf_counter() - t0
    return all_pts, edges, length, elapsed


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="I1S Steiner tree builder",
        add_help=True,
    )
    parser.add_argument("-m", "--modified", action="store_true",
                        help="use modified algorithm (batched I1S)")
    parser.add_argument("input", help="input JSON with terminals")
    args = parser.parse_args(argv)

    in_path = args.input
    base = os.path.basename(in_path)
    if base.lower().endswith(".json"):
        base = base[:-5]
    out_path = os.path.join(os.getcwd(), f"{base}_out.json")

    terminals = read_input(in_path)
    points, edges, length, elapsed = build_tree(terminals, args.modified)
    algo = "I1S-batched" if args.modified else "I1S-basic"
    write_output(out_path, terminals, points, edges, length, elapsed, algo)

    num_steiner = len(points) - len(terminals)
    print(f"{algo}: {base}.json "
          f"terminals={len(terminals)} steiner={num_steiner} "
          f"length={int(length)} time={elapsed:.3f}s -> {out_path}")


if __name__ == "__main__":
    main()
