#!/usr/bin/env python3
import json
from pathlib import Path

GRAPH_FILE = Path.home() / ".hermes-hub" / "config" / "graph.json"

with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = data.get("nodes", {})
edges = data.get("edges", [])

cleaned_edges = []
removed = 0
for e in edges:
    if e.get("source") in nodes and e.get("target") in nodes:
        cleaned_edges.append(e)
    else:
        removed += 1

data["edges"] = cleaned_edges
with open(GRAPH_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Removed {removed} dangling edges. Clean edges count: {len(cleaned_edges)}")
