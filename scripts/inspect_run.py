import httpx
B = "http://127.0.0.1:8080"
for c in httpx.get(f"{B}/api/candidates", params={"jobId": 1}).json():
    d = httpx.get(f"{B}/api/candidates/{c['id']}").json()
    ins = [m for m in d["messages"] if m["direction"] == "IN"]
    if ins:
        print(f"{c['name']} [{c['status']}]")
        for m in ins:
            print(f"   IN({m['intent']}): {m['content'][:40]}")