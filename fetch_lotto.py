import requests
import json
import os

def get_lotto():
    # 최신 회차 정보를 가져오는 로직 (예시로 1110회 설정)
    url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo=1110"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("returnValue") == "success":
            # public 폴더에 저장 (Next.js 접근용)
            os.makedirs('public', exist_ok=True)
            with open("public/lotto_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("데이터 업데이트 완료")
        else:
            print("데이터를 가져오는 데 실패했습니다.")
            exit(1)
    except Exception as e:
        print(f"오류 발생: {e}")
        exit(1)

if __name__ == "__main__":
    get_lotto()
