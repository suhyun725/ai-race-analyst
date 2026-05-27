"""
=============================================================
AI Race Analyst - Step 5: 섹터 분석
=============================================================

목표: 2025 Bahrain GP 전체 드라이버 섹터 타임 분석
실행: python3 step5_sector_analysis.py
=============================================================
"""

from pathlib import Path

from src.analysis.sector import (
    get_sector_bests,
    get_sector_times,
    plot_overall_bars,
    plot_sector_bars,
    plot_sector_table,
)
from src.data.session_loader import load_session, setup_cache

OUTPUT_DIR = Path("outputs")


def section(title: str) -> None:
    """섹션 구분선을 출력한다."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    # ── 0. 세션 로드 ──────────────────────────────────────────
    setup_cache()
    session = load_session(year=2025, gp="Bahrain", session_type="R")

    # ── 1. 섹터 타임 확인 ─────────────────────────────────────
    section("1. 섹터 타임 데이터 준비")
    sector_df = get_sector_times(session.laps)
    print(f"유효 섹터 랩 수: {len(sector_df)}")
    print(f"드라이버 수: {sector_df['Driver'].nunique()}")
    print(
        sector_df[["Driver", "LapNumber", "Sector1", "Sector2", "Sector3"]]
        .head(5)
        .to_string(index=False)
    )

    # ── 2. 섹터 베스트 요약 ───────────────────────────────────
    section("2. Sector Bests Summary")
    bests = get_sector_bests(session)
    print(
        bests[
            [
                "Pos",
                "Driver",
                "Team",
                "BestLap",
                "UltimateLap",
                "S1",
                "S2",
                "S3",
                "SpeedTrap",
            ]
        ].to_string(index=False)
    )

    # ── 3. 섹터 표 이미지 + CSV ───────────────────────────────
    section("3. 섹터 표 생성")
    table_png = str(OUTPUT_DIR / "sector_table_bahrain_2025.png")
    csv_path = str(OUTPUT_DIR / "sector_summary_bahrain_2025.csv")
    plot_sector_table(session, save_path=table_png, csv_path=csv_path)

    # ── 4. 섹터별 막대 그래프 ─────────────────────────────────
    section("4. 섹터별 막대 그래프")
    plot_sector_bars(
        session,
        save_path=str(OUTPUT_DIR / "sector_bars_bahrain_2025.png"),
    )

    # ── 5. 종합 막대 그래프 ───────────────────────────────────
    section("5. 종합 막대 그래프 (최고기록 / 얼티밋랩 / 스피드트랩)")
    plot_overall_bars(
        session,
        save_path=str(OUTPUT_DIR / "overall_bars_bahrain_2025.png"),
    )

    print("\n✅ 섹터 분석 완료. outputs/ 폴더 확인.")
    print(f"  - {table_png}")
    print(f"  - {csv_path}")
    print(f"  - {str(OUTPUT_DIR / 'sector_bars_bahrain_2025.png')}")
    print(f"  - {str(OUTPUT_DIR / 'overall_bars_bahrain_2025.png')}")


if __name__ == "__main__":
    main()
