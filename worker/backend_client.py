# -*- coding: utf-8 -*-
"""后台客户端：优先连 Spring Boot；不可达时降级 standalone 本地存储（同构接口）。"""
import json
import time
from datetime import datetime, timezone

import httpx

from config import BACKEND_URL, OUT

JOB_SEED = {
    "id": 1,
    "title": "资深Java工程师（远程）",
    "jdText": "负责业务全流程自动化：Java/Spring Boot 业务服务开发，浏览器自动化与RPA，大模型在简历评估、信息理解、自动回复场景的应用。要求3年以上Java经验，熟悉Spring Boot、PostgreSQL，熟悉JavaScript/Python者优先。",
    "hardFilters": {"minYears": 3, "degree": "本科", "mustSkills": ["Java", "Spring"]},
    "rubric": {"weights": {"skill": 40, "experience": 30, "education": 20, "stability": 10}, "rejectLine": 60},
    "faq": {"薪资范围": "20-30K，14薪，具体面议", "工作地点": "杭州滨江区，支持全职远程办公",
            "远程政策": "全职远程，每季度一次线下团建", "工时制度": "弹性工作制，双休"},
    "greetingStyle": "专业、简洁、突出候选人亮点，不超过120字",
    "dailyLimit": 20,
}


def _norm_job(raw: dict) -> dict:
    j = dict(raw)
    for k in ("hardFilters", "rubric", "faq"):
        if isinstance(j.get(k), str):
            j[k] = json.loads(j[k])
    return j


class BackendClient:
    mode = "backend"

    def __init__(self):
        self.http = httpx.Client(base_url=BACKEND_URL, timeout=15)

    @staticmethod
    def probe() -> bool:
        try:
            httpx.get(f"{BACKEND_URL}/api/jobs", timeout=2).raise_for_status()
            return True
        except Exception:
            return False

    def get_job(self, job_id):
        r = self.http.get(f"/api/jobs/{job_id}"); r.raise_for_status()
        return _norm_job(r.json())
    def claim(self, job_id, worker_id):
        r = self.http.post("/api/worker/tasks/claim", json={"jobId": job_id, "workerId": worker_id})
        r.raise_for_status()
        return r.json()["id"]
    def heartbeat(self, task_id): self.http.post(f"/api/worker/tasks/{task_id}/heartbeat").raise_for_status()
    def finish(self, task_id, stats, state="FINISHED"):
        self.http.post(f"/api/worker/tasks/{task_id}/finish", json={"state": state, "stats": json.dumps(stats, ensure_ascii=False)}).raise_for_status()
    def upsert(self, cand: dict) -> dict:
        r = self.http.post("/api/worker/candidates", json=[cand]); r.raise_for_status()
        return r.json()[0]
    def create_review(self, cid, msg): self.http.post("/api/worker/reviews", json={"candidateId": cid, "proposedMessage": msg}).raise_for_status()
    def approved(self, job_id):
        r = self.http.get("/api/worker/approved", params={"jobId": job_id}); r.raise_for_status()
        return [{"candidate": x["candidate"], "message": x["message"]} for x in r.json()]
    def list_candidates(self, job_id, statuses):
        out = []
        for s in statuses:
            r = self.http.get("/api/candidates", params={"jobId": job_id, "status": s}); r.raise_for_status()
            out += r.json()
        return out
    def message(self, cid, direction, content, key, intent=None):
        self.http.post("/api/worker/messages", json={"candidateId": cid, "direction": direction,
                                                     "content": content, "idempotencyKey": key, "intent": intent}).raise_for_status()
    def set_status(self, cid, status):
        self.http.post("/api/worker/status", json={"candidateId": cid, "status": status}).raise_for_status()
    def escalate(self, cid): self.http.post(f"/api/worker/escalate/{cid}").raise_for_status()
    def incident(self, task_id, kind, detail, shot=""):
        self.http.post("/api/worker/incidents", json={"taskRunId": task_id, "kind": kind, "detail": detail, "screenshotPath": shot}).raise_for_status()


