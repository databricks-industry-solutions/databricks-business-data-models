"""v4.8.2 alias=verifier-relation-target-resolvable (second layer).

The resolvability guard stops a scope_target that names nothing in the model from
scoring the VREQ failed. But a target that DOES name a real product in the vibe's own
wording ("finished package" for product finished_package) still missed, because
_rel_linked matched the raw target text as a substring of "domain.product.attribute"
strings, which are snake_case. Resolution and matching have to share one normal form or
the guard just moves the false-fail one step later.

So the resolution scan now records WHICH product keys the target resolved to, and
_rel_linked matches on those canonical keys as well as the raw text. Broadening the
match set is safe in both verbs: for add/link it finds the real FK (fulfilled), for
remove it can only see MORE surviving links, never fewer, so it cannot false-fulfil.
"""

import json
import sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"

OLD = """                _rel_norm = lambda _s: re.sub(r"[^a-z0-9]", "", str(_s or "").lower())
                _rel_tn = _rel_norm(tl)
                _rel_known = (
                    tl in domain_names
                    or tl in product_keys
                    or any(_rel_tn == _rel_norm(_d) for _d in domain_names)
                    or any(_rel_tn in (_rel_norm(_pk), _rel_norm(_pk.split(".")[-1])) for _pk in product_keys)
                    or any(_rel_tn == _rel_norm(_ak.split(".")[-1]) for _ak in attr_keys)
                )
                if not _rel_known:
"""

NEW = """                _rel_norm = lambda _s: re.sub(r"[^a-z0-9]", "", str(_s or "").lower())
                _rel_tn = _rel_norm(tl)
                _rel_canon = {_pk for _pk in product_keys
                              if _rel_tn in (_rel_norm(_pk), _rel_norm(_pk.split(".")[-1]))}
                _rel_known = bool(_rel_canon) or (
                    tl in domain_names
                    or tl in product_keys
                    or any(_rel_tn == _rel_norm(_d) for _d in domain_names)
                    or any(_rel_tn == _rel_norm(_ak.split(".")[-1]) for _ak in attr_keys)
                )
                if not _rel_known:
"""

OLD_LINKED = (
    '                _rel_linked = [a for a in fk_attrs if tl in a.get("foreign_key_to", "").lower()'
    ' or tl in f"{a.get(\'domain\',\'\')}.{a.get(\'product\',\'\')}.{a.get(\'attribute\',\'\')}".lower()'
    ' or (_rtl != tl and (_rtl in a.get("foreign_key_to", "").lower()'
    ' or _rtl in f"{a.get(\'domain\',\'\')}.{a.get(\'product\',\'\')}.{a.get(\'attribute\',\'\')}".lower()))]\n'
)

NEW_LINKED = """                _rel_needles = {tl, _rtl} | _rel_canon
                _rel_linked = [a for a in fk_attrs
                               if any(_n and (_n in a.get("foreign_key_to", "").lower()
                                              or _n in f"{a.get('domain','')}.{a.get('product','')}.{a.get('attribute','')}".lower())
                                      for _n in _rel_needles)]
"""


def main():
    nb = json.load(open(NB))
    cell = nb["cells"][100]
    text = "".join(cell.get("source", []))

    if "_rel_canon" in text:
        print("already applied")
        return 0

    for old, new, label in ((OLD, NEW, "canonical resolution set"),
                            (OLD_LINKED, NEW_LINKED, "canonical FK match")):
        assert text.count(old) == 1, f"{label}: anchor count = {text.count(old)}, want 1"
        text = text.replace(old, new, 1)
        print("applied:", label)

    cell["source"] = text
    with open(NB, "w") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=True)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
