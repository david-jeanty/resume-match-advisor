import os
from pathlib import Path

import pytest

# Tests must never hit the network.
os.environ["COMPANY_LOOKUP"] = "off"

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _read(relative: str) -> str:
    return (EXAMPLES / relative).read_text(encoding="utf-8")


@pytest.fixture
def mixed_resume() -> str:
    return _read("sample_resumes/mixed_experience_student.txt")


@pytest.fixture
def club_resume() -> str:
    return _read("sample_resumes/club_leadership_parttime.txt")


@pytest.fixture
def sparse_finance_resume() -> str:
    return _read("sample_resumes/missing_tools_finance.txt")


@pytest.fixture
def marketing_jd() -> str:
    return _read("sample_job_descriptions/marketing_intern.txt")


@pytest.fixture
def btm_jd() -> str:
    return _read("sample_job_descriptions/business_analyst_btm.txt")


@pytest.fixture
def finance_jd() -> str:
    return _read("sample_job_descriptions/finance_intern.txt")