class LocalStore:
    """standalone：内存同构存储 + 运行结束落盘报告。--auto-approve 时模拟 HR 秒批。"""
    mode = "standalone"

    def __init__(self, auto_approve=False):
        self.auto_approve = auto_approve
        self.path = OUT / "local-store.json"
        self.cands: dict[str, dict] = {}
        self.reviews: list[dict] = []
        self.messages: dict[str, list] = {}
        self.incidents: list[dict] = []
        self._next_id = 1
        if self.path.exists():
            d = json.loads(self.path.read_text(encoding="utf-8"))
            self.cands, self.reviews = d["cands"], d["reviews"]
            self.messages, self.incidents = d["messages"], d["incidents"]
            self._next_id = d["next_id"]

    def _save(self):
        self.path.write_text(json.dumps({"cands": self.cands, "reviews": self.reviews,
                                         "messages": self.messages, "incidents": self.incidents,
                                         "next_id": self._next_id}, ensure_ascii=False, indent=1),
                             encoding="utf-8")

    def get_job(self, job_id): return dict(JOB_SEED, id=job_id)
    def claim(self, job_id, worker_id): return 1
    def heartbeat(self, task_id): pass
    def finish(self, task_id, stats, state="FINISHED"):
        report = {"finishedAt": datetime.now(timezone.utc).isoformat(), "state": state, "stats": stats,
                  "candidates": list(self.cands.values()), "reviews": self.reviews,
                  "messages": self.messages, "incidents": self.incidents}
        path = OUT / f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[store] standalone 运行报告: {path}")
    def upsert(self, cand: dict) -> dict:
        key = f"{cand['jobId']}-{cand['externalId']}"
        if key in self.cands:
            old = self.cands[key]
            old.update({k: v for k, v in cand.items() if k != "status"})
            self._save()
            return old
        c = dict(cand, id=self._next_id, status=cand.get("status", "SCORED"))
        self._next_id += 1
        self.cands[key] = c
        self._save()
        return c
    def create_review(self, cid, msg):
        r = {"id": len(self.reviews) + 1, "candidateId": cid, "proposedMessage": msg,
             "decision": "APPROVED" if self.auto_approve else "PENDING"}
        self.reviews.append(r)
        for c in self.cands.values():
            if c["id"] == cid:
                c["status"] = "APPROVED" if self.auto_approve else "PENDING_REVIEW"
        self._save()
    def approved(self, job_id):
        out = []
        for r in self.reviews:
            if r["decision"] != "APPROVED":
                continue
            c = next(c for c in self.cands.values() if c["id"] == r["candidateId"])
            if c["status"] == "APPROVED":
                out.append({"candidate": c, "message": r["proposedMessage"]})
        return out
    def list_candidates(self, job_id, statuses):
        return [c for c in self.cands.values() if c["status"] in statuses]
    def message(self, cid, direction, content, key, intent=None):
        msgs = self.messages.setdefault(str(cid), [])
        if any(m.get("key") == key for m in msgs):
            return
        msgs.append({"dir": direction.lower(), "content": content, "key": key, "intent": intent})
        self._save()
        for c in self.cands.values():
            if c["id"] == cid:
                if direction == "OUT" and c["status"] == "APPROVED":
                    c["status"] = "GREETED"
                if direction == "IN" and c["status"] == "GREETED":
                    c["status"] = "CHATTING"
        self._save()
    def set_status(self, cid, status):
        for c in self.cands.values():
            if c["id"] == cid:
                c["status"] = status
        self._save()
    def escalate(self, cid): self.set_status(cid, "ESCALATED")
    def incident(self, task_id, kind, detail, shot=""):
        self.incidents.append({"kind": kind, "detail": detail, "screenshot": shot})
        self._save()


def build_store(auto_approve=False):
    if BackendClient.probe():
        print(f"[store] 已连接后台 {BACKEND_URL}")
        return BackendClient()
    print(f"[store] 后台不可达，降级 standalone 模式（auto_approve={auto_approve}）")
    return LocalStore(auto_approve=auto_approve)