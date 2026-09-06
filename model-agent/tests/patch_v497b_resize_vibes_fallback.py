import json, sys

NB = "tests/vibe_tester.ipynb"
nb = json.load(open(NB))
cells = nb["cells"]
CI = 0


def cell_text(ci):
    s = cells[ci].get("source", "")
    return "".join(s) if isinstance(s, list) else s


def set_cell_text(ci, text):
    cells[ci]["source"] = text.splitlines(keepends=True)


def replace_n(text, old, new, label, expected):
    n = text.count(old)
    if n != expected:
        raise SystemExit(f"[patch_v497b] ANCHOR '{label}' found {n} (expected {expected}) — aborting")
    return text.replace(old, new)


t = cell_text(CI)

# 1) define the shared cap default right after the model_vibes widget read
t = replace_n(
    t,
    '    w_model_vibes = dbutils.widgets.get("model_vibes").strip()\n',
    '    w_model_vibes = dbutils.widgets.get("model_vibes").strip()\n'
    '    _DEFAULT_TEST_VIBES = "maximum of 2 domains, and 8 tables for any model you generate"  # v497-resize-vibes-fallback\n',
    "widget-read",
    1,
)

# 2) both model-producing builders (_build_base_model L470, _build_resize L523) inherit the
#    session cap when the widget is empty — same behaviour the base-model builder already had.
t = replace_n(
    t,
    '                "org_divisions": _pick(org_pool),\n'
    '                "model_vibes": w_model_vibes,\n',
    '                "org_divisions": _pick(org_pool),\n'
    '                "model_vibes": (w_model_vibes or _DEFAULT_TEST_VIBES),\n',
    "builder-model_vibes",
    2,
)

# 3) refactor the base-model inline literal to the shared constant (DRY)
t = replace_n(
    t,
    '"model_vibes": w_model_vibes if w_model_vibes else "maximum of 2 domains, and 8 tables for any model you generate",',
    '"model_vibes": (w_model_vibes or _DEFAULT_TEST_VIBES),',
    "base-literal",
    1,
)

set_cell_text(CI, t)
with open(NB, "w") as _f:
    json.dump(nb, _f, indent=2)
    _f.write("\n")

# verification
full = "".join(json.load(open(NB))["cells"][CI]["source"])
checks = {
    "constant defined": '_DEFAULT_TEST_VIBES = "maximum of 2 domains, and 8 tables for any model you generate"' in full,
    "builders use fallback (x2)": full.count('"model_vibes": (w_model_vibes or _DEFAULT_TEST_VIBES),') == 3,  # 2 builders + base
    "no bare w_model_vibes builder left": full.count('"org_divisions": _pick(org_pool),\n                "model_vibes": w_model_vibes,\n') == 0,
    "old base literal gone": 'w_model_vibes if w_model_vibes else "maximum' not in full,
}
for k, v in checks.items():
    print(("OK  " if v else "FAIL") + " " + k)
if not all(checks.values()):
    sys.exit(1)
print("[patch_v497b] all checks passed")
