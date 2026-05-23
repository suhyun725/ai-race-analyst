"""
lap_data.py
===========
여러 드라이버의 랩 데이터를 수집·전처리·필터링하는 모듈

FastF1 세션에서 드라이버별 랩 데이터를 가져오고,
분석에 적합한 형태로 정제하는 함수들을 제공한다.
"""

import fastf1
import pandas as pd


def get_drivers_laps(
    session: fastf1.core.Session,
    drivers: list[str] | None = None,
) -> pd.DataFrame:
    """
    여러 드라이버의 랩 데이터를 한 번에 가져온다.

    Args:
        session: 로드된 FastF1 세션 객체
        drivers: 드라이버 약자 리스트 (예: ['NOR', 'VER', 'LEC']).
                 None이면 전체 드라이버 반환.

    Returns:
        요청한 드라이버들의 랩 데이터 DataFrame

    Example:
        >>> laps = get_drivers_laps(session, ['NOR', 'VER'])
        >>> laps = get_drivers_laps(session)  # 전체 드라이버
    """
    if drivers is None:
        return session.laps.copy()

    return session.laps.pick_drivers(drivers).copy()


def clean_lap_data(laps: pd.DataFrame) -> pd.DataFrame:
    """
    랩 데이터에서 결측치를 제거하고 LapTime을 초(seconds)로 변환한다.

    처리 내용:
    - LapTime이 NaT인 행 제거 (인랩, 아웃랩, 세이프티카 랩 등)
    - LapTimeSeconds 컬럼 추가 (float, 초 단위)

    Args:
        laps: 원시 랩 데이터 DataFrame

    Returns:
        정제된 랩 데이터 DataFrame (LapTimeSeconds 컬럼 추가됨)

    Example:
        >>> cleaned = clean_lap_data(laps)
        >>> cleaned['LapTimeSeconds'].describe()
    """
    df = laps.copy()

    # LapTime이 NaT인 행 제거
    df = df.dropna(subset=["LapTime"])

    # LapTime을 초 단위 float으로 변환
    df = df.copy()
    df["LapTimeSeconds"] = df["LapTime"].dt.total_seconds()

    # 비정상적인 랩타임 제거 (0초 이하)
    df = df[df["LapTimeSeconds"] > 0]

    return df.reset_index(drop=True)


def filter_by_compound(laps: pd.DataFrame, compound: str) -> pd.DataFrame:
    """
    특정 타이어 컴파운드로 필터링한다.

    Args:
        laps: 랩 데이터 DataFrame
        compound: 타이어 컴파운드 이름
                  ('SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET')

    Returns:
        해당 컴파운드 랩만 포함한 DataFrame

    Example:
        >>> soft_laps = filter_by_compound(laps, 'SOFT')
        >>> medium_laps = filter_by_compound(laps, 'MEDIUM')
    """
    return laps[laps["Compound"] == compound.upper()].copy()


def filter_quick_laps(
    laps: pd.DataFrame,
    threshold: float = 1.07,
) -> pd.DataFrame:
    """
    전체 최속 랩 대비 일정 비율 이내의 빠른 랩만 남긴다.

    F1 107% 룰에서 착안한 필터. 아웃랩·인랩·세이프티카 랩 등
    비정상적으로 느린 랩을 제외할 때 사용한다.

    Args:
        laps: 랩 데이터 DataFrame (LapTimeSeconds 컬럼 필요)
        threshold: 최속 랩 대비 허용 배율 (기본값 1.07 = 107%)

    Returns:
        threshold 이내의 빠른 랩만 포함한 DataFrame

    Example:
        >>> quick = filter_quick_laps(cleaned_laps)           # 107% 기준
        >>> quick = filter_quick_laps(cleaned_laps, 1.05)     # 105% 기준
    """
    if "LapTimeSeconds" not in laps.columns:
        raise ValueError(
            "LapTimeSeconds 컬럼이 없습니다. clean_lap_data()를 먼저 실행하세요."
        )

    fastest = laps["LapTimeSeconds"].min()
    cutoff = fastest * threshold
    return laps[laps["LapTimeSeconds"] <= cutoff].copy()


def filter_lap_range(
    laps: pd.DataFrame,
    start: int,
    end: int,
) -> pd.DataFrame:
    """
    특정 랩 번호 범위로 필터링한다.

    Args:
        laps: 랩 데이터 DataFrame
        start: 시작 랩 번호 (포함)
        end: 종료 랩 번호 (포함)

    Returns:
        start ~ end 범위의 랩만 포함한 DataFrame

    Example:
        >>> mid_race = filter_lap_range(laps, 20, 40)
    """
    return laps[(laps["LapNumber"] >= start) & (laps["LapNumber"] <= end)].copy()


def get_pace_summary(laps: pd.DataFrame) -> pd.DataFrame:
    """
    드라이버별 페이스 요약 통계를 계산한다.

    Args:
        laps: 랩 데이터 DataFrame (LapTimeSeconds 컬럼 필요).
              clean_lap_data() + filter_quick_laps() 적용 후 사용 권장.

    Returns:
        드라이버별 페이스 통계 DataFrame.
        컬럼: Driver, LapCount, Mean, Median, Std, Best
        (시간 단위: 초)

    Example:
        >>> summary = get_pace_summary(quick_laps)
        >>> print(summary.sort_values('Median'))
    """
    if "LapTimeSeconds" not in laps.columns:
        raise ValueError(
            "LapTimeSeconds 컬럼이 없습니다. clean_lap_data()를 먼저 실행하세요."
        )

    summary = (
        laps.groupby("Driver")["LapTimeSeconds"]
        .agg(
            LapCount="count",
            Mean="mean",
            Median="median",
            Std="std",
            Best="min",
        )
        .round(3)
        .reset_index()
    )

    return summary.sort_values("Median").reset_index(drop=True)
