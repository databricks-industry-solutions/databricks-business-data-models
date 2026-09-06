import json, sys

NB = "/Users/user/Documents/projects/vibe-modelling-agent/agent/dbx_vibe_modelling_agent.ipynb"
nb = json.load(open(NB))
cells = nb["cells"]

def set_source(ci, new_text):
    cells[ci]["source"] = new_text.splitlines(keepends=True)

def get_source(ci):
    return "".join(cells[ci]["source"])

# ---- Edit 1: append shared classifier to cell 5 (after PII_FALSE_POSITIVE_RE) ----
HELPER = '''

# v4.6.4 alias=pii-verifier-sa-parity — SINGLE SOURCE OF TRUTH for "person-pattern attribute
# lacking a PII tag", shared by the deterministic SA gate (pii_tagging_missing) and the VREQ
# verifier (verifier-model-wide-pii-tag). ROOT CAUSE of the lying scoreboard: the verifier used
# a DIFFERENT (substring) person detector and a 0.7 "fulfilled" threshold, so it credited the
# PII VREQ fulfilled while the SA gate (word-boundary regex, 100% expectation) still flagged N
# untagged person columns and the SelfFixer no-op'd (selffixer-noop-guard). Reusing the SA
# gate's EXACT regex + false-positive guard here, and requiring 0 missing for 'fulfilled',
# makes the scoreboard honest and forces the closed loop to tag every remaining person column.
_PII_NAME_PATTERNS_RE = re.compile(
    r'(^|_)(name|email|phone|address|ssn|salary|dob|date_of_birth|photo|biometric'
    r'|approver|approved_by|released_by|requested_by|inspector|owner|assignee'
    r'|created_by|modified_by|signed_by|reviewer|operator_name)(_|$)',
    re.IGNORECASE
)

def _v464_classify_pii_column(attr_name, tags):
    """Classify a column for the person-PII gate: 'missing' (person-pattern, untagged),
    'fp_skip' (matched a generic false-positive like equipment_serial), or 'ok' (not a person
    column, already PII-tagged, or a primary key). Used by BOTH the SA gate and the VREQ
    verifier so the scoreboard cannot claim fulfilled while the SA gate flags missing tags
    (v4.6.4 alias=pii-verifier-sa-parity)."""
    an = (attr_name or "").lower()
    tg = (tags or "").lower()
    if not _PII_NAME_PATTERNS_RE.search(an):
        return 'ok'
    if 'pii' in tg or 'primary_key' in tg:
        return 'ok'
    try:
        if PII_FALSE_POSITIVE_RE.search(an):
            return 'fp_skip'
    except NameError:
        pass
    return 'missing'
'''
s5 = get_source(5)
# PII_FALSE_POSITIVE_RE is the LAST statement in cell 5 (verified: unique tail below).
assert "address_type|address_format|address_count|email_type|email_format" in s5, "cell5 missing PII_FALSE_POSITIVE_RE"
assert s5.rstrip().endswith(")"), "cell5 does not end with PII_FALSE_POSITIVE_RE close"
assert "_v464_classify_pii_column" not in s5, "helper already present"
set_source(5, s5.rstrip("\n") + "\n" + HELPER)

# ---- Edit 2: SA gate loop (cell 172) ----
SA_OLD = """_pii_name_patterns = re.compile(r'(^|_)(name|email|phone|address|ssn|salary|dob|date_of_birth|photo|biometric|approver|approved_by|released_by|requested_by|inspector|owner|assignee|created_by|modified_by|signed_by|reviewer|operator_name)(_|$)', re.IGNORECASE)
    _pii_missing_count = 0
    _v061_pii_skipped_fp = 0
    for attr in attributes_data:
        attr_name = (attr.get('attribute') or '').lower()
        tags = (attr.get('tags') or '').lower()
        if _pii_name_patterns.search(attr_name) and 'pii' not in tags and 'primary_key' not in tags:
            try:
                if PII_FALSE_POSITIVE_RE.search(attr_name):
                    _v061_pii_skipped_fp += 1
                    continue
            except NameError:
                pass
            _pii_missing_count += 1
"""
SA_NEW = """# v4.6.4 alias=pii-verifier-sa-parity — use the shared classifier so the deterministic SA
    # gate and the VREQ verifier count the SAME person columns (behavior-identical to the prior
    # inline regex; the classifier encodes the exact same word-boundary pattern + FP guard).
    _pii_missing_count = 0
    _v061_pii_skipped_fp = 0
    for attr in attributes_data:
        _pii_cls = _v464_classify_pii_column(attr.get('attribute'), attr.get('tags'))
        if _pii_cls == 'fp_skip':
            _v061_pii_skipped_fp += 1
        elif _pii_cls == 'missing':
            _pii_missing_count += 1
"""
s172 = get_source(172)
assert s172.count(SA_OLD) == 1, f"cell172 SA_OLD count={s172.count(SA_OLD)}"
set_source(172, s172.replace(SA_OLD, SA_NEW))

