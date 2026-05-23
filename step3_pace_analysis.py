"""
=============================================================
AI Race Analyst - Step 3: Pace Analysis & Race Trace
=============================================================

목표: 2024 브라질 GP 본경기 페이스 분석 + 경기 전체 시각화
실행: python3 step3_pace_analysis.py
=============================================================
"""

from pathlib import Path

from src.analysis.pace import (
    compare_drivers_pace,
    plot_pace_evolution,
)
from src.analysis.position import (
    DRIVER_NUMBERS,
    get_pit_stops,
    get_position_history,
    get_track_events,
    plot_race_trace,
)
from src.data.lap_data import (
    clean_lap_data,
    filter_quick_laps,
    get_drivers_laps,
    get_pace_summary,
)
from src.data.session_loader import load_session, setup_cache

# 분석 대상 드라이버
DRIVERS_TOP5 = ["VER", "NOR", "LEC", "OCO", "GAS"]
DRIVERS_TO_HIGHLIGHT = ["VER", "NOR", "OCO", "GAS"]


def print_track_events_summary(events: dict, pit_stops) -> None:
    """트랙 이벤트 및 주요 드라이버 피트스톱을 콘솔에 출력한다."""
    print("\n" + "=" * 60)
    print("Track Events Summary")
    print("=" * 60)

    rain = events.get("rain_periods", [])
    sc = events.get("safety_car_periods", [])
    vsc = events.get("vsc_periods", [])

    if rain:
        for start, end in rain:
            print(f"  Rain:         Lap {start}-{end}")
    else:
        print("  Rain:         Not detected")

    if sc:
        for start, end in sc:
            print(f"  Safety Car:   Lap {start}-{end}")
    else:
        print("  Safety Car:   Not detected")

    if vsc:
        for start, end in vsc:
            print(f"  VSC:          Lap {start}-{end}")
    else:
        print("  VSC:          Not detected")

    print()
    for driver in DRIVERS_TO_HIGHLIGHT:
        driver_pits = pit_stops[pit_stops["Driver"] == driver]
        if driver_pits.empty:
            print(f"  {driver} pit stops: None")
        else:
            lap_list = ", ".join(str(int(r)) for r in driver_pits["LapNumber"])
            print(f"  {driver} pit stops: Lap {lap_list}")


def main() -> None:
    # outputs/ 폴더 생성
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    # 세션 로드
    setup_cache()
    session = load_session(2024, "Brazil", "R")

    # ----------------------------------------------------------------
    # 페이스 분석 (상위 5명)
    # ----------------------------------------------------------------
    print("\n[1] Pace analysis ...")
    all_laps = get_drivers_laps(session, DRIVERS_TOP5)
    cleaned = clean_lap_data(all_laps)
    quick = filter_quick_laps(cleaned, threshold=1.07)

    pace_df = compare_drivers_pace(quick, DRIVERS_TOP5)
    summary = get_pace_summary(quick)

    print("\nPace summary (top 5 drivers):")
    print(summary.to_string(index=False))

    # ----------------------------------------------------------------
    # 경기 전체 분석
    # ----------------------------------------------------------------
    print("\n[2] Race trace analysis ...")
    position_history = get_position_history(session)
    pit_stops = get_pit_stops(session)
    track_events = get_track_events(session)

    print_track_events_summary(track_events, pit_stops)

    # ----------------------------------------------------------------
    # 그래프 저장
    # ----------------------------------------------------------------
    print("\n[3] Generating charts ...")

    # ① 메인: Race Trace
    plot_race_trace(
        position_history=position_history,
        pit_stops=pit_stops,
        track_events=track_events,
        drivers_to_highlight=DRIVERS_TO_HIGHLIGHT,
        driver_numbers=DRIVER_NUMBERS,
        save_path=str(output_dir / "race_trace_brazil_2024.png"),
        title="Brazil GP 2024 - Race Trace",
    )

    # ② 페이스 변화
    plot_pace_evolution(
        laps=pace_df,
        drivers=DRIVERS_TOP5,
        save_path=str(output_dir / "pace_evolution_brazil_2024.png"),
        title="Brazil GP 2024 - Pace Evolution (Top 5)",
    )

    print("\nDone. Charts saved to outputs/")


if __name__ == "__main__":
    main()
