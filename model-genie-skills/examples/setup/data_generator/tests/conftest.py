"""Ensure the MVM-profile bronze is generated once before the MVM tests read it."""
import pathlib, pytest
from data_generator import config, generate_bronze

_MVM_CSVS = ["status_log", "atp_log", "sched_agreement", "cpq_config", "likp", "lips"]


@pytest.fixture(scope="session", autouse=True)
def _mvm_bronze():
    out = config.OUTPUT_DIR / "sap_sd"
    if not all((out / f"{n}.csv").exists() for n in _MVM_CSVS):
        generate_bronze.main(profile="mvm")
    return out
