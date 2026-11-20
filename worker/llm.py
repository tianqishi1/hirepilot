# -*- coding: utf-8 -*-
"""LLM 层：OpenAI 兼容接口（可接 DashScope/OpenAI/本地 vLLM），无 Key 自动降级 MockLLM。
MockLLM 为确定性规则实现，保证离线可演示、评测可复现；真实模型与 Mock 共用同一接口与评测入口。
"""
import json
import re

import httpx

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

DEGREE_RANK = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}
KNOWN_SKILLS = ["Java", "Spring Boot", "Spring Cloud", "Spring MVC", "Spring", "Python",
                "Playwright", "Selenium", "Appium", "PostgreSQL", "MySQL", "Redis", "Kafka",
                "Docker", "Kubernetes", "RPA", "视觉Agent", "多模态", "JavaScript",
                "TypeScript", "React", "PHP", "Laravel", "Vue", "JUnit", "MyBatis"]
BONUS_SKILLS = {"Python", "Playwright", "Selenium", "Appium", "RPA", "视觉Agent", "多模态", "PostgreSQL"}
AUTO_DECL = "（本消息由招聘助手自动发送）"


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, flags=re.S)
    return json.loads(m.group(0) if m else text)


class MockLLM:
    name = "mock"

    def extract(self, resume: str) -> dict:
        name = re.split(r"[｜|]", resume.strip().splitlines()[0])[0].strip()
        years = int(m.group(1)) if (m := re.search(r"工作经验[：:]\s*(\d+)", resume)) else 0
        degree = next((d for d in ["博士", "硕士", "本科", "大专"] if d in resume), "未知")
        low = resume.lower()
        skills = [s for s in KNOWN_SKILLS if s.lower() in low]
        if any(s.startswith("Spring") for s in skills) and "Spring" not in skills:
            skills.append("Spring")
        highlight = m.group(1).strip() if (m := re.search(r"亮点[：:](.+)", resume)) else ""
        salary = int(m.group(1)) if (m := re.search(r"期望薪资\s*(\d+)\s*K", resume, re.I)) else None
        return {"name": name, "years": years, "degree": degree, "skills": skills,
                "highlight": highlight, "expectedSalaryK": salary}

    def score(self, profile: dict, job: dict, resume: str) -> dict:
        must = job["hardFilters"].get("mustSkills", [])
        covered = [s for s in must if any(s.lower() in k.lower() for k in profile["skills"])]
        skill = 30 * len(covered) / max(1, len(must))
        skill += min(10, 2 * len(BONUS_SKILLS & set(profile["skills"])))
        hits = sum(1 for kw in ["自动化", "Agent", "RPA", "微服务", "架构", "稳定性"] if kw.lower() in resume.lower())
        exp = min(30, (6 if profile["years"] >= 3 else 0) + 8 * hits)
        edu = {"博士": 20, "硕士": 20, "本科": 16, "大专": 8}.get(profile["degree"], 5)
        stab = 10 if profile["years"] >= 5 else 8 if profile["years"] >= 3 else 5
        total = round(min(100, skill + exp + edu + stab))
        reasons = [f"必备技能覆盖 {len(covered)}/{len(must)}", f"相关经验关键词命中 {hits} 项",
                   f"学历 {profile['degree']}，{profile['years']} 年经验"]
        risks = []
        if profile.get("expectedSalaryK") and profile["expectedSalaryK"] > 30:
            risks.append(f"期望薪资 {profile['expectedSalaryK']}K 超出预算")
        return {"score": total, "reasons": reasons, "risks": risks}

    def greet(self, profile: dict, job: dict) -> str:
        hi = (profile.get("highlight") or "、".join(profile["skills"][:3]))[:40]
        return (f"您好{profile['name']}！您在{hi}方面的经验与我们「{job['title']}」岗位很契合，"
                f"团队支持全职远程。方便进一步沟通吗？{AUTO_DECL}")[:120]

    def classify(self, text: str) -> str:
        if re.search(r"\d+\s*K|不然免谈|低于这个数|投诉|合同条款", text):
            return "SENSITIVE"
        if re.search(r"约.*面试|面试.*时间|可以.*聊|再聊|期待|发.*简历|随时可以", text):
            return "INTEREST"
        if re.search(r"[？?]|吗$", text) and re.search(r"薪资|远程|坐班|技术栈|团队|出差|加班|学历|汇报|工时", text):
            return "FAQ"
        return "OTHER"

    def answer(self, question: str, faq: dict, job: dict) -> str | None:
        rules = [("薪资", "薪资范围"), ("远程|坐班", "远程政策"), ("地点|在哪", "工作地点"),
                 ("加班|工时|双休", "工时制度")]
        for pat, key in rules:
            if re.search(pat, question) and key in faq:
                return faq[key] + AUTO_DECL
        if re.search(r"技术栈", question):
            return "主要技术栈为 Java/Spring Boot + PostgreSQL，自动化侧用 Python/Playwright。" + AUTO_DECL
        if re.search(r"团队|汇报", question):
            return "团队目前约10人，该岗位直接汇报给研发负责人。" + AUTO_DECL
        if re.search(r"出差", question):
            return "该岗位无需出差，支持全职远程。" + AUTO_DECL
        return None


