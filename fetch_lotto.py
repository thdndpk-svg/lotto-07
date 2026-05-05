#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
로또 6/45 데이터 자동 수집기
- GitHub Actions / 로컬 둘 다 실행 가능
- lotto_data.json 자동 생성/갱신
- 기존 데이터 보존
- 최신 회차 자동 탐색
"""

import json
import os
import time
import subprocess
import urllib.request
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

DATA_PATH = Path("lotto_data.json")
KST = timezone(timedelta(hours=9))
FIRST_DRAW_DATE = date(2002, 12, 7)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://www.dhlottery.co.kr/gameResult.do?method=byWin",
    "X-Requested-With": "XMLHttpRequest",
}

def lotto_url(round_no: int) -> str:
    return f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_no}"

def parse_lotto_json(text: str):
    text = (text or "").strip()

    if not text:
        return None

    if text.startswith("<"):
        return None

    try:
        d = json.loads(text)
    except Exception:
        return None

    if d.get("returnValue") != "success":
        return None

    try:
        return {
            "round": int(d["drwNo"]),
            "date": str(d["drwNoDate"]),
            "numbers": [int(d[f"drwtNo{i}"]) for i in range(1, 7)],
            "bonus": int(d["bnusNo"]),
            "w1": int(d.get("firstPrzwnerCo") or 0),
            "a1": int(d.get("firstWinamnt") or 0),
            "w2": int(d.get("secondPrzwnerCo") or 0),
            "a2": int(d.get("secondWinamnt") or 0),
            "w3": int(d.get("thirdPrzwnerCo") or 0),
            "a3": int(d.get("thirdWinamnt") or 0),
        }
    except Exception:
        return None

def fetch_with_python(round_no: int):
    req = urllib.request.Request(lotto_url(round_no), headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            raw = res.read().decode("utf-8", errors="replace")
        return parse_lotto_json(raw)
    except Exception as e:
        print(f"  python 요청 실패 {round_no}회: {e}")
        return None

def fetch_with_curl(round_no: int):
    cmd = [
        "curl",
        "-sS",
        "--max-time",
        "20",
        "-H", f"User-Agent: {HEADERS['User-Agent']}",
        "-H", f"Accept: {HEADERS['Accept']}",
        "-H", f"Accept-Language: {HEADERS['Accept-Language']}",
        "-H", f"Referer: {HEADERS['Referer']}",
        "-H", f"X-Requested-With: {HEADERS['X-Requested-With']}",
        "--compressed",
        lotto_url(round_no),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        return parse_lotto_json(result.stdout)
    except Exception as e:
        print(f"  curl 요청 실패 {round_no}회: {e}")
        return None

def fetch_one(round_no: int):
    for attempt in range(1, 4):
        result = fetch_with_python(round_no)
        if result:
            return result

        time.sleep(0.4)

        result = fetch_with_curl(round_no)
        if result:
            return result

        time.sleep(0.8 * attempt)

    return None

def estimated_latest_round() -> int:
    today_kst = datetime.now(KST).date()
    weeks = (today_kst - FIRST_DRAW_DATE).days // 7
    return max(1, weeks + 1)

def find_latest_round():
    print("최신 회차 탐색 중...")

    estimate = estimated_latest_round()

    # 추첨 직후 반영 지연, 날짜 오차를 고려해서 위아래로 넓게 탐색
    for round_no in range(estimate + 3, max(1, estimate - 20), -1):
        result = fetch_one(round_no)
        if result:
            print(f"최신 회차 확인: {result['round']}회 / {result['date']} / {result['numbers']} + {result['bonus']}")
            return result["round"], result

        time.sleep(0.25)

    raise RuntimeError("최신 회차를 찾지 못했습니다.")

def load_existing():
    if not DATA_PATH.exists():
        return {}

    try:
        old = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        draws = old.get("draws", [])
        existing = {}

        for item in draws:
            if "round" in item:
                existing[int(item["round"])] = item

        print(f"기존 데이터 로드: {len(existing)}회차")
        return existing
    except Exception as e:
        print(f"기존 lotto_data.json 읽기 실패. 새로 생성합니다: {e}")
        return {}

def save_data(existing):
    draws = sorted(existing.values(), key=lambda x: int(x["round"]), reverse=True)

    if not draws:
        raise RuntimeError("저장할 로또 데이터가 없습니다.")

    payload = {
        "status": "ok",
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST"),
        "latest_round": int(draws[0]["round"]),
        "total": len(draws),
        "source": "dhlottery.co.kr",
        "draws": draws,
    }

    temp_path = DATA_PATH.with_suffix(".json.tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_path.replace(DATA_PATH)

    print("저장 완료")
    print(f"파일: {DATA_PATH}")
    print(f"총 회차: {payload['total']}")
    print(f"최신 회차: {payload['latest_round']}회")
    print(f"업데이트: {payload['updated']}")

def main():
    print("=" * 60)
    print("로또 데이터 자동 업데이트 시작")
    print("=" * 60)

    existing = load_existing()

    latest_round, latest_data = find_latest_round()
    existing[latest_round] = latest_data

    # 기본값:
    # 기존 데이터가 없으면 전체에 가깝게 수집
    # 기존 데이터가 있으면 최근 80회만 점검해서 빠르게 업데이트
    history_limit = int(os.getenv("LOTTO_HISTORY_LIMIT", "1200" if not existing else "80"))

    start_round = latest_round
    end_round = max(1, latest_round - history_limit + 1)

    # 최근 회차는 당첨금/당첨자 수 갱신 가능성이 있어서 5회는 다시 확인
    refresh_recent = 5

    targets = []
    for round_no in range(start_round, end_round - 1, -1):
        if round_no not in existing:
            targets.append(round_no)
        elif round_no > latest_round - refresh_recent:
            targets.append(round_no)

    targets = sorted(set(targets), reverse=True)

    print(f"수집 대상: {len(targets)}개")
    print(f"범위: {start_round}회 ~ {end_round}회")

    success = 0
    fail = 0

    for idx, round_no in enumerate(targets, start=1):
        result = fetch_one(round_no)

        if result:
            existing[round_no] = result
            success += 1
            print(f"  ✓ {round_no}회 {result['date']} {result['numbers']} + {result['bonus']}")
        else:
            fail += 1
            print(f"  ✗ {round_no}회 실패")

        # 너무 빠른 요청으로 차단되는 것 방지
        time.sleep(0.25)

        # 실패가 너무 많고 기존 데이터도 없으면 중단
        if fail >= 20 and success == 0 and len(existing) <= 1:
            raise RuntimeError("연속 실패가 많아서 중단합니다.")

    save_data(existing)

    print("=" * 60)
    print(f"완료: 성공 {success}개 / 실패 {fail}개")
    print("=" * 60)

if __name__ == "__main__":
    main()
