# -*- coding: utf-8 -*-
"""稳定性工程：重试/幂等/断点/限速/留证。"""
import functools
import hashlib
import json
import random
import time
from pathlib import Path

from config import OUT


class StepFailure(Exception):
    """页面步骤彻底失败（含降级后），携带现场信息。"""
    def __init__(self, step: str, detail: str, screenshot: str = "", html_snapshot: str = ""):
        super().__init__(f"{step}: {detail}")
        self.step = step
        self.detail = detail
        self.screenshot = screenshot
        self.html_snapshot = html_snapshot


def retry(times: int = 3, base: float = 0.5, exceptions=(Exception,)):
    """指数退避重试。仅用于网络/超时类可恢复异常。"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last = None
            for i in range(times):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last = e
                    if i < times - 1:
                        time.sleep(base * (2 ** i) + random.uniform(0, 0.3))
            raise last
        return wrapper
    return deco


def idem_key(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:32]


class Checkpoint:
    """断点续跑：seen 集合 + 每候选人已处理消息数。"""
    def __init__(self, job_id: str):
        self.path = OUT / f"checkpoint-{job_id}.json"
        self.data = {"seen": [], "msg_cursor": {}}
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def seen(self, key: str) -> bool:
        return key in self.data["seen"]

    def mark(self, key: str):
        if key not in self.data["seen"]:
            self.data["seen"].append(key)
            self.save()

    def cursor(self, cid: str) -> int:
        return self.data["msg_cursor"].get(cid, 0)

    def set_cursor(self, cid: str, n: int):
        self.data["msg_cursor"][cid] = n
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")


def throttle(lo: float, hi: float):
    time.sleep(random.uniform(lo, hi))


def capture(page, name: str) -> tuple[str, str]:
    """失败留证：截图 + HTML 快照。"""
    shot = OUT / "incidents" / f"{name}.png"
    snap = OUT / "incidents" / f"{name}.html"
    try:
        page.screenshot(path=str(shot), full_page=True)
        snap.write_text(page.content(), encoding="utf-8")
    except Exception:
        return "", ""
    return str(shot), str(snap)