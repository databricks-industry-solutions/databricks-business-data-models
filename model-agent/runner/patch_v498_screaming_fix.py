import json, sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"
nb = json.load(open(NB))


def cell_str(i):
    s = nb["cells"][i]["source"]
    return "".join(s) if isinstance(s, list) else s


def set_cell(i, text):
    nb["cells"][i]["source"] = text


def repl(i, old, new, label):
    t = cell_str(i)
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[patch_v498] anchor '{label}' count={n} (expected 1) — aborting")
    set_cell(i, t.replace(old, new))


# 1) version bump 4.9.7 -> 4.9.8
repl(1, '__AGENT_VERSION__ = "4.9.7"', '__AGENT_VERSION__ = "4.9.8"', "version")

# 2) PRE-FIX attribute conflict guard false-positive: seed set contains the attribute's OWN
#    lowercased name, so a case-only rename (snake_case -> SCREAMING_CASE) sees itself as a
#    collision and is skipped, leaving regular attrs in snake_case. Exclude the self case so a
#    case-only rename proceeds while real cross-attribute collisions are still blocked.
repl(
    166,
    "if new_an.lower() in _attr_names_by_table.get(table_key, set()):",
    "if new_an.lower() in _attr_names_by_table.get(table_key, set()) and new_an.lower() != old_an.lower():",
    "attr-self-collision-guard",
)

with open(NB, "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)
    f.write("\n")

# verify
raw = open(NB).read()
checks = {
    "version 4.9.8": raw.count("4.9.8") == 1 and raw.count("4.9.7") == 0,
    "guard self-exclusion added": "!= old_an.lower():" in raw,
    "old guard gone": raw.count("if new_an.lower() in _attr_names_by_table.get(table_key, set()):") == 0,
}
for k, v in checks.items():
    print(("OK  " if v else "FAIL") + " " + k)
if not all(checks.values()):
    sys.exit(1)
# syntax
c166 = "".join(json.load(open(NB))["cells"][166]["source"])
compile(c166, "cell166", "exec")
print("[patch_v498] applied + syntax OK")
