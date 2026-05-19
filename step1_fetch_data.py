"""
=============================================================
AI Race Analyst - Step 1: FastF1 첫 데이터 받아오기
=============================================================

목표: FastF1을 설치하고, 2024년 모나코 GP 데이터를 받아본다.

실행 전 준비:
1. Python 3.9 이상 설치 확인: python --version
2. 필요한 라이브러리 설치:
   pip install fastf1 pandas
   
=============================================================
"""

import fastf1
import pandas as pd
from pathlib import Path

# -------------------------------------------------------------
# 1. 캐시 설정 (매우 중요!)
# -------------------------------------------------------------
# FastF1은 받아온 데이터를 캐시에 저장해서, 두 번째 호출부터는
# 인터넷 없이도 빠르게 데이터를 가져올 수 있어요.
# 처음 한 번만 다운로드하고, 이후엔 캐시에서 읽어옵니다.

CACHE_DIR = Path('./f1_cache')
CACHE_DIR.mkdir(exist_ok=True)  # 폴더가 없으면 생성
fastf1.Cache.enable_cache(str(CACHE_DIR))

print("✓ 캐시 설정 완료:", CACHE_DIR.absolute())


# -------------------------------------------------------------
# 2. 세션(Session) 로드하기
# -------------------------------------------------------------
# F1은 한 그랑프리 주말이 여러 세션으로 구성됩니다:
#   - FP1, FP2, FP3 (연습 세션 1, 2, 3)
#   - Q (Qualifying, 예선)
#   - R (Race, 본 경기)
#
# 우리는 '본 경기' 데이터를 받을 거예요.

print("\n[1/3] 2024 모나코 GP 본경기 데이터 로드 중...")
print("    (처음 실행 시 30초~1분 정도 걸릴 수 있어요)")

session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()  # 실제로 데이터를 다운로드/로드하는 부분

print("✓ 데이터 로드 완료!")


# -------------------------------------------------------------
# 3. 기본 정보 출력
# -------------------------------------------------------------
print("\n" + "=" * 60)
print("📍 경기 기본 정보")
print("=" * 60)
print(f"이벤트명: {session.event['EventName']}")
print(f"경기 날짜: {session.event['EventDate'].strftime('%Y-%m-%d')}")
print(f"개최 국가: {session.event['Country']}")
print(f"서킷명:   {session.event['Location']}")


# -------------------------------------------------------------
# 4. 최종 결과 (상위 5명)
# -------------------------------------------------------------
print("\n" + "=" * 60)
print("🏆 최종 결과 (상위 5명)")
print("=" * 60)

# session.results는 Pandas DataFrame이라 바로 조작할 수 있어요
results = session.results[[
    'Position',       # 최종 순위
    'Abbreviation',   # 드라이버 약자 (예: NOR, VER, LEC)
    'TeamName',       # 팀명
    'Time',           # 1위와의 시간차
    'Points'          # 획득 포인트
]].head(5)

print(results.to_string(index=False))


# -------------------------------------------------------------
# 5. 랩타임 데이터 살짝 들여다보기
# -------------------------------------------------------------
print("\n" + "=" * 60)
print("⏱  랩타임 데이터 미리보기 (Lando Norris)")
print("=" * 60)

# pick_driver: 특정 드라이버의 랩만 필터링
# 'NOR' = Lando Norris의 약자
norris_laps = session.laps.pick_drivers('NOR')

print(f"\n총 랩 수: {len(norris_laps)}")
print(f"\n처음 5랩 데이터:")
print(norris_laps[[
    'LapNumber',      # 랩 번호
    'LapTime',        # 랩타임
    'Compound',       # 타이어 컴파운드 (SOFT/MEDIUM/HARD)
    'TyreLife',       # 타이어 사용 랩 수
]].head().to_string(index=False))


# -------------------------------------------------------------
# 6. 가장 빠른 랩 찾기
# -------------------------------------------------------------
print("\n" + "=" * 60)
print("⚡ 노리스의 가장 빠른 랩")
print("=" * 60)

fastest = norris_laps.pick_fastest()
print(f"랩 번호:   {fastest['LapNumber']}")
print(f"랩타임:    {fastest['LapTime']}")
print(f"컴파운드:  {fastest['Compound']}")
print(f"타이어 수명: {fastest['TyreLife']}랩 사용한 상태")


print("\n" + "=" * 60)
print("✅ 첫 데이터 수집 완료!")
print("=" * 60)
print("\n다음 단계:")
print("  - 텔레메트리 데이터 (속도, 스로틀, 브레이크) 살펴보기")
print("  - 드라이버별 페이스 비교")
print("  - 타이어 디그라데이션 분석")