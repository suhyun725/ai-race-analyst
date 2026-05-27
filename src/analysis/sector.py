"""
sector.py
=========
섹터 타임 분석 모듈

드라이버별 섹터 시간을 정리하고, 베스트 섹터 / 얼티밋 랩 / 스피드트랩을
계산·시각화하는 함수들을 제공한다.
"""

import fastf1
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analysis.pace import TEAM_COLORS

# 2025 시즌 드라이버 → 팀명 매핑
DRIVER_TEAM: dict[str, str] = {
    "VER": "Red Bull",
    "LAW": "Red Bull",
    "NOR": "McLaren",
    "PIA": "McLaren",
    "LEC": "Ferrari",
    "HAM": "Ferrari",
    "RUS": "Mercedes",
    "ANT": "Mercedes",
    "ALO": "Aston Martin",
    "STR": "Aston Martin",
    "GAS": "Alpine",
    "DOO": "Alpine",
    "TSU": "RB",
    "HAD": "RB",
    "HUL": "Sauber",
    "BEA": "Haas",
    "ALB": "Williams",
    "SAI": "Williams",
    "OCO": "Haas",
    "BOT": "Sauber",
    "BOR": "Sauber",
}


# 시각화 색상 팔레트
_BG = "#080d1a"
_ROW_EVEN = "#0d1117"
_ROW_ODD = "#111827"
_HEADER_BG = "#161d2e"
_TITLE_BG = "#0f172a"
_PURPLE_BG = "#2d1b69"
_PURPLE_TEXT = "#c084fc"
_HIGHLIGHT = "#e8d057"


def _to_seconds(td_series: pd.Series) -> pd.Series:
    """Timedelta 시리즈를 float 초로 변환한다. 이미 float이면 그대로 반환."""
    if pd.api.types.is_timedelta64_dtype(td_series):
        return td_series.dt.total_seconds()
    return td_series.astype(float)


