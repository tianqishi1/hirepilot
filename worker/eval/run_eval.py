# -*- coding: utf-8 -*-
"""评估回归：shortlist 准确率 / 硬条件误放行(必须=0) / 分数 MAE。
MockLLM 与真实 LLM 共用本入口；模型或 prompt 改动先跑回归再上线。
用法: python run_eval.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # worker/
sys.path.insert(0, str(HERE.parent.parent / "mock-site"))

from backend_client import JOB_SEED
from llm import build_llm
from pipeline import hard_check


def main():
    rows = [json.loads(l) for l in (HERE / "dataset.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    llm = build_llm()
    job = JOB_SEED
    correct, leaks, aes, details = 0, 0, [], []
    for r in rows:
        p = llm.extract(r["resume"])
        ok, reasons = hard_check(p, job["hardFilters"])
        s = llm.score(p, job, r["resume"])["score"]
        pred = ok and s >= job["rubric"]["rejectLine"]
        hit = pred == r["shortlist"]
        correct += hit
        if pred and not ok:
            leaks += 1
        aes.append(abs(s - r["expected_score"]))
        details.append({"id": r["id"], "name": p.get("name"), "score": s, "pred": pred,
                        "label": r["shortlist"], "hit": hit})
        print(f"{'OK ' if hit else 'MISS'} {r['id']} {p.get('name')}: score={s} pred={pred} label={r['shortlist']}")
    n = len(rows)
    report = {"n": n, "accuracy": round(correct / n, 3), "hard_filter_leaks": leaks,
              "score_mae": round(sum(aes) / n, 1), "llm": llm.name, "details": details}
    out = HERE / "last_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n准确率 {report['accuracy']:.0%} | 硬条件误放行 {leaks} (红线=0) | 分数MAE {report['score_mae']}")
    print(f"报告: {out}")
    if leaks > 0 or report["accuracy"] < 0.8:
        sys.exit(1)


if __name__ == "__main__":
    main()