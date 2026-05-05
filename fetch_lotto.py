#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import time
import urllib.request
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

DATA_PATH = Path("lotto_data.json")
KST = timezone(timedelta(hours=9))
FIRST_DRAW_DATE = date(2002, 12, 7)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://www.dhlottery.co.kr/gameResult.do?method=byWin",
    "X-Requested-With": "XMLHttpRequest",
}

def log(msg):
    print(msg, flush=True)

def lotto_url(round_no):
    return f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_no}"

def parse_lotto(text):
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

def fetch_one(round_no):
    req = urllib.request.Request(lotto_url(round_no), headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            text = res.read().decode("utf-8", errors="replace")
        return parse_lotto(text)
    except Exception as e:
        log(f"  실패 {round_no}회: {e}")
        return None

def estimated_latest_round():
    today = datetime.now(KST).date()
    weeks = (today - FIRST_DRAW_DATE).days // 7
    return max(1, weeks + 1)

def find_latest():
    log("최신 회차 탐색 시작")

    estimate = estimated_latest_round()
    log(f"예상 최신 회차: {estimate}")

    for round_no in range(estimate + 2, max(1, estimate - 12), -1):
        log(f"확인 중: {round_no}회")
        result = fetch_one(round_no)

        if result:
            log(f"최신 회차 발견: {result['round']}회 {result['date']} {result['numbers']} + {result['bonus']}")
            return result["round"]

        time.sleep(0.2)

    raise RuntimeError("최신 회차를 찾지 못했습니다.")

def load_existing():
    if not DATA_PATH.exists():
        log("기존 lotto_data.json 없음. 새로 생성합니다.")
        return {}

    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        draws = data.get("draws", [])
        existing = {}

        for item in draws:
            if "round" in item:
                existing[int(item["round"])] = item

        log(f"기존 데이터: {len(existing)}회차")
        return existing
    except Exception as e:
        log(f"기존 파일 읽기 실패: {e}")
        return {}

def save_data(existing):
    draws = sorted(existing.values(), key=lambda x: int(x["round"]), reverse=True)

    if not draws:
        raise RuntimeError("저장할 데이터가 없습니다.")

    payload = {
        "status": "ok",
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST"),
        "latest_round": int(draws[0]["round"]),
        "total": len(draws),
        "source": "dhlottery.co.kr",
        "draws": draws,
    }

    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    log("저장 완료")
    log(f"latest_round: {payload['latest_round']}")
    log(f"total: {payload['total']}")

def main():
    log("=" * 50)
    log("로또 데이터 업데이트 시작")
    log("=" * 50)

    existing = load_existing()
    latest = find_latest()

    limit = int(os.getenv("LOTTO_HISTORY_LIMIT", "60"))
    start = latest
    end = max(1, latest - limit + 1)

    log(f"수집 범위: {start}회 ~ {end}회")

    success = 0
    fail = 0

    for round_no in range(start, end - 1, -1):
        # 이미 있더라도 최근 3회는 다시 갱신
        if round_no in existing and round_no < latest - 2:
            continue

        log(f"수집 중: {round_no}회")
        result = fetch_one(round_no)

        if result:
            existing[round_no] = result
            success += 1
            log(f"  성공 {round_no}회 {result['numbers']} + {result['bonus']}")
        else:
            fail += 1
            log(f"  실패 {round_no}회")

        time.sleep(0.2)

    save_data(existing)

    log("=" * 50)
    log(f"완료 성공: {success}, 실패: {fail}")
    log("=" * 50)

if __name__ == "__main__":
    main()
