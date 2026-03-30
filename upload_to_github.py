#!/usr/bin/env python3
"""Upload all public/ files to GitHub using Git data API (tree+commit)."""
import os, base64, json, subprocess, sys

REPO = "arturo1503/smokescan"
BRANCH = "main"
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
VERCEL_JSON = os.path.join(os.path.dirname(__file__), "vercel.json")

# Get the GitHub token from the MCP server
def get_github_token():
    """Try to find the GitHub token."""
    # Try environment variable
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    # Try gh CLI
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return ""

token = get_github_token()
if not token:
    print("ERROR: No GitHub token found. Set GITHUB_TOKEN env var or login with 'gh auth login'")
    sys.exit(1)

import urllib.request

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
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode()[:200]}")
        raise

# 1. Get current commit SHA
print("Getting current commit...")
ref = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
current_sha = ref["object"]["sha"]
print(f"  Current commit: {current_sha[:8]}")

# 2. Get current tree
commit = api("GET", f"/repos/{REPO}/git/commits/{current_sha}")
base_tree_sha = commit["tree"]["sha"]

# 3. Collect all files
tree_items = []
file_count = 0

for root, dirs, files in os.walk(PUBLIC_DIR):
    for fname in files:
        filepath = os.path.join(root, fname)
        relpath = "public/" + os.path.relpath(filepath, PUBLIC_DIR)
        
        with open(filepath, "rb") as f:
            content = f.read()
        
        # Create blob
        b64 = base64.b64encode(content).decode()
        blob = api("POST", f"/repos/{REPO}/git/blobs", {
            "content": b64,
            "encoding": "base64"
        })
        
        tree_items.append({
            "path": relpath,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"]
        })
        file_count += 1
        print(f"  [{file_count}] {relpath} ({len(content)} bytes)")

# Also add vercel.json
with open(VERCEL_JSON, "rb") as f:
    content = f.read()
b64 = base64.b64encode(content).decode()
blob = api("POST", f"/repos/{REPO}/git/blobs", {"content": b64, "encoding": "base64"})
tree_items.append({"path": "vercel.json", "mode": "100644", "type": "blob", "sha": blob["sha"]})
print(f"  [{file_count+1}] vercel.json")

# 4. Create tree
print(f"\nCreating tree with {len(tree_items)} files...")
tree = api("POST", f"/repos/{REPO}/git/trees", {
    "base_tree": base_tree_sha,
    "tree": tree_items
})
print(f"  Tree SHA: {tree['sha'][:8]}")

# 5. Create commit
print("Creating commit...")
new_commit = api("POST", f"/repos/{REPO}/git/commits", {
    "message": "feat: add full SmokeStudio website with all pages, images, and SmokeScan integration\n\n- Homepage (index.html) with full SmokeStudio landing\n- Services page (servicios.html)\n- About Us page (nosotros.html)\n- Contact page (contacto.html)\n- Blog page (blog.html)\n- All images and SVG assets (172 files)\n- CSS files (landing.css, styles.css)\n- SmokeScan moved to /smokescan/ subdirectory\n- Updated vercel.json routing\n- Back to Studio link in SmokeScan header",
    "tree": tree["sha"],
    "parents": [current_sha]
})
print(f"  Commit SHA: {new_commit['sha'][:8]}")

# 6. Update ref
api("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}", {
    "sha": new_commit["sha"]
})
print(f"\n✅ Pushed {len(tree_items)} files to {REPO}/main")
