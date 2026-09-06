"""v4.3.5 FIX B behavioral test (alias=verifier-removal-structural).

Root cause (RP11 lying-scoreboard): _verify_structural_target was additive-only. A
"remove/drop/consolidate the <column>" directive named an attribute to DELETE but no branch
checked ABSENCE, so it hit the col-is-None early return and fell to the coarse count-diff,
which false-fulfilled the removal. FIX B verifies the named column(s) are GONE from the
after-state; failed if any still present.

Fail-pre / pass-post: pre-patch the method returns None for a removal directive whose column
is still present (coarse-diff would false-credit it) -> the `status == failed` assertion
raises on None. Post-patch it deterministically returns failed (still present) / fulfilled
(absent).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v435_helpers import concat_source, slice_method_as_function, Req, FakeVerifierSelf

_TEXT = ("Remove the redundant email_opt_in_flag column from customer.profile "
         "because it duplicates the consent tracking columns.")
_SCOPE = ["customer.profile.email_opt_in_flag"]


def _verifier():
    src = concat_source()
    fn = slice_method_as_function(
        "_verify_structural_target", src,
        extra_globals={"_v407_resolve_dp": (lambda p, s: p)})
    return fn


def _attrs(include_removed_col: bool):
    rows = [{"domain": "customer", "product": "profile",
             "attribute": "profile_id", "foreign_key_to": "", "tags": None}]
    if include_removed_col:
        rows.append({"domain": "customer", "product": "profile",
                     "attribute": "email_opt_in_flag", "foreign_key_to": "", "tags": None})
    return rows


def test_fixB_reports_failed_when_column_still_present():
    fn = _verifier()
    req = Req(original_text=_TEXT, scope_targets=_SCOPE, rid="RP11")
    result = fn(FakeVerifierSelf(), req, [], _attrs(include_removed_col=True))
    assert result is not None, "pre-patch false-fulfill: verifier had no removal branch (returned None)"
    assert result["status"] == "failed", result


def test_fixB_reports_fulfilled_when_column_absent():
    fn = _verifier()
    req = Req(original_text=_TEXT, scope_targets=_SCOPE, rid="RP11")
    result = fn(FakeVerifierSelf(), req, [], _attrs(include_removed_col=False))
    assert result is not None and result["status"] == "fulfilled", result
