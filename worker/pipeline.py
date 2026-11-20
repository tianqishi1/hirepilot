# -*- coding: utf-8 -*-
"""Agent 执行循环：发现→抽取→硬条件规则→LLM评分→审核→触达→意图应答/转人工。"""
import json

from config import GREET_DELAY_RANGE, MOCK_URL, MAX_PAGES
from llm import DEGREE_RANK, AUTO_DECL
from stability import StepFailure, idem_key, throttle


def new_stats() -> dict:
    return {"discovered": 0, "hard_rejected": 0, "score_rejected": 0, "reviews": 0,
            "greeted": 0, "replies": 0, "faq_answered": 0, "interest": 0, "escalated": 0,
            "failures": 0, "skipped_existing": 0, "print_fallbacks": 0, "visual_fallbacks": 0, "send_retries": 0,
            "llm_fallbacks": 0}


def hard_check(profile: dict, hf: dict) -> tuple[bool, list[str]]:
    """确定性护栏：硬性条件绝不交给 LLM 判断。"""
    reasons = []
    if profile.get("years", 0) < hf.get("minYears", 0):
        reasons.append(f"年限 {profile.get('years', 0)} < 要求 {hf['minYears']}")
    need = hf.get("degree")
    if need and DEGREE_RANK.get(profile.get("degree", "未知"), 0) < DEGREE_RANK.get(need, 0):
        reasons.append(f"学历 {profile.get('degree')} 低于要求 {need}")
    skills_low = " ".join(profile.get("skills", [])).lower()
    for s in hf.get("mustSkills", []):
        if s.lower() not in skills_low:
            reasons.append(f"缺少必备技能 {s}")
    return (not reasons), reasons


def run_pipeline(job, llm, browser, store, ckpt, stats, task_id):
    job_id = job["id"]
    reject_line = job["rubric"].get("rejectLine", 60)

    # ---- Phase 1: 发现 + 评估 ----
    # 后台已处理过的候选人直接跳过（状态机护栏的前置检查，避免重复评估/重复送审）
    done_statuses = {"REJECTED", "PENDING_REVIEW", "APPROVED", "GREETED", "CHATTING",
                     "INTERVIEW", "ESCALATED", "CLOSED"}
    existing = {c["externalId"]: c["status"] for c in store.list_candidates(
        job_id, ["DISCOVERED", "SCORED"] + sorted(done_statuses))}
    for item in browser.discover(MOCK_URL, MAX_PAGES):
        ext = item["externalId"]
        if ckpt.seen(ext):
            continue
        if existing.get(ext) in done_statuses:
            stats["skipped_existing"] += 1
            ckpt.mark(ext)
            continue
        stats["discovered"] += 1
        try:
            resume = browser.extract_resume(item["url"])
        except StepFailure as e:
            stats["failures"] += 1
            store.incident(task_id, e.step, e.detail, e.screenshot)
            ckpt.mark(ext)
            continue
        profile = llm.extract(resume)
        hard_pass, hard_reasons = hard_check(profile, job["hardFilters"])
        result = llm.score(profile, job, resume)
        status = "SCORED"
        if not hard_pass:
            status = "REJECTED"; stats["hard_rejected"] += 1
            result["reasons"] = hard_reasons + result.get("reasons", [])
        elif result["score"] < reject_line:
            status = "REJECTED"; stats["score_rejected"] += 1
        cand = store.upsert({"jobId": job_id, "externalId": ext, "name": profile.get("name") or item["name"],
                             "resumeText": resume, "profile": json.dumps(profile, ensure_ascii=False),
                             "score": result["score"], "scoreReason": json.dumps(result, ensure_ascii=False),
                             "hardPass": hard_pass, "status": status})
        if status == "SCORED":
            msg = llm.greet(profile, job)
            store.create_review(cand["id"], msg)
            stats["reviews"] += 1
            print(f"[score] {profile.get('name')} {result['score']}分 → 待审核")
        else:
            print(f"[score] {profile.get('name')} {result['score']}分 → 拒绝 ({'; '.join(result['reasons'][:2])})")
        ckpt.mark(ext)
        throttle(0.2, 0.5)

    # ---- Phase 2: 执行已批准触达 ----
    approved = store.approved(job_id)[: job.get("dailyLimit", 20)]
    for entry in approved:
        c, msg = entry["candidate"], entry["message"]
        url = f"{MOCK_URL}/candidate/{c['externalId']}"
        try:
            retries = browser.send_message(url, msg)
            store.message(c["id"], "OUT", msg, idem_key(str(job_id), c["externalId"], msg))
            stats["greeted"] += 1
            print(f"[greet] {c['name']} 已发送 (重试{retries}次)")
        except StepFailure as e:
            stats["failures"] += 1
            store.incident(task_id, e.step, e.detail, e.screenshot)
        throttle(*GREET_DELAY_RANGE)

    # ---- Phase 3: 收回复 → 意图 → 应答/转人工 ----
    for c in store.list_candidates(job_id, ["GREETED", "CHATTING"]):
        url = f"{MOCK_URL}/candidate/{c['externalId']}"
        try:
            msgs = browser.read_messages(url)
        except StepFailure as e:
            stats["failures"] += 1
            store.incident(task_id, e.step, e.detail, e.screenshot)
            continue
        cursor = ckpt.cursor(c["externalId"])
        for m in msgs[cursor:]:
            if m["dir"] != "in":
                continue
            stats["replies"] += 1
            intent = llm.classify(m["content"])
            store.message(c["id"], "IN", m["content"], idem_key(c["externalId"], str(cursor), m["content"]), intent)
            print(f"[chat] {c['name']}: {m['content'][:30]} → {intent}")
            if intent == "FAQ":
                ans = llm.answer(m["content"], job.get("faq", {}), job)
                if ans:
                    browser.send_message(url, ans)
                    store.message(c["id"], "OUT", ans, idem_key(c["externalId"], "ans", m["content"]))
                    stats["faq_answered"] += 1
                else:
                    store.escalate(c["id"]); stats["escalated"] += 1
            elif intent == "INTEREST":
                ans = "太好了！我们稍后发您面试邀约，请留意消息。" + AUTO_DECL
                browser.send_message(url, ans)
                store.message(c["id"], "OUT", ans, idem_key(c["externalId"], "itv", m["content"]))
                store.set_status(c["id"], "INTERVIEW")
                stats["interest"] += 1
            else:   # SENSITIVE / OTHER → 转人工
                store.escalate(c["id"]); stats["escalated"] += 1
                print(f"[chat] {c['name']} 转人工处理")
            throttle(0.5, 1.0)
        ckpt.set_cursor(c["externalId"], len(msgs))

    stats["print_fallbacks"] = browser.stats["print_fallbacks"]
    stats["visual_fallbacks"] = browser.stats["visual_fallbacks"]
    stats["send_retries"] = browser.stats["send_retries"]
    stats["llm_fallbacks"] = getattr(llm, "fallbacks", 0)
    return stats