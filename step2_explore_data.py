"""
=============================================================
AI Race Analyst - Step 2: 멀티 드라이버 데이터 탐색
=============================================================

목표: src/data/lap_data.py 모듈의 모든 함수를 2024 모나코 GP로 검증한다.
실행: python3 step2_explore_data.py
=============================================================
"""

from src.data.lap_data import (
    clean_lap_data,
    filter_by_compound,
    filter_lap_range,
    filter_quick_laps,
    get_drivers_laps,
    get_pace_summary,
)
from src.data.session_loader import load_session, setup_cache

# 분석 대상 드라이버
TARGET_DRIVERS = ["NOR", "VER", "LEC", "PIA", "SAI"]


def section(title: str) -> None:
    """섹션 구분선을 출력한다."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def main() -> None:
    # ── 0. 세션 로드 ──────────────────────────────────────────
    setup_cache()
    session = load_session(year=2024, gp="Monaco", session_type="R")

    # ── 1. get_drivers_laps ───────────────────────────────────
    section("1. get_drivers_laps — 멀티 드라이버 수집")

    all_laps = get_drivers_laps(session)
    target_laps = get_drivers_laps(session, TARGET_DRIVERS)

    print(f"전체 드라이버 랩 수:   {len(all_laps):>5}행")
    print(f"대상 드라이버 랩 수:   {len(target_laps):>5}행  {TARGET_DRIVERS}")
    print(f"컬럼 수:               {len(target_laps.columns)}")

    # ── 2. clean_lap_data ─────────────────────────────────────
    section("2. clean_lap_data — 결측치 제거 + 초 변환")

    cleaned = clean_lap_data(target_laps)
    removed = len(target_laps) - len(cleaned)

    print(f"정제 전 행 수:         {len(target_laps):>5}")
    print(f"정제 후 행 수:         {len(cleaned):>5}  (제거: {removed}행)")
    print(
        f"LapTimeSeconds 범위:   {cleaned['LapTimeSeconds'].min():.3f}s"
        f" ~ {cleaned['LapTimeSeconds'].max():.3f}s"
    )
    print("\n[LapTimeSeconds 기술통계]")
    print(cleaned["LapTimeSeconds"].describe().round(3).to_string())

    # ── 3. filter_by_compound ─────────────────────────────────
    section("3. filter_by_compound — 컴파운드별 필터")

    for compound in ["SOFT", "MEDIUM", "HARD"]:
        filtered = filter_by_compound(cleaned, compound)
        print(f"  {compound:<12}: {len(filtered):>4}랩")

    soft_laps = filter_by_compound(cleaned, "SOFT")
    print("\n[SOFT 컴파운드 드라이버별 랩 수]")
    print(soft_laps.groupby("Driver").size().to_string())

    # ── 4. filter_quick_laps ──────────────────────────────────
    section("4. filter_quick_laps — 빠른 랩 필터 (107%)")

    quick = filter_quick_laps(cleaned)
    removed_slow = len(cleaned) - len(quick)
    fastest_time = cleaned["LapTimeSeconds"].min()
    cutoff = fastest_time * 1.07

    print(f"전체 최속 랩:          {fastest_time:.3f}s")
    print(f"107% 기준 컷오프:      {cutoff:.3f}s")
    print(f"필터 전 행 수:         {len(cleaned):>5}")
    print(f"필터 후 행 수:         {len(quick):>5}  (제거: {removed_slow}행)")

    # ── 5. filter_lap_range ───────────────────────────────────
    section("5. filter_lap_range — 랩 범위 필터 (30~50랩)")

    mid_race = filter_lap_range(quick, start=30, end=50)

    print(f"30~50랩 필터 결과:     {len(mid_race)}행")
    print(
        f"실제 랩 번호 범위:     {int(mid_race['LapNumber'].min())}"
        f" ~ {int(mid_race['LapNumber'].max())}"
    )
    print("\n[드라이버별 해당 구간 랩 수]")
    print(mid_race.groupby("Driver").size().to_string())

    # ── 6. get_pace_summary ───────────────────────────────────
    section("6. get_pace_summary — 드라이버별 페이스 통계")

    summary = get_pace_summary(quick)

    print(
        f"{'Driver':<8} {'랩수':>5}  {'평균(s)':>9}  "
        f"{'중앙값(s)':>10}  {'편차(s)':>8}  {'최속(s)':>9}"
    )
    print("-" * 58)
    for _, row in summary.iterrows():
        print(
            f"{row['Driver']:<8} {int(row['LapCount']):>5}  "
            f"{row['Mean']:>9.3f}  {row['Median']:>10.3f}  "
            f"{row['Std']:>8.3f}  {row['Best']:>9.3f}"
        )

    print(
        f"\n가장 빠른 페이스 (중앙값 기준): {summary.iloc[0]['Driver']}"
        f"  {summary.iloc[0]['Median']:.3f}s"
    )

    # ── 완료 ──────────────────────────────────────────────────
    section("완료")
    print("모든 lap_data 함수 검증 완료.")


if __name__ == "__main__":
    main()
