from app.discipline_classifier import classify
from app.jd_parser import parse_jd


def test_marketing_jd_classified_as_marketing(marketing_jd):
    fits = classify(parse_jd(marketing_jd))
    assert fits
    assert fits[0].discipline_id == "marketing"
    assert fits[0].matched_signals


def test_btm_jd_classified_as_btm(btm_jd):
    fits = classify(parse_jd(btm_jd))
    assert fits
    assert fits[0].discipline_id == "btm_mis"


def test_finance_jd_classified_as_finance(finance_jd):
    fits = classify(parse_jd(finance_jd))
    assert fits
    assert fits[0].discipline_id in ("finance", "accounting")
    assert fits[0].discipline_id == "finance"


def test_target_discipline_is_honored(marketing_jd):
    fits = classify(parse_jd(marketing_jd), target_discipline="consulting")
    assert fits[0].discipline_id == "consulting"
    assert fits[0].confidence == "high"


def test_no_crash_on_unclassifiable_text():
    fits = classify(parse_jd("hello world"))
    assert isinstance(fits, list)
