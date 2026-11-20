# -*- coding: utf-8 -*-
"""UI 验收：真点按钮走 筛选→审批→触达 流程并截图。"""
import httpx
from playwright.sync_api import sync_playwright

SHOT = r"D:\codex\hirepilot\docs"
httpx.post("http://127.0.0.1:8080/api/dev/reset", params={"jobId": 1})
httpx.post("http://127.0.0.1:9000/api/reset")

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://127.0.0.1:8080", wait_until="networkidle")
    page.wait_for_selector(".fcard")
    print("页面加载 OK, Worker:", page.inner_text("#worker-text"))

    def wait_run_done(timeout=180000):
        page.wait_for_selector("#run-banner:not(.hidden)", timeout=15000)  # 先等横幅出现(轮询≤3s)
        page.wait_for_selector("#run-banner.hidden", state="attached", timeout=timeout)
        page.wait_for_timeout(800)

    # 1) 筛选：等任务完成再数卡片
    page.click("#btn-screen")
    page.wait_for_selector(".review-card", timeout=120000)
    wait_run_done()
    n = page.locator(".review-card").count()
    print(f"筛选完成，审核队列 {n} 条")
    page.screenshot(path=f"{SHOT}\\ui-1-reviews.png", full_page=True)

    # 2) 批准第一条
    page.locator(".review-card .btn.green").first.click()
    page.wait_for_timeout(1200)
    print("批准第一条 OK, toast:", page.inner_text("#toast"))

    # 3) 执行触达：等完成
    page.click("#btn-engage")
    wait_run_done()
    page.click('.tab[data-tab="candidates"]')
    page.wait_for_selector("table tr.clickable")
    page.screenshot(path=f"{SHOT}\\ui-2-candidates.png", full_page=True)

    # 4) 候选人详情弹窗
    page.locator("tr.clickable").first.click()
    page.wait_for_selector("#modal-cand .chat")
    page.screenshot(path=f"{SHOT}\\ui-3-detail.png")
    print("详情弹窗 OK, 消息数:", page.locator("#modal-cand .bubble").count())
    page.locator("#modal-cand [data-close]").click()

    # 5) 运行记录
    page.click('.tab[data-tab="runs"]')
    page.wait_for_selector("#tab-runs table")
    page.screenshot(path=f"{SHOT}\\ui-4-runs.png", full_page=True)
    print("运行记录 OK")
    b.close()
print("UI 验收完成")