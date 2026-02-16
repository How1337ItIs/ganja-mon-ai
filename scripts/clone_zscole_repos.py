#!/usr/bin/env python3
"""Clone all public repos from GitHub user zscole into cloned-repos/zscole/."""
import json
import os
import subprocess
import urllib.request

BASE = os.path.join(os.path.dirname(__file__), "cloned-repos", "zscole")
API = "https://api.github.com/users/zscole/repos?per_page=100"

def main():
    os.makedirs(BASE, exist_ok=True)
    repos = []
    page = 1
    while True:
        url = f"{API}&page={page}" if page > 1 else API
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode())
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1

    cloned = 0
    skipped = 0
    failed = []
    for repo in repos:
        name = repo["name"]
        clone_url = repo["clone_url"]
        dest = os.path.join(BASE, name)
        if os.path.isdir(dest) and os.path.isdir(os.path.join(dest, ".git")):
            skipped += 1
            continue
        print(f"Cloning {name}...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, dest],
                check=True,
                capture_output=True,
                timeout=300,
                cwd=os.path.dirname(__file__),
            )
            cloned += 1
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            failed.append((name, str(e)))
            print(f"  FAILED: {e}")

    print(f"\nDone: {cloned} cloned, {skipped} skipped (already present), {len(failed)} failed.")
    if failed:
        for name, err in failed:
            print(f"  - {name}: {err}")

if __name__ == "__main__":
    main()
