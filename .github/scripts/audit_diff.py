"""Fail if the PR's requirements introduce vulnerabilities not already present on the base branch."""
import json, sys

def ids(path):
    data = json.load(open(path))
    out = set()
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            out.add((dep["name"].lower(), v["id"]))
    return out

head, base = ids(sys.argv[1]), ids(sys.argv[2])
new = sorted(head - base)
print(f"head vulns: {len(head)}, base vulns: {len(base)}, fixed by this change: {len(base - head)}")
for name, vid in new:
    print(f"NEW: {name} {vid}")
sys.exit(1 if new else 0)
