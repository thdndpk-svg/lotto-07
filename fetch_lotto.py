#!/usr/bin/env python3
"""
GitHub Actions 로또 데이터 수집기
최신 200회차만 수집 (빠른 실행)
"""
import json, time, os, requests
from datetime import datetime

API = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.dhlottery.co.kr/gameResult.do?method=byWin",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}
MAX_ROUNDS = 200   # 최근 200회차만 수집 (약 2~3분)

def fetch_one(n):
    for attempt in range(2):
        try:
            r = requests.get(API.format(n), headers=HEADERS, timeout=15)
            text = r.text.strip()
            if not text or text.startswith("<"):
                return None
            d = json.loads(text)
            if d.get("returnValue") == "success":
                return {
                    "round":   int(d["drwNo"]),
                    "date":    str(d["drwNoDate"]),
                    "numbers": [int(d[f"drwtNo{i}"]) for i in range(1, 7)],
                    "bonus":   int(d["bnusNo"]),
                    "w1": int(d.get("firstPrzwnerCo") or 0),
                    "a1": int(d.get("firstWinamnt") or 0),
                    "w2": int(d.get("secondPrzwnerCo") or 0),
                    "a2": int(d.get("secondWinamnt") or 0),
                    "w3": int(d.get("thirdPrzwnerCo") or 0),
                    "a3": int(d.get("thirdWinamnt") or 0),
                }
        except Exception as e:
            print(f"  {n}회 시도{attempt+1} 실패: {e}")
            time.sleep(1)
    return None

def find_latest():
    """최신 회차 탐색 (1300부터 내려오며)"""
    print("최신 회차 탐색 중...")
    for n in range(1300, 1100, -1):
        try:
            r = requests.get(API.format(n), headers=HEADERS, timeout=10)
            text = r.text.strip()
            if text and not text.startswith("<"):
                d = json.loads(text)
                if d.get("returnValue") == "success":
                    print(f"  최신 회차: {n}회 ({d['drwNoDate']})")
                    return n
        except:
            pass
        time.sleep(0.15)
    return 1200

def main():
    print("=" * 50)
    print(f"로또 데이터 수집 (최근 {MAX_ROUNDS}회차)")
    print("=" * 50)

    # 기존 데이터 로드
    existing = {}
    if os.path.exists("lotto_data.json"):
        try:
            with open("lotto_data.json", "r", encoding="utf-8") as f:
                old = json.load(f)
            existing = {d["round"]: d for d in old.get("draws", [])}
            print(f"기존 데이터: {len(existing)}회차")
        except:
            print("기존 데이터 없음")

    latest = find_latest()
    start  = max(1, latest - MAX_ROUNDS + 1)

    # 수집할 회차 (기존에 없는 것만)
    to_fetch = [n for n in range(latest, start - 1, -1) if n not in existing]
    print(f"신규 수집 대상: {len(to_fetch)}회차 ({start}~{latest}회)")

    success = 0
    for i, n in enumerate(to_fetch):
        d = fetch_one(n)
        if d:
            existing[n] = d
            success += 1
            print(f"  ✓ {n}회 ({d['date']}) {d['numbers']}")
        time.sleep(0.2)

    print(f"\n수집 완료: {success}회")

    # 최근 MAX_ROUNDS 회차만 유지
    all_draws = sorted(existing.values(), key=lambda x: x["round"], reverse=True)
    all_draws = all_draws[:MAX_ROUNDS]

    if not all_draws:
        print("❌ 수집 데이터 없음!")
        raise SystemExit(1)

    out = {
        "updated":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latest_round": all_draws[0]["round"],
        "total":        len(all_draws),
        "draws":        all_draws,
    }
    with open("lotto_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"✅ lotto_data.json 저장 완료")
    print(f"   회차: {all_draws[-1]['round']}~{all_draws[0]['round']}회")
    print(f"   최신: {all_draws[0]['numbers']} + {all_draws[0]['bonus']}")

if __name__ == "__main__":
    main()
