"""
position.py
===========
경기 순위 변동 및 Race Trace 시각화 모듈

랩별 순위 기록, 피트스톱 정보, 트랙 이벤트(비/SC/VSC)를 추출하고,
F1 공식 방송 스타일의 Race Trace 그래프를 생성한다.
"""

import fastf1
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
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

# 2024 시즌 드라이버 번호
DRIVER_NUMBERS = {
    "VER": 1,
    "PER": 11,
    "NOR": 4,
    "PIA": 81,
    "LEC": 16,
    "SAI": 55,
    "HAM": 44,
    "RUS": 63,
    "OCO": 31,
    "GAS": 10,
    "STR": 18,
    "ALO": 14,
    "TSU": 22,
    "LAW": 30,
    "RIC": 3,
    "BOT": 77,
    "ZHO": 24,
    "MAG": 20,
    "HUL": 27,
    "BEA": 38,
    "ALB": 23,
    "COL": 43,
    "SAR": 2,
}


def get_position_history(
    session: fastf1.core.Session,
    drivers: list[str] | None = None,
) -> pd.DataFrame:
    """
    랩별 각 드라이버의 순위를 추출한다. Lap 0에 그리드 출발 위치를 포함한다.

    Args:
        session: 로드된 FastF1 세션 객체
        drivers: 드라이버 약자 리스트. None이면 전체 드라이버.

    Returns:
        랩별 순위 DataFrame. Lap 0은 그리드 출발 위치.
        컬럼: ['LapNumber', 'Driver', 'Position']

    Example:
        >>> pos_history = get_position_history(session, ['VER', 'NOR'])
    """
    laps = session.laps.copy()
    if drivers is not None:
        laps = laps[laps["Driver"].isin(drivers)]

    cols = ["LapNumber", "Driver", "Position"]
    available = [c for c in cols if c in laps.columns]
    result = laps[available].dropna(subset=["Position"]).copy()
    result["Position"] = result["Position"].astype(int)

    # Lap 0: session.results에서 그리드 출발 위치 추가
    try:
        results_df = session.results[["Abbreviation", "GridPosition"]].dropna(
            subset=["GridPosition"]
        )
        results_df = results_df[results_df["GridPosition"] > 0]
        grid_rows = []
        for _, row in results_df.iterrows():
            driver = row["Abbreviation"]
            if drivers is not None and driver not in drivers:
                continue
            grid_rows.append(
                {
                    "LapNumber": 0,
                    "Driver": driver,
                    "Position": int(row["GridPosition"]),
                }
            )
        if grid_rows:
            grid_df = pd.DataFrame(grid_rows)
            result = pd.concat([grid_df, result], ignore_index=True)
    except Exception:
        pass

    result["LapNumber"] = result["LapNumber"].astype(int)
    return result.sort_values(["LapNumber", "Driver"]).reset_index(drop=True)


def get_pit_stops(
    session: fastf1.core.Session,
    drivers: list[str] | None = None,
) -> pd.DataFrame:
    """
    각 드라이버의 피트스톱 정보를 추출한다.

    PitInTime이 있는 랩을 피트스톱 랩으로 간주한다.

    Args:
        session: 로드된 FastF1 세션 객체
        drivers: 드라이버 약자 리스트. None이면 전체 드라이버.

    Returns:
        피트스톱 정보 DataFrame.
        컬럼: ['Driver', 'LapNumber', 'CompoundIn', 'CompoundOut']

    Example:
        >>> pits = get_pit_stops(session, ['VER', 'NOR'])
    """
    laps = session.laps.copy()
    if drivers is not None:
        laps = laps[laps["Driver"].isin(drivers)]

    pit_laps = laps[laps["PitInTime"].notna()].copy()

    records = []
    for _, row in pit_laps.iterrows():
        driver = row["Driver"]
        lap_num = int(row["LapNumber"])
        compound_in = row.get("Compound", "UNKNOWN")

        # 다음 랩의 컴파운드를 OutCompound로 사용
        next_lap = laps[(laps["Driver"] == driver) & (laps["LapNumber"] == lap_num + 1)]
        compound_out = (
            next_lap["Compound"].values[0] if not next_lap.empty else "UNKNOWN"
        )

        records.append(
            {
                "Driver": driver,
                "LapNumber": lap_num,
                "CompoundIn": compound_in,
                "CompoundOut": compound_out,
            }
        )

    if not records:
        return pd.DataFrame(
            columns=["Driver", "LapNumber", "CompoundIn", "CompoundOut"]
        )

    return pd.DataFrame(records).reset_index(drop=True)


