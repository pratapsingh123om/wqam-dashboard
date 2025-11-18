# repo_check.py
# Run from project root. Produces repo_check_report.txt and prints summary to stdout.
# Works on Windows/Linux/macOS without external deps.

import os
import sys
import json
import textwrap

ROOT = os.getcwd()
OUTFILE = os.path.join(ROOT, "repo_check_report.txt")

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return None

def list_dir(path, depth=2):
    out = []
    for root, dirs, files in os.walk(path):
        level = root[len(path):].count(os.sep)
        if level > depth:
            # skip deeper
            dirs[:] = []
            continue
        rel = os.path.relpath(root, path)
        out.append((rel, sorted(dirs), sorted(files)))
    return out

def analyze_docker_compose(path):
    text = read_file(path)
    if not text:
        return None
    # simple parser to extract frontend service block and volumes lines
    lines = text.splitlines()
    svc = None
    svc_indent = None
    frontend_block = []
    for i, ln in enumerate(lines):
        stripped = ln.lstrip()
        if stripped.startswith("frontend:") and (ln.startswith(" ") or ln.startswith("\t") or ln == "frontend:"):
            svc = "frontend"
            svc_indent = len(ln) - len(stripped)
            frontend_block.append(ln)
            # collect following indented lines
            j = i+1
            while j < len(lines):
                ln2 = lines[j]
                indent2 = len(ln2) - len(ln2.lstrip())
                if ln2.strip() == "":
                    frontend_block.append(ln2)
                    j += 1
                    continue
                if indent2 <= svc_indent:
                    break
                frontend_block.append(ln2)
                j += 1
            break
    return {
        "raw": text,
        "frontend_block": "\n".join(frontend_block)
    }

def find_dockerfile_info(path):
    txt = read_file(path)
    if not txt:
        return None
    lines = txt.splitlines()
    info = {"workdir": None, "copies": [], "exposes": [], "cmd": None}
    for ln in lines:
        s = ln.strip()
        if s.upper().startswith("WORKDIR"):
            info["workdir"] = s.split(None,1)[1] if len(s.split(None,1))>1 else None
        if s.upper().startswith("COPY"):
            # naive parse
            info["copies"].append(s)
        if s.upper().startswith("EXPOSE"):
            info["exposes"].append(s.split(None,1)[1] if len(s.split(None,1))>1 else None)
        if s.upper().startswith("CMD") or s.upper().startswith("ENTRYPOINT"):
            info["cmd"] = s
    return info

def summary():
    s = []
    s.append("REPO CHECK REPORT")
    s.append(f"Root: {ROOT}")
    s.append("")
    # top-level listing
    top = sorted([f for f in os.listdir(ROOT)])
    s.append("Top-level entries:")
    s.append(", ".join(top))
    s.append("")
    # check frontend dir
    frontend = os.path.join(ROOT, "frontend")
    if not os.path.isdir(frontend):
        s.append("No 'frontend' directory found in root.")
    else:
        s.append("Frontend directory listing (first-level):")
        s.append(", ".join(sorted(os.listdir(frontend))))
        s.append("")
        # detailed shallow walk
        entries = list_dir(frontend, depth=2)
        s.append("Frontend tree (depth=2):")
        for rel, dirs, files in entries:
            s.append(f"  {rel} -> dirs: {dirs} files: {files}")
        s.append("")
        # Dockerfile
        df = os.path.join(frontend, "Dockerfile")
        df_info = find_dockerfile_info(df)
        s.append("frontend/Dockerfile content preview:")
        s.append(read_file(df)[:2000] if read_file(df) else "MISSING")
        s.append("")
        s.append("Parsed Dockerfile info:")
        s.append(json.dumps(df_info, indent=2))
        s.append("")
        # package.json
        pj = read_file(os.path.join(frontend, "package.json"))
        s.append("frontend/package.json exists: " + ("YES" if pj else "NO"))
        if pj:
            try:
                pj_obj = json.loads(pj)
                s.append("  name: " + str(pj_obj.get("name")))
                s.append("  scripts keys: " + ", ".join(pj_obj.get("scripts", {}).keys()))
            except:
                s.append("  package.json parse failed")
        # check index.html and src/
        s.append("frontend/index.html exists: " + str(os.path.exists(os.path.join(frontend, "index.html"))))
        s.append("frontend/src exists: " + str(os.path.exists(os.path.join(frontend, "src"))))
        s.append("")
        # dockerignore
        base_dockerignore = os.path.join(ROOT, ".dockerignore")
        front_dockerignore = os.path.join(frontend, ".dockerignore")
        s.append(".dockerignore at repo root exists: " + str(os.path.exists(base_dockerignore)))
        if os.path.exists(base_dockerignore):
            s.append("--- .dockerignore (root) ---")
            s.append(read_file(base_dockerignore)[:2000])
        s.append("frontend/.dockerignore exists: " + str(os.path.exists(front_dockerignore)))
        if os.path.exists(front_dockerignore):
            s.append("--- frontend/.dockerignore ---")
            s.append(read_file(front_dockerignore)[:2000])
    # docker-compose
    dc = os.path.join(ROOT, "docker-compose.yml")
    s.append("")
    s.append("docker-compose.yml exists: " + str(os.path.exists(dc)))
    if os.path.exists(dc):
        comp = analyze_docker_compose(dc)
        s.append("--- Extracted frontend service block from docker-compose.yml ---")
        s.append(comp["frontend_block"] if comp else "COULD NOT PARSE")
    s.append("")
    s.append("Helpful automated checks:")
    s.append(" - Does docker-compose frontend define a host bind mount like './frontend:/app'?")
    s.append(" - Does docker-compose accidentally mount a named volume to /app (e.g. 'some_volume:/app') which hides host files?")
    s.append("")
    s.append("Manual next-step commands to run (paste into your shell):")
    s.append(textwrap.dedent("""
    # check mounts for the running frontend container:
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | findstr /I frontend

    # inspect mounts (use the container name shown; e.g. wqam-dashboard-frontend)
    docker inspect --format '{{json .Mounts}}' wqam-dashboard-frontend

    # list volumes:
    docker volume ls

    # inspect the named volume that might be present:
    docker volume inspect wqam-dashboard_frontend_node_modules

    # enter the container and show content and mount points:
    docker compose exec frontend sh -c "ls -la /app && mount | sed -n '1,200p'"

    # check from host (Windows) if bind mount path exists and files visible:
    dir .\\frontend
    """))
    return "\n".join(s)

if __name__ == "__main__":
    report = summary()
    print(report[:4000])
    try:
        with open(OUTFILE, "w", encoding="utf-8") as f:
            f.write(report)
        print("\nFull report written to:", OUTFILE)
    except Exception as e:
        print("Could not write report to file:", e)
