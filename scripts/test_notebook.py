import json, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/"worker/notebook/syj_video_forge_gpu.ipynb"
try: nb=json.loads(p.read_text(encoding="utf-8"))
except Exception as exc: print(f"NOTEBOOK CHECK: FAIL ({exc})"); sys.exit(1)
if nb.get("nbformat")!=4 or not isinstance(nb.get("cells"),list): print("NOTEBOOK CHECK: FAIL (invalid nbformat 4 structure)"); sys.exit(1)
source="\n".join("".join(c.get("source",[])) for c in nb["cells"])
code_cells=0
for index, cell in enumerate(nb["cells"]):
    if cell.get("cell_type")=="code":
        try: compile("".join(cell.get("source",[])), f"{p}:cell-{index}", "exec")
        except SyntaxError as exc: print(f"NOTEBOOK CHECK: FAIL (code cell {index}: {exc})"); sys.exit(1)
        code_cells += 1
checks=["Kaggle","Colab","smoke-test","requirements-worker.txt","job.json","result.mp4","manifest.json","HF_TOKEN","UNVERIFIED ON REAL HARDWARE"]
missing=[x for x in checks if x not in source]
if missing: print("NOTEBOOK CHECK: FAIL missing "+", ".join(missing)); sys.exit(1)
if not any(c.get("cell_type")=="code" for c in nb["cells"]) or not any(c.get("cell_type")=="markdown" for c in nb["cells"]): print("NOTEBOOK CHECK: FAIL (missing markdown or code cells)"); sys.exit(1)
print(f"NOTEBOOK CHECK: PASS (nbformat 4, {len(nb['cells'])} cells, {code_cells} code cells compile, required platform/worker sections present)")
