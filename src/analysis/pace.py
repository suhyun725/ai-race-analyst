"""
pace.py
=======
드라이버 페이스 비교 및 시각화 모듈

여러 드라이버의 랩별 페이스를 비교하고, 두 드라이버 간의 페이스 차이를
시각화하는 함수들을 제공한다.
"""

import matplotlib.pyplot as plt
import pandas as pd

# F1 팀 컬러 (2025 시즌 기준)
TEAM_COLORS = {
    # Red Bull
    "VER": "#3671C6",
    "LAW": "#3671C6",
    # McLaren
    "NOR": "#FF8000",
    "PIA": "#FF8000",
    # Ferrari  (HAM 이적)
    "LEC": "#E80020",
    "HAM": "#E80020",
    # Mercedes  (ANT 승격)
    "RUS": "#27F4D2",
    "ANT": "#27F4D2",
    # Aston Martin
    "ALO": "#229971",
    "STR": "#229971",
    # Alpine
    "GAS": "#FF87BC",
    "DOO": "#FF87BC",
    # RB
    "TSU": "#6692FF",
    "HAD": "#6692FF",
    # Haas  (OCO·BEA)
    "OCO": "#B6BABD",
    "BEA": "#B6BABD",
    # Williams  (SAI 이적)
    "ALB": "#64C4FF",
    "SAI": "#64C4FF",
    # Sauber/Audi  (HUL 이적)
    "HUL": "#52E252",
    "BOR": "#52E252",
    # 2024 이전 드라이버 (pace 분석 하위 호환)
    "PER": "#3671C6",
    "ZHO": "#52E252",
    "BOT": "#52E252",
    "MAG": "#B6BABD",
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


def plot_pace_evolution_styled(
    laps: pd.DataFrame,
    drivers: list[str],
    save_path: str | None = None,
    title: str | None = None,
    sc_laps: list[tuple[int, int]] | None = None,
    vsc_laps: list[tuple[int, int]] | None = None,
) -> None:
    """
    전체 드라이버 랩타임 추이를 다크 모드로 시각화한다.

    plot_pace_evolution의 스타일 강화 버전.
    SC/VSC 구간 음영, 드라이버 이름 인라인 레이블(영어)을 추가로 제공한다.

    Args:
        laps: long-format 페이스 DataFrame (compare_drivers_pace 반환값)
        drivers: 표시할 드라이버 목록
        save_path: 저장 경로. None이면 화면 출력.
        title: 그래프 제목. None이면 기본값 사용.
        sc_laps: Safety Car 구간 목록. 예: [(12, 15), (30, 32)]
        vsc_laps: Virtual SC 구간 목록. 예: [(20, 22)]

    Example:
        >>> plot_pace_evolution_styled(
        ...     pace_df, ['VER', 'NOR'], sc_laps=[(12, 15)], save_path='out.png'
        ... )
    """
    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(16, 8), dpi=150)

        # SC 구간 음영 (중복 레전드 방지)
        sc_labeled = False
        for start, end in sc_laps or []:
            ax.axvspan(
                start,
                end,
                alpha=0.20,
                color="#FFD700",
                label="Safety Car" if not sc_labeled else "_nolegend_",
                zorder=0,
            )
            sc_labeled = True

        # VSC 구간 음영
        vsc_labeled = False
        for start, end in vsc_laps or []:
            ax.axvspan(
                start,
                end,
                alpha=0.20,
                color="#00BFFF",
                label="Virtual SC" if not vsc_labeled else "_nolegend_",
                zorder=0,
            )
            vsc_labeled = True

        for driver in drivers:
            driver_laps = laps[laps["Driver"] == driver].sort_values("LapNumber")
            if driver_laps.empty:
                continue
            color = TEAM_COLORS.get(driver, "#888888")
            ax.plot(
                driver_laps["LapNumber"],
                driver_laps["LapTimeSeconds"],
                color=color,
                linewidth=1.8,
                marker="o",
                markersize=3,
                alpha=0.9,
                zorder=2,
            )
            # 마지막 랩 옆에 드라이버 이름 레이블 (영어)
            last = driver_laps.iloc[-1]
            ax.text(
                last["LapNumber"] + 0.5,
                last["LapTimeSeconds"],
                driver,
                color=color,
                fontsize=9,
                fontweight="bold",
                va="center",
                zorder=3,
            )

        ax.set_xlabel("Lap Number", fontsize=12)
        ax.set_ylabel("Lap Time (seconds)", fontsize=12)
        ax.set_title(title or "Pace Evolution", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, linestyle="--")

        # SC/VSC 음영이 있을 때만 레전드 표시
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, labels, loc="upper right", fontsize=10)

        fig.tight_layout()

        if save_path:
            fig.savefig(save_path, bbox_inches="tight")
            print(f"Saved: {save_path}")
        else:
            plt.show()

        plt.close(fig)


