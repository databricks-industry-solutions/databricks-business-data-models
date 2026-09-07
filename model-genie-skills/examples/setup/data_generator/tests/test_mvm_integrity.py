"""B6 — the MVM-profile integrity gate: validate_mvm() returns zero failures."""
from data_generator import validate


def test_validate_mvm_clean():
    fails = validate.validate_mvm()
    assert fails == [], f"MVM integrity failures: {fails}"
