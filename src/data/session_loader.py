"""
session_loader.py
=================
FastF1 세션 데이터 로딩을 담당하는 모듈

이 모듈은 F1 그랑프리의 한 세션(연습/예선/본경기)을 로드하고,
캐싱을 관리하는 기능을 제공합니다.
"""

import fastf1
from pathlib import Path
from typing import Optional


# 캐시 디렉토리 (프로젝트 루트의 f1_cache)
DEFAULT_CACHE_DIR = Path(__file__).parent.parent.parent / 'f1_cache'


def setup_cache(cache_dir: Optional[Path] = None) -> Path:
    """
    FastF1 캐시 디렉토리를 설정한다.
    
    Args:
        cache_dir: 캐시 디렉토리 경로. None이면 기본값 사용.
    
    Returns:
        설정된 캐시 디렉토리 경로
    """
    cache_path = cache_dir or DEFAULT_CACHE_DIR
    cache_path.mkdir(exist_ok=True, parents=True)
    fastf1.Cache.enable_cache(str(cache_path))
    return cache_path


def load_session(
    year: int,
    gp: str,
    session_type: str = 'R',
    verbose: bool = True
) -> fastf1.core.Session:
    """
    F1 세션 데이터를 로드한다.
    
    Args:
        year: 시즌 연도 (예: 2024)
        gp: 그랑프리 이름 (예: 'Monaco', 'Spain')
        session_type: 세션 유형
            - 'FP1', 'FP2', 'FP3': 연습 세션
            - 'Q': 예선 (Qualifying)
            - 'R': 본 경기 (Race)
            - 'S': 스프린트 (Sprint)
        verbose: 진행 상황 출력 여부
    
    Returns:
        로드된 FastF1 Session 객체
    
    Example:
        >>> session = load_session(2024, 'Monaco', 'R')
        >>> print(session.event['EventName'])
    """
    if verbose:
        print(f"📥 {year} {gp} GP ({session_type}) 로드 중...")
    
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    
    if verbose:
        print(f"✓ 로드 완료: {session.event['EventName']}")
    
    return session


def print_session_info(session: fastf1.core.Session) -> None:
    """세션의 기본 정보를 출력한다."""
    print("\n" + "=" * 60)
    print("📍 경기 기본 정보")
    print("=" * 60)
    print(f"이벤트명:  {session.event['EventName']}")
    print(f"경기 날짜: {session.event['EventDate'].strftime('%Y-%m-%d')}")
    print(f"개최 국가: {session.event['Country']}")
    print(f"서킷:      {session.event['Location']}")
