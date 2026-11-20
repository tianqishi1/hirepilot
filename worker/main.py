# -*- coding: utf-8 -*-
"""HirePilot Agent Worker 入口。
用法:
  python main.py --job 1 --auto-approve          # standalone 演示（自动模拟HR批准）
  python main.py --job 1                         # 连后台；触达需 HR 在审核队列批准
  python main.py --job 1 --headful               # 有头模式观察浏览器
"""
import argparse
import json
import threading
import time

from backend_client import build_store
from browser import Browser
from config import OUT
from llm import build_llm
from pipeline import new_stats, run_pipeline
from stability import Checkpoint


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", type=int, default=1)
    ap.add_argument("--auto-approve", action="store_true", help="仅演示：standalone 模式模拟HR自动批准")
    ap.add_argument("--headful", action="store_true")
    ap.add_argument("--worker-id", default="worker-1")
    ap.add_argument("--fresh", action="store_true", help="清除断点，从头跑")
    ap.add_argument("--standalone", action="store_true", help="强制本地模式，不连后台")
    ap.add_argument("--reset", action="store_true", help="重开一局：清空后台该职位数据(开发用)")
    args = ap.parse_args()

    if args.standalone:
        from backend_client import LocalStore
        store = LocalStore(auto_approve=args.auto_approve)
        print("[store] 强制 standalone 模式")
    else:
        store = build_store(auto_approve=args.auto_approve)
    if args.reset:
        store.reset(args.job)
        print("[main] 已重置职位数据（开发模式）")
    job = store.get_job(args.job)
    llm = build_llm()
    ckpt = Checkpoint(str(args.job))
    if args.fresh:
        ckpt.data = {"seen": [], "msg_cursor": {}}
        ckpt.save()

    try:
        task_id = store.claim(args.job, args.worker_id)
    except Exception as e:
        print(f"[main] 领取任务失败（可能已有活跃任务）: {e}")
        return

    stop = threading.Event()
    def heartbeat():
        while not stop.wait(30):
            try:
                store.heartbeat(task_id)
            except Exception:
                pass
    threading.Thread(target=heartbeat, daemon=True).start()

    browser = Browser(headless=not args.headful)
    stats = new_stats()
    state = "FINISHED"
    t0 = time.time()
    try:
        run_pipeline(job, llm, browser, store, ckpt, stats, task_id)
    except Exception as e:
        state = "FAILED"
        store.incident(task_id, "pipeline", repr(e))
        raise
    finally:
        stop.set()
        browser.close()
        stats["elapsed_sec"] = round(time.time() - t0, 1)
        store.finish(task_id, stats, state)
        print("\n===== 运行报表 =====")
        print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()