def get_sector_times(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Sector1/2/3Time을 초 단위로 변환하고 드라이버별로 정리한다.

    Args:
        laps: FastF1 랩 데이터 DataFrame.
              Sector1Time, Sector2Time, Sector3Time 컬럼 필요.

    Returns:
        Driver, LapNumber, Sector1, Sector2, Sector3 컬럼을 가진 DataFrame (초 단위).

    Example:
        >>> sector_df = get_sector_times(session.laps)
    """
    df = laps.copy()
    cols_needed = ["Driver", "LapNumber", "Sector1Time", "Sector2Time", "Sector3Time"]
    available = [c for c in cols_needed if c in df.columns]
    df = df[available].copy()

    for col, out in [
        ("Sector1Time", "Sector1"),
        ("Sector2Time", "Sector2"),
        ("Sector3Time", "Sector3"),
    ]:
        if col in df.columns:
            df[out] = _to_seconds(df[col])

    drop_cols = [
        c for c in ["Sector1Time", "Sector2Time", "Sector3Time"] if c in df.columns
    ]
    df = df.drop(columns=drop_cols)

    df = df.dropna(subset=["Sector1", "Sector2", "Sector3"])
    df = df[(df["Sector1"] > 0) & (df["Sector2"] > 0) & (df["Sector3"] > 0)]

    return df.reset_index(drop=True)


def get_sector_summary(
    laps: pd.DataFrame,
    drivers: list[str] | None = None,
) -> pd.DataFrame:
    """
    드라이버별 섹터 평균 시간을 계산한다.

    Args:
        laps: get_sector_times() 반환 DataFrame
        drivers: 필터링할 드라이버 목록. None이면 전체.

    Returns:
        Driver, S1_Mean, S2_Mean, S3_Mean 컬럼을 가진 DataFrame (초 단위)

    Example:
        >>> summary = get_sector_summary(sector_df, ['VER', 'NOR'])
    """
    df = laps.copy()
    if drivers:
        df = df[df["Driver"].isin(drivers)]

    summary = (
        df.groupby("Driver")[["Sector1", "Sector2", "Sector3"]]
        .mean()
        .round(3)
        .reset_index()
    )
    summary.columns = ["Driver", "S1_Mean", "S2_Mean", "S3_Mean"]
    return summary


def get_sector_bests(
    session: fastf1.core.Session,
    drivers: list[str] | None = None,
) -> pd.DataFrame:
    """
    드라이버별 섹터 베스트 타임, 얼티밋 랩, 스피드트랩 최고속도를 계산한다.

    얼티밋 랩 = BestS1 + BestS2 + BestS3 (이론상 최속 랩타임).
    강점 섹터는 각 섹터에서 전체 드라이버 대비 최상위 분위에 속하는 섹터.

    Args:
        session: 로드된 FastF1 세션 객체
        drivers: 필터링할 드라이버 목록. None이면 전체.

    Returns:
        DataFrame with columns:
            Pos | Team | No | Driver | BestLap | UltimateLap | S1 | S2 | S3 | SpeedTrap | StrengthSector

    Example:
        >>> bests = get_sector_bests(session, ['VER', 'NOR', 'PIA'])
    """
    laps = session.laps.copy()

    if drivers:
        laps = laps[laps["Driver"].isin(drivers)]

    # 섹터 타임 초 변환
    for col, out in [
        ("Sector1Time", "S1"),
        ("Sector2Time", "S2"),
        ("Sector3Time", "S3"),
    ]:
        if col in laps.columns:
            laps[out] = _to_seconds(laps[col])

    # LapTime 초 변환
    if "LapTime" in laps.columns:
        laps["LapTimeSeconds"] = _to_seconds(laps["LapTime"])

    # SpeedST (속도 트랩) 처리
    speed_col = None
    for candidate in ["SpeedST", "SpeedFL", "SpeedI1", "SpeedI2"]:
        if candidate in laps.columns:
            speed_col = candidate
            break

    rows = []
    for driver, grp in laps.groupby("Driver"):
        grp_valid = grp.dropna(subset=["S1", "S2", "S3"])
        if grp_valid.empty:
            continue

        best_s1 = grp_valid["S1"].min()
        best_s2 = grp_valid["S2"].min()
        best_s3 = grp_valid["S3"].min()
        ultimate = best_s1 + best_s2 + best_s3

        # 최속 랩타임 (전체 랩 기준)
        grp_lap = (
            grp.dropna(subset=["LapTimeSeconds"])
            if "LapTimeSeconds" in grp.columns
            else grp_valid
        )
        best_lap = (
            grp_lap["LapTimeSeconds"].min()
            if "LapTimeSeconds" in grp_lap.columns
            else np.nan
        )

        # 스피드트랩 최고속도
        speed_trap = np.nan
        if speed_col and speed_col in grp.columns:
            sp = grp[speed_col].dropna()
            if not sp.empty:
                speed_trap = sp.max()

        # 드라이버 번호
        driver_no = ""
        if "DriverNumber" in grp.columns:
            driver_no = str(grp["DriverNumber"].iloc[0])

        # 최종 순위 (결승선 기준)
        pos = np.nan
        if "Position" in grp.columns:
            last_pos = grp["Position"].dropna()
            if not last_pos.empty:
                pos = int(last_pos.iloc[-1])

        rows.append(
            {
                "Pos": pos,
                "Team": DRIVER_TEAM.get(str(driver), ""),
                "No": driver_no,
                "Driver": str(driver),
                "BestLap": round(best_lap, 3) if not np.isnan(best_lap) else np.nan,
                "UltimateLap": round(ultimate, 3),
                "S1": round(best_s1, 3),
                "S2": round(best_s2, 3),
                "S3": round(best_s3, 3),
                "SpeedTrap": (
                    round(speed_trap, 1) if not np.isnan(speed_trap) else np.nan
                ),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # 강점 섹터 계산: 각 섹터 순위 기준 (낮을수록 좋음)
    for s in ["S1", "S2", "S3"]:
        df[f"{s}_rank"] = df[s].rank()

    def _strength(row: pd.Series) -> str:
        ranks = {"S1": row["S1_rank"], "S2": row["S2_rank"], "S3": row["S3_rank"]}
        best = min(ranks, key=lambda k: ranks[k])
        # 1~3위면 강점 섹터로 표시
        if ranks[best] <= 3:
            return best
        return ""

    df["StrengthSector"] = df.apply(_strength, axis=1)
    df = df.drop(columns=["S1_rank", "S2_rank", "S3_rank"])

    # 순위 정렬
    df = df.sort_values("Pos", na_position="last").reset_index(drop=True)

    return df


def _fmt_time(seconds: float) -> str:
    """초를 M:SS.mmm 형식 문자열로 변환한다."""
    if np.isnan(seconds):
        return "—"
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m}:{s:06.3f}"


def _fmt_sector(seconds: float) -> str:
    """섹터 시간을 SS.mmm 형식으로 변환한다."""
    if np.isnan(seconds):
        return "—"
    return f"{seconds:.3f}"


def plot_sector_table(
    session: fastf1.core.Session,
    save_path: str,
    csv_path: str | None = None,
) -> pd.DataFrame:
    """
    전체 드라이버 섹터 요약 표를 matplotlib 이미지로 저장한다.

    컬럼: 순위 | 팀 | 번호 | 드라이버 | 최고기록 | 얼티밋랩 | S1 | S2 | S3 | 스피드트랩
    전체 드라이버, 팀 컬러 배경, 다크 배경 스타일.

    Args:
        session: 로드된 FastF1 세션 객체
        save_path: PNG 저장 경로
        csv_path: CSV 저장 경로. None이면 저장 안 함.

    Returns:
        get_sector_bests() 반환 DataFrame

    Example:
        >>> df = plot_sector_table(session, 'outputs/sector_table.png', 'outputs/sector_table.csv')
    """
    df = (
        get_sector_bests(session)
        .sort_values("BestLap", na_position="last")
        .reset_index(drop=True)
    )

    if csv_path:
        df.to_csv(csv_path, index=False)
        print(f"Saved CSV: {csv_path}")

    # 컬럼별 베스트 드라이버 (보라색 하이라이트 대상)
    best_drivers: dict[int, str] = {}
    for col_idx, col_key in [
        (4, "BestLap"),
        (5, "UltimateLap"),
        (6, "S1"),
        (7, "S2"),
        (8, "S3"),
    ]:
        valid = df[col_key].dropna()
        if not valid.empty:
            best_drivers[col_idx] = df.loc[valid.idxmin(), "Driver"]
    # SpeedTrap: 최고속도 = max
    valid_speed = df["SpeedTrap"].dropna()
    if not valid_speed.empty:
        best_drivers[9] = df.loc[valid_speed.idxmax(), "Driver"]

    # 표 데이터 구성
    col_headers = [
        "Pos",
        "Team",
        "No",
        "Driver",
        "Best Lap",
        "Ultimate",
        "S1",
        "S2",
        "S3",
        "Speed\nTrap",
    ]
    col_widths = [0.06, 0.14, 0.06, 0.10, 0.13, 0.13, 0.10, 0.10, 0.10, 0.10]

    table_data = []
    for _, row in df.iterrows():
        pos_str = (
            str(int(row["Pos"]))
            if not (isinstance(row["Pos"], float) and np.isnan(row["Pos"]))
            else "—"
        )
        speed_str = f"{row['SpeedTrap']:.0f}" if not np.isnan(row["SpeedTrap"]) else "—"
        table_data.append(
            [
                pos_str,
                row["Team"],
                row["No"],
                row["Driver"],
                _fmt_time(row["BestLap"]),
                _fmt_time(row["UltimateLap"]),
                _fmt_sector(row["S1"]),
                _fmt_sector(row["S2"]),
                _fmt_sector(row["S3"]),
                speed_str,
            ]
        )

    n_rows = len(table_data)

    row_h = 0.44
    header_h = 0.70
    title_h = 0.60
    fig_h = title_h + header_h + n_rows * row_h + 0.3
    fig_w = 18

    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, fig_h)
        ax.axis("off")
        fig.patch.set_facecolor(_BG)
        ax.set_facecolor(_BG)

        # 타이틀 배너
        title_rect = plt.Rectangle(
            (0, fig_h - title_h),
            1.0,
            title_h,
            facecolor=_TITLE_BG,
            edgecolor="none",
            zorder=1,
        )
        ax.add_patch(title_rect)
        # 타이틀 왼쪽 강조 바
        ax.add_patch(
            plt.Rectangle(
                (0, fig_h - title_h),
                0.007,
                title_h,
                facecolor="#e80020",
                edgecolor="none",
                zorder=2,
            )
        )
        ax.text(
            0.5,
            fig_h - title_h / 2,
            "2025 Bahrain GP  —  Sector Analysis",
            ha="center",
            va="center",
            fontsize=17,
            fontweight="bold",
            color="white",
            zorder=3,
        )

        # 컬럼 x 위치
        x_positions = []
        x = 0.01
        for w in col_widths:
            x_positions.append(x + w / 2)
            x += w

        # 헤더 행
        header_top = fig_h - title_h
        header_y = header_top - header_h / 2
        ax.add_patch(
            plt.Rectangle(
                (0, header_top - header_h),
                1.0,
                header_h,
                facecolor=_HEADER_BG,
                edgecolor="none",
                zorder=1,
            )
        )
        for hdr, xp in zip(col_headers, x_positions, strict=True):
            ax.text(
                xp,
                header_y,
                hdr,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color="#94a3b8",
                zorder=2,
            )

        # 데이터 행
        data_top = header_top - header_h
        for r_idx, row_data in enumerate(table_data):
            driver = row_data[3]
            team_color = TEAM_COLORS.get(driver, "#444466")
            row_top = data_top - r_idx * row_h
            row_bottom = row_top - row_h
            row_center_y = (row_top + row_bottom) / 2

            bg_color = _ROW_EVEN if r_idx % 2 == 0 else _ROW_ODD
            ax.add_patch(
                plt.Rectangle(
                    (0, row_bottom),
                    1.0,
                    row_h,
                    facecolor=bg_color,
                    edgecolor="none",
                    zorder=1,
                )
            )
            # 팀 컬러 사이드바 (더 굵게)
            ax.add_patch(
                plt.Rectangle(
                    (0, row_bottom),
                    0.008,
                    row_h,
                    facecolor=team_color,
                    edgecolor="none",
                    zorder=2,
                )
            )
            # 행 구분선
            ax.axhline(
                y=row_bottom,
                xmin=0,
                xmax=1,
                color="#1e293b",
                linewidth=0.6,
                zorder=3,
            )

            for c_idx, (cell, xp) in enumerate(zip(row_data, x_positions, strict=True)):
                is_best = best_drivers.get(c_idx) == driver

                # 베스트 셀: 보라색 배경
                if is_best:
                    cell_w = col_widths[c_idx] * 0.92
                    ax.add_patch(
                        plt.Rectangle(
                            (xp - cell_w / 2, row_bottom + row_h * 0.08),
                            cell_w,
                            row_h * 0.84,
                            facecolor=_PURPLE_BG,
                            edgecolor="none",
                            linewidth=0,
                            zorder=2,
                        )
                    )
                    text_color = _PURPLE_TEXT
                    fw = "bold"
                elif c_idx == 3:
                    text_color = team_color
                    fw = "bold"
                elif c_idx == 0:
                    text_color = "#fbbf24"
                    fw = "bold"
                else:
                    text_color = "#cbd5e1"
                    fw = "normal"

                ax.text(
                    xp,
                    row_center_y,
                    str(cell),
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color=text_color,
                    fontweight=fw,
                    zorder=4,
                )

        fig.savefig(
            save_path, bbox_inches="tight", facecolor=fig.get_facecolor(), pad_inches=0
        )
        print(f"Saved: {save_path}")
        plt.close(fig)

    return df


def plot_sector_bars(
    session: fastf1.core.Session,
    save_path: str,
) -> None:
    """
    전체 드라이버의 S1/S2/S3 베스트 타임을 3열 수평 막대 그래프로 시각화한다.

    팀 컬러 적용, 다크 배경, 오름차순 정렬.

    Args:
        session: 로드된 FastF1 세션 객체
        save_path: PNG 저장 경로

    Example:
        >>> plot_sector_bars(session, 'outputs/sector_bars.png')
    """
    df = get_sector_bests(session)

    # 고정 Y축 순서: 얼티밋랩 기준 오름차순 (빠른 드라이버가 위)
    order = (
        df[["Driver", "UltimateLap"]]
        .dropna()
        .sort_values("UltimateLap", ascending=False)["Driver"]
        .tolist()
    )

    with plt.style.context("dark_background"):
        fig, axes = plt.subplots(1, 3, figsize=(18, 10), dpi=150)
        fig.patch.set_facecolor(_BG)

        for ax, sector, label in zip(
            axes, ["S1", "S2", "S3"], ["Sector 1", "Sector 2", "Sector 3"], strict=True
        ):
            ax.set_facecolor(_BG)
            # 고정 순서 적용 (해당 섹터 데이터 없는 드라이버 제외)
            sub = (
                df[["Driver", sector]]
                .dropna()
                .set_index("Driver")
                .reindex(order)
                .dropna()
                .reset_index()
            )
            best_driver = sub.loc[sub[sector].idxmin(), "Driver"]

            bar_colors = []
            for d in sub["Driver"]:
                bar_colors.append(
                    _HIGHLIGHT if d == best_driver else TEAM_COLORS.get(d, "#556677")
                )

            bars = ax.barh(
                sub["Driver"],
                sub[sector],
                color=bar_colors,
                edgecolor="none",
                height=0.65,
            )

            # 값 레이블: 시간(위) / 델타(아래) 세로 분리
            min_val = sub[sector].min()
            h = bars[0].get_height()
            for bar, val in zip(bars, sub[sector], strict=False):
                delta = val - min_val
                x0 = bar.get_width() + 0.006
                cy = bar.get_y() + h / 2
                ax.text(
                    x0,
                    cy + h * 0.22,
                    f"{val:.3f}",
                    va="center",
                    ha="left",
                    fontsize=7.5,
                    color="#e2e8f0",
                    fontweight="bold",
                )
                ax.text(
                    x0,
                    cy - h * 0.22,
                    "BEST" if delta == 0 else f"+{delta:.3f}",
                    va="center",
                    ha="left",
                    fontsize=6.5,
                    color=_HIGHLIGHT if delta == 0 else "#475569",
                )

            x_min = sub[sector].min() - 0.08
            x_max = sub[sector].max() + 0.40
            ax.set_xlim(x_min, x_max)
            ax.set_xlabel("Time (s)", fontsize=10, color="#64748b")
            ax.set_title(label, fontsize=13, fontweight="bold", color="white", pad=12)
            ax.tick_params(axis="y", labelsize=9, colors="#cbd5e1")
            ax.tick_params(axis="x", labelsize=8, colors="#475569")
            ax.grid(axis="x", alpha=0.15, linestyle="--", color="#334155")
            for spine in ax.spines.values():
                spine.set_color("#1e293b")

        fig.suptitle(
            "2025 Bahrain GP  —  Best Sector Times",
            fontsize=15,
            fontweight="bold",
            color="white",
            y=1.02,
        )
        fig.tight_layout(pad=1.5)
        fig.savefig(save_path, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"Saved: {save_path}")
        plt.close(fig)


def plot_overall_bars(
    session: fastf1.core.Session,
    save_path: str,
) -> None:
    """
    전체 드라이버의 최고기록 / 얼티밋랩 / 스피드트랩을 3열 수평 막대 그래프로 시각화한다.

    Args:
        session: 로드된 FastF1 세션 객체
        save_path: PNG 저장 경로

    Example:
        >>> plot_overall_bars(session, 'outputs/overall_bars.png')
    """
    df = get_sector_bests(session)

    # 고정 Y축 순서: BestLap 기준 오름차순 (빠른 드라이버가 위)
    order = (
        df[["Driver", "BestLap"]]
        .dropna()
        .sort_values("BestLap", ascending=False)["Driver"]
        .tolist()
    )

    with plt.style.context("dark_background"):
        fig, axes = plt.subplots(1, 3, figsize=(18, 10), dpi=150)
        fig.patch.set_facecolor(_BG)

        configs = [
            ("BestLap", "Best Lap Time", "Time (s)", False),
            ("UltimateLap", "Ultimate Lap", "Time (s)", False),
            ("SpeedTrap", "Speed Trap", "Speed (km/h)", True),
        ]

        for ax, (col, label, xlabel, higher_is_better) in zip(
            axes, configs, strict=True
        ):
            ax.set_facecolor(_BG)
            sub = (
                df[["Driver", col]]
                .dropna()
                .set_index("Driver")
                .reindex(order)
                .dropna()
                .reset_index()
            )

            if higher_is_better:
                best_driver = sub.loc[sub[col].idxmax(), "Driver"]
            else:
                best_driver = sub.loc[sub[col].idxmin(), "Driver"]

            bar_colors = [
                _HIGHLIGHT if d == best_driver else TEAM_COLORS.get(d, "#556677")
                for d in sub["Driver"]
            ]
            bars = ax.barh(
                sub["Driver"], sub[col], color=bar_colors, edgecolor="none", height=0.65
            )

            best_val = sub.loc[sub["Driver"] == best_driver, col].iloc[0]
            h = bars[0].get_height()
            for bar, val in zip(bars, sub[col], strict=False):
                delta = val - best_val
                is_best_bar = delta == 0
                cy = bar.get_y() + h / 2

                if higher_is_better:
                    val_str = f"{val:.0f}"
                    delta_str = "BEST" if is_best_bar else f"{delta:+.1f}"
                    x0 = bar.get_width() + sub[col].max() * 0.003
                else:
                    val_str = _fmt_time(val)
                    delta_str = "BEST" if is_best_bar else f"+{delta:.3f}"
                    x0 = bar.get_width() + 0.01

                # 실제 값 위쪽, 델타 아래쪽 세로 분리
                ax.text(
                    x0,
                    cy + h * 0.22,
                    val_str,
                    va="center",
                    ha="left",
                    fontsize=7.5,
                    color="#e2e8f0",
                    fontweight="bold",
                )
                ax.text(
                    x0,
                    cy - h * 0.22,
                    delta_str,
                    va="center",
                    ha="left",
                    fontsize=6.5,
                    color=_HIGHLIGHT if is_best_bar else "#475569",
                )

            if higher_is_better:
                x_min = sub[col].min() * 0.994
                x_max = sub[col].max() * 1.022
            else:
                x_min = sub[col].min() - 0.08
                x_max = sub[col].max() + 1.5

            ax.set_xlim(x_min, x_max)
            ax.set_xlabel(xlabel, fontsize=10, color="#64748b")
            ax.set_title(label, fontsize=13, fontweight="bold", color="white", pad=12)
            ax.tick_params(axis="y", labelsize=9, colors="#cbd5e1")
            ax.tick_params(axis="x", labelsize=8, colors="#475569")
            ax.grid(axis="x", alpha=0.15, linestyle="--", color="#334155")
            for spine in ax.spines.values():
                spine.set_color("#1e293b")

        fig.suptitle(
            "2025 Bahrain GP  —  Lap Time & Speed Overview",
            fontsize=15,
            fontweight="bold",
            color="white",
            y=1.02,
        )
        fig.tight_layout(pad=1.5)
        fig.savefig(save_path, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"Saved: {save_path}")
        plt.close(fig)
