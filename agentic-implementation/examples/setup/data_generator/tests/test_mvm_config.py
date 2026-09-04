# tests/test_mvm_config.py
from data_generator import config

def test_mvm_rows_present_and_deterministic():
    assert config.SEED == 42
    for k in ("status_events","atp_log","sched_agreement","cpq_config","delivery","delivery_line"):
        assert k in config.MVM_ROWS and config.MVM_ROWS[k] > 0
