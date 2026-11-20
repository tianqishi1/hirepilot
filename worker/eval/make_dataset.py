# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "mock-site"))
from data import CANDIDATES
LABELS = {"c001": (True, 85), "c002": (True, 82), "c003": (True, 80), "c004": (False, 45),
          "c005": (False, 30), "c006": (False, 55), "c007": (True, 92), "c008": (True, 68),
          "c009": (True, 78), "c010": (False, 35)}
out = Path(__file__).resolve().parent / "dataset.jsonl"
with out.open("w", encoding="utf-8") as f:
    for c in CANDIDATES:
        sl, es = LABELS[c["id"]]
        f.write(json.dumps({"id": c["id"], "resume": c["resume"], "shortlist": sl,
                            "expected_score": es}, ensure_ascii=False) + "\n")
print("dataset:", out, len(CANDIDATES), "rows")