class ApiLLM(MockLLM):
    """真实 LLM：同一接口，失败逐次降级到 Mock 规则，保证流程不中断。"""
    name = "api"

    def __init__(self):
        self.client = httpx.Client(base_url=LLM_BASE_URL, timeout=60,
                                   headers={"Authorization": f"Bearer {LLM_API_KEY}"})
        self.fallbacks = 0

    def _chat(self, system: str, user: str) -> str:
        r = self.client.post("/chat/completions", json={
            "model": LLM_MODEL, "temperature": 0,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def _safe(self, fn, mock_fn, *args):
        try:
            return fn()
        except Exception as e:
            self.fallbacks += 1
            print(f"[llm] API 失败降级 Mock ({e.__class__.__name__})")
            return mock_fn(*args)

    def extract(self, resume: str) -> dict:
        def call():
            out = self._chat("你是简历解析器。只输出 JSON，字段: name,years(整数),degree(大专/本科/硕士/博士),skills(数组),highlight(字符串),expectedSalaryK(整数或null)。", resume)
            p = _parse_json(out)
            p.setdefault("skills", []); p.setdefault("years", 0)
            return p
        return self._safe(call, super().extract, resume)

    def score(self, profile: dict, job: dict, resume: str) -> dict:
        def call():
            sys = ("你是招聘初筛评估器。按 rubric 权重打分(0-100)：技能匹配40/经验相关30/年限学历20/稳定性10。"
                   "只输出 JSON: {score, reasons:[...], risks:[...]}。硬性条件由规则引擎另行校验，你只评估软匹配。")
            user = json.dumps({"rubric": job["rubric"], "jd": job["jdText"], "profile": profile, "resume": resume}, ensure_ascii=False)
            return _parse_json(self._chat(sys, user))
        return self._safe(call, super().score, profile, job, resume)

    def greet(self, profile: dict, job: dict) -> str:
        def call():
            sys = (f"你是招聘顾问。写一条≤120字的个性化打招呼：引用候选人1-2个真实亮点+职位卖点，风格：{job.get('greetingStyle','专业简洁')}。"
                   f"结尾必须附：{AUTO_DECL}")
            return self._chat(sys, json.dumps({"profile": profile, "job": job["title"]}, ensure_ascii=False)).strip()
        return self._safe(call, super().greet, profile, job)

    def classify(self, text: str) -> str:
        def call():
            out = self._chat("对候选人消息分类，只输出一个词: FAQ(常见问题)/INTEREST(表达意向或约面)/SENSITIVE(谈薪施压、投诉、合同等需人工)/OTHER。", text)
            label = out.strip().upper()
            return label if label in {"FAQ", "INTEREST", "SENSITIVE", "OTHER"} else "OTHER"
        return self._safe(call, super().classify, text)

    def answer(self, question: str, faq: dict, job: dict) -> str | None:
        def call():
            sys = ("你是招聘助理。仅依据 FAQ 知识库回答候选人问题，≤80字，不得编造承诺；知识库覆盖不了就只输出 ESCALATE。"
                   f"回答结尾附：{AUTO_DECL}")
            out = self._chat(sys, json.dumps({"faq": faq, "question": question}, ensure_ascii=False)).strip()
            return None if "ESCALATE" in out else out
        return self._safe(call, super().answer, question, faq, job)


def build_llm():
    if LLM_API_KEY:
        print(f"[llm] 使用真实模型 {LLM_MODEL} @ {LLM_BASE_URL}")
        return ApiLLM()
    print("[llm] 未配置 LLM_API_KEY，使用离线 MockLLM（确定性规则）")
    return MockLLM()