def get_track_events(session: fastf1.core.Session) -> dict:
    """
    비, 세이프티카, VSC 등 주요 트랙 이벤트를 추출한다.

    TrackStatus 코드:
        '1' = 정상, '2' = Yellow flag, '4' = Safety Car,
        '5' = Red flag, '6' = VSC deployed, '7' = VSC ending

    Args:
        session: 로드된 FastF1 세션 객체

    Returns:
        이벤트 정보 딕셔너리.
        {
            'rain_periods': [(start_lap, end_lap), ...],
            'safety_car_periods': [(start_lap, end_lap), ...],
            'vsc_periods': [(start_lap, end_lap), ...],
        }

    Example:
        >>> events = get_track_events(session)
        >>> print(events['safety_car_periods'])
    """
    result: dict = {
        "rain_periods": [],
        "safety_car_periods": [],
        "vsc_periods": [],
    }

    laps = session.laps.copy()
    if laps.empty:
        return result

    # 랩별 대표 TrackStatus 추출 (드라이버별 중복 제거)
    lap_status = (
        laps[["LapNumber", "TrackStatus"]]
        .dropna(subset=["TrackStatus"])
        .drop_duplicates(subset="LapNumber")
        .sort_values("LapNumber")
    )

    def _extract_periods(status_codes: list[str]) -> list[tuple[int, int]]:
        """주어진 상태 코드에 해당하는 랩 번호 구간을 추출한다."""
        active_laps = (
            lap_status[
                lap_status["TrackStatus"].apply(
                    lambda s: any(code in str(s) for code in status_codes)
                )
            ]["LapNumber"]
            .astype(int)
            .sort_values()
            .tolist()
        )

        if not active_laps:
            return []

        periods = []
        start = active_laps[0]
        prev = active_laps[0]
        for lap in active_laps[1:]:
            if lap - prev > 2:
                periods.append((start, prev))
                start = lap
            prev = lap
        periods.append((start, prev))
        return periods

    try:
        result["safety_car_periods"] = _extract_periods(["4"])
    except Exception:
        pass

    try:
        result["vsc_periods"] = _extract_periods(["6", "7"])
    except Exception:
        pass

    # 비 구간: weather_data의 Rainfall 컬럼 활용
    try:
        weather = session.weather_data
        if weather is not None and not weather.empty and "Rainfall" in weather.columns:
            rain_weather = weather[weather["Rainfall"] == True].copy()  # noqa: E712
            if not rain_weather.empty:
                # 랩 시간 매핑: 각 랩의 시작 시각 기준
                lap_times = laps[["LapNumber", "Time", "LapTime"]].dropna()
                lap_times = lap_times.drop_duplicates(subset="LapNumber").sort_values(
                    "LapNumber"
                )

                # 비가 오는 시각을 랩 번호로 변환
                rain_laps = set()
                for _, lap_row in lap_times.iterrows():
                    lap_end = lap_row["Time"]
                    lap_start = lap_end - lap_row["LapTime"]
                    # 해당 랩 구간에 비가 온 기록이 있는지 확인
                    if hasattr(rain_weather.index, "to_timedelta64"):
                        rain_in_lap = rain_weather[
                            (rain_weather.index >= lap_start)
                            & (rain_weather.index <= lap_end)
                        ]
                    else:
                        rain_in_lap = rain_weather[
                            (rain_weather["Time"] >= lap_start)
                            & (rain_weather["Time"] <= lap_end)
                        ]
                    if not rain_in_lap.empty:
                        rain_laps.add(int(lap_row["LapNumber"]))

                sorted_rain_laps = sorted(rain_laps)
                if sorted_rain_laps:
                    periods = []
                    start = sorted_rain_laps[0]
                    prev = sorted_rain_laps[0]
                    for lap in sorted_rain_laps[1:]:
                        if lap - prev > 2:
                            periods.append((start, prev))
                            start = lap
                        prev = lap
                    periods.append((start, prev))
                    result["rain_periods"] = periods
    except Exception:
        pass

    return result


