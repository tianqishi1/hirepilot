import sys
sys.path.insert(0, r"D:\codex\hirepilot\worker")
from playwright.sync_api import sync_playwright
import visual_agent

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://127.0.0.1:9000/candidate/c007", wait_until="domcontentloaded")
    page.wait_for_selector("h1")
    text = visual_agent.read_screen(page)
    print(f"视觉读屏成功，转录 {len(text)} 字:")
    print(text[:300])
    b.close()