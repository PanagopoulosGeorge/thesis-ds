"""Shared test fixtures for the test suite."""
import pytest
from typing import List

from src.interfaces.models import FewShotExample


@pytest.fixture
def sample_activity_description() -> str:
    """Sample activity description for testing."""
    return (
        'Given a composite activity description, provide the rules in RTEC.\n'
        'Composite Activity Description - "gap": A communication gap starts when '
        'we stop receiving messages from a vessel.'
    )


@pytest.fixture
def sample_prerequisites() -> List[FewShotExample]:
    """Sample prerequisite fluents for testing."""
    return [
        FewShotExample(
            user='Generate rules for "withinArea": starts when vessel enters area.',
            assistant='initiatedAt(withinArea(Vessel, AreaType)=true, T) :- happensAt(entersArea(Vessel, Area), T).'
        ),
        FewShotExample(
            user='Generate rules for "stopped": starts when vessel becomes idle.',
            assistant='initiatedAt(stopped(Vessel)=nearPorts, T) :- happensAt(stop_start(Vessel), T).'
        ),
    ]


@pytest.fixture
def empty_prerequisites() -> List[FewShotExample]:
    """Empty prerequisites list."""
    return []

