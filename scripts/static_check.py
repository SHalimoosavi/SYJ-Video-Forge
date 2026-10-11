from pathlib import Path
import re, sys
R=Path(__file__).resolve().parents[1]
errors=[]
required=["index.html","styles.css","src/app.js","src/core.js","src/providers.js","backend/server.py","backend/jobs.py","backend/media.py","backend/config.py","backend/providers/base.py","backend/providers/testpattern.py","backend/tests/test_backend.py","scripts/build-site.sh","scripts/build-site.ps1","docs/QA-CHECKLIST.md"]
for rel in required:
    if not (R/rel).is_file():errors.append("Missing required file: "+rel)
html=(R/"index.html").read_text(encoding="utf-8")
for target in re.findall(r'(?:href|src)=["\']([^"\']+)',html,re.I):
    if target.startswith(("#","mailto:","tel:")):continue
    if re.match(r"^[a-z]+:",target,re.I) or target.startswith("//"):
        if target.startswith(("http://","https://")):errors.append("External runtime asset/link in index.html: "+target)
        continue
    path=target.split("?",1)[0].split("#",1)[0]
    if path and not (R/path).resolve().is_file():errors.append("Missing local link/asset: "+target)
# Detect common secret formats in source and docs; don't inspect generated binaries or Git internals.
for p in R.rglob("*"):
    if not p.is_file() or any(part in {".git","__pycache__","site","data"} for part in p.parts):continue
    if p.suffix.lower() in {".js",".html",".css",".py",".yml",".yaml",".md",".ps1",".sh"}:
        text=p.read_text(encoding="utf-8",errors="ignore")
        for pat in (r"AKIA[0-9A-Z]{16}",r"gh[pousr]_[A-Za-z0-9]{30,}",r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",r"sk-[A-Za-z0-9]{20,}"):
            if re.search(pat,text):errors.append("Possible secret pattern: "+str(p.relative_to(R)))
# Confirm the generated Pages artifact contains only the intended static files.
site=R/"site"
expected={"index.html","styles.css","src/app.js","src/core.js","src/providers.js"}
if not site.is_dir():errors.append("Missing generated site/ directory; run scripts/build-site.sh first")
else:
    actual={str(p.relative_to(site)).replace("\\","/") for p in site.rglob("*") if p.is_file()}
    if actual!=expected:errors.append(f"site/ file set mismatch: expected {sorted(expected)}, got {sorted(actual)}")
    if any(p.suffix.lower() in {".py",".yml",".yaml",".md"} for p in site.rglob("*")):errors.append("Non-site project files found in site/ output")
if "Settings" not in (R/"README.md").read_text(encoding="utf-8") or "GitHub Actions" not in (R/"README.md").read_text(encoding="utf-8"):errors.append("README must document Pages Source = GitHub Actions")
if "test_pattern" not in (R/"src/app.js").read_text(encoding="utf-8"):errors.append("Frontend must label test-pattern output")
if errors:
    print("STATIC CHECK: FAIL");[print(" - "+e) for e in errors];sys.exit(1)
print(f"STATIC CHECK: PASS ({len(required)} required files; {len(expected)} built-site files; local links resolved; no known secret patterns)")
