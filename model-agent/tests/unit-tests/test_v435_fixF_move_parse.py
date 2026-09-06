"""v4.3.5 FIX F behavioral test (alias=v435-move-parse-broaden).

Root cause: _v337_extract_move_target's verb gate only matched move/relocate/reassign, so
cross-domain rehome directives phrased "rehome/migrate/belongs in/should live under" returned
None and deferred the whole batch to the flaky LLM sandbox. FIX F broadens the verb cue and
adds tolerant destination patterns.

Fail-pre / pass-post: pre-patch these phrasings return None; post-patch they extract the
destination domain. move/relocate phrasing keeps working (no regression).
"""
import re as _re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v435_helpers import concat_source, slice_functions


def _fn():
    src = concat_source()
    ns = slice_functions(["_v337_extract_move_target"], src, extra_globals={"re": _re})
    return ns["_v337_extract_move_target"]


def test_fixF_rehome_phrasing_extracts_domain():
    fn = _fn()
    assert fn("Rehome the returns product to the logistics domain.") == "logistics"


def test_fixF_should_live_under_phrasing_extracts_domain():
    fn = _fn()
    assert fn("The returns product should live under the logistics domain.") == "logistics"


def test_fixF_migrate_phrasing_extracts_domain():
    fn = _fn()
    assert fn("Migrate shipment into the fulfillment domain going forward.") == "fulfillment"


def test_fixF_no_regression_on_classic_move_phrasing():
    fn = _fn()
    assert fn("Move the returns product to the logistics domain.") == "logistics"
