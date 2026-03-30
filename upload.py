#!/usr/bin/env python3
"""Upload files to GitHub using Git Data API via MCP-style auth."""
import os, base64, json, urllib.request, urllib.error, sys

REPO = "arturo1503/smokescan"
BRANCH = "main"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
VERCEL_JSON = os.path.join(BASE_DIR, "vercel.json")

# Token passed as argument
if len(sys.argv) < 2:
    print("Usage: python3 upload.py <GITHUB_TOKEN>")
    sys.exit(1)
token = sys.argv[1]

def api(method, path, data=None):
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = json.dumps(data).encode() if data else None
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# 1. Get current commit
print("Getting current commit...")
ref = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
current_sha = ref["object"]["sha"]
commit = api("GET", f"/repos/{REPO}/git/commits/{current_sha}")
base_tree = commit["tree"]["sha"]
print(f"  Current: {current_sha[:8]}")

# 2. Create blobs for all files
tree_items = []
count = 0

for root, dirs, files in os.walk(PUBLIC_DIR):
    for fname in sorted(files):
        filepath = os.path.join(root, fname)
        relpath = "public/" + os.path.relpath(filepath, PUBLIC_DIR)
        with open(filepath, "rb") as f:
            content = f.read()
        b64 = base64.b64encode(content).decode()
        blob = api("POST", f"/repos/{REPO}/git/blobs", {"content": b64, "encoding": "base64"})
        tree_items.append({"path": relpath, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        count += 1
        print(f"  [{count}] {relpath} ({len(content)} bytes)")

# Add vercel.json
with open(VERCEL_JSON, "rb") as f:
    content = f.read()
b64 = base64.b64encode(content).decode()
blob = api("POST", f"/repos/{REPO}/git/blobs", {"content": b64, "encoding": "base64"})
tree_items.append({"path": "vercel.json", "mode": "100644", "type": "blob", "sha": blob["sha"]})
count += 1
print(f"  [{count}] vercel.json")

# 3. Create tree
print(f"\nCreating tree ({len(tree_items)} items)...")
tree = api("POST", f"/repos/{REPO}/git/trees", {"base_tree": base_tree, "tree": tree_items})

# 4. Create commit
msg = """feat: add full SmokeStudio website with all pages and SmokeScan integration

- Homepage with full SmokeStudio landing page
- Services, About Us, Contact, Blog pages
- All images and SVG assets
- SmokeScan moved to /smokescan/ subdirectory
- Updated vercel.json routing"""

new_commit = api("POST", f"/repos/{REPO}/git/commits", {
    "message": msg, "tree": tree["sha"], "parents": [current_sha]
})

# 5. Update ref
api("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}", {"sha": new_commit["sha"]})
print(f"\n✅ Pushed {len(tree_items)} files! Commit: {new_commit['sha'][:8]}")
