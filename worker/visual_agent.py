# -*- coding: utf-8 -*-
"""视觉 Agent 降级路线：截图 → VLM 理解/定位 → 坐标执行。
配置 LLM_API_KEY 后启用真实 VLM；离线时抛 VisualUnavailable，由上层挂起并留证。
"""
import base64
import json
import re

import httpx

from config import LLM_API_KEY, LLM_BASE_URL, VLM_MODEL


class VisualUnavailable(Exception):
    pass


def _vlm(image_png: bytes, prompt: str) -> str:
    if not LLM_API_KEY:
        raise VisualUnavailable("未配置 LLM_API_KEY，视觉路线不可用")
    b64 = base64.b64encode(image_png).decode()
    try:
        r = httpx.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            timeout=90,
            json={"model": VLM_MODEL, "temperature": 0, "thinking": {"type": "disabled"},
                  "messages": [{
                      "role": "user", "content": [
                          {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                          {"type": "text", "text": prompt}]}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise VisualUnavailable(f"VLM 调用失败: {e.__class__.__name__}: {str(e)[:120]}")


def read_screen(page) -> str:
    """读屏抽取简历文本（DOM 与打印版均失效时）。"""
    text = _vlm(page.screenshot(full_page=True),
                "这是一张招聘网站简历页截图。请逐字转录其中的简历正文（姓名/学历/经验/技能/经历），只输出转录文本。")
    if len(text.strip()) < 50:
        raise VisualUnavailable("VLM 读屏结果过短")
    return text.strip()


def click_by_hint(page, hint: str):
    """按自然语言描述定位元素并坐标点击，例如『蓝色的立即沟通按钮』。"""
    out = _vlm(page.screenshot(),
               f"在截图中找到「{hint}」，只输出 JSON: {{\"x\": 中心横坐标, \"y\": 中心纵坐标}}（像素，左上角为原点）。")
    m = re.search(r"\{.*\}", out, flags=re.S)
    pos = json.loads(m.group(0))
    page.mouse.click(pos["x"], pos["y"])