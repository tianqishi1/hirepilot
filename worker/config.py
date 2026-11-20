# -*- coding: utf-8 -*-
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"


def _load_dotenv():
    """从项目根 .env 读取配置（已 gitignore，密钥不入库）。"""
    p = ROOT.parent / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()
INCIDENTS = OUT / "incidents"
OUT.mkdir(exist_ok=True)
INCIDENTS.mkdir(exist_ok=True)

BACKEND_URL = os.getenv("HIREFIX_BACKEND", "http://127.0.0.1:8080")
MOCK_URL = os.getenv("HIREFIX_MOCK", "http://127.0.0.1:9000")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "") or os.getenv("DASHSCOPE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen-vl-max")

GREET_DELAY_RANGE = (1.0, 2.5)   # 演示用限速；生产建议 2-5s
MAX_PAGES = 10