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
from pipeline import new_stats, run_pipeline, screen_phase, engage_phase, merge_stats
from stability import Checkpoint


def serve(args):
    """守护模式：UI 点按钮 → 后台排队 → 这里领取执行。"""
    from backend_client import BackendClient
    if not BackendClient.probe():
        print("[serve] 后台不可达，serve 模式需要 Spring Boot 后台")
        return
    store = BackendClient()
    llm = build_llm()
    browser = Browser(headless=not args.headful)
    print(f"[serve] Worker 已上线，轮询运行请求… ({args.worker_id})")
    try:
        while True:
            store.ping(args.worker_id)
            run = store.claim_run()
            if run is None:
                time.sleep(3)
                continue
            job = store.get_job(run["jobId"])
            ckpt = Checkpoint(str(run["jobId"]))
            stats = new_stats()
            print(f"[serve] 领取运行 #{run['id']} kind={run['kind']} job={run['jobId']}")
            try:
                if run["kind"] == "SCREEN":
                    screen_phase(job, llm, browser, store, ckpt, stats, run["id"])
                else:
                    engage_phase(job, llm, browser, store, ckpt, stats, run["id"])
                merge_stats(stats, browser, llm)
                store.finish_run(run["id"], "DONE", stats)
                print(f"[serve] 运行 #{run['id']} 完成")
            except Exception as e:
                store.finish_run(run["id"], "FAILED", stats, repr(e))
                print(f"[serve] 运行 #{run['id']} 失败: {e!r}")
    except KeyboardInterrupt:
        print("[serve] 退出")
    finally:
        browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", type=int, default=1)
    ap.add_argument("--auto-approve", action="store_true", help="仅演示：standalone 模式模拟HR自动批准")
    ap.add_argument("--headful", action="store_true")
    ap.add_argument("--worker-id", default="worker-1")
    ap.add_argument("--fresh", action="store_true", help="清除断点，从头跑")
    ap.add_argument("--standalone", action="store_true", help="强制本地模式，不连后台")
    ap.add_argument("--reset", action="store_true", help="重开一局：清空后台该职位数据(开发用)")
    ap.add_argument("--serve", action="store_true", help="守护模式：轮询后台运行请求，供 UI 按钮驱动")
    args = ap.parse_args()
    if args.serve:
        serve(args)
        return

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