# ---- Edit 3: verifier block (cell 100) ----
VER_OLD = '''                _v336_pp = ("name","first_name","last_name","full_name","middle_name","email","phone","mobile","ssn","social_security","dob","date_of_birth","birth","address","gender","age","passport","license","national_id","tax_id","nationality","ethnicity","marital")
                _v336_tot = 0; _v336_tag = 0
                for _v336_pk, _v336_cm in prod_cols.items():
                    for _v336_cn in _v336_cm:
                        if any(_pp in _v336_cn for _pp in _v336_pp):
                            _v336_tot += 1
                            _v336_tg = (prod_tags.get(_v336_pk, {}) or {}).get(_v336_cn)
                            _v336_ts = ""
                            if isinstance(_v336_tg, dict):
                                _v336_ts = (" ".join([str(k) for k in _v336_tg.keys()]) + " " + " ".join([str(v) for v in _v336_tg.values()])).lower()
                            elif _v336_tg:
                                _v336_ts = str(_v336_tg).lower()
                            if ("pii" in _v336_ts) or ("classif" in _v336_ts) or ("sensitive" in _v336_ts) or ("personal" in _v336_ts):
                                _v336_tag += 1
                if _v336_tot > 0:
                    _v336_cov = _v336_tag / _v336_tot
                    _v336_rid = getattr(req, "id", "?")
                    if _v336_cov >= 0.7:
                        self.logger.info(f"  [verifier-model-wide-pii-tag FIRED v3.3.6] {_v336_rid}: {_v336_tag}/{_v336_tot} person-pattern cols PII-tagged (cov={_v336_cov:.0%}) -> fulfilled alias=verifier-model-wide-pii-tag")
                        return {"status": "fulfilled", "evidence": f"[verifier-model-wide-pii-tag FIRED v3.3.6] {_v336_tag}/{_v336_tot} person-pattern columns carry PII/classification tags (coverage {_v336_cov:.0%})"}
                    if _v336_tag == 0:
                        self.logger.info(f"  [verifier-model-wide-pii-tag FIRED v3.3.6] {_v336_rid}: 0/{_v336_tot} person-pattern cols tagged -> failed alias=verifier-model-wide-pii-tag")
                        return {"status": "failed", "evidence": f"[verifier-model-wide-pii-tag FIRED v3.3.6] 0/{_v336_tot} person-pattern columns carry PII tags"}
                    self.logger.info(f"  [verifier-model-wide-pii-tag FIRED v3.3.6] {_v336_rid}: {_v336_tag}/{_v336_tot} partial (cov={_v336_cov:.0%}) alias=verifier-model-wide-pii-tag")
                    return {"status": "partial", "evidence": f"[verifier-model-wide-pii-tag FIRED v3.3.6] {_v336_tag}/{_v336_tot} person-pattern columns tagged (coverage {_v336_cov:.0%})"}
'''
VER_NEW = '''                # v4.6.4 alias=pii-verifier-sa-parity — count person columns with the SAME
                # word-boundary detector + FP guard the deterministic SA gate uses, and require
                # FULL coverage (0 missing) for 'fulfilled'. Prevents the lying scoreboard where
                # the verifier credited fulfilled at 0.7 while the SA gate still flagged untagged
                # person columns and the SelfFixer no-op'd.
                _v336_tot = 0; _v336_tag = 0; _v336_missing = 0
                for _v336_pk, _v336_cm in prod_cols.items():
                    for _v336_cn in _v336_cm:
                        _v336_tg = (prod_tags.get(_v336_pk, {}) or {}).get(_v336_cn)
                        _v336_ts = ""
                        if isinstance(_v336_tg, dict):
                            _v336_ts = (" ".join([str(k) for k in _v336_tg.keys()]) + " " + " ".join([str(v) for v in _v336_tg.values()])).lower()
                        elif _v336_tg:
                            _v336_ts = str(_v336_tg).lower()
                        _v336_cls = _v464_classify_pii_column(_v336_cn, _v336_ts)
                        if _v336_cls == 'missing':
                            _v336_tot += 1; _v336_missing += 1
                        elif _v336_cls == 'ok' and _PII_NAME_PATTERNS_RE.search((_v336_cn or '').lower()) and (("pii" in _v336_ts) or ("classif" in _v336_ts) or ("sensitive" in _v336_ts) or ("personal" in _v336_ts)):
                            _v336_tot += 1; _v336_tag += 1
                if _v336_tot > 0:
                    _v336_cov = _v336_tag / _v336_tot
                    _v336_rid = getattr(req, "id", "?")
                    if _v336_missing == 0:
                        self.logger.info(f"  [verifier-model-wide-pii-tag FIRED v4.6.4] {_v336_rid}: {_v336_tag}/{_v336_tot} person-pattern cols PII-tagged (cov={_v336_cov:.0%}, 0 missing) -> fulfilled alias=pii-verifier-sa-parity")
                        return {"status": "fulfilled", "evidence": f"[verifier-model-wide-pii-tag FIRED v4.6.4] {_v336_tag}/{_v336_tot} person-pattern columns carry PII/classification tags (coverage {_v336_cov:.0%}, 0 untagged)"}
                    if _v336_tag == 0:
                        self.logger.info(f"  [verifier-model-wide-pii-tag FIRED v4.6.4] {_v336_rid}: 0/{_v336_tot} person-pattern cols tagged, {_v336_missing} untagged -> failed alias=pii-verifier-sa-parity")
                        return {"status": "failed", "evidence": f"[verifier-model-wide-pii-tag FIRED v4.6.4] 0/{_v336_tot} person-pattern columns carry PII tags ({_v336_missing} untagged)"}
                    self.logger.info(f"  [verifier-model-wide-pii-tag FIRED v4.6.4] {_v336_rid}: {_v336_tag}/{_v336_tot} tagged, {_v336_missing} untagged -> partial (cov={_v336_cov:.0%}) alias=pii-verifier-sa-parity")
                    return {"status": "partial", "evidence": f"[verifier-model-wide-pii-tag FIRED v4.6.4] {_v336_tag}/{_v336_tot} person-pattern columns tagged (coverage {_v336_cov:.0%}, {_v336_missing} untagged)"}
'''
s100 = get_source(100)
assert s100.count(VER_OLD) == 1, f"cell100 VER_OLD count={s100.count(VER_OLD)}"
set_source(100, s100.replace(VER_OLD, VER_NEW))

json.dump(nb, open(NB, "w"), indent=1, ensure_ascii=True)
print("PATCHED OK: 3 edits applied")
