# -*- coding: utf-8 -*-
"""Vue 控制台多视图截图验收"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8080"
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 950})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1800)
    page.screenshot(path="docs/ui-vue-1-reviews.png", full_page=True)
    # 候选人页
    page.click("text=候选人")
    page.wait_for_timeout(800)
    page.screenshot(path="docs/ui-vue-2-candidates.png", full_page=True)
    # 详情抽屉
    page.click("table tbody tr >> nth=0")
    page.wait_for_timeout(1200)
    page.screenshot(path="docs/ui-vue-3-drawer.png")
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    # 运行记录
    page.click("text=运行记录")
    page.wait_for_timeout(800)
    page.screenshot(path="docs/ui-vue-4-runs.png", full_page=True)
    # 新建职位弹窗
    page.click("text=新职位")
    page.wait_for_timeout(800)
    page.screenshot(path="docs/ui-vue-5-jobdialog.png")
    b.close()
    print("console/page errors:", errors if errors else "none")