"""
pace.py
=======
드라이버 페이스 비교 및 시각화 모듈

여러 드라이버의 랩별 페이스를 비교하고, 두 드라이버 간의 페이스 차이를
시각화하는 함수들을 제공한다.
"""

import matplotlib.pyplot as plt
import pandas as pd

# F1 팀 컬러 (2024 시즌)
TEAM_COLORS = {
    "VER": "#3671C6",  # Red Bull
    "PER": "#3671C6",
    "NOR": "#FF8000",  # McLaren
    "PIA": "#FF8000",
    "LEC": "#E80020",  # Ferrari
    "SAI": "#E80020",
    "HAM": "#27F4D2",  # Mercedes
    "RUS": "#27F4D2",
    "OCO": "#0093CC",  # Alpine
    "GAS": "#FF87BC",  # Alpine (핑크로 구분)
    "STR": "#229971",  # Aston Martin
    "ALO": "#229971",
    "TSU": "#6692FF",  # RB
    "LAW": "#6692FF",
    "BOT": "#52E252",  # Sauber
    "ZHO": "#52E252",
    "MAG": "#B6BABD",  # Haas
    "HUL": "#B6BABD",
    "ALB": "#64C4FF",  # Williams
    "COL": "#64C4FF",
    "SAR": "#64C4FF",
}


def compare_drivers_pace(
    laps: pd.DataFrame,
    drivers: list[str],
) -> pd.DataFrame:
    """
    여러 드라이버의 랩별 페이스 데이터를 long-format으로 정리한다.

    Args:
        laps: 랩 데이터 DataFrame (LapTimeSeconds, Compound 컬럼 필요)
        drivers: 비교할 드라이버 약자 리스트 (예: ['VER', 'NOR', 'LEC'])

    Returns:
        long-format 페이스 DataFrame.
        컬럼: ['LapNumber', 'Driver', 'LapTimeSeconds', 'Compound']

    Example:
        >>> pace_df = compare_drivers_pace(laps, ['VER', 'NOR', 'LEC'])
    """
    filtered = laps[laps["Driver"].isin(drivers)].copy()
    cols = ["LapNumber", "Driver", "LapTimeSeconds", "Compound"]
    available = [c for c in cols if c in filtered.columns]
    return filtered[available].reset_index(drop=True)


def calculate_pace_delta(
    laps: pd.DataFrame,
    driver1: str,
    driver2: str,
) -> pd.DataFrame:
    """
    두 드라이버의 랩별 페이스 차이를 계산한다.

    Args:
        laps: 랩 데이터 DataFrame (LapTimeSeconds 컬럼 필요)
        driver1: 기준 드라이버 약자
        driver2: 비교 드라이버 약자

    Returns:
        랩별 페이스 차이 DataFrame.
        컬럼: ['LapNumber', 'Driver1Time', 'Driver2Time', 'Delta']
        Delta = Driver1Time - Driver2Time (양수면 Driver1이 더 느림)

    Example:
        >>> delta = calculate_pace_delta(laps, 'VER', 'NOR')
    """
    d1 = laps[laps["Driver"] == driver1][["LapNumber", "LapTimeSeconds"]].rename(
        columns={"LapTimeSeconds": "Driver1Time"}
    )
    d2 = laps[laps["Driver"] == driver2][["LapNumber", "LapTimeSeconds"]].rename(
        columns={"LapTimeSeconds": "Driver2Time"}
    )

    merged = pd.merge(d1, d2, on="LapNumber", how="inner")
    merged["Delta"] = merged["Driver1Time"] - merged["Driver2Time"]
    return merged.reset_index(drop=True)


def plot_pace_evolution(
    laps: pd.DataFrame,
    drivers: list[str],
    save_path: str | None = None,
    title: str | None = None,
) -> None:
    """
    여러 드라이버의 랩별 페이스 변화를 라인 그래프로 시각화한다.

    Args:
        laps: long-format 페이스 DataFrame (compare_drivers_pace 반환값)
        drivers: 표시할 드라이버 목록 (최대 5명 권장)
        save_path: 저장 경로. None이면 화면 출력.
        title: 그래프 제목. None이면 기본값 사용.

    Example:
        >>> plot_pace_evolution(pace_df, ['VER', 'NOR'], save_path='out.png')
    """
    fig, ax = plt.subplots(figsize=(14, 7), dpi=150)

    for driver in drivers:
        driver_laps = laps[laps["Driver"] == driver].sort_values("LapNumber")
        if driver_laps.empty:
            continue
        color = TEAM_COLORS.get(driver, "#888888")
        ax.plot(
            driver_laps["LapNumber"],
            driver_laps["LapTimeSeconds"],
            color=color,
            linewidth=2,
            label=driver,
            marker="o",
            markersize=3,
        )

    ax.set_xlabel("Lap Number", fontsize=12)
    ax.set_ylabel("Lap Time (seconds)", fontsize=12)
    ax.set_title(title or "Pace Evolution", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    else:
        plt.show()

    plt.close(fig)


def plot_pace_delta(
    delta_df: pd.DataFrame,
    save_path: str | None = None,
    title: str | None = None,
) -> None:
    """
    두 드라이버 간의 랩별 페이스 차이를 시각화한다.

    Args:
        delta_df: calculate_pace_delta 반환 DataFrame
        save_path: 저장 경로. None이면 화면 출력.
        title: 그래프 제목. None이면 기본값 사용.

    Example:
        >>> plot_pace_delta(delta_df, save_path='delta.png')
    """
    fig, ax = plt.subplots(figsize=(14, 6), dpi=150)

    laps = delta_df["LapNumber"]
    delta = delta_df["Delta"]

    ax.plot(laps, delta, color="#888888", linewidth=1.5, zorder=3)
    ax.axhline(y=0, color="white", linewidth=1, linestyle="--", alpha=0.7, zorder=2)

    ax.fill_between(
        laps,
        delta,
        0,
        where=(delta > 0),
        color="#E84040",
        alpha=0.4,
        label="Driver1 slower",
    )
    ax.fill_between(
        laps,
        delta,
        0,
        where=(delta <= 0),
        color="#40C0E8",
        alpha=0.4,
        label="Driver1 faster",
    )

    ax.set_xlabel("Lap Number", fontsize=12)
    ax.set_ylabel("Delta (seconds)", fontsize=12)
    ax.set_title(title or "Pace Delta", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    else:
        plt.show()

    plt.close(fig)
