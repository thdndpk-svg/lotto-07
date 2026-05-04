import json, time, os, requests
from datetime import datetime

API = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
HEADERS = {"User-Agent":"Mozilla/5.0","Referer":"https://www.dhlottery.co.kr/","X-Requested-With":"XMLHttpRequest"}

def fetch_one(n):
    try:
        d = requests.get(API.format(n), headers=HEADERS, timeout=10).json()
        if d.get("returnValue") == "success":
            return {"round":int(d["drwNo"]),"date":str(d["drwNoDate"]),
                    "numbers":[int(d[f"drwtNo{i}"]) for i in range(1,7)],
                    "bonus":int(d["bnusNo"]),
                    "w1":int(d.get("firstPrzwnerCo")or 0),"a1":int(d.get("firstWinamnt")or 0),
                    "w2":int(d.get("secondPrzwnerCo")or 0),"a2":int(d.get("secondWinamnt")or 0),
                    "w3":int(d.get("thirdPrzwnerCo")or 0),"a3":int(d.get("thirdWinamnt")or 0)}
    except: pass
    return None

def find_latest():
    for n in range(1230,1150,-1):
        try:
            d = requests.get(API.format(n), headers=HEADERS, timeout=8).json()
            if d.get("returnValue") == "success":
                print(f"최신: {n}회 {d['drwNoDate']}"); return n
        except: pass
        time.sleep(0.1)
    return 1200

existing = {}
if os.path.exists("lotto_data.json"):
    try:
        old = json.load(open("lotto_data.json","r",encoding="utf-8"))
        existing = {d["round"]:d for d in old.get("draws",[])}
        print(f"기존 {len(existing)}회차")
    except: pass

latest = find_latest()
to_fetch = [n for n in range(latest, max(1,latest-50), -1) if n not in existing]
print(f"수집: {len(to_fetch)}회차")

for n in to_fetch:
    d = fetch_one(n)
    if d: existing[n]=d; print(f"✓ {n}회")
    time.sleep(0.15)

draws = sorted(existing.values(), key=lambda x:x["round"], reverse=True)[:500]
json.dump({"updated":datetime.now().strftime("%Y-%m-%d %H:%M"),"latest_round":draws[0]["round"],"total":len(draws),"draws":draws},
          open("lotto_data.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"✅ {len(draws)}회차 저장 완료")