def plot_race_trace(
    position_history: pd.DataFrame,
    pit_stops: pd.DataFrame,
    track_events: dict,
    drivers_to_highlight: list[str] | None = None,
    driver_numbers: dict[str, int] | None = None,
    save_path: str | None = None,
    title: str | None = None,
) -> None:
    """
    F1 공식 방송 스타일의 Race Trace 차트를 생성한다.

    랩별 순위 변동, 피트스톱 마커, 세이프티카/비 구간 음영을 한 장에 표시한다.

    Args:
        position_history: get_position_history 반환 DataFrame
        pit_stops: get_pit_stops 반환 DataFrame
        track_events: get_track_events 반환 딕셔너리
        drivers_to_highlight: 강조 표시할 드라이버 목록. None이면 전체 동일 처리.
        driver_numbers: 드라이버 번호 딕셔너리 (좌우 라벨용).
        save_path: 저장 경로. None이면 화면 출력.
        title: 그래프 제목. None이면 기본값 사용.

    Example:
        >>> plot_race_trace(pos_history, pits, events, ['VER', 'NOR'])
    """
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(20, 10), dpi=200)

    fig.patch.set_facecolor("#0a0a0a")
    ax.set_facecolor("#0a0a0a")

    highlight = set(drivers_to_highlight or [])
    dn = driver_numbers or DRIVER_NUMBERS
    all_drivers = sorted(position_history["Driver"].unique())
    max_lap = int(position_history["LapNumber"].max())
    # 유효 포지션 범위를 1~20으로 고정 (드라이버 번호와 혼용 방지)
    max_pos = min(int(position_history["Position"].max()), 20)

    # 세로 그리드 (흐릿한 회색) — Lap 0(그리드) 포함
    for lap in range(0, max_lap + 1):
        ax.axvline(lap, color="#2a2a2a", linewidth=0.3, zorder=1)

    # 이벤트 음영: 이벤트 타입별 첫 번째 구간에만 라벨 표시
    def _shade_periods(
        periods: list[tuple[int, int]], color: str, alpha: float, label: str
    ) -> None:
        for i, (start, end) in enumerate(periods):
            ax.axvspan(start - 0.5, end + 0.5, color=color, alpha=alpha, zorder=2)
            if i == 0:
                ax.text(
                    (start + end) / 2,
                    0.97,
                    label,
                    transform=ax.get_xaxis_transform(),
                    color=color,
                    fontsize=7,
                    fontweight="bold",
                    ha="center",
                    va="top",
                    alpha=0.95,
                )

    _shade_periods(track_events.get("safety_car_periods", []), "#FFD700", 0.3, "SC")
    _shade_periods(track_events.get("vsc_periods", []), "#FFEB99", 0.15, "VSC")
    _shade_periods(track_events.get("rain_periods", []), "#4A90E2", 0.2, "RAIN")

    # 비강조 드라이버 라인 먼저 (뒤에 깔림)
    for driver in all_drivers:
        if driver in highlight:
            continue
        driver_data = position_history[
            position_history["Driver"] == driver
        ].sort_values("LapNumber")
        if driver_data.empty:
            continue
        ax.plot(
            driver_data["LapNumber"],
            driver_data["Position"],
            color="#888888",
            linewidth=1.0,
            alpha=0.7,
            zorder=3,
            solid_capstyle="round",
            solid_joinstyle="round",
        )

    # 강조 드라이버 라인 (위에 그려서 항상 보임)
    for driver in drivers_to_highlight or []:
        driver_data = position_history[
            position_history["Driver"] == driver
        ].sort_values("LapNumber")
        if driver_data.empty:
            continue
        color = TEAM_COLORS.get(driver, "#FFFFFF")
        ax.plot(
            driver_data["LapNumber"],
            driver_data["Position"],
            color=color,
            linewidth=3.5,
            alpha=1.0,
            zorder=5,
            solid_capstyle="round",
            solid_joinstyle="round",
        )

    # 피트스톱 마커 (강조 드라이버만)
    if not pit_stops.empty:
        for driver in highlight:
            driver_pits = pit_stops[pit_stops["Driver"] == driver]
            for _, pit_row in driver_pits.iterrows():
                lap = pit_row["LapNumber"]
                pos_at_lap = position_history[
                    (position_history["Driver"] == driver)
                    & (position_history["LapNumber"] == lap)
                ]
                if pos_at_lap.empty:
                    continue
                pos = pos_at_lap["Position"].values[0]
                color = TEAM_COLORS.get(driver, "#FFFFFF")
                ax.plot(
                    lap,
                    pos,
                    marker="D",
                    markersize=8,
                    color=color,
                    markeredgecolor="white",
                    markeredgewidth=0.8,
                    zorder=6,
                )

    # 좌측 라벨: 시작 그리드 (첫 번째 랩 순위 = 그리드 시작 위치)
    min_lap = int(position_history["LapNumber"].min())
    lap1_data = position_history[position_history["LapNumber"] == min_lap]
    for _, row in lap1_data.iterrows():
        driver = row["Driver"]
        pos = int(row["Position"])
        if pos > max_pos:
            continue
        num = dn.get(driver, "?")
        if driver in highlight:
            color = TEAM_COLORS.get(driver, "#FFFFFF")
            ax.plot(
                -0.5,
                pos,
                marker="o",
                markersize=10,
                color=color,
                zorder=7,
                clip_on=False,
            )
            ax.text(
                -1.2,
                pos,
                str(num),
                color=color,
                fontsize=9,
                fontweight="bold",
                ha="right",
                va="center",
                clip_on=False,
            )
        else:
            ax.text(
                -1.2,
                pos,
                str(num),
                color="#888888",
                fontsize=7,
                ha="right",
                va="center",
                clip_on=False,
            )

    # 우측 라벨: 최종 순위
    final_laps = position_history.groupby("Driver")["LapNumber"].max().reset_index()
    final_positions = []
    for _, fr in final_laps.iterrows():
        driver = fr["Driver"]
        last_lap = fr["LapNumber"]
        pos_row = position_history[
            (position_history["Driver"] == driver)
            & (position_history["LapNumber"] == last_lap)
        ]
        if pos_row.empty:
            continue
        final_pos = int(pos_row["Position"].values[0])
        if final_pos > max_pos:
            continue
        is_dnf = last_lap < max_lap - 2
        final_positions.append((driver, last_lap, final_pos, is_dnf))

    for driver, _last_lap, final_pos, is_dnf in final_positions:
        num = dn.get(driver, "?")
        suffix = " DNF" if is_dnf else ""
        if driver in highlight:
            color = TEAM_COLORS.get(driver, "#FFFFFF")
            ax.text(
                max_lap + 1.0,
                final_pos,
                f"{num}{suffix}",
                color=color,
                fontsize=9,
                fontweight="bold",
                ha="left",
                va="center",
                clip_on=False,
            )
            ax.plot(
                max_lap + 0.3,
                final_pos,
                marker="P",
                markersize=8,
                color=color,
                zorder=7,
                clip_on=False,
            )
        else:
            ax.text(
                max_lap + 1.0,
                final_pos,
                str(num),
                color="#888888",
                fontsize=7,
                ha="left",
                va="center",
                clip_on=False,
            )

    # 축 설정
    # set_ylim(큰값, 작은값) 으로 이미 반전 → invert_yaxis() 불필요 (이중반전 방지)
    ax.set_xlim(-0.3, max_lap + 2.5)
    ax.set_ylim(max_pos + 0.5, 0.5)
    ax.set_yticks(list(range(1, max_pos + 1)))
    ax.set_yticklabels([str(i) for i in range(1, max_pos + 1)])
    # x=0은 "Grid"로 표시
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: "Grid" if int(x) == 0 else str(int(x)))
    )
    ax.tick_params(colors="white", labelsize=10)
    ax.spines[:].set_color("#333333")
    ax.set_xlabel("Lap", fontsize=11, color="white", labelpad=10)
    ax.set_ylabel("Position", fontsize=11, color="white", labelpad=10)

    # 제목 / 부제
    main_title = title or "Brazil GP 2024 - Race Trace"
    fig.text(
        0.5,
        0.97,
        main_title,
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
        color="white",
        fontfamily="sans-serif",
    )
    fig.text(
        0.5,
        0.93,
        "Lap-by-lap position changes",
        ha="center",
        va="top",
        fontsize=11,
        color="#AAAAAA",
        fontfamily="sans-serif",
    )

    # 범례: 드라이버 + 이벤트 통합, 그래프 위쪽에 가로 배치
    all_legend_handles = []
    for driver in drivers_to_highlight or []:
        color = TEAM_COLORS.get(driver, "#FFFFFF")
        num = dn.get(driver, "?")
        all_legend_handles.append(
            mpatches.Patch(color=color, label=f"{driver} (#{num})")
        )
    if track_events.get("safety_car_periods"):
        all_legend_handles.append(
            mpatches.Patch(color="#FFD700", alpha=0.8, label="Safety Car")
        )
    if track_events.get("vsc_periods"):
        all_legend_handles.append(
            mpatches.Patch(color="#FFEB99", alpha=0.8, label="VSC")
        )
    if track_events.get("rain_periods"):
        all_legend_handles.append(
            mpatches.Patch(color="#4A90E2", alpha=0.8, label="Rain")
        )

    if all_legend_handles:
        fig.legend(
            handles=all_legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.90),
            ncol=len(all_legend_handles),
            fontsize=9,
            framealpha=0.7,
            facecolor="#1a1a1a",
            edgecolor="#444444",
            labelcolor="white",
        )

    plt.subplots_adjust(left=0.07, right=0.93, top=0.82, bottom=0.07)

    if save_path:
        fig.savefig(save_path, bbox_inches="tight", facecolor="#0a0a0a")
        print(f"Saved: {save_path}")
    else:
        plt.show()

    plt.close(fig)
