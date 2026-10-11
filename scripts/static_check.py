from pathlib import Path
import re,sys
R=Path(__file__).resolve().parents[1];errors=[];checked=0
html=(R/"index.html").read_text()
for target in re.findall(r'(?:href|src)=[\"\']([^\"\']+)',html,re.I):
 if target.startswith(("#","mailto:","tel:")):continue
 if re.match(r"^[a-z]+:",target,re.I) or target.startswith("//"):errors.append("External URL in index.html: "+target);continue
 path=target.split("?",1)[0].split("#",1)[0]
 if path and not (R/path).resolve().is_file():errors.append("Missing local link/asset: "+target)
 elif path:checked+=1
for p in R.rglob("*"):
 if not p.is_file() or ".git" in p.parts:continue
 if p.suffix.lower() in (".js",".html",".css"):
  t=p.read_text(errors="ignore")
  for pat in (r"AKIA[0-9A-Z]{16}",r"gh[pousr]_[A-Za-z0-9]{30,}",r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",r"sk-[A-Za-z0-9]{20,}"):
   if re.search(pat,t):errors.append("Possible secret pattern: "+str(p.relative_to(R)))
  if p.suffix==".html" and re.search(r'<(?:script|link)[^>]+(?:src|href)=[\"\']https?://',t,re.I):errors.append("External runtime asset: "+str(p.relative_to(R)))
if "/SYJ-Video-Forge/" not in (R/"README.md").read_text():errors.append("Pages subpath not documented")
if errors:
 print("STATIC CHECK: FAIL");[print(" - "+e) for e in errors];sys.exit(1)
print(f"STATIC CHECK: PASS ({checked} local HTML links/assets resolved; no external runtime URLs or known secret patterns; Pages subpath documented)")
