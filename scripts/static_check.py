from pathlib import Path
import re, sys
R=Path(__file__).resolve().parents[1]
errors=[]
required=["index.html","styles.css","src/app.js","src/core.js","src/providers.js","src/bundles.js","src/bundle-flow.js","backend/server.py","backend/jobs.py","backend/media.py","backend/config.py","backend/providers/base.py","backend/providers/testpattern.py","backend/tests/test_backend.py","worker/__main__.py","worker/cli.py","worker/schema.py","worker/runtime.py","worker/engines/fake.py","worker/tests/test_worker.py","worker/notebook/syj_video_forge_gpu.ipynb","scripts/build-site.sh","scripts/build-site.ps1","scripts/test_notebook.py","docs/QA-CHECKLIST.md","docs/BUNDLE-FORMAT.md","docs/WORKER-VERIFY.md","docs/WORKER-LIVE.md","docs/PLATFORM-POLICIES.md","docs/verification/REPORT-TEMPLATE.md"]
for rel in required:
    if not (R/rel).is_file(): errors.append("Missing required file: "+rel)
html=(R/"index.html").read_text(encoding="utf-8")
# Runtime assets must remain local. Plain documentation anchors are allowed only when explicitly protected.
for tag in re.findall(r'<(script|link|a)\b([^>]*)>',html,re.I):
    name,attrs=tag
    for attr,target in re.findall(r'\b(href|src)=["\']([^"\']+)',attrs,re.I):
        if target.startswith(("#","mailto:","tel:")): continue
        if re.match(r"^[a-z]+:",target,re.I) or target.startswith("//"):
            is_doc_anchor=name.lower()=="a" and attr.lower()=="href" and "noopener" in attrs.lower() and "noreferrer" in attrs.lower()
            if not is_doc_anchor: errors.append(f"External runtime asset/link in {name}: {target}")
            continue
        path=target.split("?",1)[0].split("#",1)[0]
        if path and not (R/path).resolve().is_file(): errors.append("Missing local link/asset: "+target)
# No literal remote fetch endpoint or remote script/link asset in runtime source.
for rel in ("src/app.js","src/core.js","src/providers.js","src/bundles.js","src/bundle-flow.js","index.html","styles.css"):
    text=(R/rel).read_text(encoding="utf-8",errors="ignore")
    if re.search(r'fetch\s*\(\s*[`\'"]https?://',text,re.I): errors.append("Literal external fetch URL in "+rel)
    if re.search(r'<script[^>]+src=["\']https?://|<link[^>]+href=["\']https?://',text,re.I): errors.append("External runtime script/link asset in "+rel)
    for attrs in re.findall(r'<a\b([^>]*)>',text,re.I):
        if re.search(r'href=["\']https?://',attrs,re.I) and not ("noopener" in attrs.lower() and "noreferrer" in attrs.lower()):
            errors.append("External documentation anchor must use rel=\"noopener noreferrer\": "+rel)
# Detect common secret formats; skip generated site, local data, and bytecode.
for p in R.rglob("*"):
    if not p.is_file() or any(part in {".git","__pycache__","site","data"} for part in p.parts): continue
    if p.suffix.lower() in {".js",".html",".css",".py",".yml",".yaml",".md",".ps1",".sh",".txt",".ipynb"}:
        text=p.read_text(encoding="utf-8",errors="ignore")
        for pat in (r"AKIA[0-9A-Z]{16}",r"gh[pousr]_[A-Za-z0-9]{30,}",r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",r"sk-[A-Za-z0-9]{20,}"):
            if re.search(pat,text): errors.append("Possible secret pattern: "+str(p.relative_to(R)))
site=R/"site"
expected={"index.html","styles.css","src/app.js","src/core.js","src/providers.js","src/bundles.js","src/bundle-flow.js"}
if not site.is_dir(): errors.append("Missing generated site/ directory; run scripts/build-site.sh first")
else:
    actual={str(p.relative_to(site)).replace("\\","/") for p in site.rglob("*") if p.is_file()}
    if actual!=expected: errors.append(f"site/ file set mismatch: expected {sorted(expected)}, got {sorted(actual)}")
    if any(p.suffix.lower() in {".py",".yml",".yaml",".md"} for p in site.rglob("*")): errors.append("Non-site project files found in site/ output")
if "Settings" not in (R/"README.md").read_text(encoding="utf-8") or "GitHub Actions" not in (R/"README.md").read_text(encoding="utf-8"): errors.append("README must document Pages Source = GitHub Actions")
if "test_pattern" not in (R/"src/app.js").read_text(encoding="utf-8"): errors.append("Frontend must label test-pattern output")
if "UNVERIFIED ON REAL HARDWARE" not in (R/"README.md").read_text(encoding="utf-8") or "UNVERIFIED ON REAL HARDWARE" not in (R/"docs/MODELS.md").read_text(encoding="utf-8"): errors.append("Hardware verification status must be disclosed")
if errors:
    print("STATIC CHECK: FAIL"); [print(" - "+e) for e in errors]; sys.exit(1)
print(f"STATIC CHECK: PASS ({len(required)} required files; {len(expected)} built-site files; local runtime assets; documented external anchors allowed; no known secret patterns)")
