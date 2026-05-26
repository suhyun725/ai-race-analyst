"""
=============================================================
AI Race Analyst - Step 4: 타이어 디그라데이션 분석
=============================================================

목표: 2025 Bahrain GP 상위 5명의 스틴트별 디그라데이션을 연료 보정 후 정량 비교
실행: python3 step4_degradation_analysis.py
=============================================================
"""

from pathlib import Path

import pandas as pd

from src.analysis.degradation import (
    apply_fuel_correction,
    get_degradation_summary,
    plot_stint_degradation_overview,
)
from src.analysis.pace import plot_race_pace_overview
from src.data.lap_data import clean_lap_data, filter_quick_laps, get_drivers_laps
from src.data.session_loader import load_session, setup_cache

DRIVERS = ["PIA", "NOR", "VER", "RUS", "LEC"]
OUTPUT_DIR = Path("outputs")


def section(title: str) -> None:
    """섹션 구분선을 출력한다."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def extract_sc_vsc_ranges(
    laps: pd.DataFrame,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """TrackStatus에서 SC/VSC 구간을 (시작_랩, 끝_랩) 튜플 목록으로 추출한다."""

    def to_ranges(lap_nums: list[int]) -> list[tuple[int, int]]:
        if not lap_nums:
            return []
        sorted_laps = sorted(set(lap_nums))
        ranges: list[tuple[int, int]] = []
        start = prev = sorted_laps[0]
        for lap in sorted_laps[1:]:
            if lap > prev + 1:
                ranges.append((start, prev))
                start = lap
            prev = lap
        ranges.append((start, prev))
        return ranges

    if "TrackStatus" not in laps.columns:
        return [], []
    sc_nums = (
        laps[laps["TrackStatus"].str.contains("3", na=False)]["LapNumber"]
        .dropna()
        .astype(int)
        .tolist()
    )
    vsc_nums = (
        laps[laps["TrackStatus"].str.contains("6", na=False)]["LapNumber"]
        .dropna()
        .astype(int)
        .tolist()
    )
    return to_ranges(sc_nums), to_ranges(vsc_nums)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    # ── 0. 세션 로드 ──────────────────────────────────────────
    setup_cache()
    session = load_session(year=2025, gp="Bahrain", session_type="R")

    # ── 1. 랩 데이터 준비 ─────────────────────────────────────
    section("1. 데이터 준비")
    laps = get_drivers_laps(session, drivers=DRIVERS)
    clean = clean_lap_data(laps)
    quick = filter_quick_laps(clean, threshold=1.07)
    print(f"드라이버: {DRIVERS}")
    print(
        f"전체 랩 수: {len(laps)}  →  클린: {len(clean)}  →  107% 필터 후: {len(quick)}"
    )

    # ── 2. 연료 보정 ──────────────────────────────────────────
    section("2. 연료 보정 (0.03s/lap)")
    corrected = apply_fuel_correction(quick, fuel_effect_per_lap=0.03)
    sample = corrected[
        ["Driver", "LapNumber", "LapTimeSeconds", "LapTimeFuelCorrected"]
    ].head(3)
    print(sample.to_string(index=False))

    # ── 3. 디그라데이션 요약 테이블 ───────────────────────────
    section("3. Degradation Summary")
    summary = get_degradation_summary(corrected, drivers=DRIVERS)
    print(summary.to_string(index=False))

    # ── 4. 컴파운드별 평균 디그라데이션 ──────────────────────
    section("4. Average Degradation by Compound")
    avg = summary.groupby("Compound")["Slope"].agg(["mean", "std", "count"])
    avg.columns = ["Mean (s/lap)", "Std", "Stints"]
    print(avg.round(4).to_string())

    # ── 5. 시각화 ─────────────────────────────────────────────
    section("5. 시각화 생성")
    sc_ranges, vsc_ranges = extract_sc_vsc_ranges(quick)
    plot_race_pace_overview(
        quick,
        drivers=DRIVERS,
        save_path=str(OUTPUT_DIR / "race_pace_overview_bahrain_2025.png"),
        title="Race Pace Overview — 2025 Bahrain GP",
        sc_laps=sc_ranges,
        vsc_laps=vsc_ranges,
    )

    plot_stint_degradation_overview(
        corrected,
        drivers=DRIVERS,
        save_path=str(OUTPUT_DIR / "stint_degradation_overview_bahrain_2025.png"),
        title="Stint Degradation Overview — 2025 Bahrain GP",
    )

    print("\n✅ 분석 완료. outputs/ 폴더 확인.")


if __name__ == "__main__":
    main()
