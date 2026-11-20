import httpx
B = "http://127.0.0.1:8080"
for r in httpx.get(f"{B}/api/reviews", params={"decision": "PENDING"}).json():
    c = httpx.get(f"{B}/api/candidates/{r['candidateId']}").json()["candidate"]
    if c["name"] == "王志强":
        httpx.post(f"{B}/api/reviews/{r['id']}/reject", json={"note": "期望薪资超预算，AI风险提示成立"})
        print("REJECT", c["name"])
    else:
        httpx.post(f"{B}/api/reviews/{r['id']}/approve", json={})
        print("APPROVE", c["name"])