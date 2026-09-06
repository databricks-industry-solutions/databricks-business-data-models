import json, sys

NB = "tests/vibe_tester.ipynb"
nb = json.load(open(NB))
cells = nb["cells"]
CI = 0  # main code cell


def cell_text(ci):
    return "".join(cells[ci].get("source", []))


def set_cell_text(ci, text):
    cells[ci]["source"] = text.splitlines(keepends=True)  # HEAD tester stores source as a list of lines


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"[patch_v497_conv] ANCHOR '{label}' found {n} times (expected 1) — aborting")
    return text.replace(old, new)


t = cell_text(CI)

# 1) TestResult gains produced_model flag (default True)
t = replace_once(
    t,
    '    def __init__(self, test_name, test_label, status, duration_seconds, error_msg="", params=None):',
    '    def __init__(self, test_name, test_label, status, duration_seconds, error_msg="", params=None, produced_model=True):',
    "TestResult signature",
)
t = replace_once(
    t,
    "        self.params = params or {}\n",
    "        self.params = params or {}\n        self.produced_model = produced_model  # v497-conv-produced-model\n",
    "TestResult body",
)

# 2) audit loop skips tests that did not actually build/advance a model
t = replace_once(
    t,
    "        if op not in _MODEL_PRODUCING_OPS:\n            continue\n",
    "        if op not in _MODEL_PRODUCING_OPS:\n            continue\n"
    "        if not getattr(tr, \"produced_model\", True):  # v497-conv-skip-nonproducing\n            continue\n",
    "audit-loop skip",
)

# 3) mark the two guard-rail/negative tests as non-producing
t = replace_once(
    t,
    '            R.append(TestResult("10_empty_vibes", "Empty Vibes Graceful Exit", "PASSED", r12.duration_seconds,\n'
    '                f"Negative test passed (agent rejected empty vibes): {r12.error_msg[:300]}", td_10["params"]))',
    '            R.append(TestResult("10_empty_vibes", "Empty Vibes Graceful Exit", "PASSED", r12.duration_seconds,\n'
    '                f"Negative test passed (agent rejected empty vibes): {r12.error_msg[:300]}", td_10["params"], produced_model=False))',
    "10_empty_vibes append",
)
t = replace_once(
    t,
    'R.append(TestResult("13_no_biz_name", "Missing Business Name Guard-Rail", "PASSED", r15.duration_seconds, params=td_13["params"]))',
    'R.append(TestResult("13_no_biz_name", "Missing Business Name Guard-Rail", "PASSED", r15.duration_seconds, params=td_13["params"], produced_model=False))',
    "13_no_biz_name append",
)

set_cell_text(CI, t)
with open(NB, "w") as _f:
    json.dump(nb, _f, indent=2)
    _f.write("\n")

# verification
nb2 = json.load(open(NB))
full = "".join(nb2["cells"][CI].get("source", []))
checks = {
    "produced_model param": "params=None, produced_model=True):" in full,
    "produced_model assign": "self.produced_model = produced_model" in full,
    "audit skip": "v497-conv-skip-nonproducing" in full,
    "10 non-producing": 'td_10["params"], produced_model=False))' in full,
    "13 non-producing": 'params=td_13["params"], produced_model=False))' in full,
}
for k, v in checks.items():
    print(("OK  " if v else "FAIL") + " " + k)
if not all(checks.values()):
    sys.exit(1)
print("[patch_v497_conv] all checks passed")
