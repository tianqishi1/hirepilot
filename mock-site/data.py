# -*- coding: utf-8 -*-
"""Mock 招聘站候选人数据。简历为虚构人物，仅用于演示与评测。"""

CANDIDATES = [
    {
        "id": "c001", "name": "陈昊", "title": "Java 后端工程师 · 6年 · 本科",
        "resume": """陈昊 ｜ 男 ｜ 30岁 ｜ 本科（浙江大学 计算机科学）
工作经验：6年
技能：Java / Spring Boot / PostgreSQL / Redis / Playwright / Docker
经历：
2021-至今 某电商公司 高级Java工程师：负责订单系统 Spring Boot 微服务改造，PostgreSQL 分库分表，QPS 提升3倍。
2018-2021 某软件公司 Java工程师：用 Python+Playwright 搭建内部运营自动化平台，覆盖浏览器自动化与报表生成。
亮点：主导过 RPA 平台从0到1；熟悉大模型 API 集成。""",
        "replies": ["请问这个岗位的薪资范围大概是多少？", "条件不错，方便约个面试时间吗？"],
    },
    {
        "id": "c002", "name": "林晓雨", "title": "Java/Python 自动化工程师 · 4年 · 本科",
        "resume": """林晓雨 ｜ 女 ｜ 27岁 ｜ 本科（杭州电子科技大学 软件工程）
工作经验：4年
技能：Java / Spring / Python / Selenium / Appium / MySQL
经历：
2022-至今 某互联网公司 自动化工程师：负责移动端 Appium 自动化与桌面 RPA（Windows UIA），维护 200+ 用例。
2020-2022 某外包公司 Java开发：Spring MVC 业务系统开发。
亮点：浏览器/桌面/移动三端自动化实战经验；做过 LLM 简历解析小工具。""",
        "replies": ["远程办公是全职远程吗？还是需要坐班？", "好的，我稍后发一份最新简历给你。"],
    },
    {
        "id": "c003", "name": "王志强", "title": "Java 架构师 · 8年 · 硕士",
        "resume": """王志强 ｜ 男 ｜ 33岁 ｜ 硕士（南京大学 软件工程）
工作经验：8年
技能：Java / Spring Cloud / PostgreSQL / Kafka / Kubernetes
经历：
2019-至今 某金融科技公司 架构师：主导核心交易系统架构，团队8人。
2016-2019 某大厂 高级开发：Spring Boot 服务治理与稳定性建设。
亮点：大型系统稳定性经验丰富；期望薪资 35K 以上。""",
        "replies": ["我目前期望薪资35K以上，低于这个数就不用聊了，能满足吗？"],
    },
    {
        "id": "c004", "name": "赵敏", "title": "Java 开发 · 2年 · 本科",
        "resume": """赵敏 ｜ 女 ｜ 24岁 ｜ 本科（浙江工业大学）
工作经验：2年
技能：Java / Spring Boot / MySQL
经历：
2024-至今 某创业公司 Java开发：CRUD 业务模块开发。
亮点：学习能力强，但经验尚浅。""",
        "replies": ["请问加班多吗？"],
    },
    {
        "id": "c005", "name": "李强", "title": "PHP 开发 · 5年 · 本科",
        "resume": """李强 ｜ 男 ｜ 28岁 ｜ 本科
工作经验：5年
技能：PHP / Laravel / MySQL / Vue
经历：
2021-至今 某电商公司 PHP开发：商城系统开发与维护。
2019-2021 某工作室 全栈：Laravel + Vue 外包项目。""",
        "replies": ["你们接受转Java吗？"],
    },
    {
        "id": "c006", "name": "孙丽", "title": "Java 开发 · 4年 · 大专",
        "resume": """孙丽 ｜ 女 ｜ 26岁 ｜ 大专（某职业技术学院 计算机应用）
工作经验：4年
技能：Java / Spring / MyBatis / MySQL
经历：
2022-至今 某软件公司 Java开发：政企项目后端开发。
2020-2022 某公司 初级开发。""",
        "replies": ["学历是硬性要求吗？"],
    },
    {
        "id": "c007", "name": "周涛", "title": "自动化/Agent 工程师 · 5年 · 本科",
        "resume": """周涛 ｜ 男 ｜ 29岁 ｜ 本科（华中科技大学）
工作经验：5年
技能：Java / Spring Boot / Python / Playwright / 视觉Agent / 多模态大模型
经历：
2022-至今 某AI公司 Agent工程师：构建视觉Agent执行闭环（截图理解→工具调用→自动执行），负责评测与持续优化。
2019-2022 某公司 Java开发：Spring Boot 业务服务。
亮点：视觉Agent落地经验稀缺且对口；主导过自动化系统长期维护与故障诊断。""",
        "replies": ["这个岗位需要出差吗？", "好的，期待进一步沟通，我随时可以面试。"],
        "obfuscated": True,
    },
    {
        "id": "c008", "name": "吴倩", "title": "测试开发 · 3年 · 本科",
        "resume": """吴倩 ｜ 女 ｜ 26岁 ｜ 本科（宁波大学）
工作经验：3年
技能：Java / Spring / JUnit / Selenium / Python
经历：
2023-至今 某公司 测试开发：Java 测试框架与 Selenium UI 自动化。
亮点：有自动化经验，但业务开发经验偏少。""",
        "replies": ["你们主要用什么技术栈？", "听起来不错，可以再聊聊。"],
    },
    {
        "id": "c009", "name": "郑凯", "title": "资深 Java · 10年 · 本科",
        "resume": """郑凯 ｜ 男 ｜ 35岁 ｜ 本科（西安电子科技大学）
工作经验：10年
技能：Java / Spring Boot / PostgreSQL / Python / RPA
经历：
2018-至今 某上市公司 技术专家：业务中台与流程自动化，带4人小组。
2014-2018 某公司 高级开发。
亮点：业务全流程自动化经验完整；有团队管理经验。""",
        "replies": ["请问团队规模多大？向谁汇报？", "可以，约个时间面试吧。"],
    },
    {
        "id": "c010", "name": "何静", "title": "前端工程师 · 3年 · 本科",
        "resume": """何静 ｜ 女 ｜ 25岁 ｜ 本科
工作经验：3年
技能：JavaScript / TypeScript / React / CSS
经历：
2023-至今 某公司 前端开发：中后台系统前端。
亮点：熟悉浏览器运行机制，但无 Java 后端经验。""",
        "replies": ["这个岗位是纯后端吗？"],
    },
]

BY_ID = {c["id"]: c for c in CANDIDATES}
PAGE_SIZE = 4