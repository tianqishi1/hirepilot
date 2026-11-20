# -*- coding: utf-8 -*-
"""DOM 执行层（Playwright）：语义选择器抗 class 混淆；失败按 打印版→视觉Agent 降级。"""
import time

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from stability import StepFailure, capture
import visual_agent


class Browser:
    def __init__(self, headless: bool = True):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=headless)
        self.page = self._browser.new_page(viewport={"width": 1280, "height": 900})
        self.stats = {"print_fallbacks": 0, "visual_fallbacks": 0, "send_retries": 0}

    def close(self):
        self._browser.close()
        self._pw.stop()

    # ---- 发现 ----
    def discover(self, base: str, max_pages: int = 10) -> list[dict]:
        out, url = [], f"{base}/candidates"
        for _ in range(max_pages):
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_selector('[id^="list-"] a', timeout=8000)   # 懒加载
            for a in self.page.locator('[id^="list-"] a').all():
                href = a.get_attribute("href") or ""
                out.append({"externalId": href.rsplit("/", 1)[-1],
                            "name": a.inner_text().strip(),
                            "url": base + href})
            nxt = self.page.locator('a[rel="next"]')
            if nxt.count() == 0:
                break
            url = base + nxt.first.get_attribute("href")
        return out

    # ---- 简历抽取（三级降级） ----
    def extract_resume(self, url: str) -> str:
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_selector("h1", timeout=8000)
        # 1) 语义 DOM
        try:
            art = self.page.locator('article[data-role="resume"]')
            art.wait_for(timeout=2500)
            text = art.inner_text().strip()
            if len(text) > 50 and "占位文本" not in text:
                return text
        except PWTimeout:
            pass
        # 2) 打印版路线（组合方案：换视图而非死磕选择器）
        try:
            link = self.page.get_by_role("link", name="打印版简历")
            if link.count():
                link.first.click()
                self.page.wait_for_selector("#resume-plain", timeout=5000)
                text = self.page.locator("#resume-plain").inner_text().strip()
                if len(text) > 50:
                    self.stats["print_fallbacks"] += 1
                    print(f"[browser] DOM 失效，降级打印版路线: {url}")
                    return text
        except PWTimeout:
            pass
        # 3) 视觉 Agent 读屏
        try:
            text = visual_agent.read_screen(self.page)
            self.stats["visual_fallbacks"] += 1
            print(f"[browser] 降级视觉 Agent 读屏: {url}")
            return text
        except visual_agent.VisualUnavailable as e:
            shot, snap = capture(self.page, f"extract-{url.rsplit('/', 1)[-1]}-{int(time.time())}")
            raise StepFailure("extract_resume", f"三级路线全部失败: {e}", shot, snap)

    # ---- 聊天 ----
    def _open_chat(self, url: str):
        if self.page.url != url:
            self.page.goto(url, wait_until="domcontentloaded")
        self.page.get_by_role("button", name="立即沟通").click()
        self.page.wait_for_selector("#chat-panel", state="visible", timeout=5000)

    def send_message(self, url: str, content: str, max_attempts: int = 4) -> int:
        """UI 发送；503 时重试点击。站点按内容 hash 幂等，重试不会重发。返回重试次数。"""
        self._open_chat(url)
        self.page.get_by_placeholder("输入消息...").fill(content)
        retries = 0
        for attempt in range(max_attempts):
            self.page.get_by_role("button", name="发送").click()
            status = self.page.get_by_role("status")
            try:
                status.wait_for(timeout=6000)
                self.page.wait_for_function(
                    "() => document.getElementById('send-status').textContent !== '发送中...'", timeout=6000)
            except PWTimeout:
                pass
            txt = status.inner_text()
            if txt == "已发送":
                self.stats["send_retries"] += retries
                return retries
            retries += 1
            time.sleep(0.6 * (attempt + 1))
        shot, snap = capture(self.page, f"send-{url.rsplit('/', 1)[-1]}-{int(time.time())}")
        raise StepFailure("send_message", f"发送 {max_attempts} 次仍失败", shot, snap)

    def read_messages(self, url: str) -> list[dict]:
        self._open_chat(url)
        try:
            self.page.wait_for_selector("[data-dir]", timeout=3000)
        except PWTimeout:
            return []
        time.sleep(0.8)   # 等待轮询渲染稳定
        msgs = []
        for el in self.page.locator("[data-dir]").all():
            raw = el.inner_text()
            direction = "in" if el.get_attribute("data-dir") == "in" else "out"
            content = raw.split(": ", 1)[-1]
            msgs.append({"dir": direction, "content": content})
        return msgs