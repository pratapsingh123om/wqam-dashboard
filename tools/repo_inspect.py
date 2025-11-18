
#!/usr/bin/env python3
import os, json, sys

root = sys.argv[1] if len(sys.argv)>1 else "."
out = {"root": os.path.abspath(root), "structure": []}
for p, dirs, files in os.walk(root):
    # skip .git and node_modules
    if "/.git" in p or "/node_modules" in p:
        continue
    rel = os.path.relpath(p, root)
    level = rel.count(os.sep)
    if level <= 2:  # top 3 levels
        out["structure"].append({
            "path": rel,
            "dirs": sorted(dirs),
            "files": sorted(files)
        })
print(json.dumps(out, indent=2))
