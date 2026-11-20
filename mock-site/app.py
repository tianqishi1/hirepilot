# -*- coding: utf-8 -*-
"""Mock 招聘站：刻意复刻真实站点的脏特性，用于演示与测试 Agent 的鲁棒性。
- class 名每次渲染带随机后缀（逼迫语义选择器）
- 列表懒加载（JS 延迟渲染）
- 两种简历页模板；c007 为混淆模板（含隐藏占位文本，需降级到打印版/视觉路线）
- /api/chat/*/send 20% 概率 503（演示重试+幂等）
- 候选人脚本化自动回复（FAQ/敏感/意向三类）
运行: python app.py  (http://127.0.0.1:9000)
"""
import json
import random
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import uvicorn

from data import CANDIDATES, BY_ID, PAGE_SIZE

app = FastAPI(title="MockRecruit")
CHAT: dict = {}


def chat_state(cid: str) -> dict:
    if cid not in CHAT:
        CHAT[cid] = {"messages": [], "script_idx": 0, "keys": set()}
    return CHAT[cid]


def rnd() -> str:
    return uuid.uuid4().hex[:4]


@app.get("/")
def index():
    return RedirectResponse("/candidates")


@app.get("/candidates", response_class=HTMLResponse)
def candidates(page: int = 1):
    total = (len(CANDIDATES) + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(1, min(page, total))
    items = CANDIDATES[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]
    payload = json.dumps([{"id": c["id"], "name": c["name"], "title": c["title"]} for c in items], ensure_ascii=False)
    next_link = f'<a href="/candidates?page={page + 1}" rel="next">下一页</a>' if page < total else ""
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>候选人 - MockRecruit</title>
<style>.card-{rnd()}{{border:1px solid #ddd;margin:8px;padding:12px;border-radius:8px}}</style></head>
<body><h1>候选人列表</h1><p>共 {len(CANDIDATES)} 位候选人，第 {page}/{total} 页</p>
<div id="list-{rnd()}"></div><nav>{next_link}</nav>
<script>
const items = {payload};
setTimeout(() => {{
  const box = document.querySelector('[id^="list-"]');
  for (const it of items) {{
    const d = document.createElement('div');
    d.className = 'card-' + Math.random().toString(16).slice(2, 6);
    d.innerHTML = `<a href="/candidate/${{it.id}}"><strong>${{it.name}}</strong></a><span> ｜ ${{it.title}}</span>`;
    box.appendChild(d);
  }}
}}, 400);
</script></body></html>"""


def chat_js(cid: str) -> str:
    return """
<script>
function hash(s){let h=0;for(const ch of s){h=(h*31+ch.charCodeAt(0))|0}return 'k'+h}
const panel=document.getElementById('chat-panel');
document.getElementById('open-chat').onclick=()=>{panel.style.display='block';poll()};
let timer=null;
async function poll(){
  const r=await fetch('/api/chat/CID');const j=await r.json();
  const box=document.getElementById('msgs');box.innerHTML='';
  for(const m of j.messages){
    const d=document.createElement('div');d.dataset.dir=m.dir;d.textContent=(m.dir==='out'?'我: ':'候选人: ')+m.content;
    box.appendChild(d);
  }
  if(panel.style.display==='block')timer=setTimeout(poll,600);
}
document.getElementById('send-btn').onclick=async()=>{
  const ta=document.getElementById('msg-input');const content=ta.value.trim();if(!content)return;
  const status=document.getElementById('send-status');status.textContent='发送中...';
  const r=await fetch('/api/chat/CID/send',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({content,key:hash(content)})});
  if(r.ok){status.textContent='已发送';ta.value='';poll();}
  else{status.textContent='发送失败，请重试';}
};
</script>""".replace("CID", cid)


@app.get("/candidate/{cid}", response_class=HTMLResponse)
def resume(cid: str):
    c = BY_ID.get(cid)
    if not c:
        return HTMLResponse("<h1>404</h1>", status_code=404)
    chat_html = f"""
<button id="open-chat" class="btn-{rnd()}">立即沟通</button>
<div id="chat-panel" style="display:none;border:1px solid #ccc;padding:12px;margin-top:12px">
  <div id="msgs" aria-label="聊天记录"></div>
  <textarea id="msg-input" placeholder="输入消息..." rows="3" cols="60"></textarea><br>
  <button id="send-btn" class="btn-{rnd()}">发送</button>
  <span id="send-status" role="status"></span>
</div>"""
    if c.get("obfuscated"):
        lines = "".join(
            f'<span class="t-{rnd()}">{line}</span><span style="display:none">占位文本请勿采集##{rnd()}</span><br>'
            for line in c["resume"].splitlines()
        )
        body = f"""<h1>{c['name']}</h1><p>{c['title']}</p>
<div class="wrap-{rnd()}"><div class="inner-{rnd()}">{lines}</div></div>
<p><a href="/candidate/{cid}/print">打印版简历</a></p>"""
    else:
        body = f"""<h1>{c['name']}</h1><p>{c['title']}</p>
<article data-role="resume" class="r-{rnd()}" style="white-space:pre-wrap">{c['resume']}</article>
<p><a href="/candidate/{cid}/print">打印版简历</a></p>"""
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>{c['name']} - 简历</title></head>
<body>{body}{chat_html}{chat_js(cid)}</body></html>"""


@app.get("/candidate/{cid}/print", response_class=HTMLResponse)
def resume_print(cid: str):
    c = BY_ID.get(cid)
    if not c:
        return HTMLResponse("<h1>404</h1>", status_code=404)
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>打印版</title></head>
<body><pre id="resume-plain">{c['resume']}</pre></body></html>"""


@app.get("/api/candidates")
def api_candidates():
    return [{"id": c["id"], "name": c["name"], "title": c["title"]} for c in CANDIDATES]


@app.get("/api/chat/{cid}")
def api_chat(cid: str):
    return {"messages": chat_state(cid)["messages"]}


@app.post("/api/chat/{cid}/send")
async def api_send(cid: str, request: Request):
    if cid not in BY_ID:
        return JSONResponse({"error": "not found"}, status_code=404)
    body = await request.json()
    content, key = body.get("content", ""), body.get("key", "")
    st = chat_state(cid)
    if key and key in st["keys"]:                      # 幂等：重复 key 直接成功，不重复追加
        return {"ok": True, "duplicate": True}
    if random.random() < 0.2:                          # 模拟网络抖动
        return JSONResponse({"error": "service busy"}, status_code=503)
    if key:
        st["keys"].add(key)
    st["messages"].append({"dir": "out", "content": content})
    replies = BY_ID[cid]["replies"]
    if st["script_idx"] < len(replies):                # 候选人脚本化回复
        st["messages"].append({"dir": "in", "content": replies[st["script_idx"]]})
        st["script_idx"] += 1
    return {"ok": True}


@app.post("/api/reset")
def reset():
    CHAT.clear()
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000, log_level="warning")