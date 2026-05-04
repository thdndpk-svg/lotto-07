import json,time,os,requests
from datetime import datetime
API="https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
H={"User-Agent":"Mozilla/5.0","Referer":"https://www.dhlottery.co.kr/","X-Requested-With":"XMLHttpRequest"}
ex={}
if os.path.exists("lotto_data.json"):
    ex={d["round"]:d for d in json.load(open("lotto_data.json","r",encoding="utf-8")).get("draws",[])}
    print(f"기존 {len(ex)}회차")
lat=0
for n in range(1220,1180,-1):
    try:
        d=requests.get(API.format(n),headers=H,timeout=8).json()
        if d.get("returnValue")=="success":
            lat=n;print(f"최신:{n}회");break
    except:pass
    time.sleep(0.1)
if not lat:lat=1200
need=[n for n in range(lat,max(lat-30,-1),-1) if n not in ex]
print(f"수집:{len(need)}회차")
for n in need:
    try:
        d=requests.get(API.format(n),headers=H,timeout=8).json()
        if d.get("returnValue")=="success":
            ex[n]={"round":int(d["drwNo"]),"date":str(d["drwNoDate"]),"numbers":[int(d[f"drwtNo{i}"]) for i in range(1,7)],"bonus":int(d["bnusNo"]),"w1":int(d.get("firstPrzwnerCo")or 0),"a1":int(d.get("firstWinamnt")or 0),"w2":int(d.get("secondPrzwnerCo")or 0),"a2":int(d.get("secondWinamnt")or 0),"w3":int(d.get("thirdPrzwnerCo")or 0),"a3":int(d.get("thirdWinamnt")or 0)}
            print(f"✓{n}회")
    except:pass
    time.sleep(0.15)
dr=sorted(ex.values(),key=lambda x:x["round"],reverse=True)
json.dump({"updated":datetime.now().strftime("%Y-%m-%d %H:%M"),"latest_round":dr[0]["round"],"total":len(dr),"draws":dr},open("lotto_data.json","w",encoding="utf-8"),ensure_ascii=False)
print(f"✅{len(dr)}회차 완료")
