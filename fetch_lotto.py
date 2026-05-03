#!/usr/bin/env python3
"""
GitHub Actions에서 매주 토요일 밤 자동 실행
동행복권 API → lotto_data.json 생성/업데이트
"""
import json, requests, time
from datetime import datetime

BASE = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="

def fetch_one(n):
    try:
        r = requests.get(BASE + str(n), timeout=10)
        d = r.json()
        if d.get("returnValue") != "success":
            return None
        return {
            "round":   d["drwNo"],
            "date":    d["drwNoDate"],
            "numbers": [d[f"drwtNo{i}"] for i in range(1,7)],
            "bonus":   d["bnusNo"],
            "w1":      d.get("firstWinamnt"),
            "a1":      d.get("firstWinamnt"),
            "w2":      d.get("secondWinamnt"),
            "a2":      d.get("secondWinamnt"),
            "w3":      d.get("thirdWinamnt"),
            "a3":      d.get("thirdWinamnt"),
        }
    except Exception as e:
        print(f"  오류 {n}회: {e}")
        return None

def main():
    # 현재 최신 회차 파악
    print("최신 회차 파악 중...")
    lo, hi = 1, 1300
    while lo < hi:
        mid = (lo + hi + 1) // 2
        r = requests.get(BASE + str(mid), timeout=10).json()
        if r.get("returnValue") == "success":
            lo = mid
        else:
            hi = mid - 1
    latest_round = lo
    print(f"최신 회차: {latest_round}회")

    # 기존 데이터 로드
    try:
        with open("lotto_data.json","r",encoding="utf-8") as f:
            existing = json.load(f)
        draws = {d["round"]: d for d in existing.get("draws",[])}
        print(f"기존 데이터: {len(draws)}회차")
    except:
        draws = {}
        print("기존 데이터 없음 — 전체 수집 시작")

    # 없는 회차 수집
    to_fetch = [n for n in range(1, latest_round+1) if n not in draws]
    print(f"수집 대상: {len(to_fetch)}회차")

    for n in to_fetch:
        d = fetch_one(n)
        if d:
            draws[n] = d
            print(f"  ✓ {n}회 수집")
        time.sleep(0.15)

    # 저장
    all_draws = sorted(draws.values(), key=lambda x: x["round"], reverse=True)
    result = {
        "updated":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latest_round": latest_round,
        "total":        len(all_draws),
        "draws":        all_draws,
    }
    with open("lotto_data.json","w",encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 저장 완료: {len(all_draws)}회차 → lotto_data.json")

if __name__ == "__main__":
    main()
