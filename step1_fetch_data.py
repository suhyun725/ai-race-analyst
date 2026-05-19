"""
=============================================================
AI Race Analyst - Step 1: FastF1 데이터 수집 (모듈화 버전)
=============================================================

목표: src/data 모듈을 사용해서 2024 모나코 GP 데이터를 수집한다.

실행: python3 step1_fetch_data.py
=============================================================
"""

from src.data.session_loader import (
    setup_cache,
    load_session,
    print_session_info,
)


def main():
    # 1. 캐시 설정
    cache_dir = setup_cache()
    print(f"✓ 캐시 디렉토리: {cache_dir}\n")
    
    # 2. 2024 모나코 GP 본경기 로드
    session = load_session(year=2024, gp='Monaco', session_type='R')
    
    # 3. 기본 정보 출력
    print_session_info(session)
    
    # 4. 최종 결과 (상위 5명)
    print("\n" + "=" * 60)
    print("🏆 최종 결과 (상위 5명)")
    print("=" * 60)
    results = session.results[[
        'Position', 'Abbreviation', 'TeamName', 'Time', 'Points'
    ]].head(5)
    print(results.to_string(index=False))
    
    # 5. 노리스의 가장 빠른 랩
    print("\n" + "=" * 60)
    print("⚡ Lando Norris의 가장 빠른 랩")
    print("=" * 60)
    norris_laps = session.laps.pick_drivers('NOR')
    fastest = norris_laps.pick_fastest()
    print(f"랩 번호:     {fastest['LapNumber']}")
    print(f"랩타임:      {fastest['LapTime']}")
    print(f"컴파운드:    {fastest['Compound']}")
    print(f"타이어 수명: {fastest['TyreLife']}랩 째")
    
    print("\n" + "=" * 60)
    print("✅ 데이터 수집 완료!")
    print("=" * 60)


if __name__ == '__main__':
    main()
