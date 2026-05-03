#!/usr/bin/env python3
"""
GitHub Actions 로또 데이터 수집기
동행복권 API → lotto_data.json 생성
"""
import json, time, os, requests
from datetime import datetime

# 동행복권 공식 API
API = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.dhlottery.co.kr/gameResult.do?method=byWin",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

def fetch_round(n):
    """단일 회차 수집 — 에러 방어 강화"""
    for attempt in range(3):
        try:
            r = requests.get(API.format(n), headers=HEADERS, timeout=20)
            # 응답 텍스트 확인
            text = r.text.strip()
            if not text or text.startswith("<"):
                print(f"  {n}회: HTML 응답 (skip)")
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
            return None
        except Exception as e:
            print(f"  {n}회 시도{attempt+1} 실패: {e}")
            time.sleep(2)
    return None

def find_latest():
    """최신 회차 이진탐색"""
    print("최신 회차 탐색 중...")
    lo, hi = 1150, 1300
    latest = 1150
    for n in range(hi, lo, -1):
        try:
            r = requests.get(API.format(n), headers=HEADERS, timeout=15)
            text = r.text.strip()
            if text and not text.startswith("<"):
                d = json.loads(text)
                if d.get("returnValue") == "success":
                    latest = n
                    print(f"  최신 회차: {n}회 ({d['drwNoDate']})")
                    break
        except:
            pass
        time.sleep(0.3)
    return latest

def main():
    print("=" * 50)
    print("로또 데이터 수집 시작")
    print("=" * 50)

    # 기존 데이터 로드
    existing = {}
    if os.path.exists("lotto_data.json"):
        try:
            with open("lotto_data.json", "r", encoding="utf-8") as f:
                old = json.load(f)
            existing = {d["round"]: d for d in old.get("draws", [])}
            print(f"기존 데이터: {len(existing)}회차")
        except Exception as e:
            print(f"기존 데이터 없음: {e}")

    latest = find_latest()
    to_fetch = [n for n in range(1, latest + 1) if n not in existing]
    print(f"신규 수집: {len(to_fetch)}회차")

    success = 0
    for i, n in enumerate(to_fetch):
        d = fetch_round(n)
        if d:
            existing[n] = d
            success += 1
        if i % 100 == 0:
            print(f"  진행: {i+1}/{len(to_fetch)}")
        time.sleep(0.25)

    print(f"수집 완료: {success}회")

    all_draws = sorted(existing.values(), key=lambda x: x["round"], reverse=True)
    if not all_draws:
        print("❌ 데이터 없음!")
        raise SystemExit(1)

    out = {
        "updated":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latest_round": all_draws[0]["round"],
        "total":        len(all_draws),
        "draws":        all_draws,
    }
    with open("lotto_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"✅ 저장 완료: {len(all_draws)}회차")
    print(f"   최신: {all_draws[0]['round']}회 {all_draws[0]['date']}")
    print(f"   번호: {all_draws[0]['numbers']} + {all_draws[0]['bonus']}")

if __name__ == "__main__":
    main()
