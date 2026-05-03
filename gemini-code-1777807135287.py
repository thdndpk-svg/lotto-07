name: 로또 데이터 자동 업데이트

on:
  schedule:
    - cron: '0 15 * * 6' # 매주 토요일 밤
  workflow_dispatch:      # 수동 실행 버튼 활성화

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write    # 쓰기 권한 명시

    steps:
      - name: 체크아웃
        uses: actions/checkout@v4

      - name: Python 설정
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 의존성 설치
        run: pip install requests

      - name: 데이터 수집
        run: python fetch_lotto.py

      - name: 변경사항 반영
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add public/lotto_data.json
          # 변경사항이 있을 때만 커밋
          git diff --staged --quiet || (git commit -m "🎯 로또 데이터 업데이트 $(date +'%Y-%m-%d')" && git push)
