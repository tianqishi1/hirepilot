# -*- coding: utf-8 -*-
"""用 Playwright 对控制台页面截图，供 UI 视觉验收。用法: python scripts/ui_screenshot.py [url] [out.png]"""
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
out = sys.argv[2] if len(sys.argv) > 2 else "docs/ui-vue-overview.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 950})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.screenshot(path=out, full_page=True)
    browser.close()
print("saved", out)