def plot_race_pace_overview(
    laps: pd.DataFrame,
    drivers: list[str],
    save_path: str | None = None,
    title: str | None = None,
    sc_laps: list[tuple[int, int]] | None = None,
    vsc_laps: list[tuple[int, int]] | None = None,
) -> None:
    """
    전체 드라이버의 랩별 페이스 추이를 다크 모드로 시각화한다.

    피트랩·SC랩 등 이상치(드라이버별 평균 + 3σ 초과)를 제거하고 메인 페이스
    범위에 y축을 자동 설정한다. SC/VSC 구간 음영, 라인 끝 인라인 레이블 포함.

    Args:
        laps: Driver, LapNumber, LapTimeSeconds 컬럼이 있는 DataFrame
        drivers: 표시할 드라이버 약자 리스트
        save_path: 저장 경로. None이면 화면 출력.
        title: 그래프 제목. None이면 기본값 사용.
        sc_laps: Safety Car 구간 목록. 예: [(12, 15), (30, 32)]
        vsc_laps: Virtual SC 구간 목록. 예: [(20, 22)]

    Example:
        >>> plot_race_pace_overview(
        ...     laps, ['VER', 'NOR', 'PIA'], sc_laps=[(12, 15)], save_path='out.png'
        ... )
    """
    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(16, 8), dpi=150)

        sc_labeled = False
        for start, end in sc_laps or []:
            ax.axvspan(
                start,
                end,
                alpha=0.20,
                color="#FFD700",
                label="Safety Car" if not sc_labeled else "_nolegend_",
                zorder=0,
            )
            sc_labeled = True

        vsc_labeled = False
        for start, end in vsc_laps or []:
            ax.axvspan(
                start,
                end,
                alpha=0.20,
                color="#00BFFF",
                label="Virtual SC" if not vsc_labeled else "_nolegend_",
                zorder=0,
            )
            vsc_labeled = True

        all_valid_times: list[float] = []

        for driver in drivers:
            driver_laps = laps[laps["Driver"] == driver].sort_values("LapNumber")
            if driver_laps.empty:
                continue
            times = driver_laps["LapTimeSeconds"].dropna()
            if times.empty:
                continue
            # 드라이버별 이상치 제거 (평균 + 3σ 초과 — 피트랩·SC랩 등)
            cutoff = times.mean() + 3 * times.std()
            filtered = driver_laps[driver_laps["LapTimeSeconds"] <= cutoff].copy()
            if filtered.empty:
                continue

            color = TEAM_COLORS.get(driver, "#888888")
            ax.plot(
                filtered["LapNumber"],
                filtered["LapTimeSeconds"],
                color=color,
                linewidth=1.8,
                marker="o",
                markersize=3,
                alpha=0.9,
                zorder=2,
            )
            last = filtered.iloc[-1]
            ax.text(
                last["LapNumber"] + 0.5,
                last["LapTimeSeconds"],
                driver,
                color=color,
                fontsize=9,
                fontweight="bold",
                va="center",
                zorder=3,
            )
            all_valid_times.extend(filtered["LapTimeSeconds"].tolist())

        # y축: 이상치 제거 후 데이터 범위에 맞게 자동 설정
        if all_valid_times:
            ax.set_ylim(min(all_valid_times) - 1.0, max(all_valid_times) + 1.0)

        ax.set_xlabel("Lap Number", fontsize=12)
        ax.set_ylabel("Pace (s)", fontsize=12)
        ax.set_title(title or "Race Pace Overview", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, linestyle="--")

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, labels, loc="upper right", fontsize=10)

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
