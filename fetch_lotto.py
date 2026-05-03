import requests
import json
import os

def fetch_lotto(drwNo):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drwNo}"
    response = requests.get(url)
    data = response.json()
    if data.get("returnValue") == "success":
        return data
    return None

def main():
    # 폴더가 없으면 생성
    os.makedirs('data', exist_ok=True)
    
    file_path = 'data/lotto_data.json'
    
    # 1회차부터 최신회차까지 수집 (간단 예시)
    all_data = []
    round_num = 1
    while True:
        result = fetch_lotto(round_num)
        if not result: break
        all_data.append(result)
        round_num += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
